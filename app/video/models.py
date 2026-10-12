from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class VideoMetadata:
    path: Path
    duration: float
    fps: float
    width: int
    height: int
    frame_count: int
    codec: str | None

@dataclass(frozen=True)
class TrackBox:
    """Bounding box in source-frame pixels. Use one or more boxes to define crop ROI."""

    frame_index: int
    x: int
    y: int
    width: int
    height: int

