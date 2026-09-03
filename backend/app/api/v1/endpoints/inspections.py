import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.core.enums import (
    CheckResult,
    ComplianceResult,
    ImageType,
    InspectionStatus,
    ReportType,
    UserRole,
    ViolationSeverity,
    ViolationStatus,
)
from app.models.audit_log import AuditLog
from app.models.compliance_check import ComplianceCheck
from app.models.declaration import Declaration
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.legal_rule import LegalRule
from app.models.ocr_result import OCRResult
from app.models.product import Product
from app.models.report import Report
from app.models.user import User
from app.models.violation import Violation

from app.schemas.declaration import DeclarationResponse, DeclarationUpdate
from app.schemas.image_quality import ImageQualityResponse
from app.schemas.inspection import (
    EvaluationResponse,
    InspectionCreate,
    InspectionDetailResponse,
    InspectionImageResponse,
    InspectionResponse,
)
from app.schemas.listing import (
    DigitalListingCrossCheckResponse,
    DigitalListingInput,
    DigitalListingItemResponse,
)
from app.schemas.measurement import MeasurementInput, MeasurementResponse
from app.schemas.ocr import OCRExtractionResponse
from app.schemas.pipeline import PipelineExecutionResponse
from app.schemas.report import ReportCreate, ReportResponse
from app.schemas.review import (
    AuditLogResponse,
    FinalizeInspectionRequest,
    ReviewSubmissionRequest,
    ReviewWorkspaceResponse,
)
from app.schemas.violation import ComplianceCheckResponse, EvidenceResponse, ViolationResponse

from app.services.evidence_service import link_evidence_for_inspection
from app.services.image_quality import assess_image_quality
from app.services.listing_service import DigitalListingData, cross_check_digital_listing
from app.services.measurement_service import evaluate_reference_assisted_measurement
from app.services.ocr.extractor import extract_declaration_from_ocr
from app.services.ocr.tesseract_ocr import ocr_service
from app.services.pipeline_service import run_full_inspection_pipeline
from app.services.report_service import create_inspection_report
from app.services.rule_engine import evaluate_inspection
from app.services.storage import storage_service
from app.services.violation_service import generate_violations_for_inspection

router = APIRouter()


def check_inspection_not_completed(inspection: Inspection) -> None:
    """
    Enforces backend mutation lock.
    Rejects any modification requests on finalized (COMPLETED) inspections.
    """
    if inspection.status == InspectionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inspection is finalized (COMPLETED) and locked against further mutations.",
        )


async def get_authorized_inspection(
    inspection_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
    load_relations: bool = False,
) -> Inspection:
    """
    Retrieves inspection and verifies RBAC ownership/permissions.
    """
    if not load_relations:
        stmt = select(Inspection).where(Inspection.id == inspection_id)
    else:
        stmt = (
            select(Inspection)
            .where(Inspection.id == inspection_id)
            .options(
                selectinload(Inspection.inspector),
                selectinload(Inspection.product),
                selectinload(Inspection.images).selectinload(InspectionImage.ocr_result),
                selectinload(Inspection.declaration),
                selectinload(Inspection.compliance_checks).selectinload(ComplianceCheck.legal_rule),
                selectinload(Inspection.violations).selectinload(Violation.evidence_items),
                selectinload(Inspection.evidence_items),
            )
        )

    result = await db.execute(stmt)
    inspection = result.scalar_one_or_none()

    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID '{inspection_id}' not found.",
        )

    # RBAC Enforcement: Inspectors can only access their own inspections
    if current_user.role == UserRole.INSPECTOR and inspection.inspector_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: You do not have permission to access this inspection.",
        )

    return inspection


async def log_audit_event(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    actor_id: Optional[uuid.UUID],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Records a chronological audit trail event for inspection lifecycle actions.
    """
    audit = AuditLog(
        inspection_id=inspection_id,
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata_json,
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    return audit


# -----------------------------------------------------------------------------
# CORE INSPECTION CRUD
# -----------------------------------------------------------------------------

@router.post("/", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED, tags=["Inspections"])
async def create_inspection(
    inspection_in: InspectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = Inspection(
        inspector_id=current_user.id,
        product_id=inspection_in.product_id,
        store_name=inspection_in.store_name,
        store_address=inspection_in.store_address,
        district=inspection_in.district,
        state=inspection_in.state,
        gps_latitude=inspection_in.gps_latitude,
        gps_longitude=inspection_in.gps_longitude,
        status=InspectionStatus.CREATED,
        overall_result=ComplianceResult.PENDING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(inspection)
    await db.flush()

    await log_audit_event(
        db=db,
        inspection_id=inspection.id,
        actor_id=current_user.id,
        action="INSPECTION_CREATED",
        entity_type="Inspection",
        entity_id=inspection.id,
        metadata_json={"store_name": inspection.store_name, "district": inspection.district, "state": inspection.state},
    )

    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("/", response_model=List[InspectionResponse], tags=["Inspections"])
async def list_inspections(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Limit for pagination"),
    status_filter: InspectionStatus | None = Query(None, description="Filter by inspection status"),
    result_filter: ComplianceResult | None = Query(None, description="Filter by compliance result"),
    state_filter: str | None = Query(None, description="Filter by state name"),
    district_filter: str | None = Query(None, description="Filter by district name"),
    search: str | None = Query(None, description="Search store name or address"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Inspection)
    if current_user.role == UserRole.INSPECTOR:
        stmt = stmt.where(Inspection.inspector_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Inspection.status == status_filter)
    if result_filter:
        stmt = stmt.where(Inspection.overall_result == result_filter)
    if state_filter:
        stmt = stmt.where(Inspection.state.ilike(f"%{state_filter}%"))
    if district_filter:
        stmt = stmt.where(Inspection.district.ilike(f"%{district_filter}%"))
    if search:
        stmt = stmt.where(
            (Inspection.store_name.ilike(f"%{search}%")) | (Inspection.store_address.ilike(f"%{search}%"))
        )

    stmt = stmt.order_by(Inspection.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inspection_id}", response_model=InspectionDetailResponse, tags=["Inspections"])
async def get_inspection_detail(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_authorized_inspection(inspection_id, current_user, db, load_relations=True)


@router.patch("/{inspection_id}/declaration", response_model=DeclarationResponse, tags=["Inspections"])
async def update_inspection_declaration(
    inspection_id: uuid.UUID,
    decl_in: DeclarationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    result = await db.execute(stmt)
    declaration = result.scalar_one_or_none()

    if not declaration:
        declaration = Declaration(inspection_id=inspection_id)
        db.add(declaration)

    update_data = decl_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(declaration, field, value)

    declaration.is_human_verified = True

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="DECLARATION_UPDATED",
        entity_type="Declaration",
        entity_id=declaration.id,
        metadata_json={"updated_fields": list(update_data.keys()), "is_human_verified": True},
    )

    await db.commit()
    await db.refresh(declaration)
    return declaration


# -----------------------------------------------------------------------------
# IMAGE INGESTION & QUALITY GATE
# -----------------------------------------------------------------------------

@router.post("/{inspection_id}/images", response_model=InspectionImageResponse, status_code=status.HTTP_201_CREATED, tags=["Inspections"])
async def upload_inspection_image(
    inspection_id: uuid.UUID,
    file: UploadFile = File(..., description="Image file to upload"),
    image_type: ImageType = Form(ImageType.OTHER, description="Type of image (FRONT, BACK, LABEL, etc.)"),
    sequence_number: int | None = Form(None, description="Order/sequence of the image in inspection"),
    resolution_width: int | None = Form(None, description="Image pixel width"),
    resolution_height: int | None = Form(None, description="Image pixel height"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if sequence_number is None:
        seq_stmt = select(func.coalesce(func.max(InspectionImage.sequence_number), 0)).where(
            InspectionImage.inspection_id == inspection_id
        )
        max_seq = (await db.execute(seq_stmt)).scalar_one()
        sequence_number = max_seq + 1
    else:
        check_seq_stmt = select(InspectionImage).where(
            InspectionImage.inspection_id == inspection_id,
            InspectionImage.sequence_number == sequence_number,
        )
        existing_seq = (await db.execute(check_seq_stmt)).scalar_one_or_none()
        if existing_seq:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sequence number {sequence_number} already exists for this inspection.",
            )

    saved_url, sha256_hash = await storage_service.save_image(
        file_bytes=file_bytes,
        filename=file.filename or "image.jpg",
        inspection_id=inspection.id,
        content_type=file.content_type,
    )

    image_record = InspectionImage(
        inspection_id=inspection.id,
        image_url=saved_url,
        image_type=image_type,
        sequence_number=sequence_number,
        resolution_width=resolution_width,
        resolution_height=resolution_height,
        sha256_hash=sha256_hash,
    )
    db.add(image_record)
    await db.flush()

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="IMAGE_UPLOADED",
        entity_type="InspectionImage",
        entity_id=image_record.id,
        metadata_json={
            "image_type": image_type.value,
            "sequence_number": sequence_number,
            "sha256_hash": sha256_hash,
        },
    )

    await db.commit()
    await db.refresh(image_record)
    return image_record


@router.get("/{inspection_id}/images", response_model=List[InspectionImageResponse], tags=["Inspections"])
async def list_inspection_images(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = (
        select(InspectionImage)
        .where(InspectionImage.inspection_id == inspection_id)
        .order_by(InspectionImage.sequence_number.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/{inspection_id}/images/{image_id}/diagnostics",
    response_model=ImageQualityResponse,
    tags=["Image Diagnostics"],
)
@router.post(
    "/{inspection_id}/images/{image_id}/quality-gate",
    response_model=ImageQualityResponse,
    tags=["Image Diagnostics"],
)
async def get_image_quality_diagnostics(
    inspection_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)

    stmt = select(InspectionImage).where(InspectionImage.id == image_id)
    img_res = await db.execute(stmt)
    image = img_res.scalar_one_or_none()

    if not image or image.inspection_id != inspection_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found for inspection '{inspection_id}'.",
        )

    rel_path = image.image_url.lstrip("/")
    img_path = Path(rel_path)
    if not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file '{image.image_url}' could not be located on storage.",
        )

    quality_res = assess_image_quality(img_path)
    image.quality_gate_result = quality_res.to_dict()
    await db.commit()

    return ImageQualityResponse(
        image_id=image_id,
        width=quality_res.width,
        height=quality_res.height,
        blur_score=quality_res.blur_score,
        blur_status=quality_res.blur_status.value,
        glare_ratio=quality_res.glare_ratio,
        glare_status=quality_res.glare_status.value,
        glare_detected=quality_res.glare_detected,
        exposure_mean=quality_res.exposure_mean,
        exposure_status=quality_res.exposure_status.value,
        resolution_status=quality_res.resolution_status.value,
        gate_decision=quality_res.gate_decision.value,
        overall_status=quality_res.overall_status.value,
        is_acceptable=quality_res.is_acceptable,
        guidance_message=quality_res.guidance_message,
        actionable_reasons=quality_res.actionable_reasons,
        sha256_hash=image.sha256_hash,
    )


# -----------------------------------------------------------------------------
# OCR, RULE ENGINE & PIPELINE
# -----------------------------------------------------------------------------

@router.post(
    "/{inspection_id}/images/{image_id}/ocr",
    response_model=OCRExtractionResponse,
    tags=["OCR & Perception"],
)
async def process_inspection_image_ocr(
    inspection_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    stmt = select(InspectionImage).where(InspectionImage.id == image_id)
    img_res = await db.execute(stmt)
    image = img_res.scalar_one_or_none()

    if not image or image.inspection_id != inspection_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found for inspection '{inspection_id}'.",
        )

    rel_path = image.image_url.lstrip("/")
    img_path = Path(rel_path)
    if not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image file '{image.image_url}' could not be located on storage.",
        )

    try:
        ocr_res_data = await ocr_service.extract_text(img_path)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image processing error: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR execution failed: {e}",
        )

    ocr_stmt = select(OCRResult).where(OCRResult.image_id == image_id)
    existing_ocr = (await db.execute(ocr_stmt)).scalar_one_or_none()

    if not existing_ocr:
        ocr_result = OCRResult(
            image_id=image_id,
            raw_text=ocr_res_data.raw_text,
            confidence=ocr_res_data.confidence,
            engine=ocr_res_data.engine,
            tokens_data=ocr_res_data.tokens_data,
            processing_time_ms=ocr_res_data.processing_time_ms,
        )
        db.add(ocr_result)
    else:
        ocr_result = existing_ocr
        ocr_result.raw_text = ocr_res_data.raw_text
        ocr_result.confidence = ocr_res_data.confidence
        ocr_result.engine = ocr_res_data.engine
        ocr_result.tokens_data = ocr_res_data.tokens_data
        ocr_result.processing_time_ms = ocr_res_data.processing_time_ms

    extracted_fields, field_confidences = extract_declaration_from_ocr(
        ocr_res_data.raw_text, ocr_res_data.tokens_data
    )

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    if not declaration:
        declaration = Declaration(
            inspection_id=inspection_id,
            is_human_verified=False,
            field_confidences=field_confidences,
            raw_extractions={
                "ocr_extracted": extracted_fields,
                "last_image_id": str(image_id),
            },
        )
        for field, value in extracted_fields.items():
            if hasattr(declaration, field) and value is not None:
                setattr(declaration, field, value)
        db.add(declaration)
    else:
        raw_extractions = declaration.raw_extractions or {}
        raw_extractions[f"image_{image_id}_ocr"] = extracted_fields
        declaration.raw_extractions = raw_extractions

        if declaration.is_human_verified:
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

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="OCR_PROCESSED",
        entity_type="OCRResult",
        entity_id=ocr_result.id,
        metadata_json={"image_id": str(image_id), "engine": ocr_res_data.engine, "confidence": ocr_res_data.confidence},
    )

    await db.commit()
    await db.refresh(ocr_result)
    await db.refresh(declaration)

    return OCRExtractionResponse(
        inspection_id=inspection_id,
        image_id=image_id,
        ocr_result=ocr_result,
        extracted_fields=extracted_fields,
        field_confidences=field_confidences,
        declaration=declaration,
    )


@router.post("/{inspection_id}/evaluate", response_model=EvaluationResponse, tags=["Rule Engine"])
async def run_inspection_evaluation(
    inspection_id: uuid.UUID,
    channel: str = Query("BOTH", description="PHYSICAL_PACKAGE | ECOMMERCE | BOTH"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    decl_res = await db.execute(decl_stmt)
    declaration = decl_res.scalar_one_or_none()

    overall_result, initial_checks = await evaluate_inspection(
        db, inspection, declaration, channel=channel
    )

    raw_checks_stmt = select(ComplianceCheck).where(ComplianceCheck.inspection_id == inspection_id)
    raw_checks = (await db.execute(raw_checks_stmt)).scalars().all()

    violations = await generate_violations_for_inspection(db, inspection.id, raw_checks)
    evidence_items = await link_evidence_for_inspection(db, inspection.id, raw_checks, violations)

    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.inspection_id == inspection_id)
        .options(
            selectinload(ComplianceCheck.legal_rule),
            selectinload(ComplianceCheck.violations).selectinload(Violation.evidence_items),
            selectinload(ComplianceCheck.evidence_items),
        )
        .order_by(ComplianceCheck.checked_at.asc())
    )
    checks_res = await db.execute(checks_stmt)
    loaded_checks = checks_res.scalars().all()

    passed_count = sum(1 for c in loaded_checks if c.result == CheckResult.PASS)
    failed_count = sum(1 for c in loaded_checks if c.result == CheckResult.FAIL)
    review_count = sum(1 for c in loaded_checks if c.result == CheckResult.REVIEW)

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="RULES_EVALUATED",
        entity_type="Inspection",
        entity_id=inspection.id,
        metadata_json={
            "overall_result": overall_result.value,
            "total_checks": len(loaded_checks),
            "failed_checks": failed_count,
            "review_checks": review_count,
            "channel": channel,
        },
    )
    await db.commit()

    return EvaluationResponse(
        inspection_id=inspection.id,
        overall_result=overall_result,
        status=inspection.status,
        total_checks=len(loaded_checks),
        passed_checks=passed_count,
        failed_checks=failed_count,
        review_checks=review_count,
        checks=loaded_checks,
    )


@router.post(
    "/{inspection_id}/pipeline",
    response_model=PipelineExecutionResponse,
    tags=["Inspection Pipeline"],
)
async def execute_inspection_pipeline(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    (
        updated_insp,
        decl,
        checks,
        violations,
        evidence_items,
    ) = await run_full_inspection_pipeline(db, inspection)

    passed_count = sum(1 for c in checks if c.result == CheckResult.PASS)
    failed_count = sum(1 for c in checks if c.result == CheckResult.FAIL)
    review_count = sum(1 for c in checks if c.result == CheckResult.REVIEW)

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="PIPELINE_EXECUTED",
        entity_type="Inspection",
        entity_id=inspection.id,
        metadata_json={
            "overall_result": updated_insp.overall_result.value if updated_insp.overall_result else None,
            "total_checks": len(checks),
            "total_violations": len(violations),
        },
    )
    await db.commit()

    return PipelineExecutionResponse(
        inspection_id=updated_insp.id,
        status=updated_insp.status,
        overall_result=updated_insp.overall_result,
        declaration=decl,
        total_checks=len(checks),
        passed_checks=passed_count,
        failed_checks=failed_count,
        review_checks=review_count,
        total_violations=len(violations),
        total_evidence_items=len(evidence_items),
        checks=checks,
        violations=violations,
        evidence_items=evidence_items,
    )


# -----------------------------------------------------------------------------
# DIGITAL LISTING & MEASUREMENT ENDPOINTS
# -----------------------------------------------------------------------------

@router.post("/{inspection_id}/listing", response_model=DigitalListingCrossCheckResponse, tags=["Digital Listing Cross-Check"])
async def submit_digital_listing(
    inspection_id: uuid.UUID,
    listing_in: DigitalListingInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits controlled digital marketplace listing data and cross-checks against physical package declarations.
    """
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    if not declaration:
        declaration = Declaration(inspection_id=inspection_id)
        db.add(declaration)

    listing_dict = listing_in.model_dump(exclude_unset=True)
    declaration.digital_listing_data = listing_dict

    d_listing = DigitalListingData(
        title=listing_in.title,
        description=listing_in.description,
        price=listing_in.price,
        country_of_origin=listing_in.country_of_origin,
        net_quantity=listing_in.net_quantity,
        manufacturer_name=listing_in.manufacturer_name,
        listing_url=listing_in.listing_url,
        captured_at=datetime.now(timezone.utc),
    )
    report = cross_check_digital_listing(d_listing, declaration)

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="DIGITAL_LISTING_CROSSCHECKED",
        entity_type="Declaration",
        entity_id=declaration.id,
        metadata_json={
            "has_contradictions": report.has_contradictions,
            "verdict": report.summary_verdict.value,
        },
    )

    await db.commit()
    await db.refresh(declaration)

    return DigitalListingCrossCheckResponse(
        inspection_id=inspection_id,
        has_contradictions=report.has_contradictions,
        summary_verdict=report.summary_verdict.value,
        summary_reason=report.summary_reason,
        items=[
            DigitalListingItemResponse(
                field=it.field,
                listing_value=it.listing_value,
                package_value=it.package_value,
                status=it.status,
                finding=it.finding,
                result=it.result.value,
            )
            for it in report.items
        ],
        listing_data=listing_dict,
    )


@router.post("/{inspection_id}/measurement", response_model=MeasurementResponse, tags=["Measurement Assistant"])
async def submit_numeral_measurement(
    inspection_id: uuid.UUID,
    measurement_in: MeasurementInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates reference-assisted physical numeral height under Rule 7 and Schedule II Table 1.
    """
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    if not declaration:
        declaration = Declaration(inspection_id=inspection_id)
        db.add(declaration)

    evidence = evaluate_reference_assisted_measurement(
        pdp_area_cm2=measurement_in.pdp_area_cm2,
        pixel_height=measurement_in.pixel_height,
        pixel_scale_mm_per_px=measurement_in.pixel_scale_mm_per_px,
        scale_source=measurement_in.scale_source or "REFERENCE_OBJECT",
        scale_confidence=measurement_in.scale_confidence or 0.85,
        is_blown_or_moulded=measurement_in.is_blown_or_moulded or False,
    )

    m_data = {
        "pdp_area_cm2": measurement_in.pdp_area_cm2,
        "pixel_height": measurement_in.pixel_height,
        "pixel_scale_mm_per_px": measurement_in.pixel_scale_mm_per_px,
        "scale_source": measurement_in.scale_source,
        "scale_confidence": measurement_in.scale_confidence,
        "physical_height_mm": evidence.physical_height_mm,
        "threshold_mm": evidence.threshold_mm,
        "result": evidence.result.value,
        "reason": evidence.reason,
    }
    declaration.measurement_data = m_data
    if measurement_in.pdp_area_cm2:
        declaration.pdp_area_sq_cm = measurement_in.pdp_area_cm2

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="MEASUREMENT_RECORDED",
        entity_type="Declaration",
        entity_id=declaration.id,
        metadata_json=m_data,
    )

    await db.commit()
    await db.refresh(declaration)

    return MeasurementResponse(
        inspection_id=inspection_id,
        pixel_height=evidence.pixel_height,
        physical_height_mm=evidence.physical_height_mm,
        scale_source=evidence.scale_source,
        scale_confidence=evidence.scale_confidence,
        measurement_confidence=evidence.measurement_confidence,
        threshold_mm=evidence.threshold_mm,
        pdp_area_cm2=evidence.pdp_area_cm2,
        result=evidence.result.value,
        reason=evidence.reason,
        is_prototype=True,
    )


# -----------------------------------------------------------------------------
# INSPECTOR REVIEW & FINALIZATION WORKSPACE
# -----------------------------------------------------------------------------

@router.get("/{inspection_id}/review", response_model=ReviewWorkspaceResponse, tags=["Inspector Review"])
async def get_inspection_review_workspace(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns full adjudication workspace data including blocking reasons and audit trail.
    """
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=True)

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.inspection_id == inspection_id)
        .options(
            selectinload(ComplianceCheck.legal_rule),
            selectinload(ComplianceCheck.violations),
            selectinload(ComplianceCheck.evidence_items),
        )
        .order_by(ComplianceCheck.checked_at.asc())
    )
    checks = (await db.execute(checks_stmt)).scalars().all()

    violations_stmt = select(Violation).where(Violation.inspection_id == inspection_id).order_by(Violation.created_at.asc())
    violations = (await db.execute(violations_stmt)).scalars().all()

    evidence_stmt = select(Evidence).where(Evidence.inspection_id == inspection_id).order_by(Evidence.created_at.asc())
    evidence_items = (await db.execute(evidence_stmt)).scalars().all()

    audit_stmt = select(AuditLog).where(AuditLog.inspection_id == inspection_id).order_by(AuditLog.created_at.asc())
    audit_logs = (await db.execute(audit_stmt)).scalars().all()

    passed_count = sum(1 for c in checks if c.result == CheckResult.PASS)
    failed_count = sum(1 for c in checks if c.result == CheckResult.FAIL)
    review_count = sum(1 for c in checks if c.result == CheckResult.REVIEW)

    # Determine blocking reasons for finalization
    blocking_reasons: List[str] = []
    if inspection.status == InspectionStatus.COMPLETED:
        can_finalize = False
        blocking_reasons.append("Inspection is already finalized.")
    else:
        if review_count > 0 and (not declaration or not declaration.is_human_verified):
            blocking_reasons.append(
                f"{review_count} compliance checks require inspector review before finalization."
            )
        can_finalize = len(blocking_reasons) == 0

    return ReviewWorkspaceResponse(
        inspection_id=inspection_id,
        status=inspection.status,
        overall_result=inspection.overall_result,
        review_notes=inspection.review_notes,
        reviewed_at=inspection.reviewed_at,
        finalized_at=inspection.finalized_at,
        can_finalize=can_finalize,
        blocking_reasons=blocking_reasons,
        total_checks=len(checks),
        passed_checks=passed_count,
        failed_checks=failed_count,
        review_checks=review_count,
        declaration=declaration,
        checks=checks,
        violations=violations,
        evidence_items=evidence_items,
        audit_logs=audit_logs,
    )


@router.post("/{inspection_id}/review", response_model=ReviewWorkspaceResponse, tags=["Inspector Review"])
async def submit_inspection_review(
    inspection_id: uuid.UUID,
    review_in: ReviewSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits inspector adjudication decisions (CONFIRM, CORRECT, REQUEST_RETAKE, MARK_UNRESOLVED).
    """
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    declaration = (await db.execute(decl_stmt)).scalar_one_or_none()

    if not declaration:
        declaration = Declaration(inspection_id=inspection_id)
        db.add(declaration)

    # Apply overrides if provided
    if review_in.declaration_overrides:
        for f, v in review_in.declaration_overrides.items():
            if hasattr(declaration, f) and v is not None:
                setattr(declaration, f, v)

    declaration.is_human_verified = True
    inspection.review_notes = review_in.review_notes
    inspection.reviewed_by_id = current_user.id
    inspection.reviewed_at = datetime.now(timezone.utc)

    if review_in.review_action == "REQUEST_RETAKE":
        inspection.status = InspectionStatus.REVIEW_REQUIRED
    elif review_in.review_action == "MARK_UNRESOLVED":
        inspection.status = InspectionStatus.REVIEW_REQUIRED
    else:
        inspection.status = InspectionStatus.REVIEW_REQUIRED

    # Re-evaluate rules after human verification / overrides
    overall, _ = await evaluate_inspection(db, inspection, declaration)

    # Re-generate violations & evidence
    raw_checks_stmt = select(ComplianceCheck).where(ComplianceCheck.inspection_id == inspection_id)
    raw_checks = (await db.execute(raw_checks_stmt)).scalars().all()
    violations = await generate_violations_for_inspection(db, inspection.id, raw_checks)
    await link_evidence_for_inspection(db, inspection.id, raw_checks, violations)

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="INSPECTION_REVIEWED",
        entity_type="Inspection",
        entity_id=inspection.id,
        metadata_json={
            "action": review_in.review_action,
            "notes": review_in.review_notes,
            "overrides_applied": list(review_in.declaration_overrides.keys()) if review_in.declaration_overrides else [],
        },
    )

    await db.commit()
    return await get_inspection_review_workspace(inspection_id, current_user, db)


@router.post("/{inspection_id}/finalize", response_model=InspectionResponse, tags=["Inspector Review"])
async def finalize_inspection(
    inspection_id: uuid.UUID,
    finalize_in: FinalizeInspectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalizes an inspection and permanently locks it against further modifications.
    """
    inspection = await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    check_inspection_not_completed(inspection)

    # Check for unreviewed items
    checks_stmt = select(ComplianceCheck).where(ComplianceCheck.inspection_id == inspection_id)
    checks = (await db.execute(checks_stmt)).scalars().all()
    review_checks = [c for c in checks if c.result == CheckResult.REVIEW]

    decl_stmt = select(Declaration).where(Declaration.inspection_id == inspection_id)
    decl = (await db.execute(decl_stmt)).scalar_one_or_none()

    if review_checks and (not decl or not decl.is_human_verified) and not finalize_in.override_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot finalize inspection: {len(review_checks)} checks require human verification or an override verdict.",
        )

    if finalize_in.override_result:
        inspection.overall_result = finalize_in.override_result
    elif not inspection.overall_result or inspection.overall_result == ComplianceResult.PENDING:
        inspection.overall_result = ComplianceResult.COMPLIANT if not any(c.result == CheckResult.FAIL for c in checks) else ComplianceResult.NON_COMPLIANT

    if finalize_in.finalization_notes:
        existing_notes = inspection.review_notes or ""
        inspection.review_notes = f"{existing_notes}\n[Finalization Notes]: {finalize_in.finalization_notes}".strip()

    inspection.status = InspectionStatus.COMPLETED
    inspection.completed_at = datetime.now(timezone.utc)
    inspection.finalized_by_id = current_user.id
    inspection.finalized_at = datetime.now(timezone.utc)

    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="INSPECTION_FINALIZED",
        entity_type="Inspection",
        entity_id=inspection.id,
        metadata_json={
            "final_verdict": inspection.overall_result.value,
            "finalization_notes": finalize_in.finalization_notes,
        },
    )

    await db.commit()
    await db.refresh(inspection)
    return inspection


@router.get("/{inspection_id}/audit", response_model=List[AuditLogResponse], tags=["Chronological Audit Trail"])
async def get_inspection_audit_trail(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns the chronological audit trail for the specified inspection.
    """
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = (
        select(AuditLog)
        .where(AuditLog.inspection_id == inspection_id)
        .order_by(AuditLog.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# -----------------------------------------------------------------------------
# CHECKS, VIOLATIONS & EVIDENCE GETTERS
# -----------------------------------------------------------------------------

@router.get("/{inspection_id}/checks", response_model=List[ComplianceCheckResponse], tags=["Rule Engine"])
async def get_inspection_compliance_checks(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    checks_stmt = (
        select(ComplianceCheck)
        .where(ComplianceCheck.inspection_id == inspection_id)
        .options(
            selectinload(ComplianceCheck.legal_rule),
            selectinload(ComplianceCheck.violations).selectinload(Violation.evidence_items),
            selectinload(ComplianceCheck.evidence_items),
        )
        .order_by(ComplianceCheck.checked_at.asc())
    )
    checks_res = await db.execute(checks_stmt)
    return checks_res.scalars().all()


@router.get("/{inspection_id}/violations", response_model=List[ViolationResponse], tags=["Violations & Evidence"])
async def get_inspection_violations(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = (
        select(Violation)
        .where(Violation.inspection_id == inspection_id)
        .options(selectinload(Violation.evidence_items))
        .order_by(Violation.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inspection_id}/evidence", response_model=List[EvidenceResponse], tags=["Violations & Evidence"])
async def get_inspection_evidence(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = (
        select(Evidence)
        .where(Evidence.inspection_id == inspection_id)
        .order_by(Evidence.created_at.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# -----------------------------------------------------------------------------
# REPORTS & SECTION 36 NOTICE EXPORTS
# -----------------------------------------------------------------------------

@router.post(
    "/{inspection_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inspection Reports"],
)
async def generate_inspection_report(
    inspection_id: uuid.UUID,
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report, _, _ = await create_inspection_report(
        db=db,
        inspection_id=inspection_id,
        report_type=report_in.report_type,
        current_user=current_user,
    )
    await log_audit_event(
        db=db,
        inspection_id=inspection_id,
        actor_id=current_user.id,
        action="REPORT_GENERATED",
        entity_type="Report",
        entity_id=report.id,
        metadata_json={"report_type": report_in.report_type.value},
    )
    await db.commit()
    return report


@router.get(
    "/{inspection_id}/reports",
    response_model=List[ReportResponse],
    tags=["Inspection Reports"],
)
async def list_inspection_reports(
    inspection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = (
        select(Report)
        .where(Report.inspection_id == inspection_id)
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{inspection_id}/reports/{report_id}/download",
    tags=["Inspection Reports"],
)
async def download_inspection_report(
    inspection_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_authorized_inspection(inspection_id, current_user, db, load_relations=False)
    stmt = select(Report).where(
        Report.id == report_id,
        Report.inspection_id == inspection_id,
    )
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found for this inspection.",
        )

    rel_path = report.file_url.lstrip("/")
    file_path = Path(rel_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file does not exist on storage.",
        )

    media_type = "application/pdf" if report.report_type in (ReportType.PDF, ReportType.NOTICE_SEC36, ReportType.INSPECTION_MEMO) else "application/json"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )


# -----------------------------------------------------------------------------
# CONTROLLED DEMO SEED ENDPOINT (7 Presentation Presets)
# -----------------------------------------------------------------------------

DEMO_PRESETS = [
    {
        "slug": "demo-1-compliant",
        "title": "[Controlled Demo Data] Tata Sampann Toor Dal 1kg — Fully Compliant",
        "store": "Big Bazaar, Connaught Place",
        "district": "New Delhi",
        "state": "Delhi",
        "declaration": {
            "commodity_name": "Tata Sampann 100% Unpolished Toor Dal",
            "manufacturer_name": "Tata Consumer Products Ltd",
            "address": "1, Bishop Lefroy Road, Kolkata, West Bengal 700020",
            "net_quantity": "1 kg",
            "mrp": "MRP Rs. 175.00 incl. of all taxes",
            "manufacturing_date": "08/2026",
            "consumer_care": "1800-345-0020, care@tataconsumer.com",
            "is_imported": False,
            "pdp_area_sq_cm": 180.0,
            "unit_sale_price": "Rs. 175.00/kg",
            "is_human_verified": True,
        },
        "overall_result": ComplianceResult.COMPLIANT,
    },
    {
        "slug": "demo-2-missing-declaration",
        "title": "[Controlled Demo Data] Heritage Spices Garam Masala — Missing Mandatory MRP",
        "store": "Reliance Fresh, Indiranagar",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "declaration": {
            "commodity_name": "Garam Masala Powder",
            "manufacturer_name": "Heritage Spice Mills",
            "address": "Plot 42, Industrial Area, Mysuru 570018",
            "net_quantity": "100 g",
            "mrp": None,  # Missing declaration
            "manufacturing_date": "07/2026",
            "consumer_care": "080-2345678, care@heritagespices.in",
            "is_imported": False,
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
    {
        "slug": "demo-3-poor-quality",
        "title": "[Controlled Demo Data] Premium Dry Fruits — Specular Glare / Retake Advised",
        "store": "Nature's Basket, Bandra West",
        "district": "Mumbai",
        "state": "Maharashtra",
        "declaration": {
            "commodity_name": "Roasted California Almonds",
            "manufacturer_name": "NutriFoods India Pvt Ltd",
            "address": "Andheri East, Mumbai 400069",
            "net_quantity": "250 g",
            "mrp": "MRP Rs. 380.00",
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
    {
        "slug": "demo-4-ocr-ambiguity",
        "title": "[Controlled Demo Data] Organic Honey Jar — Curved Surface / Low OCR Confidence",
        "store": "Organic India Store, Banjara Hills",
        "district": "Hyderabad",
        "state": "Telangana",
        "declaration": {
            "commodity_name": "Pure Wild Forest Honey",
            "manufacturer_name": "Natural Apiaries Pvt Ltd",
            "address": "Survey 12, Medchal 501401",
            "net_quantity": "500 g",
            "mrp": "MRP Rs. 290.00 incl of taxes",
            "manufacturing_date": "06/2026",
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
    {
        "slug": "demo-5-mrp-discrepancy",
        "title": "[Controlled Demo Data] Fortune Sunlite Oil — MRP Discrepancy vs Catalog",
        "store": "D-Mart, Kothrud",
        "district": "Pune",
        "state": "Maharashtra",
        "declaration": {
            "commodity_name": "Fortune Sunlite Refined Sunflower Oil",
            "manufacturer_name": "Adani Wilmar Limited",
            "address": "Fortune House, Navrangpura, Ahmedabad 380009",
            "net_quantity": "1 L",
            "mrp": "MRP Rs. 185.00 incl. of all taxes",  # Differs from standard catalog ₹145.00
            "raw_extractions": {
                "barcode_data": {
                    "value": "8906010500123",
                    "catalog_match": {
                        "matched": True,
                        "product_name": "Fortune Sunlite Refined Sunflower Oil",
                        "catalog_mrp": 145.00,
                        "observed_mrp": 185.00,
                        "discrepancy": "MISMATCH",
                    },
                }
            },
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
    {
        "slug": "demo-6-digital-listing-contradiction",
        "title": "[Controlled Demo Data] Imported Swiss Chocolate — Digital Listing vs Package Contradiction",
        "store": "E-Commerce Fulfillment Center",
        "district": "Gurugram",
        "state": "Haryana",
        "declaration": {
            "commodity_name": "Dark Chocolate 70% Cocoa",
            "manufacturer_name": "Chocolatier Suisse SA",
            "address": "Route de Berne 14, Switzerland",
            "country_of_origin": "Switzerland",
            "is_imported": True,
            "net_quantity": "100 g",
            "mrp": "MRP Rs. 450.00 incl. of all taxes",
            "digital_listing_data": {
                "title": "Swiss Dark Chocolate Bar",
                "country_of_origin": "India",  # Contradicts package origin Switzerland
                "price": 450.00,
                "net_quantity": "100 g",
            },
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
    {
        "slug": "demo-7-font-measurement",
        "title": "[Controlled Demo Data] Refreshing Energy Drink — Font Size Scale Verification",
        "store": "Spencer's Retail, Sector 18",
        "district": "Noida",
        "state": "Uttar Pradesh",
        "declaration": {
            "commodity_name": "Sparkling Energy Drink",
            "manufacturer_name": "Beverage Works Ltd",
            "address": "Site 4, Sahibabad Industrial Area 201010",
            "net_quantity": "250 ml",
            "mrp": "MRP Rs. 60.00 incl. of all taxes",
            "pdp_area_sq_cm": 90.0,
            "measurement_data": {
                "pdp_area_cm2": 90.0,
                "pixel_height": 18.0,
                "pixel_scale_mm_per_px": 0.07,  # -> 1.26 mm (below 1.5mm threshold for 90cm²)
                "scale_source": "REFERENCE_OBJECT",
                "scale_confidence": 0.82,
            },
            "is_human_verified": False,
        },
        "overall_result": ComplianceResult.NEEDS_REVIEW,
    },
]


@router.post("/demo-seed", status_code=status.HTTP_201_CREATED, tags=["Controlled Demo Fixtures"])
async def seed_demo_inspections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Idempotently seeds 7 controlled demo inspection scenarios for demonstration.
    Explicitly labeled as controlled test fixtures.
    """
    seeded_count = 0
    for preset in DEMO_PRESETS:
        slug = preset["slug"]
        stmt = select(Inspection).where(Inspection.store_address == slug)
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            continue

        insp = Inspection(
            inspector_id=current_user.id,
            store_name=preset["title"],
            store_address=slug,
            district=preset["district"],
            state=preset["state"],
            status=InspectionStatus.REVIEW_REQUIRED,
            overall_result=preset["overall_result"],
            started_at=datetime.now(timezone.utc),
        )
        db.add(insp)
        await db.flush()

        decl_data = preset["declaration"]
        decl = Declaration(
            inspection_id=insp.id,
            commodity_name=decl_data.get("commodity_name"),
            manufacturer_name=decl_data.get("manufacturer_name"),
            address=decl_data.get("address"),
            country_of_origin=decl_data.get("country_of_origin"),
            is_imported=decl_data.get("is_imported", False),
            net_quantity=decl_data.get("net_quantity"),
            mrp=decl_data.get("mrp"),
            unit_sale_price=decl_data.get("unit_sale_price"),
            manufacturing_date=decl_data.get("manufacturing_date"),
            consumer_care=decl_data.get("consumer_care"),
            pdp_area_sq_cm=decl_data.get("pdp_area_sq_cm"),
            digital_listing_data=decl_data.get("digital_listing_data"),
            measurement_data=decl_data.get("measurement_data"),
            raw_extractions=decl_data.get("raw_extractions"),
            is_human_verified=decl_data.get("is_human_verified", False),
        )
        db.add(decl)
        await db.flush()

        # Evaluate rules for demo case
        await evaluate_inspection(db, insp, decl)

        # Generate violations & evidence
        raw_checks_stmt = select(ComplianceCheck).where(ComplianceCheck.inspection_id == insp.id)
        raw_checks = (await db.execute(raw_checks_stmt)).scalars().all()
        violations = await generate_violations_for_inspection(db, insp.id, raw_checks)
        await link_evidence_for_inspection(db, insp.id, raw_checks, violations)

        await log_audit_event(
            db=db,
            inspection_id=insp.id,
            actor_id=current_user.id,
            action="DEMO_SEED_CREATED",
            entity_type="Inspection",
            entity_id=insp.id,
            metadata_json={"preset_slug": slug, "is_demo": True},
        )
        seeded_count += 1

    await db.commit()
    return {
        "status": "SUCCESS",
        "message": f"Successfully seeded {seeded_count} controlled demo inspection presets.",
        "total_presets": len(DEMO_PRESETS),
        "disclaimer": "All seeded records are controlled demonstration fixtures and do NOT represent official ministry records.",
    }
