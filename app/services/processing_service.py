from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.ai.detection.service import DetectionService
from app.ai.tracking.models import VehicleTrackState
from app.ai.tracking.service import TrackingService
from app.entities.enums import ClipStatus, ProcessingJobStatus, VideoStatus
from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.services.processing_models import ProcessingConfig, ProcessingError, ProcessingOutcome
from app.services.review_models import ReviewInput
from app.services.review_service import ReviewService
from app.storage.service import StorageService
from app.video.clip_service import ClipService
from app.video.video_service import VideoService
from app.core.config import settings

class ProcessingService:
    """Application pipeline coordinator; it delegates SQL, AI, FFmpeg, and storage work."""

    def __init__(
        self,
        video_repository: VideoRepository,
        job_repository: JobRepository,
        track_repository: VehicleTrackRepository | None = None,
        clip_repository: ClipRepository | None = None,
        storage_service: StorageService | None = None,
        video_service: VideoService | None = None,
        detection_service: DetectionService | None = None,
        tracking_service: TrackingService | None = None,
        clip_service: ClipService | None = None,
        review_service: ReviewService | None = None,
    ) -> None:
        self._video_repository = video_repository
        self._job_repository = job_repository
        self._track_repository = track_repository
        self._clip_repository = clip_repository
        self._storage_service = storage_service
        self._video_service = video_service
        self._detection_service = detection_service
        self._tracking_service = tracking_service
        self._clip_service = clip_service
        self._review_service = review_service

    def create_job(self, video_id: str):
        """Create a queued job. A Celery worker later invokes process(job_id)."""
        video = self._video_repository.get_by_id(video_id)
        if video is None:
            raise ProcessingError(f"Video not found: {video_id}")
        return self._job_repository.create(video_id=video.id)

    def mark_enqueue_failed(self, job_id: str, message: str) -> None:
        job = self._job_repository.get_by_id(job_id)
        if job is not None:
            self._job_repository.update(
                job, status=ProcessingJobStatus.FAILED, completed_at=datetime.now(timezone.utc), error_message=message
            )

    def process(self, job_id: str, config: ProcessingConfig | None = None) -> ProcessingOutcome:
        config = config or ProcessingConfig()
        self._require_pipeline_dependencies()
        job = self._job_repository.get_by_id(job_id)
        if job is None:
            raise ProcessingError(f"Processing job not found: {job_id}")
        video = self._video_repository.get_by_id(job.video_id)
        if video is None:
            return self._fail(job, f"Video not found: {job.video_id}")

        try:
            self._job_repository.update(
                job, status=ProcessingJobStatus.PROCESSING, progress=0, started_at=datetime.now(timezone.utc), error_message=None
            )
            self._video_repository.update(video, status=VideoStatus.PROCESSING)
            source_path = self._storage_service.get_file(video.original_path)
            metadata = self._video_service.validate_video(source_path)
            processed_tracks = 0
            created_clips = 0

            for frame_index, frame in self._video_service.iter_frames(source_path):
                if frame_index % settings.processing_frame_stride != 0:
                    continue
                detections = self._detection_service.detect(frame)
                self._tracking_service.update(frame_index, detections)
                finalized_tracks, finalized_clips = self._persist_finalized_tracks(
                    video.id, source_path, metadata, config
                )
                processed_tracks += finalized_tracks
                created_clips += finalized_clips
                progress = min(90, int((frame_index + 1) * 90 / metadata.frame_count))
                self._job_repository.update(job, progress=progress)

            self._tracking_service.finalize_all_tracks()
            finalized_tracks, finalized_clips = self._persist_finalized_tracks(
                video.id, source_path, metadata, config
            )
            processed_tracks += finalized_tracks
            created_clips += finalized_clips
            self._job_repository.update(
                job, status=ProcessingJobStatus.COMPLETED, progress=100, completed_at=datetime.now(timezone.utc)
            )
            self._video_repository.update(video, status=VideoStatus.COMPLETED)
            return ProcessingOutcome(
                job_id=job.id, processed_tracks=processed_tracks, created_clips=created_clips
            )
        except Exception as error:
            return self._fail(job, str(error), cause=error)

    def _persist_finalized_tracks(self, video_id: str, source_path: Path, metadata, config: ProcessingConfig) -> tuple[int, int]:
        processed_tracks = 0
        created_clips = 0
        for state in self._tracking_service.pop_finalized_tracks():
            processed_tracks += 1
            clip_result = self._clip_service.create_clips(
                source_path, state, config.padding_before, config.padding_after
            )
            review = self._review_service.evaluate(
                ReviewInput(
                    track=state,
                    fps=metadata.fps,
                    frame_width=metadata.width,
                    frame_height=metadata.height,
                    clip_duration=clip_result.duration,
                )
            )
            track = self._track_repository.create(
                video_id=video_id,
                track_id=state.track_id,
                vehicle_class=state.class_name,
                start_time=self._video_service.frame_to_time(state.first_frame, metadata.fps),
                end_time=self._video_service.frame_to_time(state.last_frame, metadata.fps),
                avg_confidence=state.average_confidence,
                review_required=review.required,
            )
            self._clip_repository.create(
                vehicle_track_id=track.id,
                full_clip_path=clip_result.full_clip_path,
                roi_clip_path=clip_result.roi_clip_path,
                duration=clip_result.duration,
                status=ClipStatus.NEEDS_REVIEW if review.required else ClipStatus.READY,
            )
            created_clips += 1
        return processed_tracks, created_clips

    def _require_pipeline_dependencies(self) -> None:
        if any(dependency is None for dependency in (
            self._track_repository, self._clip_repository, self._storage_service,
            self._video_service, self._detection_service, self._tracking_service,
            self._clip_service, self._review_service,
        )):
            raise ProcessingError("Processing pipeline dependencies are not configured")

    def _fail(self, job, message: str, cause: Exception | None = None) -> ProcessingOutcome:
        self._job_repository.update(
            job,
            status=ProcessingJobStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
            error_message=message,
        )
        video = self._video_repository.get_by_id(job.video_id)
        if video is not None:
            self._video_repository.update(video, status=VideoStatus.FAILED)
        if cause is not None:
            raise ProcessingError(message, details={"job_id": job.id}) from cause
        raise ProcessingError(message, details={"job_id": job.id})
