from loguru import logger

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.metrics import CHAT_MESSAGES_SENT, CHAT_ROOMS_CREATED
from app.models.chat import ChatMessage, ChatRoom
from app.models.user import User
from app.repositories import ChatMessageRepositoryProtocol, ChatRoomRepositoryProtocol


class ChatService:
    def __init__(
        self, room_repo: ChatRoomRepositoryProtocol, msg_repo: ChatMessageRepositoryProtocol
    ) -> None:
        self.room_repo = room_repo
        self.msg_repo = msg_repo

    async def create_room(self, seller_id: str, current_user: User) -> ChatRoom:
        if seller_id == str(current_user.id):
            logger.warning(f"User {current_user.id} attempted to create a chat room with themselves")
            raise BadRequestError("You cannot create a chat room with yourself")
        existing_room = await self.room_repo.get_by_users(
            buyer_id=str(current_user.id), seller_id=seller_id
        )
        if existing_room:
            return existing_room
        try:
            new_room = await self.room_repo.create(
                {"buyer_id": str(current_user.id), "seller_id": seller_id}
            )
            await self.room_repo.commit()

            logger.info(
                f"Created new chat room {new_room.id} between buyer "
                f"{current_user.id} and seller {seller_id}"
            )
            CHAT_ROOMS_CREATED.inc()

            return new_room
        except Exception as e:
            logger.error(f"Failed to create chat room: {e}")
            await self.room_repo.roll_back()
            raise

    async def get_room(self, room_id: str) -> ChatRoom:
        room = await self.room_repo.get_by_id(id=room_id)
        if not room:
            logger.warning(f"Chat room not found: {room_id}")
            raise NotFoundError("Chat room not found")
        return room

    async def get_chat_history(self, room_id: str, limit: int, offset: int) -> list[ChatMessage]:
        await self.get_room(room_id)
        messages, _ = await self.msg_repo.get_all_by_room(room_id=room_id, limit=limit, offset=offset)
        return messages

    async def save_message(
        self, room_id: str, text: str, current_user: User, attachment_url: str | None = None
    ) -> ChatMessage:
        try:
            new_message = await self.msg_repo.create(
                {
                    "room_id": room_id,
                    "sender_id": str(current_user.id),
                    "text": text,
                    "attachment_url": attachment_url,
                }
            )
            await self.msg_repo.commit()

            logger.info(f"Message sent in room {room_id} by user {current_user.id}")
            CHAT_MESSAGES_SENT.inc()

            return new_message
        except Exception as e:
            logger.error(f"Failed to save message in room {room_id}: {e}")
            await self.msg_repo.roll_back()
            raise
