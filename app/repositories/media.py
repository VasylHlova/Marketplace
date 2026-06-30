from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage
from app.models.product import Product
from app.models.user import User


class SqlMediaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_urls(self) -> set[str]:
        active_urls: set[str] = set()
        users_res = await self.session.execute(select(User.avatar_url).where(User.avatar_url.is_not(None)))
        active_urls.update(row[0] for row in users_res.fetchall())
        products_res = await self.session.execute(
            select(Product.image_url).where(Product.image_url.is_not(None))
        )
        active_urls.update(row[0] for row in products_res.fetchall())
        chats_res = await self.session.execute(
            select(ChatMessage.attachment_url).where(ChatMessage.attachment_url.is_not(None))
        )
        active_urls.update(row[0] for row in chats_res.fetchall())
        return active_urls

    async def update_product_media(self, product_id: str, new_url: str) -> None:
        await self.session.execute(
            update(Product).where(Product.id == product_id).values(image_url=new_url)
        )
        await self.session.commit()

    async def update_user_avatar(self, user_id: str, new_url: str) -> None:
        await self.session.execute(update(User).where(User.id == user_id).values(avatar_url=new_url))
        await self.session.commit()

    async def update_chat_media(self, original_url: str, new_url: str) -> None:
        await self.session.execute(
            update(ChatMessage)
            .where(ChatMessage.attachment_url == original_url)
            .values(attachment_url=new_url)
        )
        await self.session.commit()
