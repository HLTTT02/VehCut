from celery.exceptions import SoftTimeLimitExceeded
from app.workers.celery_app import celery_app
from app.workers.factory import build_processing_service
from app.core.config import settings

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=settings.celery_task_max_retries,
    name="vehcut.process_video_job",
)
def process_video_job(self, job_id: str) -> dict[str, int | str]:
    """Thin Celery entry point: business work belongs exclusively to ProcessingService."""
    service, session = build_processing_service()
    try:
        outcome = service.process(job_id)
        return {
            "job_id": outcome.job_id,
            "processed_tracks": outcome.processed_tracks,
            "created_clips": outcome.created_clips,
        }
    except SoftTimeLimitExceeded:
        # ProcessingService's failure handling updates the job on normal exceptions.
        # This explicit error is retained for a soft timeout raised outside the pipeline.
        raise
    finally:
        session.close()
