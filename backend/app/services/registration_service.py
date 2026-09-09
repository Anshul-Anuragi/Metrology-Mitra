import datetime
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.packer_registration import PackerRegistration
from app.schemas.packer_registration import RegistrationVerifyRequest, RegistrationVerifyResponse


async def verify_packer_registration(
    db: AsyncSession, request: RegistrationVerifyRequest
) -> RegistrationVerifyResponse:
    """
    Deterministically verifies manufacturer/packer/importer registration records
    under Rule 27 of the Legal Metrology (Packaged Commodities) Rules, 2011.
    """
    today = datetime.date.today()

    # 1. Search by exact registration number if provided
    if request.registration_number and request.registration_number.strip():
        reg_num = request.registration_number.strip().upper()
        stmt = select(PackerRegistration).where(
            func.upper(PackerRegistration.registration_number) == reg_num
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if record:
            if not record.is_active:
                return RegistrationVerifyResponse(
                    verification_status="REVOKED",
                    registration_number=record.registration_number,
                    matched_entity_name=record.entity_name,
                    registered_address=record.registered_address,
                    jurisdiction_level=record.jurisdiction_level,
                    state=record.state,
                    is_active=False,
                    valid_from=record.valid_from,
                    valid_to=record.valid_to,
                    is_compliant=False,
                    rationale=f"Rule 27 registration '{record.registration_number}' is marked INACTIVE/REVOKED by {record.issuing_authority}.",
                )
            if record.valid_to and record.valid_to < today:
                return RegistrationVerifyResponse(
                    verification_status="EXPIRED",
                    registration_number=record.registration_number,
                    matched_entity_name=record.entity_name,
                    registered_address=record.registered_address,
                    jurisdiction_level=record.jurisdiction_level,
                    state=record.state,
                    is_active=True,
                    valid_from=record.valid_from,
                    valid_to=record.valid_to,
                    is_compliant=False,
                    rationale=f"Rule 27 registration '{record.registration_number}' expired on {record.valid_to.isoformat()}.",
                )

            return RegistrationVerifyResponse(
                verification_status="REGISTERED_VALID",
                registration_number=record.registration_number,
                matched_entity_name=record.entity_name,
                registered_address=record.registered_address,
                jurisdiction_level=record.jurisdiction_level,
                state=record.state,
                is_active=True,
                valid_from=record.valid_from,
                valid_to=record.valid_to,
                is_compliant=True,
                rationale=f"Active Rule 27 registration confirmed with {record.issuing_authority} (Jurisdiction: {record.jurisdiction_level}).",
            )

    # 2. Search by entity name
    if request.entity_name and request.entity_name.strip():
        name_clean = request.entity_name.strip()
        stmt = select(PackerRegistration).where(
            func.lower(PackerRegistration.entity_name).contains(name_clean.lower())
        )
        res = await db.execute(stmt)
        record = res.scalars().first()

        if record:
            if not record.is_active or (record.valid_to and record.valid_to < today):
                return RegistrationVerifyResponse(
                    verification_status="EXPIRED",
                    registration_number=record.registration_number,
                    matched_entity_name=record.entity_name,
                    registered_address=record.registered_address,
                    jurisdiction_level=record.jurisdiction_level,
                    state=record.state,
                    is_active=record.is_active,
                    valid_from=record.valid_from,
                    valid_to=record.valid_to,
                    is_compliant=False,
                    rationale=f"Matched registration '{record.registration_number}' for entity '{record.entity_name}' is expired or inactive.",
                )

            return RegistrationVerifyResponse(
                verification_status="REGISTERED_VALID",
                registration_number=record.registration_number,
                matched_entity_name=record.entity_name,
                registered_address=record.registered_address,
                jurisdiction_level=record.jurisdiction_level,
                state=record.state,
                is_active=True,
                valid_from=record.valid_from,
                valid_to=record.valid_to,
                is_compliant=True,
                rationale=f"Entity name matched registered pre-packer '{record.entity_name}' under Rule 27 registration {record.registration_number}.",
            )
        else:
            return RegistrationVerifyResponse(
                verification_status="UNREGISTERED_VIOLATION",
                registration_number=None,
                matched_entity_name=None,
                registered_address=None,
                is_active=False,
                is_compliant=False,
                rationale=f"Pre-packer/manufacturer '{name_clean}' not found in Rule 27 statutory registry. Mandatory pre-packer registration required under Rule 27.",
            )

    # 3. Insufficient inputs
    return RegistrationVerifyResponse(
        verification_status="NEEDS_REVIEW",
        registration_number=None,
        matched_entity_name=None,
        registered_address=None,
        is_active=False,
        is_compliant=False,
        rationale="Insufficient identification facts: Registration number or pre-packer name required to verify Rule 27 compliance.",
    )

