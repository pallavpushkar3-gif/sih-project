from celery import Celery  # type: ignore[import-untyped]

from fleet_maintenance.settings import get_settings

settings = get_settings()
app = Celery(
    "fleet_maintenance",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=[
        "fleet_maintenance.workers.planning_tasks",
        "fleet_maintenance.workers.simulation_tasks",
        "fleet_maintenance.workers.job_tasks",
    ],
)
app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_ignore_result=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    worker_enable_remote_control=False,
    task_publish_retry=True,
    broker_transport_options={"confirm_publish": True},
)
