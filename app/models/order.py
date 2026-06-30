import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums.order import OrderStatus
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatus] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id], back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column()
    price_at_purchase: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(
        foreign_keys=[product_id], lazy="joined", overlaps="order_items"
    )
    __table_args__ = (
        CheckConstraint("quantity > 0 AND quantity <= 100000", name="check_quantity_range"),
        CheckConstraint(
            "price_at_purchase > 0 AND price_at_purchase <= 9999999999999",
            name="check_price_at_purchase_range",
        ),
    )
