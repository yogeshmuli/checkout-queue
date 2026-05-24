import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.queue_cleanup_service import QueueCleanupService


logger = logging.getLogger(__name__)


def run_nightly_queue_cleanup_job() -> None:
    with SessionLocal() as db:
        result = QueueCleanupService(db).run_nightly_cleanup()
    logger.info(
        "Nightly queue cleanup completed: checkout_tokens_cancelled=%s, "
        "trial_tokens_cancelled=%s, checkout_counters_reset=%s, "
        "trial_studios_reset=%s, ran_at=%s",
        result.checkout_tokens_cancelled,
        result.trial_tokens_cancelled,
        result.checkout_counters_reset,
        result.trial_studios_reset,
        result.ran_at.isoformat(),
    )


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
    scheduler.add_job(
        run_nightly_queue_cleanup_job,
        trigger=CronTrigger(
            hour=settings.NIGHTLY_QUEUE_CLEANUP_HOUR,
            minute=settings.NIGHTLY_QUEUE_CLEANUP_MINUTE,
            timezone=settings.SCHEDULER_TIMEZONE,
        ),
        id="nightly_queue_cleanup",
        name="Nightly queue cleanup",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60 * 30,
    )
    return scheduler
