from fastapi import APIRouter

from app.routes import (
    auth_routes,
    calendar_routes,
    counter_routes,
    health_routes,
    ml_routes,
    queue_routes,
    section_routes,
    staff_routes,
    store_config_routes,
    store_routes,
)

api_router = APIRouter()
api_router.include_router(auth_routes.router)
api_router.include_router(health_routes.router, tags=["health"])
api_router.include_router(queue_routes.router)
api_router.include_router(store_routes.router)
api_router.include_router(store_config_routes.router)
api_router.include_router(calendar_routes.router)
api_router.include_router(section_routes.router)
api_router.include_router(counter_routes.router)
api_router.include_router(staff_routes.router)
api_router.include_router(ml_routes.router)
