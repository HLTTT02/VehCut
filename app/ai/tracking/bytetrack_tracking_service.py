from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.detection.models import DetectionResult
from app.ai.tracking.errors import TrackingError
from app.ai.tracking.models import TrackResult, VehicleTrackState

if TYPE_CHECKING:
    import numpy as np

class ByteTrackTrackingService:
    """ByteTrack adapter. Create one instance per worker/pipeline, not per frame."""

    def __init__(self, max_missing_frames: int = 30, track_activation_threshold: float = 0.25) -> None:
        if max_missing_frames < 0:
            raise ValueError("max_missing_frames must be non-negative")
        self._max_missing_frames = max_missing_frames
        self._numpy, self._supervision = self._load_dependencies()
        self._tracker = self._supervision.ByteTrack(track_activation_threshold=track_activation_threshold)
        self._active_tracks: dict[int, VehicleTrackState] = {}
        self._finalized_tracks: list[VehicleTrackState] = []

    def update(self, frame_index: int, detections: list[DetectionResult]) -> list[TrackResult]:
        """Assign persistent IDs to one frame of detections and update track state."""

        if frame_index < 0:
            raise TrackingError("frame_index must be non-negative")
        tracked_detections = self._to_supervision_detections(detections)
        try:
            tracked_detections = self._tracker.update_with_detections(tracked_detections)
        except Exception as error:
            raise TrackingError("ByteTrack update failed") from error

        results: list[TrackResult] = []
        tracker_ids = tracked_detections.tracker_id
        if tracker_ids is not None:
            for index, track_id in enumerate(tracker_ids):
                if track_id is None:
                    continue
                x1, y1, x2, y2 = (float(value) for value in tracked_detections.xyxy[index])
                class_id = int(tracked_detections.class_id[index])
                result = TrackResult(
                    track_id=int(track_id),
                    class_name=self._class_name(class_id),
                    bbox=self._bounding_box(x1, y1, x2, y2),
                    confidence=float(tracked_detections.confidence[index]),
                    frame_index=frame_index,
                )
                results.append(result)
                self._record(result)

        self._finalize_missing_tracks(frame_index)
        return results

    def finalized_tracks(self) -> list[VehicleTrackState]:
        """Return a snapshot of states finalized after exceeding max_missing_frames."""
        return list(self._finalized_tracks)

    def pop_finalized_tracks(self) -> list[VehicleTrackState]:
        """Consume tracks finalized since the last call."""
        finalized = list(self._finalized_tracks)
        self._finalized_tracks.clear()
        return finalized

    def finalize_all_tracks(self) -> None:
        """Finalize remaining active tracks when the source video reaches EOF."""
        self._finalized_tracks.extend(self._active_tracks.values())
        self._active_tracks.clear()

    def active_tracks(self) -> list[VehicleTrackState]:
        return list(self._active_tracks.values())

    def _record(self, result: TrackResult) -> None:
        state = self._active_tracks.get(result.track_id)
        if state is None:
            state = VehicleTrackState(
                track_id=result.track_id,
                class_name=result.class_name,
                first_frame=result.frame_index,
                last_frame=result.frame_index,
            )
            self._active_tracks[result.track_id] = state
        state.add(result)

    def _finalize_missing_tracks(self, frame_index: int) -> None:
        stale_ids = [
            track_id for track_id, state in self._active_tracks.items()
            if frame_index - state.last_frame > self._max_missing_frames
        ]
        for track_id in stale_ids:
            self._finalized_tracks.append(self._active_tracks.pop(track_id))

    def _to_supervision_detections(self, detections: list[DetectionResult]):
        numpy = self._numpy
        if not detections:
            return self._supervision.Detections(
                xyxy=numpy.empty((0, 4), dtype=float),
                confidence=numpy.empty((0,), dtype=float),
                class_id=numpy.empty((0,), dtype=int),
            )
        return self._supervision.Detections(
            xyxy=numpy.array([[item.bbox.x1, item.bbox.y1, item.bbox.x2, item.bbox.y2] for item in detections]),
            confidence=numpy.array([item.confidence for item in detections]),
            class_id=numpy.array([self._class_id(item.class_name) for item in detections]),
        )

    @staticmethod
    def _class_id(class_name: str) -> int:
        classes = {"car": 2, "motorcycle": 3, "bus": 5, "truck": 7}
        try:
            return classes[class_name]
        except KeyError as error:
            raise TrackingError(f"Unsupported vehicle class: {class_name}") from error

    @staticmethod
    def _class_name(class_id: int) -> str:
        classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        try:
            return classes[class_id]
        except KeyError as error:
            raise TrackingError(f"Unexpected ByteTrack class ID: {class_id}") from error

    @staticmethod
    def _bounding_box(x1: float, y1: float, x2: float, y2: float):
        from app.ai.detection.models import BoundingBox
        return BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2)

    @staticmethod
    def _load_dependencies():
        try:
            import numpy
            import supervision
            return numpy, supervision
        except ImportError as error:
            raise TrackingError("ByteTrack requires numpy and supervision") from error
