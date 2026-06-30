from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=4096)
    attachment_url: str | None = None


class ChatMessageRespond(BaseModel):
    id: str
    room_id: str
    sender_id: str
    text: str
    attachment_url: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatRoomCreate(BaseModel):
    seller_id: str


class ChatRoomRespond(BaseModel):
    id: str
    buyer_id: str
    seller_id: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatRoomWithMessages(ChatRoomRespond):
    messages: list[ChatMessageRespond] = []
