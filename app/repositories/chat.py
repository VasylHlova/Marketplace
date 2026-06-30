from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatRoom
from app.repositories.base.crud import CRUDRepository
from app.repositories.base.mixins import GetAllByFieldMixin


class ChatRoomRepository(CRUDRepository[ChatRoom], GetAllByFieldMixin[ChatRoom]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChatRoom)

    async def get_all_by_buyer(self, buyer_id: str, limit: int, offset: int) -> tuple[list[ChatRoom], int]:
        return await self.get_all_by_field(
            column=self.model.buyer_id, value=buyer_id, limit=limit, offset=offset
        )

    async def get_all_by_seller(
        self, seller_id: str, limit: int, offset: int
    ) -> tuple[list[ChatRoom], int]:
        return await self.get_all_by_field(
            column=self.model.seller_id, value=seller_id, limit=limit, offset=offset
        )

    async def get_by_users(self, buyer_id: str, seller_id: str) -> ChatRoom | None:
        result = await self.session.execute(
            select(self.model).where(
                and_(self.model.buyer_id == buyer_id, self.model.seller_id == seller_id)
            )
        )
        return result.scalar_one_or_none()


class ChatMessageRepository(CRUDRepository[ChatMessage], GetAllByFieldMixin[ChatMessage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChatMessage)

    async def get_all_by_room(self, room_id: str, limit: int, offset: int) -> tuple[list[ChatMessage], int]:
        return await self.get_all_by_field(
            column=self.model.room_id,
            value=room_id,
            limit=limit,
            offset=offset,
            order_by=self.model.created_at.asc(),
        )
