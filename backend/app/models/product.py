from typing import List, TYPE_CHECKING
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.enums import ProductCategory
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    commodity_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    manufacturer_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, name="product_category", native_enum=True),
        default=ProductCategory.GENERAL,
        nullable=False,
    )
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    inspections: Mapped[List["Inspection"]] = relationship("Inspection", back_populates="product")

