import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.enums import (
    ComplianceResult,
    DossierPriority,
    DossierStatus,
    InspectionStatus,
    ProductCategory,
    UserRole,
)
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.company import Company
from app.models.dossier import DossierInspection, InvestigationDossier
from app.models.inspection import Inspection
from app.models.user import User
from app.schemas.dossier import (
    InvestigationDossierCreate,
    InvestigationDossierDetailResponse,
    InvestigationDossierResponse,
)
from app.services.dossier_service import (
    _format_dossier_detail_response,
    _format_dossier_response,
)


async def get_or_create_test_user(db):
    user = (await db.execute(select(User).where(User.email == "model_test_user@gov.in"))).scalar_one_or_none()
    if not user:
        user = User(
            name="Model Test User",
            email="model_test_user@gov.in",
            password_hash=get_password_hash("SecretPassword123!"),
            role=UserRole.SUPERVISOR,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def test_01_create_investigation_dossier_minimal():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-TEST-{uuid.uuid4().hex[:6].upper()}",
            title="Minimal Model Test Dossier",
            lead_supervisor_id=user.id,
        )
        db.add(dossier)
        await db.commit()
        await db.refresh(dossier)

        assert dossier.id is not None
        assert dossier.status == DossierStatus.ACTIVE
        assert dossier.priority == DossierPriority.NORMAL
        print("PASS: test_01_create_investigation_dossier_minimal")


async def test_02_create_investigation_dossier_full():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        comp = Company(
            cin=f"L{uuid.uuid4().hex[:7].upper()}2026PLC999999",
            company_name="Full Model Test Corp",
            registered_office="Test Office",
            state="Delhi",
        )
        db.add(comp)
        await db.commit()
        await db.refresh(comp)

        dossier = InvestigationDossier(
            dossier_number=f"DOS-FULL-{uuid.uuid4().hex[:6].upper()}",
            title="Full Model Test Dossier",
            description="Testing all fields",
            target_entity_name="Full Model Test Brand",
            company_id=comp.id,
            status=DossierStatus.EVALUATION,
            priority=DossierPriority.CRITICAL,
            lead_supervisor_id=user.id,
            tags=["FMCG", "HIGH_RISK"],
            metadata_={"test_key": "test_val"},
        )
        db.add(dossier)
        await db.commit()
        await db.refresh(dossier)

        assert dossier.status == DossierStatus.EVALUATION
        assert dossier.priority == DossierPriority.CRITICAL
        assert dossier.company_id == comp.id
        print("PASS: test_02_create_investigation_dossier_full")


async def test_03_dossier_number_unique_constraint():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dup_num = f"DOS-DUP-{uuid.uuid4().hex[:6].upper()}"
        d1 = InvestigationDossier(
            dossier_number=dup_num,
            title="Dossier 1",
            lead_supervisor_id=user.id,
        )
        db.add(d1)
        await db.commit()

        d2 = InvestigationDossier(
            dossier_number=dup_num,
            title="Dossier 2",
            lead_supervisor_id=user.id,
        )
        db.add(d2)
        try:
            await db.commit()
            assert False, "Should have raised IntegrityError"
        except IntegrityError:
            await db.rollback()
            print("PASS: test_03_dossier_number_unique_constraint")


async def test_04_link_inspection_to_dossier():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-LINK-{uuid.uuid4().hex[:6].upper()}",
            title="Link Test Dossier",
            lead_supervisor_id=user.id,
        )
        insp = Inspection(
            inspector_id=user.id,
            store_name="Link Model Store",
            district="Pune",
            state="Maharashtra",
            status=InspectionStatus.CREATED,
        )
        db.add_all([dossier, insp])
        await db.commit()
        await db.refresh(dossier)
        await db.refresh(insp)

        link = DossierInspection(
            dossier_id=dossier.id,
            inspection_id=insp.id,
            added_by_id=user.id,
            relevance_notes="Model link test",
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)

        assert link.id is not None
        assert link.dossier_id == dossier.id
        assert link.inspection_id == insp.id
        print("PASS: test_04_link_inspection_to_dossier")


async def test_05_duplicate_inspection_link_rejected():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-LINKDUP-{uuid.uuid4().hex[:6].upper()}",
            title="Link Dup Dossier",
            lead_supervisor_id=user.id,
        )
        insp = Inspection(
            inspector_id=user.id,
            store_name="Link Dup Store",
            district="Pune",
            state="Maharashtra",
            status=InspectionStatus.CREATED,
        )
        db.add_all([dossier, insp])
        await db.commit()
        await db.refresh(dossier)
        await db.refresh(insp)

        l1 = DossierInspection(dossier_id=dossier.id, inspection_id=insp.id)
        db.add(l1)
        await db.commit()

        l2 = DossierInspection(dossier_id=dossier.id, inspection_id=insp.id)
        db.add(l2)
        try:
            await db.commit()
            assert False, "Should have raised IntegrityError"
        except IntegrityError:
            await db.rollback()
            print("PASS: test_05_duplicate_inspection_link_rejected")


async def test_06_dossier_deletion_cascade():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-CASC-{uuid.uuid4().hex[:6].upper()}",
            title="Cascade Dossier",
            lead_supervisor_id=user.id,
        )
        insp = Inspection(
            inspector_id=user.id,
            store_name="Cascade Store",
            district="Pune",
            state="Maharashtra",
            status=InspectionStatus.CREATED,
        )
        db.add_all([dossier, insp])
        await db.commit()
        await db.refresh(dossier)
        await db.refresh(insp)

        link = DossierInspection(dossier_id=dossier.id, inspection_id=insp.id)
        db.add(link)
        await db.commit()

        await db.delete(dossier)
        await db.commit()

        # Link deleted
        link_check = (await db.execute(select(DossierInspection).where(DossierInspection.id == link.id))).scalar_one_or_none()
        assert link_check is None

        # Inspection intact
        insp_check = (await db.execute(select(Inspection).where(Inspection.id == insp.id))).scalar_one_or_none()
        assert insp_check is not None
        print("PASS: test_06_dossier_deletion_cascade")


async def test_07_inspection_deletion_cascade():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-INSPC-{uuid.uuid4().hex[:6].upper()}",
            title="Insp Cascade Dossier",
            lead_supervisor_id=user.id,
        )
        insp = Inspection(
            inspector_id=user.id,
            store_name="Insp Cascade Store",
            district="Pune",
            state="Maharashtra",
            status=InspectionStatus.CREATED,
        )
        db.add_all([dossier, insp])
        await db.commit()
        await db.refresh(dossier)
        await db.refresh(insp)

        link = DossierInspection(dossier_id=dossier.id, inspection_id=insp.id)
        db.add(link)
        await db.commit()

        await db.delete(insp)
        await db.commit()

        # Link deleted
        link_check = (await db.execute(select(DossierInspection).where(DossierInspection.id == link.id))).scalar_one_or_none()
        assert link_check is None

        # Dossier intact
        dossier_check = (await db.execute(select(InvestigationDossier).where(InvestigationDossier.id == dossier.id))).scalar_one_or_none()
        assert dossier_check is not None
        print("PASS: test_07_inspection_deletion_cascade")


async def test_08_dossier_status_enum_values():
    assert set(DossierStatus) == {
        DossierStatus.ACTIVE,
        DossierStatus.EVALUATION,
        DossierStatus.NOTICE_REVIEW,
        DossierStatus.COMPOUNDING_REVIEW,
        DossierStatus.CLOSED,
    }
    print("PASS: test_08_dossier_status_enum_values")


async def test_09_dossier_without_company():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-NOCOMP-{uuid.uuid4().hex[:6].upper()}",
            title="No Company Dossier",
            company_id=None,
            lead_supervisor_id=user.id,
        )
        db.add(dossier)
        await db.commit()
        await db.refresh(dossier)

        assert dossier.company_id is None
        print("PASS: test_09_dossier_without_company")


async def test_10_pydantic_schemas_serialization():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_test_user(db)
        dossier = InvestigationDossier(
            dossier_number=f"DOS-SCHEMA-{uuid.uuid4().hex[:6].upper()}",
            title="Schema Serialization Dossier",
            lead_supervisor_id=user.id,
            tags=["TEST"],
        )
        db.add(dossier)
        await db.commit()
        await db.refresh(dossier)

        resp = _format_dossier_response(dossier)
        assert resp.title == "Schema Serialization Dossier"
        assert resp.status == DossierStatus.ACTIVE

        detail = _format_dossier_detail_response(dossier)
        assert detail.dossier_number == dossier.dossier_number
        assert isinstance(detail.dossier_inspections, list)
        print("PASS: test_10_pydantic_schemas_serialization")


async def main():
    print("Running Sub-Batch 1 Dossier Model Tests (10 Tests)...")
    await test_01_create_investigation_dossier_minimal()
    await test_02_create_investigation_dossier_full()
    await test_03_dossier_number_unique_constraint()
    await test_04_link_inspection_to_dossier()
    await test_05_duplicate_inspection_link_rejected()
    await test_06_dossier_deletion_cascade()
    await test_07_inspection_deletion_cascade()
    await test_08_dossier_status_enum_values()
    await test_09_dossier_without_company()
    await test_10_pydantic_schemas_serialization()
    print("\nALL 10 SUB-BATCH 1 DOSSIER MODEL TESTS PASSED (100%)!")


if __name__ == "__main__":
    asyncio.run(main())
