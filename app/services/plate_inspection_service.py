from __future__ import annotations

from dataclasses import dataclass

from app.ai.plate.service import PlateDetectionService
from app.ai.ocr.service import PlateOcrService
from app.ai.tracking.models import TrackResult


@dataclass(frozen=True)
class PlateInspectionResult:
    track_id: int
    vehicle_class: str
    plate_detected: bool
    plate_text: str | None
    detector_confidence: float | None
    evidence_image: object | None = None

    @property
    def alert_required(self) -> bool:
        return self.vehicle_class in {"car", "motorcycle"} and not self.plate_text


class PlateInspectionService:
    """Secondary plate-model + OCR service, called only for a tracked vehicle entering ROI."""

    _VEHICLE_CLASSES = frozenset({"car", "motorcycle"})

    def __init__(self, detector: PlateDetectionService, ocr: PlateOcrService) -> None:
        self._detector = detector
        self._ocr = ocr

    def inspect_entry(self, track: TrackResult, frame: object) -> PlateInspectionResult | None:
        if track.class_name not in self._VEHICLE_CLASSES:
            return None
        vehicle_roi = self._crop(frame, track.bbox.x1, track.bbox.y1, track.bbox.x2, track.bbox.y2)
        candidates = self._detector.detect(vehicle_roi)
        if not candidates:
            return PlateInspectionResult(track.track_id, track.class_name, False, None, None, vehicle_roi)
        best = max(candidates, key=lambda item: item.confidence)
        plate_roi = self._crop(vehicle_roi, best.bbox.x1, best.bbox.y1, best.bbox.x2, best.bbox.y2)
        return PlateInspectionResult(track.track_id, track.class_name, True, self._ocr.read(plate_roi), best.confidence, vehicle_roi)

    @staticmethod
    def _crop(image: object, x1: float, y1: float, x2: float, y2: float):
        height, width = image.shape[:2]
        left, top = max(0, int(x1)), max(0, int(y1))
        right, bottom = min(width, int(x2)), min(height, int(y2))
        return image[top:bottom, left:right]
