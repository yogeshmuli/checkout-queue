from fastapi import APIRouter

from app.routes import (
    trial_calendar_routes,
    trial_queue_routes,
    trial_store_config_routes,
    trial_studio_routes,
    trial_zone_routes,
)

router = APIRouter(tags=["trial-queue"])
router.include_router(trial_zone_routes.router)
router.include_router(trial_studio_routes.router)
router.include_router(trial_store_config_routes.router)
router.include_router(trial_calendar_routes.router)
router.include_router(trial_queue_routes.router)
