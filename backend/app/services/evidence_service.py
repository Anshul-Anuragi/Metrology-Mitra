import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import CheckResult, EvidenceType
from app.models.compliance_check import ComplianceCheck
from app.models.evidence import Evidence
from app.models.inspection_image import InspectionImage
from app.models.ocr_result import OCRResult
from app.models.violation import Violation


def _find_tokens_bounding_box(
    tokens_data: List[Dict[str, Any]], search_terms: List[str]
) -> Optional[Dict[str, Any]]:
    """Finds enclosing bounding box for matching words in OCR tokens."""
    if not tokens_data:
        return None

    matched_boxes = []
    terms = []
    for st in search_terms:
        if st and st != "NOT DECLARED":
            for word in st.replace("\n", " ").split():
                clean_w = word.strip(":,.-/₹()").lower()
                if len(clean_w) >= 2 and clean_w not in {"the", "and", "for", "with", "all"}:
                    terms.append(clean_w)

    if not terms:
        return None

    for token in tokens_data:
        word = str(token.get("text", "")).strip(":,.-/₹()").lower()
        bbox = token.get("bbox")  # [left, top, width, height]
        if bbox and word and any(term in word or word in term for term in terms):
            matched_boxes.append(bbox)

    if not matched_boxes:
        return None

    min_x = min(b[0] for b in matched_boxes)
    min_y = min(b[1] for b in matched_boxes)
    max_x = max(b[0] + b[2] for b in matched_boxes)
    max_y = max(b[1] + b[3] for b in matched_boxes)

    return {
        "x": int(min_x),
        "y": int(min_y),
        "width": int(max_x - min_x),
        "height": int(max_y - min_y),
    }


async def link_evidence_for_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    checks: List[ComplianceCheck],
    violations: List[Violation],
) -> List[Evidence]:
    """
    Extracts spatial bounding boxes from OCR token results and links visual evidence
    to compliance checks and generated violations.
    """
    # Delete existing evidence for this inspection
    del_stmt = delete(Evidence).where(Evidence.inspection_id == inspection_id)
    await db.execute(del_stmt)

    # Fetch all OCR results and inspection images directly for this inspection
    ocr_stmt = (
        select(OCRResult)
        .join(InspectionImage, OCRResult.image_id == InspectionImage.id)
        .where(InspectionImage.inspection_id == inspection_id)
    )
    ocr_results = (await db.execute(ocr_stmt)).scalars().all()

    img_stmt = select(InspectionImage).where(InspectionImage.inspection_id == inspection_id)
    images = (await db.execute(img_stmt)).scalars().all()
    primary_image_id = images[0].id if images else None

    # Map violations by compliance_check_id
    violation_map = {v.compliance_check_id: v for v in violations}

    evidence_items: List[Evidence] = []

    for check in checks:
        matched_box = None
        matched_image_id = None

        search_keywords = []
        if check.field_name:
            search_keywords.append(check.field_name)
        if check.observed_value and check.observed_value != "NOT DECLARED":
            search_keywords.append(check.observed_value)

        for ocr in ocr_results:
            if ocr.tokens_data:
                bbox = _find_tokens_bounding_box(ocr.tokens_data, search_keywords)
                if bbox:
                    matched_box = bbox
                    matched_image_id = ocr.image_id
                    break

        v_record = violation_map.get(check.id)

        if matched_box and matched_image_id:
            ev = Evidence(
                inspection_id=inspection_id,
                compliance_check_id=check.id,
                violation_id=v_record.id if v_record else None,
                image_id=matched_image_id,
                evidence_type=EvidenceType.BOUNDING_BOX,
                description=f"Visual OCR region for {check.field_name or 'declaration'}: '{check.observed_value}'",
                bounding_box=matched_box,
            )
            evidence_items.append(ev)
            db.add(ev)
        else:
            desc = (
                f"Absence of mandatory declaration '{check.field_name}' verified across package photographs."
                if check.result == CheckResult.FAIL
                else f"Declaration text verified: {check.observed_value}"
            )
            ev = Evidence(
                inspection_id=inspection_id,
                compliance_check_id=check.id,
                violation_id=v_record.id if v_record else None,
                image_id=primary_image_id,
                evidence_type=EvidenceType.OCR_SNIPPET,
                description=desc,
                bounding_box=None,
            )
            evidence_items.append(ev)
            db.add(ev)

    await db.commit()
    for ev in evidence_items:
        await db.refresh(ev)

    return evidence_items

