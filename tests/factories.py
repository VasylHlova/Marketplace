import uuid
from datetime import UTC, datetime

import factory
from faker import Faker

from app.core.enums.order import OrderStatus
from app.core.enums.user import UserRole
from app.models.chat import ChatMessage, ChatRoom
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User

faker = Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.LazyFunction(lambda: faker.password())
    role = UserRole.BUYER.value
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    seller_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.LazyFunction(lambda: faker.word())
    price = factory.Faker("pyfloat", positive=True, min_value=1.0, max_value=1000.0)
    stock = factory.Faker("pyint", min_value=1, max_value=100)
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class OrderFactory(factory.Factory):
    class Meta:
        model = Order

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    buyer_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    status = OrderStatus.ACTIVE.value
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class OrderItemFactory(factory.Factory):
    class Meta:
        model = OrderItem

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    order_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    product_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    quantity = factory.Faker("pyint", min_value=1, max_value=10)
    price_at_purchase = factory.Faker("pyfloat", positive=True, min_value=1.0, max_value=1000.0)
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class ChatRoomFactory(factory.Factory):
    class Meta:
        model = ChatRoom

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    buyer_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    seller_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class ChatMessageFactory(factory.Factory):
    class Meta:
        model = ChatMessage

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    room_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    sender_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    text = factory.LazyFunction(lambda: faker.sentence())
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
