from app.repositories.clip_repository import ClipRepository
from app.repositories.job_repository import JobRepository
from app.repositories.vehicle_track_repository import VehicleTrackRepository
from app.repositories.video_repository import VideoRepository
from app.services.errors import ResourceNotFoundError
from app.schemas.history import JobHistoryResponse

class QueryService:
    """Read-only application service; controllers do not access repositories."""

    def __init__(self, job_repository: JobRepository, track_repository: VehicleTrackRepository, clip_repository: ClipRepository, video_repository: VideoRepository) -> None:
        self._job_repository = job_repository
        self._track_repository = track_repository
        self._clip_repository = clip_repository
        self._video_repository = video_repository

    def get_job(self, job_id: str):
        job = self._job_repository.get_by_id(job_id)
        if job is None:
            raise ResourceNotFoundError("Job not found")
        return job

    def list_job_history(self) -> list[JobHistoryResponse]:
        history: list[JobHistoryResponse] = []
        for job in self._job_repository.list(limit=1_000):
            video = self._video_repository.get_by_id(job.video_id)
            history.append(JobHistoryResponse(
                id=job.id, video_id=job.video_id, filename=video.filename if video else None,
                status=job.status, progress=job.progress, started_at=job.started_at,
                completed_at=job.completed_at, error_message=job.error_message,
            ))
        return history

    def list_tracks(self, video_id: str):
        return self._track_repository.list(video_id=video_id)

    def list_clips(self, video_id: str):
        tracks = self._track_repository.list(video_id=video_id)
        clips = []
        for track in tracks:
            clips.extend(self._clip_repository.list(vehicle_track_id=track.id))
        return clips
