from app.entities.enums import ClipStatus, ProcessingJobStatus
from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.statistics import StatisticsResponse, VehicleClassCounts

class StatisticsService:
    """Aggregates persisted records through repositories; it contains no SQL."""

    def __init__(self, video_repository: VideoRepository, job_repository: JobRepository, track_repository: VehicleTrackRepository, clip_repository: ClipRepository) -> None:
        self._videos = video_repository
        self._jobs = job_repository
        self._tracks = track_repository
        self._clips = clip_repository

    def get_summary(self) -> StatisticsResponse:
        videos = self._videos.list(limit=10_000)
        jobs = self._jobs.list(limit=10_000)
        tracks = self._tracks.list(limit=10_000)
        clips = self._clips.list(limit=10_000)
        counts = {"person": 0, "car": 0, "motorcycle": 0, "truck": 0, "bus": 0}
        for track in tracks:
            if track.vehicle_class in counts:
                counts[track.vehicle_class] += 1
        return StatisticsResponse(
            total_videos=len(videos),
            total_vehicles=len(tracks),
            total_clips=len(clips),
            pending_review=sum(clip.status == ClipStatus.NEEDS_REVIEW for clip in clips),
            completed_jobs=sum(job.status == ProcessingJobStatus.COMPLETED for job in jobs),
            failed_jobs=sum(job.status == ProcessingJobStatus.FAILED for job in jobs),
            vehicle_classes=VehicleClassCounts(**counts),
        )

