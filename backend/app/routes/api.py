from fastapi import APIRouter

from app.core.config import settings
from app.routes import (
    analytics_routes,
    auth_routes,
    calendar_routes,
    counter_routes,
    demo_tools_routes,
    health_routes,
    ml_routes,
    notification_routes,
    queue_routes,
    section_routes,
    staff_routes,
    store_config_routes,
    store_routes,
    trial_routes,
)

api_router = APIRouter()
api_router.include_router(analytics_routes.router)
api_router.include_router(auth_routes.router)
api_router.include_router(health_routes.router, tags=["health"])
api_router.include_router(store_routes.router)
api_router.include_router(staff_routes.router)
api_router.include_router(notification_routes.router)

if settings.ENABLE_CHECKOUT_QUEUE:
    api_router.include_router(queue_routes.router)
    api_router.include_router(store_config_routes.router)
    api_router.include_router(calendar_routes.router)
    api_router.include_router(section_routes.router)
    api_router.include_router(counter_routes.router)

if settings.ENABLE_CHECKOUT_QUEUE or settings.ENABLE_TRIAL_QUEUE:
    api_router.include_router(ml_routes.router)

if settings.ENABLE_TRIAL_QUEUE:
    api_router.include_router(trial_routes.router)

if settings.ENABLE_DEMO_TOOLS:
    api_router.include_router(demo_tools_routes.router)
