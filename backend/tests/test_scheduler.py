from app.core.scheduler import create_scheduler


def test_scheduler_registers_nightly_queue_cleanup_job() -> None:
    scheduler = create_scheduler()

    job = scheduler.get_job("nightly_queue_cleanup")

    assert job is not None
    assert job.name == "Nightly queue cleanup"
    assert str(job.trigger) == "cron[hour='0', minute='5']"
    assert job.max_instances == 1
    assert job.coalesce is True
