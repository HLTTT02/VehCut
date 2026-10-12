from celery import Celery
from celery.signals import worker_process_init
from app.core.config import settings

celery_app = Celery(
    "vehcut",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    # The worker imports its task module itself; it must not rely on FastAPI
    # controllers importing it before a job is queued.
    imports=("app.workers.tasks",),
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_soft_time_limit=settings.celery_task_soft_time_limit_seconds,
    task_time_limit=settings.celery_task_time_limit_seconds,
    worker_prefetch_multiplier=1,
)

@worker_process_init.connect
def preload_worker_models(**kwargs) -> None:
    from app.workers.factory import preload_detection_model
    preload_detection_model(**kwargs)
