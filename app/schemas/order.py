from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums.order import OrderStatus


class SellerSummaryRespond(BaseModel):
    seller_id: str
    total_orders: int
    total_revenue: float


class OrderItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, le=100000)


class OrderItemRespond(BaseModel):
    id: str
    product_id: str
    quantity: int
    price_at_purchase: float
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderBuyerRespond(BaseModel):
    id: str
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemRespond] = []
    model_config = {"from_attributes": True}


class OrdersBuyerRespond(BaseModel):
    data: list[OrderBuyerRespond]
    count: int


class OrderSellerRespond(BaseModel):
    id: str
    buyer_id: str
    status: OrderStatus
    created_at: datetime
    items: list[OrderItemRespond] = []
    model_config = {"from_attributes": True}


class OrdersSellerRespond(BaseModel):
    data: list[OrderSellerRespond]
    count: int
