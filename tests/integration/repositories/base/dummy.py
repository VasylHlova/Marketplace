import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.models.base import Base
from app.repositories.base.crud import CRUDRepository
from app.repositories.base.mixins import GetAllByFieldMixin


class DummyModel(Base):
    __tablename__ = "dummy_models"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class DummyRepository(CRUDRepository[DummyModel], GetAllByFieldMixin[DummyModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DummyModel)

    async def get_all_by_status(self, status: str, limit: int, offset: int):
        status_col = cast(InstrumentedAttribute, self.model.status)
        return await self.get_all_by_field(column=status_col, value=status, limit=limit, offset=offset)
