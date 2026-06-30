import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    buyer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id], back_populates="chats_as_buyer")
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id], back_populates="chats_as_seller")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="room", order_by="ChatMessage.created_at"
    )
    __table_args__ = (
        CheckConstraint("buyer_id != seller_id", name="check_chat_room_different_users"),
        UniqueConstraint("buyer_id", "seller_id", name="uq_chat_room_buyer_seller"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str] = mapped_column(ForeignKey("chat_rooms.id"))
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    attachment_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
