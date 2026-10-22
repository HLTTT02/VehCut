from typing import Protocol

from app.ai.plate.models import PlateDetectionResult


class PlateDetectionService(Protocol):
    """Port for plate detection. It has no controller, DB, or OCR dependency."""

    def detect(self, vehicle_roi: object) -> list[PlateDetectionResult]: ...
