import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.core.enums import ProductCategory


class ProductBase(BaseModel):
    commodity_name: str | None = None
    brand_name: str | None = None
    manufacturer_name: str | None = None
    category: ProductCategory = ProductCategory.GENERAL
    barcode: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

