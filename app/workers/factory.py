from app.ai.detection.yolo_detection_service import YoloDetectionService
from app.ai.ocr.tesseract_plate_ocr_service import TesseractPlateOcrService
from app.ai.plate.yolo_plate_detection_service import YoloPlateDetectionService
from app.ai.tracking.bytetrack_tracking_service import ByteTrackTrackingService
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.roi_zone_repository import RoiZoneRepository
from app.repositories.plate_inspection_repository import PlateInspectionRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.suspicious_event_repository import SuspiciousEventRepository
from app.services.plate_inspection_service import PlateInspectionService
from app.services.processing_service import ProcessingService
from app.services.review_service import ReviewService
from app.storage.local_storage import LocalStorageService
from app.video.clip_service import ClipService
from app.video.video_service import VideoService
from pathlib import Path

_detection_service: YoloDetectionService | None = None
_plate_inspection_service: PlateInspectionService | None = None

def preload_detection_model(**_kwargs) -> None:
    """Celery worker-process startup hook: load YOLO once, before any frame task."""
    global _detection_service
    if _detection_service is None:
        _detection_service = YoloDetectionService(
            model_path=settings.yolo_model_path,
            confidence_threshold=settings.yolo_confidence_threshold,
            device=settings.yolo_device,
            image_size=settings.yolo_image_size,
            allowed_classes=settings.detection_classes,
        )

def _get_detection_service() -> YoloDetectionService:
    preload_detection_model()
    assert _detection_service is not None
    return _detection_service

def _get_plate_inspection_service() -> PlateInspectionService:
    global _plate_inspection_service
    if _plate_inspection_service is None:
        _plate_inspection_service = PlateInspectionService(
            YoloPlateDetectionService(
                model_path=settings.plate_model_path,
                confidence_threshold=settings.plate_confidence_threshold,
                device=settings.yolo_device,
                image_size=settings.yolo_image_size,
            ),
            TesseractPlateOcrService(),
        )
    return _plate_inspection_service

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
        roi_repository=RoiZoneRepository(session),
        plate_inspection_repository=PlateInspectionRepository(session),
        review_repository=ReviewRepository(session),
        suspicious_event_repository=SuspiciousEventRepository(session),
        storage_service=storage,
        video_service=video_adapter,
        detection_service=_get_detection_service(),
        tracking_service=ByteTrackTrackingService(),
        clip_service=ClipService(video_adapter, storage),
        review_service=ReviewService(),
        plate_inspection_service=_get_plate_inspection_service(),
    )
    return service, session
