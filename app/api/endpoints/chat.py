from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.api.dependencies.current_user import CurrentBuyerDep, CurrentUserDep
from app.api.dependencies.policies import ChatPoliciesDep, get_chat_policies
from app.api.dependencies.services import ChatServiceDep, MediaServiceDep, get_chat_service
from app.core.exceptions import ForbiddenError
from app.core.websockets import websocket_manager
from app.db.database import async_session
from app.schemas.chat import ChatMessageCreate, ChatMessageRespond, ChatRoomCreate, ChatRoomRespond
from app.schemas.media import UploadUrlRequest, UploadUrlResponse

router = APIRouter()


@router.post("/", response_model=ChatRoomRespond, status_code=201)
async def create_chat_room(
    data: ChatRoomCreate, current_buyer: CurrentBuyerDep, service: ChatServiceDep, policies: ChatPoliciesDep
):
    return await service.create_room(data.seller_id, current_buyer)


@router.get("/{room_id}/history", response_model=list[ChatMessageRespond])
async def get_chat_history(
    room_id: str,
    current_user: CurrentUserDep,
    service: ChatServiceDep,
    policies: ChatPoliciesDep,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    room = await service.get_room(room_id)
    policies.read.apply(current_user, room)
    return await service.get_chat_history(room_id, limit, offset)


@router.post("/{room_id}/attachment-url", response_model=UploadUrlResponse)
async def get_chat_attachment_upload_url(
    room_id: str,
    request: UploadUrlRequest,
    chat_service: ChatServiceDep,
    policies: ChatPoliciesDep,
    media_service: MediaServiceDep,
    current_user: CurrentUserDep,
) -> Any:
    room = await chat_service.get_room(room_id)
    policies.read.apply(current_user, room)
    object_key = f"chats/{room_id}/{current_user.id}/{request.file_name}"
    presigned_data = await media_service.generate_presigned_upload_post(
        object_name=object_key, file_type=request.file_type
    )
    return UploadUrlResponse(url=presigned_data["url"], fields=presigned_data["fields"])


@router.websocket("/{room_id}")
async def websocket_chat_endpoint(websocket: WebSocket, room_id: str, current_user: CurrentUserDep):
    async with async_session() as session:
        chat_service = get_chat_service(session)
        chat_policies = get_chat_policies()
        try:
            room = await chat_service.get_room(room_id)
            chat_policies.read.apply(current_user, room)
        except ForbiddenError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    await websocket_manager.connect(websocket, room_id, str(current_user.id))
    try:
        while True:
            data = await websocket.receive_text()
            try:
                validated_data = ChatMessageCreate(text=data)
            except ValidationError:
                await websocket.send_json({"error": "Invalid message format"})
                continue
            async with async_session() as session:
                chat_service = get_chat_service(session)
                new_message = await chat_service.save_message(
                    room_id=room_id,
                    text=validated_data.text,
                    current_user=current_user,
                    attachment_url=validated_data.attachment_url,
                )
                message_payload = ChatMessageRespond.model_validate(new_message).model_dump(mode="json")
            await websocket_manager.broadcast_to_room(room_id, message_payload)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, room_id, str(current_user.id))
