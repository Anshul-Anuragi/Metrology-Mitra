import datetime
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company, NominatedDirector
from app.schemas.company import (
    NominatedDirectorResponse,
    Section49LiabilityAssessment,
)


async def evaluate_section49_liability(
    db: AsyncSession, company_name_or_cin: str
) -> Section49LiabilityAssessment:
    """
    Evaluates corporate liability and identifies notice recipient under Section 49
    of the Legal Metrology Act, 2009 (Offences by Companies).
    """
    today = datetime.date.today()
    clean_q = company_name_or_cin.strip()

    stmt = (
        select(Company)
        .where(
            (func.upper(Company.cin) == clean_q.upper())
            | (func.lower(Company.company_name).contains(clean_q.lower()))
        )
        .options(selectinload(Company.nominated_directors))
    )
    res = await db.execute(stmt)
    company = res.scalars().first()

    if not company:
        return Section49LiabilityAssessment(
            company_id=None,
            company_name=clean_q,
            cin=None,
            has_nominated_director=False,
            nominated_director=None,
            liability_determination="UNREGISTERED_COMPANY_NEEDS_REVIEW",
            notice_recipient_name="Managing Director / Person in Charge",
            notice_recipient_designation="Person in Charge of the Company",
            rationale=(
                f"Entity '{clean_q}' is not matched in corporate database. "
                "Under Section 49(1), liability falls on every person who was in charge of the conduct of business."
            ),
        )

    # Check for active nominated director under Section 49(2)
    active_directors = [
        d for d in company.nominated_directors
        if d.is_active and d.effective_from <= today and (d.effective_to is None or d.effective_to >= today)
    ]

    if active_directors:
        nom_dir = active_directors[0]
        nom_dir_resp = NominatedDirectorResponse.model_validate(nom_dir)
        return Section49LiabilityAssessment(
            company_id=company.id,
            company_name=company.company_name,
            cin=company.cin,
            has_nominated_director=True,
            nominated_director=nom_dir_resp,
            liability_determination="NOMINATED_DIRECTOR_LIABLE",
            notice_recipient_name=nom_dir.director_name,
            notice_recipient_designation=f"{nom_dir.designation} (Nominated under Section 49(2))",
            rationale=(
                f"Company has an active Form I nomination on record for '{nom_dir.director_name}' (DIN: {nom_dir.din}) "
                f"dated {nom_dir.form_i_notice_date.isoformat()}. Under Section 49(2), statutory notice and proceedings lie against the nominated Director."
            ),
        )

    return Section49LiabilityAssessment(
        company_id=company.id,
        company_name=company.company_name,
        cin=company.cin,
        has_nominated_director=False,
        nominated_director=None,
        liability_determination="PERSON_IN_CHARGE_DEFAULT_LIABLE",
        notice_recipient_name="Managing Director / Persons in Charge",
        notice_recipient_designation="Persons in Charge under Section 49(1)",
        rationale=(
            f"No active Form I Director nomination on record for '{company.company_name}' under Section 49(2). "
            "Under Section 49(1), statutory liability defaults jointly to the company and every person in charge of and responsible for the business."
        ),
    )

