import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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
    1. Preprocesses and runs OCR on all attached inspection images.
    2. Decodes 1D/2D barcodes and cross-references controlled master catalog.
    3. Extracts structured statutory LMPC declarations from OCR.
    4. Evaluates all active LMPC 2011 legal rules (including Rule 18(2) Dual MRP).
    5. Generates structured Violations for any failed compliance checks.
    6. Links visual bounding box Evidence from OCR tokens and barcode regions.
    """
    # 1. Fetch inspection images
    img_stmt = (
        select(InspectionImage)
        .where(InspectionImage.inspection_id == inspection.id)
        .options(selectinload(InspectionImage.ocr_result))
        .order_by(InspectionImage.sequence_number.asc())
    )
    img_res = await db.execute(img_stmt)
    images = img_res.scalars().all()

    # 2. Run OCR & Barcode Decoding on attached images
    combined_raw_texts: List[str] = []
    all_tokens: List[Dict[str, Any]] = []
    detected_barcodes: List[BarcodeDetectionResult] = []

    for img in images:
        rel_path = img.image_url.lstrip("/")
        img_path = Path(rel_path)
        
        # Barcode extraction
        if img_path.exists():
            bcs = decode_barcodes_from_image(img_path, image_id=img.id)
            detected_barcodes.extend(bcs)

        # OCR extraction
        ocr_res = img.ocr_result
        if not ocr_res:
            if img_path.exists():
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

        if ocr_res:
            combined_raw_texts.append(ocr_res.raw_text)
            if ocr_res.tokens_data:
                all_tokens.extend(ocr_res.tokens_data)

    # 3. Extract structured declaration from combined OCR texts
    full_text = "\n".join(combined_raw_texts)
    extracted_fields, field_confidences = extract_declaration_from_ocr(full_text, all_tokens)

    # 4. Load or create Declaration (Preserve human verified values)
    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection.id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

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
            curr_conf = declaration.field_confidences or {}
            curr_conf.update(field_confidences)
            declaration.field_confidences = curr_conf
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

    curr_raw = declaration.raw_extractions or {}
    if barcode_payload:
        curr_raw["barcode_data"] = barcode_payload
    declaration.raw_extractions = curr_raw

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

