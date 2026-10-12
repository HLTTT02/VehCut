from app.ai.detection.yolo_detection_service import YoloDetectionService
from app.ai.tracking.bytetrack_tracking_service import ByteTrackTrackingService
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.services.processing_service import ProcessingService
from app.services.review_service import ReviewService
from app.storage.local_storage import LocalStorageService
from app.video.clip_service import ClipService
from app.video.video_service import VideoService
from pathlib import Path

_detection_service: YoloDetectionService | None = None

def preload_detection_model(**_kwargs) -> None:
    """Celery worker-process startup hook: load YOLO once, before any frame task."""
    global _detection_service
    if _detection_service is None:
        _detection_service = YoloDetectionService(
            model_path=settings.yolo_model_path,
            confidence_threshold=settings.yolo_confidence_threshold,
            device=settings.yolo_device,
            image_size=settings.yolo_image_size,
        )

def _get_detection_service() -> YoloDetectionService:
    preload_detection_model()
    assert _detection_service is not None
    return _detection_service

def build_processing_service() -> tuple[ProcessingService, object]:
    """Worker-only composition root. Caller owns and closes the DB session."""
    session = SessionLocal()
    storage = LocalStorageService(Path(settings.storage_root), settings.storage_public_base_url)
    video_adapter = VideoService()
    service = ProcessingService(
        video_repository=VideoRepository(session),
        job_repository=JobRepository(session),
        track_repository=VehicleTrackRepository(session),
        clip_repository=ClipRepository(session),
        storage_service=storage,
        video_service=video_adapter,
        detection_service=_get_detection_service(),
        tracking_service=ByteTrackTrackingService(),
        clip_service=ClipService(video_adapter, storage),
        review_service=ReviewService(),
    )
    return service, session
