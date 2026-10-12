from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from app.ai.tracking.models import VehicleTrackState
from app.storage.service import StorageService
from app.video.clip_errors import ClipProcessingError
from app.video.clip_models import ClipResult
from app.video.models import TrackBox
from app.video.video_service import VideoService

class ClipService:
    """Create full and bbox-following ROI clips; no detection, DB, or HTTP dependency."""

    def __init__(self, video_service: VideoService, storage_service: StorageService) -> None:
        self._video_service = video_service
        self._storage_service = storage_service

    def create_clips(
        self,
        video_path: str | Path,
        track: VehicleTrackState,
        padding_before: float,
        padding_after: float,
    ) -> ClipResult:
        if padding_before < 0 or padding_after < 0:
            raise ClipProcessingError("Clip padding must be non-negative")
        if not track.bounding_boxes or not track.frame_indices:
            raise ClipProcessingError("Finalized track does not contain bounding boxes")

        metadata = self._video_service.get_metadata(video_path)
        start_time = max(0.0, self._video_service.frame_to_time(track.first_frame, metadata.fps) - padding_before)
        end_time = min(metadata.duration, self._video_service.frame_to_time(track.last_frame, metadata.fps) + padding_after)
        if end_time <= start_time:
            raise ClipProcessingError("Track does not create a valid clip range")

        start_frame = self._video_service.time_to_frame(start_time, metadata.fps)
        boxes = [
            TrackBox(
                frame_index=frame_index - start_frame,
                x=round(box.x1),
                y=round(box.y1),
                width=round(box.x2 - box.x1),
                height=round(box.y2 - box.y1),
            )
            for frame_index, box in zip(track.frame_indices, track.bounding_boxes)
        ]
        full_name = f"vehicle_{track.track_id:03d}.mp4"
        roi_name = f"vehicle_{track.track_id:03d}_roi.mp4"

        temporary_directory = Path(tempfile.mkdtemp(prefix="vehcut_clip_"))
        full_local = temporary_directory / full_name
        roi_local = temporary_directory / roi_name
        try:
            self._video_service.cut_video(video_path, full_local, start_time, end_time)
            self._video_service.crop_roi_video(full_local, roi_local, boxes)
            with full_local.open("rb") as full_file:
                full_path = self._storage_service.save_clip(full_file, full_name)
            with roi_local.open("rb") as roi_file:
                roi_path = self._storage_service.save_roi_clip(roi_file, roi_name)
        except Exception as error:
            if isinstance(error, ClipProcessingError):
                raise
            raise ClipProcessingError(f"Cannot create clips for track {track.track_id}") from error
        finally:
            shutil.rmtree(temporary_directory, ignore_errors=True)

        return ClipResult(
            track_id=track.track_id,
            full_clip_path=full_path,
            roi_clip_path=roi_path,
            duration=end_time - start_time,
        )

