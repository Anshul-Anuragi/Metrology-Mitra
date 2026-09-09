import asyncio
import datetime
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.enums import UserRole
from app.core.security import create_access_token, get_password_hash
from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.company import Company, NominatedDirector
from app.models.packer_registration import PackerRegistration
from app.models.seizure import SeizureItem, SeizureRecord
from app.models.user import User


async def test_phase_2_6_rule27_prepacker_registry():
    """
    Verifies Rule 27 Pre-Packer Registry creation, validation, and statutory lookup logic.
    """
    async with AsyncSessionLocal() as session:
        # Seed test user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email=f"inspector_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("TestPass123!"),
            name="Officer Rajesh Kumar",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        session.add(user)

        # Seed an active and an expired pre-packer registration
        reg_active = PackerRegistration(
            registration_number=f"DL-LM-REG-{uuid.uuid4().hex[:6].upper()}",
            entity_name="Hindustan Edible Oils Pvt. Ltd.",
            registered_address="Plot 45, Phase II, Okhla Industrial Area, New Delhi - 110020",
            jurisdiction_level="CENTRAL_DIRECTOR",
            state="Delhi",
            issuing_authority="Director of Legal Metrology, GoI",
            registered_categories=["Edible Oils", "Vanaspati"],
            valid_from=datetime.date(2023, 1, 1),
            valid_to=datetime.date(2028, 12, 31),
            is_active=True,
        )
        reg_expired = PackerRegistration(
            registration_number=f"MH-LM-REG-{uuid.uuid4().hex[:6].upper()}",
            entity_name="Old Maharashtra Spices Mill",
            registered_address="Sector 12, MIDC, Nagpur, Maharashtra",
            jurisdiction_level="STATE_CONTROLLER",
            state="Maharashtra",
            issuing_authority="Controller of Legal Metrology, Maharashtra",
            registered_categories=["Spices"],
            valid_from=datetime.date(2020, 1, 1),
            valid_to=datetime.date(2022, 1, 1),  # Expired
            is_active=True,
        )
        session.add_all([reg_active, reg_expired])
        await session.commit()

        token = create_access_token(subject=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Verify Active Registration by Registration Number
        resp1 = await ac.post(
            "/api/v1/registrations/verify",
            headers=headers,
            json={"registration_number": reg_active.registration_number},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["verification_status"] == "REGISTERED_VALID"
        assert data1["is_compliant"] is True
        assert data1["matched_entity_name"] == "Hindustan Edible Oils Pvt. Ltd."

        # 2. Verify Active Registration by Entity Name lookup
        resp2 = await ac.post(
            "/api/v1/registrations/verify",
            headers=headers,
            json={"entity_name": "Hindustan Edible Oils"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["verification_status"] == "REGISTERED_VALID"
        assert data2["is_compliant"] is True

        # 3. Verify Expired Registration
        resp3 = await ac.post(
            "/api/v1/registrations/verify",
            headers=headers,
            json={"registration_number": reg_expired.registration_number},
        )
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["verification_status"] == "EXPIRED"
        assert data3["is_compliant"] is False

        # 4. Verify Unregistered Entity
        resp4 = await ac.post(
            "/api/v1/registrations/verify",
            headers=headers,
            json={"entity_name": "NonExistent Shadow Packers Ltd."},
        )
        assert resp4.status_code == 200
        data4 = resp4.json()
        assert data4["verification_status"] == "UNREGISTERED_VIOLATION"
        assert data4["is_compliant"] is False

        # 5. Missing facts -> NEEDS_REVIEW
        resp5 = await ac.post(
            "/api/v1/registrations/verify",
            headers=headers,
            json={},
        )
        assert resp5.status_code == 200
        data5 = resp5.json()
        assert data5["verification_status"] == "NEEDS_REVIEW"

    print("PASS: test_phase_2_6_rule27_prepacker_registry")


async def test_phase_2_7_section15_seizures_and_panchnama():
    """
    Verifies Section 15 search and seizure recording, 2-witness Panchnama requirements,
    and Form VI Panchnama PDF generation.
    """
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"officer_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("TestPass123!"),
            name="Senior Inspector Ananya Roy",
            role=UserRole.INSPECTOR,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        token = create_access_token(subject=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Execute and Record Seizure with 2 Independent Panchas
        seizure_payload = {
            "premises_name": "Metro Wholesale Mart Warehouse",
            "premises_address": "Plot 99, Anand Industrial Area, Ghaziabad, UP",
            "statutory_grounds": "Absence of mandatory Unit Sale Price and deceptive packaging under Rule 6(11) & Section 15(1)(b)",
            "witness_1": {
                "name": "Ramesh Chandra Sharma",
                "address": "B-44, Sector 12, Vasundhara, Ghaziabad",
                "phone": "9876543210",
            },
            "witness_2": {
                "name": "Surender Kumar Verma",
                "address": "C-12, Sahibabad Village, Ghaziabad",
                "phone": "9812345678",
            },
            "custody_location": "Ghaziabad Legal Metrology District Custody Room",
            "items": [
                {
                    "commodity_name": "Premium Basmati Rice 5kg",
                    "brand_name": "Royal Feast",
                    "batch_lot_number": "BATCH-RF-2024-88",
                    "declared_net_quantity": "5 kg",
                    "total_packages_seized": 120,
                    "sample_packages_taken": 4,
                    "sample_seal_tag_number": "UP-LM-SEAL-9041",
                    "mrp": "Rs. 650.00",
                },
                {
                    "commodity_name": "Refined Mustard Oil 1L",
                    "brand_name": "Kisan Shuddh",
                    "batch_lot_number": "LOT-KS-99",
                    "declared_net_quantity": "1 L",
                    "total_packages_seized": 45,
                    "sample_packages_taken": 2,
                    "sample_seal_tag_number": "UP-LM-SEAL-9042",
                    "mrp": "Rs. 175.00",
                },
            ],
            "officer_remarks": "Seized inventory inventoried, sealed with official lead seals, and deposited in safe custody.",
        }

        resp_create = await ac.post("/api/v1/seizures/", headers=headers, json=seizure_payload)
        assert resp_create.status_code == 201
        data_create = resp_create.json()
        assert data_create["seizure_memo_number"].startswith("SZ-LMA15-")
        assert len(data_create["items"]) == 2
        assert data_create["sha256_seal_hash"] is not None
        assert data_create["witness_1_name"] == "Ramesh Chandra Sharma"
        assert data_create["witness_2_name"] == "Surender Kumar Verma"

        seizure_id = data_create["id"]

        # 2. Retrieve Seizure by ID
        resp_get = await ac.get(f"/api/v1/seizures/{seizure_id}", headers=headers)
        assert resp_get.status_code == 200
        assert resp_get.json()["id"] == seizure_id

        # 3. Generate and Download Form VI Panchnama PDF
        resp_pdf = await ac.get(f"/api/v1/seizures/{seizure_id}/panchnama-pdf", headers=headers)
        assert resp_pdf.status_code == 200
        assert resp_pdf.headers["content-type"] == "application/pdf"
        assert len(resp_pdf.content) > 1000
        assert resp_pdf.content.startswith(b"%PDF")

    print("PASS: test_phase_2_7_section15_seizures_and_panchnama")


async def test_phase_2_8_section49_corporate_and_director_liability():
    """
    Verifies Section 49 Corporate Entity registration, Form I Nominated Director tracking,
    and statutory notice recipient liability determination.
    """
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"sup_{uuid.uuid4().hex[:6]}@doca.gov.in",
            password_hash=get_password_hash("TestPass123!"),
            name="Controller R. K. Singhal",
            role=UserRole.SUPERVISOR,
            is_active=True,
        )
        session.add(user)

        # 1. Company WITH active Form I Nominated Director under Section 49(2)
        comp_with_dir = Company(
            cin=f"L15400MH2000PLC{uuid.uuid4().hex[:6].upper()}",
            company_name="Apex FMCG Conglomerate India Ltd.",
            registered_office="Express Towers, Nariman Point, Mumbai - 400021",
            state="Maharashtra",
            email="legal@apexfmcg.com",
            is_active=True,
        )
        session.add(comp_with_dir)
        await session.flush()

        dir_nom = NominatedDirector(
            company_id=comp_with_dir.id,
            director_name="Dr. Vikramaditya Birla",
            din="00123456",
            designation="Executive Director (Supply & Packaging)",
            form_i_notice_date=datetime.date(2023, 4, 15),
            form_i_reference="CLM/MH/FORM1/2023/108",
            effective_from=datetime.date(2023, 4, 1),
            effective_to=datetime.date(2027, 3, 31),
            is_active=True,
        )
        session.add(dir_nom)

        # 2. Company WITHOUT nominated director (defaults to Person in Charge under Sec 49(1))
        comp_without_dir = Company(
            cin=f"U24230DL2010PTC{uuid.uuid4().hex[:6].upper()}",
            company_name="Bharat Retail Foods Private Limited",
            registered_office="Barakhamba Road, Connaught Place, New Delhi",
            state="Delhi",
            is_active=True,
        )
        session.add(comp_without_dir)
        await session.commit()

        token = create_access_token(subject=str(user.id))
        headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Evaluate Company with Active Form I Nominated Director
        resp1 = await ac.get(
            "/api/v1/companies/liability/lookup",
            headers=headers,
            params={"q": "Apex FMCG Conglomerate"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["liability_determination"] == "NOMINATED_DIRECTOR_LIABLE"
        assert data1["has_nominated_director"] is True
        assert data1["notice_recipient_name"] == "Dr. Vikramaditya Birla"
        assert "Executive Director" in data1["notice_recipient_designation"]
        assert "Section 49(2)" in data1["notice_recipient_designation"]

        # 2. Evaluate Company WITHOUT Nominated Director (Defaults to Section 49(1))
        resp2 = await ac.get(
            "/api/v1/companies/liability/lookup",
            headers=headers,
            params={"q": "Bharat Retail Foods"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["liability_determination"] == "PERSON_IN_CHARGE_DEFAULT_LIABLE"
        assert data2["has_nominated_director"] is False
        assert "Section 49(1)" in data2["notice_recipient_designation"]

        # 3. Evaluate Unregistered / Unknown Entity
        resp3 = await ac.get(
            "/api/v1/companies/liability/lookup",
            headers=headers,
            params={"q": "Completely Unknown Firm XYZ"},
        )
        assert resp3.status_code == 200
        data3 = resp3.json()
        assert data3["liability_determination"] == "UNREGISTERED_COMPANY_NEEDS_REVIEW"

    print("PASS: test_phase_2_8_section49_corporate_and_director_liability")


if __name__ == "__main__":
    async def run_all():
        await test_phase_2_6_rule27_prepacker_registry()
        await test_phase_2_7_section15_seizures_and_panchnama()
        await test_phase_2_8_section49_corporate_and_director_liability()
        print("\n=======================================================")
        print("ALL PHASE 2.6, 2.7, 2.8 TESTS PASSED SUCCESSFULLY!")
        print("=======================================================\n")

    asyncio.run(run_all())
