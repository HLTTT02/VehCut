from app.repositories.video_repository import VideoRepository
from app.schemas.video import CreateVideoRequest
from app.services.errors import VideoNotFoundError
from app.storage.service import StorageService

class VideoService:
    """Business boundary: no SQL and no HTTP handlers."""

    def __init__(self, repository: VideoRepository, storage_service: StorageService | None = None) -> None:
        self._repository = repository
        self._storage_service = storage_service

    def upload_video(self, source: object, filename: str):
        if self._storage_service is None:
            raise RuntimeError("StorageService is required for uploads")
        original_path = self._storage_service.save_original_video(source, filename)
        return self._repository.create(filename=filename, original_path=original_path, duration=None)

    def create_video(self, payload: CreateVideoRequest):
        return self._repository.create(
            filename=payload.filename, original_path=payload.original_path,
            duration=payload.duration,
        )

    def get_video(self, video_id: str):
        video = self._repository.get_by_id(video_id)
        if video is None:
            raise VideoNotFoundError("Video not found", details={"video_id": video_id})
        return video

    def list_videos(self):
        """Newest uploads first, for the dashboard source selector."""
        return self._repository.list(limit=100)
