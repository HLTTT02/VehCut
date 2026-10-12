from typing import Protocol

from app.ai.detection.models import DetectionResult
from app.ai.tracking.models import TrackResult
from app.ai.tracking.models import VehicleTrackState

class TrackingService(Protocol):
    """Tracking contract: assign persistent vehicle IDs within a video."""
    def update(self, frame_index: int, detections: list[DetectionResult]) -> list[TrackResult]: ...
    def pop_finalized_tracks(self) -> list[VehicleTrackState]: ...
    def finalize_all_tracks(self) -> None: ...
