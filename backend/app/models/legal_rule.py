import datetime
from typing import Any, Dict, List, TYPE_CHECKING
from sqlalchemy import Boolean, Date, Enum, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import RuleType
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.compliance_check import ComplianceCheck


class LegalRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "legal_rules"

    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rule_type: Mapped[RuleType] = mapped_column(
        Enum(RuleType, name="rule_type", native_enum=True),
        default=RuleType.REQUIRED_FIELD,
        nullable=False,
    )
    parameters: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="2011.1")
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)  # e.g. "Rule 6(1)(e), LMPC Rules 2011"
    penalty_clause: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g. "Section 36(1) of LM Act 2009"
    category_applicability: Mapped[List[str] | None] = mapped_column(JSONB, nullable=True)
    
    # Regulatory Intelligence & Versioning (Phase 1.7)
    effective_from: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="BOTH", nullable=False)  # PHYSICAL_PACKAGE, ECOMMERCE, BOTH
    source_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    compliance_checks: Mapped[List["ComplianceCheck"]] = relationship(
        "ComplianceCheck", back_populates="legal_rule"
    )

    __table_args__ = (
        UniqueConstraint("rule_code", "version", name="unique_rule_version"),
    )
