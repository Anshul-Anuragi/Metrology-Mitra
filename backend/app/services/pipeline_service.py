import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
from app.core.enums import ComplianceResult, InspectionStatus
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.violation import Violation
from app.services.barcode_service import (
    decode_barcodes_from_image,
    lookup_master_catalog,
    verify_mrp_against_catalog,
    BarcodeDetectionResult,
)
from app.services.evidence_fusion_service import evidence_fusion_service
from app.services.evidence_service import link_evidence_for_inspection
from app.services.ocr import extract_declaration_from_ocr, ocr_service
from app.services.rule_engine import evaluate_inspection
from app.services.violation_service import generate_violations_for_inspection


async def run_full_inspection_pipeline(
    db: AsyncSession,
    inspection: Inspection,
) -> Tuple[Inspection, Declaration, List[ComplianceCheck], List[Violation], List[Evidence]]:
    """
    Unified end-to-end automated pipeline:
    1. Preprocesses and runs OCR on all attached inspection images via multi-variant evidence fusion.
    2. Decodes 1D/2D barcodes with multi-variant quorum and cross-references controlled master catalog.
    3. Extracts corroborated statutory LMPC declarations with conflict detection.
    4. Evaluates all active LMPC 2011 legal rules (including Rule 18(2) Dual MRP).
    5. Generates structured Violations for any failed compliance checks.
    6. Links visual bounding box Evidence from OCR tokens and barcode regions.
    """
    # 0. Mutation lock: Finalized inspections cannot be re-executed
    if inspection.status == InspectionStatus.COMPLETED:
        raise ValueError(f"Cannot re-run inspection pipeline on finalized inspection {inspection.id}")

    # 1. Fetch inspection images
    img_stmt = (
        select(InspectionImage)
        .where(InspectionImage.inspection_id == inspection.id)
        .options(selectinload(InspectionImage.ocr_result))
        .order_by(InspectionImage.sequence_number.asc())
    )
    img_res = await db.execute(img_stmt)
    images = img_res.scalars().all()

    # 2. Run OCR & Barcode Decoding on attached images (Multi-modal Evidence Fusion)
    combined_raw_texts: List[str] = []
    all_tokens: List[Dict[str, Any]] = []
    detected_barcodes: List[BarcodeDetectionResult] = []
    fused_evidence_payload: Optional[Dict[str, Any]] = None

    for img in images:
        raw_url = img.image_url
        if Path(raw_url).exists():
            img_path = Path(raw_url)
        else:
            rel_path = raw_url.lstrip("/")
            img_path = Path(rel_path)
            if not img_path.exists():
                alt_path = Path("/app") / rel_path
                if alt_path.exists():
                    img_path = alt_path

        ocr_res = img.ocr_result

        # Run multi-variant evidence fusion if photograph exists on disk
        if img_path.exists():
            try:
                packet = await evidence_fusion_service.fuse_evidence(img_path)
                fused_evidence_payload = packet.to_dict()

                # Add barcodes from quorum
                for b_val in packet.barcode_quorum.get("all_barcodes", []):
                    if not any(d.value == b_val for d in detected_barcodes):
                        fmt = packet.barcode_quorum.get("winning_format") or "EAN_13"
                        detected_barcodes.append(
                            BarcodeDetectionResult(
                                value=b_val,
                                format=fmt,
                                bounding_box=None,
                                source_image_id=img.id,
                            )
                        )

                # Persist primary variant OCR if not yet saved
                ocr_res = img.ocr_result
                if not ocr_res:
                    consensus = packet.ocr_consensus.get("consensus", {})
                    primary_var_name = consensus.get("primary_variant", "NORMALIZED_ORIGINAL")
                    variants_dict = packet.ocr_consensus.get("variants_results", {})
                    primary_var_data = variants_dict.get(primary_var_name, {})
                    ocr_res = OCRResult(
                        image_id=img.id,
                        raw_text=primary_var_data.get("raw_text", ""),
                        confidence=primary_var_data.get("confidence", 0.85),
                        engine="tesseract_multi_variant",
                        tokens_data=primary_var_data.get("tokens_data", []),
                        processing_time_ms=primary_var_data.get("processing_time_ms", 10),
                    )
                    db.add(ocr_res)
                    await db.commit()
                    await db.refresh(ocr_res)
                    img.ocr_result = ocr_res

            except Exception:
                # Fallback to standard baseline decoding if fusion encountered an edge case
                bcs = decode_barcodes_from_image(img_path, image_id=img.id)
                detected_barcodes.extend(bcs)
        else:
            # Fallback for mock/virtual paths
            pass

        # Standard OCR resolution fallback if still not populated
        if not ocr_res and img_path.exists():
            ocr_data = await ocr_service.extract_text(img_path)
            ocr_res = OCRResult(
                image_id=img.id,
                raw_text=ocr_data.raw_text,
                confidence=ocr_data.confidence,
                engine=ocr_data.engine,
                tokens_data=ocr_data.tokens_data,
                processing_time_ms=ocr_data.processing_time_ms,
            )
            db.add(ocr_res)
            await db.commit()
            await db.refresh(ocr_res)
            img.ocr_result = ocr_res

        if ocr_res:
            combined_raw_texts.append(ocr_res.raw_text)
            if ocr_res.tokens_data:
                all_tokens.extend(ocr_res.tokens_data)

    # 3. Load or create Declaration (Preserve human verified values)
    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection.id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    if not fused_evidence_payload and declaration and declaration.raw_extractions:
        fused_evidence_payload = declaration.raw_extractions.get("fused_evidence")

    # Extract structured declaration from combined OCR texts and fused evidence
    full_text = "\n".join(combined_raw_texts)
    extracted_fields, field_confidences = extract_declaration_from_ocr(full_text, all_tokens)

    # Enrich with multi-variant declaration fusion if available
    if fused_evidence_payload:
        fused_decls = fused_evidence_payload.get("fused_declarations", {}).get("fused_fields", {})
        for f_name, f_data in fused_decls.items():
            if f_data.get("evidence_state") in ("CONFIRMED", "PROBABLE") and f_data.get("fused_value"):
                extracted_fields[f_name] = f_data["fused_value"]
                field_confidences[f_name] = f_data.get("aggregate_confidence", 0.85)
            elif f_data.get("evidence_state") == "CONFLICTING":
                # Cap confidence to reflect multi-variant perception contradiction
                field_confidences[f_name] = min(0.35, field_confidences.get(f_name, 0.35))

    if not declaration:
        declaration = Declaration(
            inspection_id=inspection.id,
            is_human_verified=False,
            field_confidences=field_confidences,
            raw_extractions={"ocr_extracted": extracted_fields},
        )
        for field, value in extracted_fields.items():
            if hasattr(declaration, field) and value is not None:
                setattr(declaration, field, value)
        db.add(declaration)
    else:
        if declaration.is_human_verified:
            # Only populate currently null fields
            for field, value in extracted_fields.items():
                if hasattr(declaration, field) and getattr(declaration, field) is None:
                    setattr(declaration, field, value)
        else:
            for field, value in extracted_fields.items():
                if hasattr(declaration, field) and value is not None:
                    setattr(declaration, field, value)
            curr_conf = dict(declaration.field_confidences or {})
            curr_conf.update(field_confidences)
            declaration.field_confidences = curr_conf
            flag_modified(declaration, "field_confidences")
            declaration.is_human_verified = False

    # 4b. Perform Master Catalog Cross-Referencing & Price Verification
    barcode_payload = None
    if detected_barcodes:
        primary_bc = detected_barcodes[0]
        catalog_product = lookup_master_catalog(primary_bc.value)
        observed_mrp_val = declaration.mrp or extracted_fields.get("mrp")
        comp_status, comp_reason, obs_num, cat_num = verify_mrp_against_catalog(observed_mrp_val, catalog_product)

        barcode_payload = {
            "value": primary_bc.value,
            "format": primary_bc.format,
            "bounding_box": primary_bc.bounding_box,
            "source_image_id": str(primary_bc.source_image_id) if primary_bc.source_image_id else None,
            "catalog_match": {
                "matched": catalog_product is not None,
                "product_name": catalog_product.get("commodity_name") if catalog_product else None,
                "brand_name": catalog_product.get("brand_name") if catalog_product else None,
                "catalog_mrp": cat_num,
                "observed_mrp": obs_num,
                "discrepancy": comp_status,
                "reason": comp_reason,
            } if catalog_product else {
                "matched": False,
                "discrepancy": "NO_CATALOG_MATCH",
                "reason": f"Barcode {primary_bc.value} is not registered in the controlled demo master catalog.",
            },
        }

    curr_raw = dict(declaration.raw_extractions or {})
    if barcode_payload:
        curr_raw["barcode_data"] = barcode_payload
    if fused_evidence_payload:
        curr_raw["fused_evidence"] = fused_evidence_payload
        conflicts = [
            fn for fn, fd in fused_evidence_payload.get("fused_declarations", {}).get("fused_fields", {}).items()
            if fd.get("evidence_state") == "CONFLICTING"
        ]
        if conflicts:
            curr_raw["conflicting_fields"] = conflicts
    declaration.raw_extractions = curr_raw
    flag_modified(declaration, "raw_extractions")

    await db.commit()
    await db.refresh(declaration)

    # 5. Evaluate Rule Engine (including LMPC-R18-DUAL-MRP)
    overall_result, initial_checks = await evaluate_inspection(db, inspection, declaration)

    # Re-fetch checks to ensure clean session state
    raw_checks_stmt = select(ComplianceCheck).where(ComplianceCheck.inspection_id == inspection.id)
    raw_checks = (await db.execute(raw_checks_stmt)).scalars().all()

    # 6. Generate Violations
    violations = await generate_violations_for_inspection(db, inspection.id, raw_checks)

    # 7. Link Visual Evidence
    evidence_items = await link_evidence_for_inspection(db, inspection.id, raw_checks, violations)

    # Add Barcode Evidence item if available
    if detected_barcodes and detected_barcodes[0].bounding_box:
        primary_bc = detected_barcodes[0]
        # Find if check for Rule 18 exists
        r18_check = next((c for c in raw_checks if getattr(c.legal_rule, "rule_code", "") == "LMPC-R18-DUAL-MRP"), None)
        bc_ev = Evidence(
            inspection_id=inspection.id,
            compliance_check_id=r18_check.id if r18_check else None,
            image_id=primary_bc.source_image_id,
            evidence_type="BOUNDING_BOX",
            description=f"Decoded {primary_bc.format} Barcode: {primary_bc.value}",
            bounding_box=primary_bc.bounding_box,
        )
        db.add(bc_ev)
        await db.commit()

    # 8. Re-fetch all checks and violations with eager loading of all child relations
    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.inspection_id == inspection.id)
        .options(
            selectinload(ComplianceCheck.legal_rule),
            selectinload(ComplianceCheck.violations).selectinload(Violation.evidence_items),
            selectinload(ComplianceCheck.evidence_items),
        )
        .order_by(ComplianceCheck.checked_at.asc())
    )
    checks = (await db.execute(checks_stmt)).scalars().all()

    viols_stmt = (
        select(Violation)
        .where(Violation.inspection_id == inspection.id)
        .options(selectinload(Violation.evidence_items))
        .order_by(Violation.created_at.asc())
    )
    violations = (await db.execute(viols_stmt)).scalars().all()

    ev_stmt = (
        select(Evidence)
        .where(Evidence.inspection_id == inspection.id)
        .order_by(Evidence.created_at.asc())
    )
    evidence_items = (await db.execute(ev_stmt)).scalars().all()

    await db.refresh(inspection)
    return inspection, declaration, checks, violations, evidence_items

