import sys

from fastapi import FastAPI
from loguru import logger
from prometheus_client import make_asgi_app

from app.api.endpoints import auth, chat, order, product, seller, user, webhook
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

logger.remove()
logger.add(sys.stdout, serialize=True)

app = FastAPI(
    title="Marketplace API",
    version="1.0.0",
    description=(
        "REST + WebSocket marketplace: products, orders with stock management, "
        "Celery email notifications, and real-time chat."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

register_exception_handlers(app)
app.include_router(product.router, prefix=settings.API_V1_STR)
app.include_router(user.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(order.router, prefix=settings.API_V1_STR)
app.include_router(seller.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(webhook.router, prefix=settings.API_V1_STR)
