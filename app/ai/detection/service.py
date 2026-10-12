from typing import Protocol

from app.ai.detection.models import DetectionResult

class DetectionService(Protocol):
    """Detection contract; implementations return domain detection results."""
    def detect(self, frame: object) -> list[DetectionResult]: ...
