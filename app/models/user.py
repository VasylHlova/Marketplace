import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums.user import UserRole
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.chat import ChatRoom
    from app.models.order import Order
    from app.models.product import Product


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(300))
    role: Mapped[UserRole] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    orders: Mapped[list["Order"]] = relationship(back_populates="buyer")
    products: Mapped[list["Product"]] = relationship(back_populates="seller")
    chats_as_buyer: Mapped[list["ChatRoom"]] = relationship(
        foreign_keys="ChatRoom.buyer_id", back_populates="buyer"
    )
    chats_as_seller: Mapped[list["ChatRoom"]] = relationship(
        foreign_keys="ChatRoom.seller_id", back_populates="seller"
    )
