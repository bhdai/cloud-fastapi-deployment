# ==============================================================================
# Pydantic Schemas
# ==============================================================================
#
# Separate from ORM models to keep a clear boundary between what the database
# stores and what the API accepts / returns. Using `from_attributes=True`
# allows direct conversion from SQLAlchemy model instances.

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ── Category ──────────────────────────────────────────────────────────────────


class CategoryBase(BaseModel):
    name: str
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    """All fields optional — only provided fields are updated."""

    name: str | None = None
    description: str | None = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Product ───────────────────────────────────────────────────────────────────


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional — only provided fields are updated."""

    name: str | None = None
    description: str | None = None
    price: float | None = None
    category_id: int | None = None


class ProductResponse(ProductBase):
    id: int
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
