import uuid
from typing import List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enums import CheckResult, ViolationSeverity, ViolationStatus
from app.models.compliance_check import ComplianceCheck
from app.models.legal_rule import LegalRule
from app.models.violation import Violation


def get_violation_severity(rule_code: str | None) -> ViolationSeverity:
    """Determines statutory violation severity based on LMPC 2011 rule importance."""
    if not rule_code:
        return ViolationSeverity.MEDIUM

    high_severity_codes = {
        "LMPC-R6-MRP",
        "LMPC-R6-NET-QUANTITY",
        "LMPC-R6-MANUFACTURER",
        "LMPC-R6-COMMODITY-NAME",
        "LMPC-R18-DUAL-MRP",
    }
    medium_severity_codes = {
        "LMPC-R6-DATE",
        "LMPC-R6-CONSUMER-CARE",
        "LMPC-R6-ORIGIN",
        "LMPC-R7-FONT-HEIGHT",
    }

    if rule_code in high_severity_codes:
        return ViolationSeverity.HIGH
    elif rule_code in medium_severity_codes:
        return ViolationSeverity.MEDIUM
    else:
        return ViolationSeverity.LOW


async def generate_violations_for_inspection(
    db: AsyncSession,
    inspection_id: uuid.UUID,
    checks: List[ComplianceCheck],
) -> List[Violation]:
    """
    Generates structured Violation records for every failed ComplianceCheck.
    Idempotent: Replaces open automated violations for the inspection.
    """
    # Delete existing open violations for this inspection
    del_stmt = delete(Violation).where(
        Violation.inspection_id == inspection_id,
        Violation.status == ViolationStatus.OPEN,
    )
    await db.execute(del_stmt)

    # Pre-fetch all legal rules to avoid any lazy loading / greenlet issues
    rules_stmt = select(LegalRule)
    rules_res = await db.execute(rules_stmt)
    rules_map = {r.id: r for r in rules_res.scalars().all()}

    violations: List[Violation] = []
    for check in checks:
        if check.result == CheckResult.FAIL:
            rule = rules_map.get(check.legal_rule_id)
            rule_code = rule.rule_code if rule else None
            rule_title = rule.title if rule else "Non-compliant Declaration"
            rule_citation = rule.source_reference if rule else "LMPC Rules, 2011"
            severity = get_violation_severity(rule_code)

            title = f"Violation: {rule_title}"
            desc = check.reason or f"Mandatory declaration check failed for field '{check.field_name}'."
            if check.observed_value and check.observed_value != "NOT DECLARED":
                desc += f" (Observed value: {check.observed_value})"

            violation = Violation(
                inspection_id=inspection_id,
                compliance_check_id=check.id,
                severity=severity,
                title=title,
                description=desc,
                rule_citation=rule_citation,
                status=ViolationStatus.OPEN,
            )
            db.add(violation)
            violations.append(violation)

    await db.commit()
    for v in violations:
        await db.refresh(v)

    return violations

