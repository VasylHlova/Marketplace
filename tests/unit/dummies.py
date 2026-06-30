import uuid
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar


class DummyModel:
    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, "id"):
            self.id = str(uuid.uuid4())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.__dict__ == other.__dict__


ModelType = TypeVar("ModelType", bound=DummyModel)


class DummyCRUDRepository(Generic[ModelType]):
    def __init__(self):
        self.session = "dummy"
        self.data: dict[str, ModelType] = {}
        self.should_fail = False
        self.fail_on_create = False
        self.fail_on_update = False
        self.fail_on_delete = False
        self.model_class = DummyModel

    def _check_fail(self):
        if self.should_fail:
            raise Exception("DB error")

    async def create(self, data: dict[str, Any]) -> ModelType:
        self._check_fail()
        if self.fail_on_create:
            raise Exception("DB error")
        obj = self.model_class(**data)
        if not getattr(obj, "id", None):
            obj.id = str(uuid.uuid4())
        self.data[obj.id] = obj
        return obj

    async def update(self, instance: ModelType, update_data: dict[str, Any]) -> ModelType:
        self._check_fail()
        if self.fail_on_update:
            raise Exception("DB error")
        for k, v in update_data.items():
            setattr(instance, k, v)
        self.data[instance.id] = instance
        return instance

    async def delete(self, instance: ModelType) -> None:
        self._check_fail()
        if self.fail_on_delete:
            raise Exception("DB error")
        self.data.pop(instance.id, None)

    async def get_by_id(self, id: str) -> ModelType | None:
        self._check_fail()
        return self.data.get(id)

    async def get_all(self, limit: int, offset: int) -> tuple[list[ModelType], int]:
        self._check_fail()
        items = list(self.data.values())
        return (items[offset : offset + limit], len(items))

    async def commit(self) -> None:
        self._check_fail()

    async def rollback(self) -> None:
        pass

    async def roll_back(self) -> None:
        pass


class DummyUserRepository(DummyCRUDRepository):
    async def get_by_email(self, email: str) -> DummyModel | None:
        self._check_fail()
        for u in self.data.values():
            if getattr(u, "email", None) == email:
                return u
        return None

    async def get_all_sellers(self, limit: int, offset: int) -> tuple[list[DummyModel], int]:
        self._check_fail()
        sellers = [u for u in self.data.values() if getattr(u, "role", "") == "seller"]
        return (sellers[offset : offset + limit], len(sellers))


class DummyProductRepository(DummyCRUDRepository):
    async def get_all_filtered_by_price(
        self, limit: int, offset: int, filters: list
    ) -> tuple[list[DummyModel], int]:
        self._check_fail()
        items = list(self.data.values())
        return (items[offset : offset + limit], len(items))

    async def decrement_stock(self, product_id: str, quantity: int) -> bool:
        self._check_fail()
        p = self.data.get(product_id)
        if p and getattr(p, "stock", 0) >= quantity:
            p.stock -= quantity
            return True
        return False

    async def increment_stock(self, product_id: str, quantity: int) -> bool:
        self._check_fail()
        p = self.data.get(product_id)
        if p:
            p.stock += quantity
            return True
        return False


class DummyOrderRepository(DummyCRUDRepository):
    async def get_all_by_buyer(
        self, buyer_id: str, limit: int, offset: int
    ) -> tuple[list[DummyModel], int]:
        self._check_fail()
        orders = [o for o in self.data.values() if getattr(o, "buyer_id", None) == buyer_id]
        return (orders[offset : offset + limit], len(orders))

    async def get_seller_summary(self, seller_id: str) -> dict:
        self._check_fail()
        return {"seller_id": seller_id, "total_orders": 0, "total_revenue": 0.0}


class DummyOrderItemRepository(DummyCRUDRepository):
    async def get_all_by_order(
        self, order_id: str, limit: int, offset: int
    ) -> tuple[list[DummyModel], int]:
        self._check_fail()
        items = [i for i in self.data.values() if getattr(i, "order_id", None) == order_id]
        return (items[offset : offset + limit], len(items))

    async def get_all_by_order_unpaginated(self, order_id: str) -> list[DummyModel]:
        self._check_fail()
        return [i for i in self.data.values() if getattr(i, "order_id", None) == order_id]

    async def get_seller_summary(self, seller_id: str) -> dict:
        self._check_fail()
        return {"total_orders": 3, "total_revenue": 150.0}


class DummyChatRoomRepository(DummyCRUDRepository):
    async def get_by_users(self, buyer_id: str, seller_id: str) -> DummyModel | None:
        self._check_fail()
        for r in self.data.values():
            if getattr(r, "buyer_id", None) == buyer_id and getattr(r, "seller_id", None) == seller_id:
                return r
        return None


class DummyChatMessageRepository(DummyCRUDRepository):
    async def get_all_by_room(self, room_id: str, limit: int, offset: int) -> tuple[list[DummyModel], int]:
        self._check_fail()
        msgs = [m for m in self.data.values() if getattr(m, "room_id", None) == room_id]
        return (msgs[offset : offset + limit], len(msgs))


class DummyTokenRepository:
    def __init__(self):
        self.data = {}

    async def save_token(self, key: str, ttl_seconds: int, value: str = "active") -> None:
        self.data[key] = value

    async def get_token(self, key: str) -> str | None:
        return self.data.get(key)

    async def delete_token(self, key: str) -> None:
        if key in self.data:
            del self.data[key]


class DummyStorageClient:
    def __init__(self, download_content: bytes = b"", objects=None):
        self.download_content = download_content
        self.objects = objects or []
        self.downloads = []
        self.uploads = []
        self.deletes = []

    async def download(self, object_key: str, dest_path: str) -> None:
        self.downloads.append((object_key, dest_path))
        if self.download_content:
            with open(dest_path, "wb") as f:
                f.write(self.download_content)

    async def upload(self, object_key: str, src_path: str, content_type: str) -> None:
        self.uploads.append((object_key, src_path, content_type))

    async def delete(self, object_key: str) -> None:
        self.deletes.append(object_key)

    async def list_objects(self):
        for obj in self.objects:
            yield obj


class DummyMediaRepository:
    def __init__(self, active_urls=None):
        self.active_urls = active_urls or set()
        self.product_updates: list[tuple[str, str]] = []
        self.avatar_updates: list[tuple[str, str]] = []
        self.chat_updates: list[tuple[str, str]] = []

    async def update_product_media(self, product_id: str, new_url: str) -> None:
        self.product_updates.append((product_id, new_url))

    async def update_user_avatar(self, user_id: str, new_url: str) -> None:
        self.avatar_updates.append((user_id, new_url))

    async def update_chat_media(self, original_url: str, new_url: str) -> None:
        self.chat_updates.append((original_url, new_url))

    async def get_active_urls(self) -> set[str]:
        return self.active_urls
