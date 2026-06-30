import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import OrderItem
    from app.models.user import User


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(300))
    price: Mapped[float] = mapped_column()
    description: Mapped[str] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column()
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id], back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship()
    __table_args__ = (
        CheckConstraint("price > 0 AND price <= 9999999999999", name="check_price_range"),
        CheckConstraint("stock >= 0 AND stock <= 1000000", name="check_stock_range"),
    )
