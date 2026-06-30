from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    price: float = Field(gt=0, le=9999999999999)
    description: str | None = Field(default=None, max_length=50000)
    image_url: str | None = None


class ProductCreate(ProductBase):
    stock: int = Field(ge=0, le=1000000)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    price: float | None = Field(default=None, gt=0, le=9999999999999)
    stock: int | None = Field(default=None, ge=0, le=1000000)
    image_url: str | None = None


class ProductPublic(ProductBase):
    id: str
    stock: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    model_config = {"from_attributes": True}


class ProductsPublic(BaseModel):
    data: list[ProductPublic]
    count: int


class ProductOwner(ProductBase):
    id: str
    seller_id: str
    stock: int
    created_at: datetime | None = None
    model_config = {"from_attributes": True}


class ProductsOwner(BaseModel):
    data: list[ProductOwner]
    count: int
