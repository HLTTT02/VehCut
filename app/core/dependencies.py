from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.repositories.video_repository import VideoRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.clip_repository import ClipRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.roi_zone_repository import RoiZoneRepository
from app.repositories.suspicious_event_repository import SuspiciousEventRepository
from app.services.video_service import VideoService
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.services.clip_review_service import ClipReviewService
from app.services.statistics_service import StatisticsService
from app.services.roi_service import RoiService
from app.services.suspicious_event_service import SuspiciousEventService
from app.storage.local_storage import LocalStorageService
from app.storage.service import StorageService
from app.core.config import settings
from pathlib import Path
from app.ai.detection.yolo_detection_service import YoloDetectionService

DbSession = Annotated[Session, Depends(get_db_session)]

def get_video_repository(session: DbSession) -> VideoRepository:
    return VideoRepository(session)

def get_video_service(
    repository: Annotated[VideoRepository, Depends(get_video_repository)],
) -> VideoService:
    return VideoService(repository, get_storage_service())

def get_job_repository(session: DbSession) -> JobRepository:
    return JobRepository(session)

def get_track_repository(session: DbSession) -> VehicleTrackRepository:
    return VehicleTrackRepository(session)

def get_clip_repository(session: DbSession) -> ClipRepository:
    return ClipRepository(session)

def get_review_repository(session: DbSession) -> ReviewRepository:
    return ReviewRepository(session)

def get_roi_repository(session: DbSession) -> RoiZoneRepository:
    return RoiZoneRepository(session)

def get_suspicious_event_repository(session: DbSession) -> SuspiciousEventRepository:
    return SuspiciousEventRepository(session)

def get_suspicious_event_service(repository: Annotated[SuspiciousEventRepository, Depends(get_suspicious_event_repository)]) -> SuspiciousEventService:
    return SuspiciousEventService(repository)

def get_processing_service(
    video_repository: Annotated[VideoRepository, Depends(get_video_repository)],
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
) -> ProcessingService:
    """HTTP only creates queued jobs; the worker wires full pipeline dependencies."""
    return ProcessingService(video_repository, job_repository)

def get_query_service(
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
    track_repository: Annotated[VehicleTrackRepository, Depends(get_track_repository)],
    clip_repository: Annotated[ClipRepository, Depends(get_clip_repository)],
    video_repository: Annotated[VideoRepository, Depends(get_video_repository)],
) -> QueryService:
    return QueryService(job_repository, track_repository, clip_repository, video_repository)

def get_statistics_service(
    video_repository: Annotated[VideoRepository, Depends(get_video_repository)],
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
    track_repository: Annotated[VehicleTrackRepository, Depends(get_track_repository)],
    clip_repository: Annotated[ClipRepository, Depends(get_clip_repository)],
) -> StatisticsService:
    return StatisticsService(video_repository, job_repository, track_repository, clip_repository)

def get_clip_review_service(
    clip_repository: Annotated[ClipRepository, Depends(get_clip_repository)],
    review_repository: Annotated[ReviewRepository, Depends(get_review_repository)],
) -> ClipReviewService:
    return ClipReviewService(clip_repository, review_repository)

def get_roi_service(
    video_repository: Annotated[VideoRepository, Depends(get_video_repository)],
    roi_repository: Annotated[RoiZoneRepository, Depends(get_roi_repository)],
) -> RoiService:
    return RoiService(video_repository, roi_repository)

def get_storage_service() -> StorageService:
    """Replace this binding with S3StorageService without changing ProcessingService."""
    return LocalStorageService(Path(settings.storage_root), settings.storage_public_base_url)

@lru_cache(maxsize=1)
def get_live_detection_service() -> YoloDetectionService:
    """Keep one YOLO instance for on-demand boxes in the web preview."""
    return YoloDetectionService(
        settings.yolo_model_path,
        settings.yolo_confidence_threshold,
        settings.yolo_device,
        settings.yolo_image_size,
        settings.detection_classes,
    )
