from dataclasses import dataclass

@dataclass(frozen=True)
class ClipResult:
    track_id: int
    full_clip_path: str
    roi_clip_path: str
    duration: float

