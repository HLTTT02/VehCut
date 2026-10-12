from dataclasses import dataclass, field
from app.ai.detection.models import BoundingBox, DetectionResult

@dataclass(frozen=True)
class TrackResult:
    track_id: int
    class_name: str
    bbox: BoundingBox
    confidence: float
    frame_index: int

@dataclass
class VehicleTrackState:
    track_id: int
    class_name: str
    first_frame: int
    last_frame: int
    bounding_boxes: list[BoundingBox] = field(default_factory=list)
    frame_indices: list[int] = field(default_factory=list)
    confidence_history: list[float] = field(default_factory=list)

    def add(self, result: TrackResult) -> None:
        self.last_frame = result.frame_index
        self.bounding_boxes.append(result.bbox)
        self.frame_indices.append(result.frame_index)
        self.confidence_history.append(result.confidence)

    @property
    def average_confidence(self) -> float:
        return sum(self.confidence_history) / len(self.confidence_history) if self.confidence_history else 0.0

DetectionBatch = list[DetectionResult]
