"""Video adapters never depend on controllers."""

from app.video.errors import VideoProcessingError
from app.video.clip_models import ClipResult
from app.video.clip_service import ClipService
from app.video.models import TrackBox, VideoMetadata
from app.video.video_service import VideoService

__all__ = ["ClipResult", "ClipService", "TrackBox", "VideoMetadata", "VideoProcessingError", "VideoService"]
