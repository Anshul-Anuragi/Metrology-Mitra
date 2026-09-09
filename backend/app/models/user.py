from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import UserRole
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.gravimetric_test import GravimetricTest
    from app.models.inspection import Inspection
    from app.models.inspection_batch import InspectionBatch
    from app.models.report import Report
    from app.models.dossier import InvestigationDossier



class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.INSPECTOR,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships (explicit foreign_keys to resolve multiple User->Inspection relationships)
    inspections: Mapped[List["Inspection"]] = relationship(
        "Inspection",
        back_populates="inspector",
        foreign_keys="[Inspection.inspector_id]",
        cascade="all, delete-orphan",
    )
    batches: Mapped[List["InspectionBatch"]] = relationship("InspectionBatch", back_populates="created_by")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="generator")
    gravimetric_tests: Mapped[List["GravimetricTest"]] = relationship("GravimetricTest", back_populates="created_by")
    managed_dossiers: Mapped[List["InvestigationDossier"]] = relationship(
        "InvestigationDossier",
        back_populates="lead_supervisor",
        foreign_keys="[InvestigationDossier.lead_supervisor_id]",
        lazy="selectin",
    )

