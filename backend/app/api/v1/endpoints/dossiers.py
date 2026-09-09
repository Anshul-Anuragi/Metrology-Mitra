import io
import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role, require_supervisor
from app.core.enums import DossierPriority, DossierStatus, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.dossier import (
    DossierInspectionCreate,
    DossierInspectionResponse,
    DossierSynthesisResponse,
    InvestigationDossierCreate,
    InvestigationDossierDetailResponse,
    InvestigationDossierResponse,
    InvestigationDossierUpdate,
)
from app.services.dossier_service import (
    DossierService,
    _format_dossier_detail_response,
    _format_dossier_response,
)

router = APIRouter()


# =============================================================================
# OBJECT-LEVEL AUTHORIZATION HELPER
# =============================================================================

def _check_dossier_access(dossier, current_user: User) -> None:
    """
    Object-level authorization check:
    Inspectors can only access a dossier if they authored at least one linked inspection.
    Supervisors and Admins have system-wide access.
    """
    if current_user.role == UserRole.INSPECTOR:
        has_access = any(
            link.inspection and link.inspection.inspector_id == current_user.id
            for link in (dossier.dossier_inspections or [])
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have authorization to view this investigation dossier",
            )


# =============================================================================
# DOSSIER REST ENDPOINTS
# =============================================================================

@router.post(
    "/",
    response_model=InvestigationDossierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Investigation Dossier",
)
async def create_dossier(
    data: InvestigationDossierCreate,
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new market surveillance investigation dossier.
    Available to: SUPERVISOR, ADMIN.
    """
    try:
        dossier = await DossierService.create_dossier(
            db=db,
            data=data,
            lead_supervisor_id=current_user.id,
        )
        return _format_dossier_response(dossier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=PaginatedResponse[InvestigationDossierResponse],
    summary="List Investigation Dossiers",
)
async def list_dossiers(
    status_filter: Optional[DossierStatus] = Query(None, alias="status"),
    priority_filter: Optional[DossierPriority] = Query(None, alias="priority"),
    search: Optional[str] = Query(None, min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists investigation dossiers with filtering and object-level RBAC scoping.
    Inspectors only see dossiers containing inspections they authored.
    """
    skip = (page - 1) * size
    dossiers, total = await DossierService.list_dossiers(
        db=db,
        current_user=current_user,
        status=status_filter,
        priority=priority_filter,
        search=search,
        skip=skip,
        limit=size,
    )
    pages = math.ceil(total / size) if size > 0 else 0
    items = [_format_dossier_response(d) for d in dossiers]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/{dossier_id}",
    response_model=InvestigationDossierDetailResponse,
    summary="Get Investigation Dossier Detail",
)
async def get_dossier(
    dossier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full details of an investigation dossier including linked inspections.
    Enforces object-level access for inspectors.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    _check_dossier_access(dossier, current_user)
    return _format_dossier_detail_response(dossier)


@router.patch(
    "/{dossier_id}",
    response_model=InvestigationDossierDetailResponse,
    summary="Update Investigation Dossier",
)
async def update_dossier(
    dossier_id: uuid.UUID,
    data: InvestigationDossierUpdate,
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates operational metadata, status, or priority of an investigation dossier.
    Available to: SUPERVISOR, ADMIN.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    try:
        updated = await DossierService.update_dossier(
            db=db,
            dossier=dossier,
            data=data,
            current_user=current_user,
        )
        return _format_dossier_detail_response(updated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{dossier_id}/inspections",
    response_model=DossierInspectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Link Inspection to Dossier",
)
async def link_inspection(
    dossier_id: uuid.UUID,
    data: DossierInspectionCreate,
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Links an existing inspection to an investigation dossier.
    Available to: SUPERVISOR, ADMIN.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    try:
        link = await DossierService.link_inspection(
            db=db,
            dossier=dossier,
            data=data,
            current_user=current_user,
        )
        insp = link.inspection
        return DossierInspectionResponse(
            id=link.id,
            dossier_id=link.dossier_id,
            inspection_id=link.inspection_id,
            added_by_id=link.added_by_id,
            relevance_notes=link.relevance_notes,
            added_at=link.added_at,
            inspection_number=str(getattr(insp, "id", "")),
            inspection_date=getattr(insp, "created_at", None),
            store_name=getattr(insp, "store_name", None),
            city=getattr(insp, "district", None) or getattr(insp, "city", None),
            state=getattr(insp, "state", None),
            legal_result=insp.overall_result.value if (insp and insp.overall_result) else (insp.legal_result.value if (insp and hasattr(insp, "legal_result") and insp.legal_result) else None),
            inspection_status=insp.status.value if (insp and insp.status) else None,
            inspector_name=insp.inspector.name if (insp and insp.inspector) else None,

        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{dossier_id}/inspections/{inspection_id}",
    status_code=status.HTTP_200_OK,
    summary="Unlink Inspection from Dossier",
)
async def unlink_inspection(
    dossier_id: uuid.UUID,
    inspection_id: uuid.UUID,
    current_user: User = Depends(require_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Unlinks an inspection from an investigation dossier.
    Does NOT mutate, delete, or alter the underlying inspection or its evidence.
    Available to: SUPERVISOR, ADMIN.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    try:
        await DossierService.unlink_inspection(
            db=db,
            dossier=dossier,
            inspection_id=inspection_id,
            current_user=current_user,
        )
        return {
            "success": True,
            "message": "Inspection successfully unlinked from dossier",
            "dossier_id": str(dossier_id),
            "inspection_id": str(inspection_id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{dossier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Investigation Dossier Container (Admin Only)",
)
async def delete_dossier(
    dossier_id: uuid.UUID,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes an investigation dossier container.
    Cascade preserves underlying inspection records, evidence, and seizures.
    Available to: ADMIN only.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    await db.delete(dossier)
    await db.commit()
    return None


@router.get(
    "/{dossier_id}/synthesis",
    response_model=DossierSynthesisResponse,
    summary="Get Factual Dossier Synthesis",
)
async def get_dossier_synthesis(
    dossier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a read-only factual synthesis aggregating linked inspection data.
    Enforces object-level access check for inspectors.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    _check_dossier_access(dossier, current_user)

    synthesis = await DossierService.get_dossier_synthesis(db, dossier)
    return synthesis


@router.get(
    "/{dossier_id}/pdf",
    summary="Download Consolidated Inspection & Evidence Report PDF",
)
async def download_dossier_pdf(
    dossier_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates and downloads the consolidated ReportLab PDF report for an investigation dossier.
    Enforces object-level access check for inspectors.
    """
    dossier = await DossierService.get_dossier(db, dossier_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation dossier {dossier_id} not found",
        )

    _check_dossier_access(dossier, current_user)

    pdf_bytes = await DossierService.generate_dossier_pdf(db, dossier)
    filename = f"Dossier_{dossier.dossier_number}_Report.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        },
    )
