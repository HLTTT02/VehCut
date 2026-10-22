from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.detection.errors import DetectionError
from app.ai.detection.models import BoundingBox
from app.ai.plate.models import PlateDetectionResult

if TYPE_CHECKING:
    import numpy as np


class YoloPlateDetectionService:
    """YOLO adapter for plate ROI inference; constructed once per worker process."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.4,
        device: str | None = "cpu",
        image_size: int = 640,
    ) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self._confidence_threshold = confidence_threshold
        self._device = device
        self._image_size = image_size
        self._model = self._load_model(model_path)

    def detect(self, vehicle_roi: "np.ndarray") -> list[PlateDetectionResult]:
        """Return plate boxes relative to vehicle_roi; no plate is a normal empty result."""
        if vehicle_roi is None or getattr(vehicle_roi, "size", 0) == 0:
            return []
        try:
            predictions = self._model(
                vehicle_roi,
                conf=self._confidence_threshold,
                device=self._device,
                imgsz=self._image_size,
                verbose=False,
            )
        except Exception as error:
            raise DetectionError("Plate YOLO inference failed") from error

        results: list[PlateDetectionResult] = []
        for prediction in predictions:
            if prediction.boxes is None:
                continue
            for box in prediction.boxes:
                confidence = float(box.conf[0].item())
                if confidence < self._confidence_threshold:
                    continue
                x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
                results.append(PlateDetectionResult(BoundingBox(x1, y1, x2, y2), confidence))
        return results

    @staticmethod
    def _load_model(model_path: str):
        try:
            from ultralytics import YOLO

            return YOLO(model_path)
        except ImportError as error:
            raise DetectionError("Ultralytics is not installed") from error
        except Exception as error:
            raise DetectionError(f"Cannot load plate YOLO model: {model_path}") from error
