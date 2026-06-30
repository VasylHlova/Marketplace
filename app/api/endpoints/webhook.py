from typing import Any

from fastapi import APIRouter, Request

from app.api.dependencies.services import MediaServiceDep

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/minio")
async def minio_webhook(request: Request, media_service: MediaServiceDep) -> Any:
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "detail": "Invalid JSON"}

    await media_service.process_webhook_payload(payload)

    return {"status": "success"}
