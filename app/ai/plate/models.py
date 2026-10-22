from dataclasses import dataclass

from app.ai.detection.models import BoundingBox


@dataclass(frozen=True)
class PlateDetectionResult:
    """A plate box in coordinates relative to the supplied vehicle ROI."""

    bbox: BoundingBox
    confidence: float
    class_name: str = "plate"
