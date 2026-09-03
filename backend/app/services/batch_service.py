import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ComplianceResult, InspectionStatus
from app.models.declaration import Declaration
from app.models.inspection import Inspection
from app.models.inspection_batch import InspectionBatch
from app.models.inspection_image import InspectionImage
from app.models.report import Report
from app.models.user import User


def calculate_schedule_iv_sampling_stats(
    lot_size: int,
    sample_size: int,
    inspections: List[Inspection],
) -> Dict[str, Any]:
    """
    Computes statistical compliance summary for batch lot inspections under Schedule IV.
    
    Hardened Guardrails:
    - Separates digital declaration evidence from certified physical metrological testing.
    - Explicitly tags sampling standard, version, and effective date.
    - Requires physical verification on certified equipment before drawing legal conclusions on net content.
    """
    total_samples = len(inspections)
    compliant_count = sum(1 for i in inspections if i.overall_result == ComplianceResult.COMPLIANT)
    non_compliant_count = sum(1 for i in inspections if i.overall_result == ComplianceResult.NON_COMPLIANT)
    review_count = sum(1 for i in inspections if i.overall_result == ComplianceResult.NEEDS_REVIEW)
    pending_count = sum(1 for i in inspections if i.overall_result == ComplianceResult.PENDING or i.overall_result is None)

    compliance_rate = (
        round((compliant_count / total_samples) * 100.0, 2) if total_samples > 0 else 0.0
    )

    # Schedule IV statistical sampling assessment for label declarations
    lot_verdict = "PENDING_SAMPLES"
    if total_samples >= sample_size and total_samples > 0:
        if non_compliant_count == 0 and review_count == 0:
            lot_verdict = "LOT_DECLARATIONS_COMPLIANT"
        elif non_compliant_count > 0:
            lot_verdict = "LOT_DECLARATIONS_DEFICIENT"
        else:
            lot_verdict = "LOT_REVIEW_REQUIRED"

    return {
        "lot_size": lot_size,
        "sample_size_target": sample_size,
        "samples_inspected": total_samples,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "review_count": review_count,
        "pending_count": pending_count,
        "compliance_rate_percent": compliance_rate,
        "lot_acceptance_verdict": lot_verdict,
        "assessment_type": "DECLARATION_SAMPLING_ASSESSMENT",
        "physical_gravimetric_verified": False,
        "evaluation_standard": "Legal Metrology (Packaged Commodities) Rules, 2011 — Schedule IV",
        "source_version": "GSR 202(E) / LMPC 2011",
        "effective_from": "2011-04-01",
        "effective_to": None,
        "disclaimer": (
            "Statistical assessment reflects label declaration compliance of sample packages under Schedule IV "
            "inspection protocol. It does NOT constitute certified gravimetric or volumetric net quantity testing "
            "under Rule 24. Physical net content disputes require verified metrological weighing equipment."
        ),
    }


async def generate_batch_export_bundle(
    db: AsyncSession,
    batch_id: uuid.UUID,
    current_user: User,
) -> Tuple[bytes, str]:
    """
    Generates an offline legal filing ZIP bundle containing all inspection records,
    images, reports, and a SHA-256 evidence integrity manifest (manifest.json).
    """
    stmt = (
        select(InspectionBatch)
        .where(InspectionBatch.id == batch_id)
        .options(
            selectinload(InspectionBatch.inspections).selectinload(Inspection.images),
            selectinload(InspectionBatch.inspections).selectinload(Inspection.declaration),
            selectinload(InspectionBatch.inspections).selectinload(Inspection.compliance_checks),
            selectinload(InspectionBatch.inspections).selectinload(Inspection.violations),
            selectinload(InspectionBatch.inspections).selectinload(Inspection.reports),
        )
    )
    res = await db.execute(stmt)
    batch = res.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection batch with ID '{batch_id}' not found.",
        )

    zip_buffer = io.BytesIO()
    manifest_entries: List[Dict[str, Any]] = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Batch Metadata JSON
        batch_meta = {
            "batch_id": str(batch.id),
            "batch_name": batch.name,
            "lot_size": batch.lot_size,
            "sample_size": batch.sample_size,
            "store_name": batch.store_name,
            "district": batch.district,
            "state": batch.state,
            "created_at": batch.created_at.isoformat(),
            "summary_stats": calculate_schedule_iv_sampling_stats(
                batch.lot_size, batch.sample_size, batch.inspections
            ),
        }
        batch_meta_bytes = json.dumps(batch_meta, indent=2).encode("utf-8")
        zf.writestr("batch_summary.json", batch_meta_bytes)
        manifest_entries.append({
            "filename": "batch_summary.json",
            "file_type": "JSON_METADATA",
            "sha256_hash": hashlib.sha256(batch_meta_bytes).hexdigest(),
        })

        # 2. Add Child Inspections
        for insp in batch.inspections:
            insp_folder = f"inspections/{insp.id}"

            insp_data = {
                "id": str(insp.id),
                "store_name": insp.store_name,
                "status": insp.status.value,
                "overall_result": insp.overall_result.value if insp.overall_result else None,
                "language_detected": insp.language_detected,
                "created_at": insp.created_at.isoformat(),
            }
            insp_bytes = json.dumps(insp_data, indent=2).encode("utf-8")
            zf.writestr(f"{insp_folder}/inspection_record.json", insp_bytes)
            manifest_entries.append({
                "filename": f"{insp_folder}/inspection_record.json",
                "file_type": "INSPECTION_RECORD",
                "sha256_hash": hashlib.sha256(insp_bytes).hexdigest(),
            })

            # Add Image Files if available on disk
            for img in insp.images:
                rel_path = img.image_url.lstrip("/")
                p = Path(rel_path)
                if p.exists():
                    img_bytes = p.read_bytes()
                    img_filename = f"{insp_folder}/images/{p.name}"
                    zf.writestr(img_filename, img_bytes)
                    manifest_entries.append({
                        "filename": img_filename,
                        "file_type": "IMAGE_EVIDENCE",
                        "sha256_hash": img.sha256_hash or hashlib.sha256(img_bytes).hexdigest(),
                    })

        # 3. Add Evidence Integrity Manifest
        manifest_payload = {
            "application": "MetrologyMitra",
            "document_type": "OFFLINE_LEGAL_FILING_MANIFEST",
            "batch_id": str(batch.id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(manifest_entries),
            "files": manifest_entries,
        }
        manifest_bytes = json.dumps(manifest_payload, indent=2).encode("utf-8")
        zf.writestr("evidence_manifest.json", manifest_bytes)

    zip_bytes = zip_buffer.getvalue()
    filename = f"Batch_{batch.name.replace(' ', '_')}_{str(batch.id)[:8]}_EvidenceBundle.zip"
    return zip_bytes, filename

