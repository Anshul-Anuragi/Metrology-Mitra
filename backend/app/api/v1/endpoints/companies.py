import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_db
from app.models.company import Company, NominatedDirector
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    NominatedDirectorCreate,
    NominatedDirectorResponse,
    Section49LiabilityAssessment,
)
from app.services.company_service import evaluate_section49_liability

router = APIRouter()


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Section 49 Corporate Liability"],
)
async def create_company(
    data: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a corporate entity and its nominated directors for Section 49 corporate liability management.
    """
    stmt = select(Company).where(func.upper(Company.cin) == data.cin.strip().upper())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Company with CIN '{data.cin}' is already registered.",
        )

    company = Company(
        cin=data.cin.strip().upper(),
        company_name=data.company_name.strip(),
        registered_office=data.registered_office.strip(),
        state=data.state.strip(),
        email=data.email,
        phone=data.phone,
        is_active=data.is_active,
    )
    db.add(company)
    await db.flush()

    if data.nominated_directors:
        for d in data.nominated_directors:
            nom_dir = NominatedDirector(
                company_id=company.id,
                director_name=d.director_name.strip(),
                din=d.din.strip(),
                designation=d.designation.strip(),
                form_i_notice_date=d.form_i_notice_date,
                form_i_reference=d.form_i_reference,
                effective_from=d.effective_from,
                effective_to=d.effective_to,
                is_active=d.is_active,
            )
            db.add(nom_dir)

    await db.commit()
    await db.refresh(company)
    return company


@router.get(
    "/",
    response_model=List[CompanyResponse],
    tags=["Section 49 Corporate Liability"],
)
async def list_companies(
    q: Optional[str] = Query(None, description="Search by CIN or company name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists corporate entities and their nominated directors.
    """
    stmt = select(Company).options(selectinload(Company.nominated_directors))
    if state:
        stmt = stmt.where(func.lower(Company.state) == state.strip().lower())
    if q:
        search = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Company.cin).like(search) | func.lower(Company.company_name).like(search)
        )
    stmt = stmt.order_by(Company.company_name.asc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    tags=["Section 49 Corporate Liability"],
)
async def get_company(
    company_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a single company record by ID with nominated directors.
    """
    stmt = (
        select(Company)
        .where(Company.id == company_id)
        .options(selectinload(Company.nominated_directors))
    )
    res = await db.execute(stmt)
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_id}' not found.",
        )
    return company


@router.post(
    "/{company_id}/directors",
    response_model=NominatedDirectorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Section 49 Corporate Liability"],
)
async def add_nominated_director(
    company_id: uuid.UUID,
    data: NominatedDirectorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Adds a Section 49(2) Form I nominated Director to a company.
    """
    stmt = select(Company).where(Company.id == company_id)
    res = await db.execute(stmt)
    company = res.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{company_id}' not found.",
        )

    nom_dir = NominatedDirector(
        company_id=company.id,
        director_name=data.director_name.strip(),
        din=data.din.strip(),
        designation=data.designation.strip(),
        form_i_notice_date=data.form_i_notice_date,
        form_i_reference=data.form_i_reference,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        is_active=data.is_active,
    )
    db.add(nom_dir)
    await db.commit()
    await db.refresh(nom_dir)
    return nom_dir


@router.get(
    "/liability/lookup",
    response_model=Section49LiabilityAssessment,
    tags=["Section 49 Corporate Liability"],
)
async def lookup_corporate_liability(
    q: str = Query(..., min_length=2, description="Company legal name or Corporate Identification Number (CIN)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates statutory liability under Section 49 and identifies whether liability lies
    against a nominated Director (Section 49(2)) or persons in charge (Section 49(1)).
    """
    return await evaluate_section49_liability(db, q)

