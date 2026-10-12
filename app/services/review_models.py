from dataclasses import dataclass
from enum import StrEnum

from app.ai.tracking.models import VehicleTrackState

class ReviewSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ReviewReason(StrEnum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    TRACK_GAP = "TRACK_GAP"
    SHORT_TRACK = "SHORT_TRACK"
    PARTIAL_VEHICLE = "PARTIAL_VEHICLE"
    SMALL_BOUNDING_BOX = "SMALL_BOUNDING_BOX"
    UNSTABLE_TRACK_ID = "UNSTABLE_TRACK_ID"
    SHORT_CLIP = "SHORT_CLIP"
    STRONG_TRACK_OVERLAP = "STRONG_TRACK_OVERLAP"

@dataclass(frozen=True)
class ReviewConfig:
    min_average_confidence: float = 0.55
    max_gap_frames: int = 5
    min_track_duration_seconds: float = 0.75
    min_box_width: float = 24.0
    min_box_height: float = 24.0
    edge_margin_pixels: float = 4.0
    max_id_switches: int = 0
    min_clip_duration_seconds: float = 1.0
    strong_overlap_iou: float = 0.65

@dataclass(frozen=True)
class ReviewInput:
    track: VehicleTrackState
    fps: float
    frame_width: int
    frame_height: int
    clip_duration: float
    id_switch_count: int = 0
    max_overlap_iou: float = 0.0

@dataclass(frozen=True)
class ReviewDecision:
    required: bool
    reasons: list[str]
    severity: ReviewSeverity

