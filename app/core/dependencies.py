from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db_session
from app.repositories.video_repository import VideoRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.clip_repository import ClipRepository
from app.repositories.review_repository import ReviewRepository
from app.services.video_service import VideoService
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.services.clip_review_service import ClipReviewService
from app.services.statistics_service import StatisticsService
from app.storage.local_storage import LocalStorageService
from app.storage.service import StorageService
from app.core.config import settings
from pathlib import Path

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

def get_storage_service() -> StorageService:
    """Replace this binding with S3StorageService without changing ProcessingService."""
    return LocalStorageService(Path(settings.storage_root), settings.storage_public_base_url)
