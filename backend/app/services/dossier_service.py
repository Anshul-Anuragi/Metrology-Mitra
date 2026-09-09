import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.core.enums import (
    ComplianceResult,
    DossierPriority,
    DossierStatus,
    InspectionStatus,
    UserRole,
)
from app.models.audit_log import AuditLog
from app.models.company import Company, NominatedDirector
from app.models.compliance_check import ComplianceCheck
from app.models.dossier import DossierInspection, InvestigationDossier

from app.models.inspection import Inspection
from app.models.seizure import SeizureItem, SeizureRecord
from app.models.user import User
from app.models.violation import Violation
from app.schemas.dossier import (
    DossierInspectionCreate,
    DossierInspectionResponse,
    DossierNominatedDirectorReview,
    DossierSummaryCounts,
    DossierSynthesisResponse,
    DossierTimelineEvent,
    InvestigationDossierCreate,
    InvestigationDossierDetailResponse,
    InvestigationDossierResponse,
    InvestigationDossierUpdate,
    ObservedFindingSummary,
    RecordedSeizureSummary,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _generate_dossier_number(db: AsyncSession) -> str:
    """Generates sequential operational identifier DOS-YYYY-XXXX."""
    current_year = datetime.now(timezone.utc).year
    prefix = f"DOS-{current_year}-"
    stmt = (
        select(func.count(InvestigationDossier.id))
        .where(InvestigationDossier.dossier_number.like(f"{prefix}%"))
    )
    res = await db.execute(stmt)
    count = (res.scalar() or 0) + 1
    return f"{prefix}{count:04d}"


def _format_dossier_response(dossier: InvestigationDossier) -> InvestigationDossierResponse:
    """Formats an InvestigationDossier model into InvestigationDossierResponse."""
    company_name = dossier.company.company_name if dossier.company else None
    supervisor_name = dossier.lead_supervisor.name if dossier.lead_supervisor else None
    linked_count = len(dossier.dossier_inspections) if dossier.dossier_inspections is not None else 0

    return InvestigationDossierResponse(
        id=dossier.id,
        dossier_number=dossier.dossier_number,
        title=dossier.title,
        description=dossier.description,
        target_entity_name=dossier.target_entity_name,
        company_id=dossier.company_id,
        company_name=company_name,
        status=dossier.status,
        priority=dossier.priority,
        lead_supervisor_id=dossier.lead_supervisor_id,
        lead_supervisor_name=supervisor_name,
        tags=dossier.tags or [],
        linked_inspections_count=linked_count,
        created_at=dossier.created_at,
        updated_at=dossier.updated_at,
        closed_at=dossier.closed_at,
    )


def _format_dossier_detail_response(dossier: InvestigationDossier) -> InvestigationDossierDetailResponse:
    """Formats an InvestigationDossier model into InvestigationDossierDetailResponse."""
    base_res = _format_dossier_response(dossier)
    company_cin = dossier.company.cin if dossier.company else None

    formatted_links: List[DossierInspectionResponse] = []
    if dossier.dossier_inspections:
        for link in dossier.dossier_inspections:
            insp = link.inspection
            formatted_links.append(
                DossierInspectionResponse(
                    id=link.id,
                    dossier_id=link.dossier_id,
                    inspection_id=link.inspection_id,
                    added_by_id=link.added_by_id,
                    relevance_notes=link.relevance_notes,
                    added_at=link.added_at,
                    inspection_number=str(getattr(insp, "id", "")),
                    inspection_date=getattr(insp, "created_at", None),
                    store_name=getattr(insp, "store_name", None),
                    city=getattr(insp, "district", None),
                    state=getattr(insp, "state", None),
                    legal_result=insp.overall_result.value if (insp and insp.overall_result) else (insp.legal_result.value if (insp and hasattr(insp, "legal_result") and insp.legal_result) else None),
                    inspection_status=insp.status.value if (insp and insp.status) else None,
                    inspector_name=insp.inspector.name if (insp and insp.inspector) else None,

                )
            )

    return InvestigationDossierDetailResponse(
        **base_res.model_dump(),
        metadata_=dossier.metadata_ or {},
        dossier_inspections=formatted_links,
        company_cin=company_cin,
    )


# =============================================================================
# DOSSIER SERVICE IMPLEMENTATION
# =============================================================================

class DossierService:
    @staticmethod
    async def create_dossier(
        db: AsyncSession,
        data: InvestigationDossierCreate,
        lead_supervisor_id: uuid.UUID,
    ) -> InvestigationDossier:
        """
        Creates a new market surveillance investigation dossier.
        Operational case container only; does not alter inspection verdicts.
        """
        dossier_num = data.dossier_number
        if not dossier_num or not dossier_num.strip():
            dossier_num = await _generate_dossier_number(db)
        else:
            dossier_num = dossier_num.strip().upper()

        # Validate explicit company_id if provided (NO fuzzy matching)
        if data.company_id:
            company = await db.get(Company, data.company_id)
            if not company:
                raise ValueError(f"Specified corporate entity {data.company_id} does not exist")

        now = datetime.now(timezone.utc)
        init_metadata = dict(data.metadata or {})
        init_metadata["audit_logs"] = [
            {
                "action": "DOSSIER_CREATED",
                "actor_id": str(lead_supervisor_id),
                "timestamp": now.isoformat(),
                "details": f"Dossier '{data.title}' created with status {data.status.value if data.status else 'ACTIVE'}.",
            }
        ]

        dossier = InvestigationDossier(
            dossier_number=dossier_num,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            target_entity_name=data.target_entity_name.strip() if data.target_entity_name else None,
            company_id=data.company_id,
            status=data.status or DossierStatus.ACTIVE,
            priority=data.priority or DossierPriority.NORMAL,
            lead_supervisor_id=lead_supervisor_id,
            tags=data.tags or [],
            metadata_=init_metadata,
            created_at=now,
            updated_at=now,
        )

        db.add(dossier)
        await db.commit()
        return await DossierService.get_dossier(db, dossier.id)  # type: ignore

    @staticmethod
    async def get_dossier(db: AsyncSession, dossier_id: uuid.UUID) -> Optional[InvestigationDossier]:
        """Fetches an InvestigationDossier with all necessary related models loaded."""
        stmt = (
            select(InvestigationDossier)
            .options(
                selectinload(InvestigationDossier.company).selectinload(Company.nominated_directors),
                selectinload(InvestigationDossier.lead_supervisor),
                selectinload(InvestigationDossier.dossier_inspections)
                .selectinload(DossierInspection.inspection)
                .selectinload(Inspection.inspector),
            )
            .where(InvestigationDossier.id == dossier_id)
            .execution_options(populate_existing=True)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


    @staticmethod
    async def list_dossiers(
        db: AsyncSession,
        current_user: User,
        status: Optional[DossierStatus] = None,
        priority: Optional[DossierPriority] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[InvestigationDossier], int]:
        """
        Lists dossiers with pagination, filtering, and strict object-level RBAC:
        Inspectors only see dossiers containing an inspection authored by them.
        Supervisors and Admins see all dossiers.
        """
        base_query = select(InvestigationDossier).distinct()

        # Object-level authorization for inspectors
        if current_user.role == UserRole.INSPECTOR:
            base_query = (
                base_query
                .join(InvestigationDossier.dossier_inspections)
                .join(DossierInspection.inspection)
                .where(Inspection.inspector_id == current_user.id)
            )

        conditions = []
        if status:
            conditions.append(InvestigationDossier.status == status)
        if priority:
            conditions.append(InvestigationDossier.priority == priority)
        if search and search.strip():
            term = f"%{search.strip()}%"
            conditions.append(
                (InvestigationDossier.title.ilike(term))
                | (InvestigationDossier.dossier_number.ilike(term))
                | (InvestigationDossier.target_entity_name.ilike(term))
            )

        if conditions:
            base_query = base_query.where(*conditions)

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Fetch records
        stmt = (
            base_query
            .options(
                selectinload(InvestigationDossier.company),
                selectinload(InvestigationDossier.lead_supervisor),
                selectinload(InvestigationDossier.dossier_inspections),
            )
            .order_by(InvestigationDossier.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return res.scalars().all(), total_count

    @staticmethod
    async def update_dossier(
        db: AsyncSession,
        dossier: InvestigationDossier,
        data: InvestigationDossierUpdate,
        current_user: User,
    ) -> InvestigationDossier:
        """Updates operational dossier fields and appends to audit trail."""
        now = datetime.now(timezone.utc)
        changes = []

        if data.title is not None and data.title.strip():
            dossier.title = data.title.strip()
            changes.append("title updated")

        if data.description is not None:
            dossier.description = data.description.strip() if data.description else None
            changes.append("description updated")

        if data.target_entity_name is not None:
            dossier.target_entity_name = data.target_entity_name.strip() if data.target_entity_name else None
            changes.append("target_entity_name updated")

        if data.company_id is not None:
            if data.company_id != dossier.company_id:
                if data.company_id:
                    company = await db.get(Company, data.company_id)
                    if not company:
                        raise ValueError(f"Corporate entity {data.company_id} does not exist")
                dossier.company_id = data.company_id
                changes.append("company_id updated")

        if data.priority is not None and data.priority != dossier.priority:
            changes.append(f"priority changed from {dossier.priority.value} to {data.priority.value}")
            dossier.priority = data.priority

        if data.status is not None and data.status != dossier.status:
            changes.append(f"status changed from {dossier.status.value} to {data.status.value}")
            dossier.status = data.status
            if data.status == DossierStatus.CLOSED:
                dossier.closed_at = now
            elif dossier.closed_at is not None:
                dossier.closed_at = None

        if data.tags is not None:
            dossier.tags = data.tags
            changes.append("tags updated")

        meta = dict(dossier.metadata_ or {})
        if data.metadata is not None:
            meta.update(data.metadata)

        dossier.updated_at = now

        # Append audit event
        audit_trail = list(meta.get("audit_logs", []))
        audit_trail.append({
            "action": "DOSSIER_UPDATED",
            "actor_id": str(current_user.id),
            "timestamp": now.isoformat(),
            "details": "; ".join(changes) if changes else "Metadata updated.",
        })
        meta["audit_logs"] = audit_trail
        dossier.metadata_ = meta
        flag_modified(dossier, "metadata_")

        await db.commit()
        return await DossierService.get_dossier(db, dossier.id)  # type: ignore

    @staticmethod
    async def link_inspection(
        db: AsyncSession,
        dossier: InvestigationDossier,
        data: DossierInspectionCreate,
        current_user: User,
    ) -> DossierInspection:
        """
        Links an existing inspection to an investigation dossier.

        CRITICAL LEGAL INVARIANT:
        The underlying inspection is NEVER mutated or modified.
        Finalized inspections can be linked as it is purely an external association.
        """
        # 1. Verify inspection exists
        inspection = await db.get(Inspection, data.inspection_id)
        if not inspection:
            raise ValueError(f"Inspection {data.inspection_id} does not exist")

        # 2. Check for duplicate link
        dup_stmt = select(DossierInspection).where(
            DossierInspection.dossier_id == dossier.id,
            DossierInspection.inspection_id == data.inspection_id,
        )
        existing = (await db.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise ValueError(f"Inspection {data.inspection_id} is already linked to this dossier")

        now = datetime.now(timezone.utc)

        # 3. Create link record
        link = DossierInspection(
            dossier_id=dossier.id,
            inspection_id=data.inspection_id,
            added_by_id=current_user.id,
            relevance_notes=data.relevance_notes.strip() if data.relevance_notes else None,
            added_at=now,
        )
        db.add(link)

        # 4. Record chronological audit log for inspection
        audit_entry = AuditLog(
            inspection_id=data.inspection_id,
            actor_user_id=current_user.id,
            action="DOSSIER_INSPECTION_LINKED",
            entity_type="INVESTIGATION_DOSSIER",
            entity_id=dossier.id,
            metadata_json={
                "dossier_number": dossier.dossier_number,
                "relevance_notes": data.relevance_notes,
                "action": "link",
            },
            created_at=now,
        )
        db.add(audit_entry)

        # 5. Record event in dossier metadata audit logs
        meta = dict(dossier.metadata_ or {})
        audit_trail = list(meta.get("audit_logs", []))
        audit_trail.append({
            "action": "INSPECTION_LINKED",
            "actor_id": str(current_user.id),
            "timestamp": now.isoformat(),
            "details": f"Inspection {data.inspection_id} linked to dossier.",
        })
        meta["audit_logs"] = audit_trail
        dossier.metadata_ = meta
        flag_modified(dossier, "metadata_")
        dossier.updated_at = now

        await db.commit()
        fetch_stmt = (
            select(DossierInspection)
            .options(
                selectinload(DossierInspection.inspection).selectinload(Inspection.inspector)
            )
            .where(DossierInspection.id == link.id)
        )
        loaded_link = (await db.execute(fetch_stmt)).scalar_one()
        return loaded_link


    @staticmethod
    async def unlink_inspection(
        db: AsyncSession,
        dossier: InvestigationDossier,
        inspection_id: uuid.UUID,
        current_user: User,
    ) -> bool:
        """
        Unlinks an inspection from an investigation dossier.

        CRITICAL LEGAL INVARIANT:
        NEVER deletes the inspection, violations, evidence, seizure records, or reports.
        Only removes the associative DossierInspection record.
        """
        stmt = select(DossierInspection).where(
            DossierInspection.dossier_id == dossier.id,
            DossierInspection.inspection_id == inspection_id,
        )
        link = (await db.execute(stmt)).scalar_one_or_none()
        if not link:
            raise ValueError(f"Inspection {inspection_id} is not linked to this dossier")

        now = datetime.now(timezone.utc)

        # Delete association
        await db.delete(link)

        # Record audit log for inspection
        audit_entry = AuditLog(
            inspection_id=inspection_id,
            actor_user_id=current_user.id,
            action="DOSSIER_INSPECTION_UNLINKED",
            entity_type="INVESTIGATION_DOSSIER",
            entity_id=dossier.id,
            metadata_json={
                "dossier_number": dossier.dossier_number,
                "action": "unlink",
            },
            created_at=now,
        )
        db.add(audit_entry)

        # Update dossier metadata
        meta = dict(dossier.metadata_ or {})
        audit_trail = list(meta.get("audit_logs", []))
        audit_trail.append({
            "action": "INSPECTION_UNLINKED",
            "actor_id": str(current_user.id),
            "timestamp": now.isoformat(),
            "details": f"Inspection {inspection_id} unlinked from dossier.",
        })
        meta["audit_logs"] = audit_trail
        dossier.metadata_ = meta
        flag_modified(dossier, "metadata_")
        dossier.updated_at = now

        await db.commit()
        return True

    @staticmethod
    async def get_dossier_synthesis(
        db: AsyncSession,
        dossier: InvestigationDossier,
    ) -> DossierSynthesisResponse:
        """
        Generates a read-only factual synthesis aggregating linked inspection data.

        CRITICAL LEGAL INVARIANTS:
        - NEVER creates new statutory violations.
        - NEVER alters individual inspection legal results.
        - NEVER infers director liability or collective guilt.
        - Wording is strictly factual ("Observed finding pattern", "Recorded seizure quantity").
        """
        # Ensure relationships are loaded
        full_dossier = await DossierService.get_dossier(db, dossier.id)
        if not full_dossier:
            raise ValueError(f"Dossier {dossier.id} not found")

        dossier = full_dossier

        links_stmt = (
            select(DossierInspection)
            .options(
                selectinload(DossierInspection.inspection).selectinload(Inspection.inspector)
            )
            .where(DossierInspection.dossier_id == dossier.id)
            .order_by(DossierInspection.added_at.asc())
            .execution_options(populate_existing=True)
        )
        dossier_links = (await db.execute(links_stmt)).scalars().all()
        linked_inspections = [link.inspection for link in dossier_links if link.inspection]
        inspection_ids = [insp.id for insp in linked_inspections]


        # 1. Summary Counts
        counts = DossierSummaryCounts(
            total_inspections=len(linked_inspections),
            completed_inspections=sum(1 for i in linked_inspections if i.status == InspectionStatus.COMPLETED),
            review_required_inspections=sum(1 for i in linked_inspections if i.status == InspectionStatus.REVIEW_REQUIRED),
            compliant_count=sum(1 for i in linked_inspections if getattr(i, "overall_result", None) == ComplianceResult.COMPLIANT or getattr(i, "legal_result", None) == ComplianceResult.COMPLIANT),
            non_compliant_count=sum(1 for i in linked_inspections if getattr(i, "overall_result", None) == ComplianceResult.NON_COMPLIANT or getattr(i, "legal_result", None) == ComplianceResult.NON_COMPLIANT),
            needs_review_count=sum(1 for i in linked_inspections if getattr(i, "overall_result", None) == ComplianceResult.NEEDS_REVIEW or getattr(i, "legal_result", None) == ComplianceResult.NEEDS_REVIEW),
            pending_count=sum(1 for i in linked_inspections if getattr(i, "overall_result", None) == ComplianceResult.PENDING or getattr(i, "overall_result", None) is None),
        )

        # 2. Locations / Retail Stores
        locations_set = set()
        for insp in linked_inspections:
            loc_parts = []
            if getattr(insp, "store_name", None):
                loc_parts.append(insp.store_name)
            if getattr(insp, "district", None):
                loc_parts.append(insp.district)
            elif getattr(insp, "city", None):
                loc_parts.append(insp.city)
            if getattr(insp, "state", None):
                loc_parts.append(insp.state)
            if loc_parts:
                locations_set.add(", ".join(loc_parts))
        locations = sorted(list(locations_set))


        # 3. Observed Findings (Grouped by existing legal rule violations)
        observed_findings: List[ObservedFindingSummary] = []
        if inspection_ids:
            v_stmt = (
                select(Violation)
                .options(
                    selectinload(Violation.compliance_check).selectinload(ComplianceCheck.legal_rule)
                )
                .where(Violation.inspection_id.in_(inspection_ids))
            )
            v_res = await db.execute(v_stmt)
            violations = v_res.scalars().all()

            rule_groups: Dict[str, Dict[str, Any]] = {}
            for v in violations:
                rule = v.compliance_check.legal_rule if v.compliance_check else None
                code = rule.rule_code if rule else (v.rule_citation or "STATUTORY_RULE")
                name = rule.title if rule else (v.title or "Statutory Finding")
                if code not in rule_groups:
                    rule_groups[code] = {
                        "rule_code": code,
                        "rule_name": name,
                        "inspection_ids": set(),
                        "severities": set(),
                    }
                rule_groups[code]["inspection_ids"].add(v.inspection_id)
                if hasattr(v, "severity") and v.severity:
                    rule_groups[code]["severities"].add(v.severity.value if hasattr(v.severity, "value") else str(v.severity))


            for code, grp in sorted(rule_groups.items(), key=lambda item: len(item[1]["inspection_ids"]), reverse=True):
                observed_findings.append(
                    ObservedFindingSummary(
                        rule_code=grp["rule_code"],
                        rule_name=grp["rule_name"],
                        affected_inspection_count=len(grp["inspection_ids"]),
                        severity_levels=sorted(list(grp["severities"])),
                        observation_label="Observed finding pattern",
                    )
                )

        # 4. Recorded Seizure Summary
        seizure_summary = RecordedSeizureSummary()
        if inspection_ids:
            seizure_stmt = (
                select(SeizureRecord)
                .where(SeizureRecord.inspection_id.in_(inspection_ids))
                .execution_options(populate_existing=True)
            )
            seizure_res = await db.execute(seizure_stmt)
            seizure_records = seizure_res.scalars().all()

            items_stmt = (
                select(SeizureItem)
                .join(SeizureRecord, SeizureItem.seizure_id == SeizureRecord.id)
                .where(SeizureRecord.inspection_id.in_(inspection_ids))
                .execution_options(populate_existing=True)
            )
            items_res = await db.execute(items_stmt)
            seizure_items_list = items_res.scalars().all()

            total_units = sum(
                float(getattr(item, "total_packages_seized", 0) or getattr(item, "quantity_seized", 0) or 0.0)
                for item in seizure_items_list
            )
            total_items = len(seizure_items_list)

            seizure_summary = RecordedSeizureSummary(
                total_seizure_records=len(seizure_records),
                total_seized_quantity=total_units,
                seizure_items_count=total_items,
                description="Recorded seizure quantity across linked inspection records",
            )

        # 5. Batches Count
        batch_ids = {insp.batch_id for insp in linked_inspections if getattr(insp, "batch_id", None)}
        batch_count = len(batch_ids)

        # 6. Evidence Completeness Average (Factual aggregation from inspection metadata or default calculation)
        completeness_scores = []
        for insp in linked_inspections:
            meta = getattr(insp, "metadata_", {}) or {}
            score = meta.get("evidence_completeness_index")
            if score is not None:
                completeness_scores.append(float(score))
            else:
                # Default baseline score for completed vs in-progress inspections
                completeness_scores.append(85.0 if insp.status == InspectionStatus.COMPLETED else 50.0)

        evidence_avg = round(sum(completeness_scores) / len(completeness_scores), 1) if completeness_scores else 0.0

        # 7. Timeline of Factual Events
        timeline: List[DossierTimelineEvent] = []
        for link in dossier_links:
            insp = link.inspection

            if insp:
                res_val = (
                    insp.overall_result.value
                    if getattr(insp, "overall_result", None)
                    else (insp.legal_result.value if hasattr(insp, "legal_result") and insp.legal_result else "PENDING")
                )
                timeline.append(
                    DossierTimelineEvent(
                        event_type="INSPECTION_CONDUCTED",
                        timestamp=insp.created_at,
                        description=f"Inspection conducted at {insp.store_name or 'Retail Store'} ({res_val})",
                        inspection_id=insp.id,
                    )
                )
                if getattr(insp, "finalized_at", None):
                    timeline.append(
                        DossierTimelineEvent(
                            event_type="INSPECTION_FINALIZED",
                            timestamp=insp.finalized_at,
                            description=f"Inspection review finalized with result: {res_val}",
                            inspection_id=insp.id,
                        )
                    )
            timeline.append(
                DossierTimelineEvent(
                    event_type="INSPECTION_LINKED_TO_DOSSIER",
                    timestamp=link.added_at,
                    description=f"Inspection linked to dossier. Context: {link.relevance_notes or 'Factual grouping'}",
                    inspection_id=link.inspection_id,
                )
            )

        timeline.sort(key=lambda x: x.timestamp)

        # 8. Nominated Directors Informational Review
        director_reviews: List[DossierNominatedDirectorReview] = []
        company_name = None
        company_cin = None
        if dossier.company:
            company_name = dossier.company.company_name
            company_cin = dossier.company.cin
            for dir_rec in dossier.company.nominated_directors:
                director_reviews.append(
                    DossierNominatedDirectorReview(
                        director_name=dir_rec.director_name,
                        din=dir_rec.din,
                        designation=dir_rec.designation,
                        form_i_notice_date=dir_rec.form_i_notice_date.isoformat() if dir_rec.form_i_notice_date else None,
                        review_note="Associated corporate record available for authorized officer review. Does not establish personal liability.",
                    )
                )

        # 9. Historical Repeat History (Strictly factual query, explicit relationships only, NO fuzzy matching)
        hist_count = 0
        if dossier.company_id:
            hist_stmt = (
                select(func.count(Inspection.id))
                .where(
                    Inspection.company_id == dossier.company_id,
                    Inspection.overall_result == ComplianceResult.NON_COMPLIANT,
                )
            )
            hist_res = await db.execute(hist_stmt)
            hist_count = hist_res.scalar() or 0
            repeat_note = f"{hist_count} previous non-compliant inspection records associated with the selected corporate record."
        elif dossier.target_entity_name and dossier.target_entity_name.strip():
            hist_stmt = (
                select(func.count(Inspection.id))
                .where(
                    func.lower(Inspection.store_name) == dossier.target_entity_name.strip().lower(),
                    Inspection.overall_result == ComplianceResult.NON_COMPLIANT,
                )
            )
            hist_res = await db.execute(hist_stmt)
            hist_count = hist_res.scalar() or 0
            repeat_note = f"{hist_count} previous non-compliant inspection records with matching premises store name."
        else:
            repeat_note = "No previous inspection history linked to this dossier."

        supervisor_name = dossier.lead_supervisor.name if dossier.lead_supervisor else None

        return DossierSynthesisResponse(
            dossier_id=dossier.id,
            dossier_number=dossier.dossier_number,
            title=dossier.title,
            status=dossier.status,
            priority=dossier.priority,
            target_entity_name=dossier.target_entity_name,
            company_id=dossier.company_id,
            company_name=company_name,
            company_cin=company_cin,
            lead_supervisor_id=dossier.lead_supervisor_id,
            lead_supervisor_name=supervisor_name,
            summary_counts=counts,
            locations=locations,
            observed_findings=observed_findings,
            seizure_summary=seizure_summary,
            batch_count=batch_count,
            evidence_completeness_average=evidence_avg,
            timeline=timeline,
            nominated_directors_review=director_reviews,
            repeat_history_note=repeat_note,
            historical_non_compliant_count=hist_count,
            advisory_disclaimer=(
                "Operational case-management view. Individual inspection legal results remain authoritative. "
                "System-generated synthesis for authorized officer review."
            ),
        )

    @staticmethod
    async def generate_dossier_pdf(
        db: AsyncSession,
        dossier: InvestigationDossier,
    ) -> bytes:
        """
        Generates the consolidated ReportLab PDF for an investigation dossier.
        """
        from app.models.inspection_image import InspectionImage
        from app.services.dossier_pdf_service import build_dossier_pdf_report

        synthesis = await DossierService.get_dossier_synthesis(db, dossier)
        evidence_hashes = []
        insp_ids = [di.inspection_id for di in (dossier.dossier_inspections or [])]
        if insp_ids:
            img_stmt = select(InspectionImage).where(
                InspectionImage.inspection_id.in_(insp_ids),
                InspectionImage.sha256_hash.isnot(None),
            )
            img_res = await db.execute(img_stmt)
            images = img_res.scalars().all()
            for img in images:
                type_val = getattr(img.image_type, "value", str(img.image_type))
                evidence_hashes.append({
                    "label": f"Inspection {str(img.inspection_id)[:8]} Photo ({type_val})",
                    "sha256": img.sha256_hash,
                })

        return build_dossier_pdf_report(dossier, synthesis, evidence_hashes)
