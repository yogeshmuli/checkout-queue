from app.core.database import SessionLocal
from app.services.queue_cleanup_service import QueueCleanupService


def main() -> None:
    with SessionLocal() as db:
        result = QueueCleanupService(db).run_nightly_cleanup()
    print(
        "Nightly queue cleanup completed: "
        f"checkout_tokens_cancelled={result.checkout_tokens_cancelled}, "
        f"trial_tokens_cancelled={result.trial_tokens_cancelled}, "
        f"checkout_counters_reset={result.checkout_counters_reset}, "
        f"trial_studios_reset={result.trial_studios_reset}, "
        f"ran_at={result.ran_at.isoformat()}"
    )


if __name__ == "__main__":
    main()
