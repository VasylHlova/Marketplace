from typing import Any

from fastapi import APIRouter, status

from app.api.dependencies.current_user import CurrentUserDep
from app.api.dependencies.policies import UserPoliciesDep
from app.api.dependencies.services import MediaServiceDep, UserServiceDep
from app.schemas.media import UploadUrlRequest, UploadUrlResponse
from app.schemas.user import UpdatePassword, UserRegister, UserRespond, UserUpdateSelf

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserRespond)
async def register_user(service: UserServiceDep, user_in: UserRegister) -> Any:
    return await service.create(email=user_in.email, password=user_in.password, role=user_in.role.value)


@router.get("/self", response_model=UserRespond)
async def read_user_self(current_user: CurrentUserDep) -> Any:
    return current_user


@router.patch("/self", response_model=UserRespond)
async def update_user_self(
    service: UserServiceDep,
    policies: UserPoliciesDep,
    user_in: UserUpdateSelf,
    current_user: CurrentUserDep,
) -> Any:
    user = await service.get_by_id(current_user.id)
    policies.update.apply(current_user, user)
    return await service.update(user_id=current_user.id, update_data=user_in.model_dump(exclude_unset=True))


@router.patch("/me/password")
async def update_password(
    service: UserServiceDep, body: UpdatePassword, current_user: CurrentUserDep
) -> Any:
    return await service.update_password(
        user=current_user, current_password=body.current_password, new_password=body.new_password
    )


@router.delete("/self", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_self(
    service: UserServiceDep, policies: UserPoliciesDep, current_user: CurrentUserDep
) -> None:
    user = await service.get_by_id(current_user.id)
    policies.delete.apply(current_user, user)
    await service.delete(user_id=current_user.id)


@router.post("/self/avatar-upload-url", response_model=UploadUrlResponse)
async def get_avatar_upload_url(
    request: UploadUrlRequest, media_service: MediaServiceDep, current_user: CurrentUserDep
) -> Any:
    object_key = f"avatars/{current_user.id}/{request.file_name}"
    presigned_data = await media_service.generate_presigned_upload_post(
        object_name=object_key, file_type=request.file_type
    )
    return UploadUrlResponse(url=presigned_data["url"], fields=presigned_data["fields"])
