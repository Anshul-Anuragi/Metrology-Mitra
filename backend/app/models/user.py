from typing import List, TYPE_CHECKING
from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import UserRole
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.report import Report


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
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="generator")
