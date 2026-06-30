import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import ProductFactory, UserFactory


@pytest.mark.asyncio
async def test_media_repo_get_active_urls(media_repo, db_session: AsyncSession, faker):
    from app.models.user import User
    from app.models.product import Product
    user: User = UserFactory(avatar_url=f"http://example.com/{faker.uuid4()}.jpg")  # type: ignore[assignment]
    db_session.add(user)

    product: Product = ProductFactory(seller_id=user.id, image_url=f"http://example.com/{faker.uuid4()}.jpg")  # type: ignore[assignment]
    db_session.add(product)

    await db_session.commit()

    active_urls = await media_repo.get_active_urls()
    assert user.avatar_url in active_urls
    assert product.image_url in active_urls


@pytest.mark.asyncio
async def test_media_repo_update_product_media(media_repo, db_session: AsyncSession, faker):
    from app.models.user import User
    from app.models.product import Product
    user: User = UserFactory()  # type: ignore[assignment]
    db_session.add(user)
    await db_session.flush()

    product: Product = ProductFactory(seller_id=user.id, image_url="old_url")  # type: ignore[assignment]
    db_session.add(product)
    await db_session.commit()

    new_url = f"http://example.com/{faker.uuid4()}.jpg"
    await media_repo.update_product_media(product.id, new_url)

    await db_session.refresh(product)
    assert product.image_url == new_url
