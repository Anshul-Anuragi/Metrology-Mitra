import hashlib
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.packer_registration import PackerRegistration
from app.models.user import User
from app.schemas.packer_registration import (
    PackerRegistrationCreate,
    PackerRegistrationResponse,
    RegistrationVerifyRequest,
    RegistrationVerifyResponse,
)
from app.services.registration_service import verify_packer_registration

router = APIRouter()


@router.post(
    "/",
    response_model=PackerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Rule 27 Pre-Packer Registry"],
)
async def create_packer_registration(
    data: PackerRegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new pre-packer, manufacturer, or importer in the Rule 27 statutory registry.
    """
    # Check duplicate registration number
    stmt = select(PackerRegistration).where(
        func.upper(PackerRegistration.registration_number) == data.registration_number.strip().upper()
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration number '{data.registration_number}' is already registered.",
        )

    cert_data = f"{data.registration_number}|{data.entity_name}|{data.registered_address}|{data.valid_from}"
    cert_hash = hashlib.sha256(cert_data.encode("utf-8")).hexdigest()

    reg = PackerRegistration(
        registration_number=data.registration_number.strip().upper(),
        entity_name=data.entity_name.strip(),
        registered_address=data.registered_address.strip(),
        jurisdiction_level=data.jurisdiction_level,
        state=data.state.strip(),
        issuing_authority=data.issuing_authority.strip(),
        registered_categories=data.registered_categories,
        valid_from=data.valid_from,
        valid_to=data.valid_to,
        is_active=data.is_active,
        certificate_sha256=cert_hash,
    )
    db.add(reg)
    await db.commit()
    await db.refresh(reg)
    return reg


@router.get(
    "/",
    response_model=List[PackerRegistrationResponse],
    tags=["Rule 27 Pre-Packer Registry"],
)
async def list_packer_registrations(
    q: Optional[str] = Query(None, description="Search term for registration number or entity name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    active_only: bool = Query(True, description="Filter active registrations only"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists pre-packer registration records with optional search and state filters.
    """
    stmt = select(PackerRegistration)
    if active_only:
        stmt = stmt.where(PackerRegistration.is_active.is_(True))
    if state:
        stmt = stmt.where(func.lower(PackerRegistration.state) == state.strip().lower())
    if q:
        search = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(PackerRegistration.registration_number).like(search)
            | func.lower(PackerRegistration.entity_name).like(search)
        )
    stmt = stmt.order_by(PackerRegistration.entity_name.asc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/{registration_id}",
    response_model=PackerRegistrationResponse,
    tags=["Rule 27 Pre-Packer Registry"],
)
async def get_packer_registration(
    registration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a single pre-packer registration record by ID.
    """
    stmt = select(PackerRegistration).where(PackerRegistration.id == registration_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration '{registration_id}' not found.",
        )
    return record


@router.post(
    "/verify",
    response_model=RegistrationVerifyResponse,
    tags=["Rule 27 Pre-Packer Registry"],
)
async def verify_registration(
    request: RegistrationVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stateless Rule 27 registration lookup and verification endpoint.
    """
    return await verify_packer_registration(db, request)

