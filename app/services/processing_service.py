from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.ai.detection.service import DetectionService
from app.ai.roi.polygon_filter import PolygonRoiFilter, RoiPolygon
from app.ai.tracking.models import VehicleTrackState
from app.entities.enums import ReviewStatus
from app.repositories.plate_inspection_repository import PlateInspectionRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.suspicious_event_repository import SuspiciousEventRepository
from app.ai.tracking.service import TrackingService
from app.entities.enums import ClipStatus, ProcessingJobStatus, VideoStatus
from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.repositories.roi_zone_repository import RoiZoneRepository
from app.services.processing_models import ProcessingConfig, ProcessingError, ProcessingOutcome
from app.services.review_models import ReviewInput
from app.services.review_service import ReviewService
from app.services.plate_inspection_service import PlateInspectionResult, PlateInspectionService
from app.storage.service import StorageService
from app.video.clip_service import ClipService
from app.video.video_service import VideoService
from app.video.snapshot_service import SnapshotService
from io import BytesIO
from app.core.config import settings


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

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
        roi_repository: RoiZoneRepository | None = None,
        plate_inspection_service: PlateInspectionService | None = None,
        plate_inspection_repository: PlateInspectionRepository | None = None,
        review_repository: ReviewRepository | None = None,
        suspicious_event_repository: SuspiciousEventRepository | None = None,
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
        self._roi_repository = roi_repository
        self._plate_inspection_service = plate_inspection_service
        self._plate_inspection_repository = plate_inspection_repository
        self._review_repository = review_repository
        self._suspicious_event_repository = suspicious_event_repository
        self._snapshot_service = SnapshotService()
        self._roi_filter = PolygonRoiFilter()
        self._plate_inspections_by_track: dict[int, PlateInspectionResult] = {}

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
            if source_path.suffix.lower() in _IMAGE_SUFFIXES:
                return self._process_image(job, video, source_path)
            metadata = self._video_service.validate_video(source_path)
            roi_polygons = self._enabled_roi_polygons(video.id)
            self._plate_inspections_by_track.clear()
            processed_tracks = 0
            created_clips = 0

            for frame_index, frame in self._video_service.iter_frames(source_path):
                if frame_index % settings.processing_frame_stride != 0:
                    continue
                detections = self._filter_by_roi(self._detection_service.detect(frame), roi_polygons, frame)
                tracked = self._tracking_service.update(frame_index, detections)
                self._inspect_vehicle_entries(tracked, frame)
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

    def _process_image(self, job, video, source_path: Path) -> ProcessingOutcome:
        """Detect vehicles in one image without invoking video tracking/clip generation."""
        image = self._video_service.read_image(source_path)
        height, width = image.shape[:2]
        self._video_repository.update(video, width=width, height=height, duration=0, fps=None)
        detections = self._filter_by_roi(self._detection_service.detect(image), self._enabled_roi_polygons(video.id), image)
        for track_id, detection in enumerate(detections, start=1):
            self._track_repository.create(
                video_id=video.id,
                track_id=track_id,
                vehicle_class=detection.class_name,
                start_time=0,
                end_time=0,
                avg_confidence=detection.confidence,
                review_required=detection.confidence < settings.yolo_confidence_threshold,
            )
        self._job_repository.update(
            job, status=ProcessingJobStatus.COMPLETED, progress=100, completed_at=datetime.now(timezone.utc)
        )
        self._video_repository.update(video, status=VideoStatus.COMPLETED)
        return ProcessingOutcome(job_id=job.id, processed_tracks=len(detections), created_clips=0)

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
            inspection = self._plate_inspections_by_track.pop(state.track_id, None)
            requires_plate_alert = inspection.alert_required if inspection else False
            track = self._track_repository.create(
                video_id=video_id,
                track_id=state.track_id,
                vehicle_class=state.class_name,
                start_time=self._video_service.frame_to_time(state.first_frame, metadata.fps),
                end_time=self._video_service.frame_to_time(state.last_frame, metadata.fps),
                avg_confidence=state.average_confidence,
                review_required=review.required or requires_plate_alert,
            )
            clip = self._clip_repository.create(
                vehicle_track_id=track.id,
                full_clip_path=clip_result.full_clip_path,
                roi_clip_path=clip_result.roi_clip_path,
                duration=clip_result.duration,
                status=ClipStatus.NEEDS_REVIEW if review.required or requires_plate_alert else ClipStatus.READY,
            )
            if inspection and self._plate_inspection_repository:
                self._plate_inspection_repository.create(
                    vehicle_track_id=track.id,
                    plate_detected=inspection.plate_detected,
                    plate_text=inspection.plate_text,
                    detector_confidence=inspection.detector_confidence,
                    alert_required=requires_plate_alert,
                )
            if requires_plate_alert and self._review_repository:
                self._review_repository.create(
                    clip_id=clip.id,
                    status=ReviewStatus.PENDING,
                    reason="NO_PLATE",
                    note="Không phát hiện được biển số hoặc OCR không đọc được biển số khi xe đi vào ROI.",
                )
            if requires_plate_alert and self._suspicious_event_repository:
                self._suspicious_event_repository.create(
                    video_id=video_id,
                    vehicle_track_id=track.id,
                    event_type="NO_PLATE",
                    severity="HIGH",
                    screenshot_path=self._store_alert_image(inspection, state.track_id),
                    message=f"{state.class_name} đi vào ROI nhưng không phát hiện hoặc không đọc được biển số.",
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

    def _enabled_roi_polygons(self, video_id: str) -> list[RoiPolygon]:
        if self._roi_repository is None:
            return []
        return [
            RoiPolygon(tuple((float(point["x"]), float(point["y"])) for point in zone.points))
            for zone in self._roi_repository.list_by_video_id(video_id, enabled_only=True)
        ]

    def _filter_by_roi(self, detections, polygons: list[RoiPolygon], frame):
        # Event-monitoring mode is opt-in by zone: without a configured ROI, no event may be emitted.
        if not polygons:
            return []
        height, width = frame.shape[:2]
        return self._roi_filter.filter_detections(detections, polygons, width, height)

    def _inspect_vehicle_entries(self, tracks, frame) -> None:
        """Call the second model only once: when a car/motorcycle first enters an enabled ROI."""
        if self._plate_inspection_service is None:
            return
        for track in tracks:
            if track.track_id in self._plate_inspections_by_track or track.class_name not in {"car", "motorcycle"}:
                continue
            try:
                result = self._plate_inspection_service.inspect_entry(track, frame)
            except Exception:
                result = PlateInspectionResult(track.track_id, track.class_name, False, None, None)
            if result is not None:
                self._plate_inspections_by_track[track.track_id] = result

    def _store_alert_image(self, inspection: PlateInspectionResult, track_id: int) -> str | None:
        if self._storage_service is None or inspection.evidence_image is None:
            return None
        payload = self._snapshot_service.encode_jpeg(inspection.evidence_image)
        if payload is None:
            return None
        try:
            return self._storage_service.save_alert_image(BytesIO(payload), f"no_plate_track_{track_id}.jpg")
        except Exception:
            return None

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
