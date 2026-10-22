from __future__ import annotations
from typing import TYPE_CHECKING
from app.ai.detection.errors import DetectionError
from app.ai.detection.models import BoundingBox, DetectionResult

if TYPE_CHECKING:
    import numpy as np

_CLASS_NAME_ALIASES = {
    "person": "person",
    "car": "car",
    "motorcycle": "motorcycle",
    "motorbike": "motorcycle",
    "bus": "bus",
    "truck": "truck",
}

class YoloDetectionService:
    """Ultralytics adapter. Construct once per worker to load the model once."""

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        device: str | None = "cpu",
        image_size: int = 640,
        allowed_classes: set[str] | frozenset[str] | None = None,
    ) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self._confidence_threshold = confidence_threshold
        self._device = device
        self._image_size = image_size
        self._allowed_classes = frozenset(allowed_classes or _CLASS_NAME_ALIASES.values())
        unsupported = self._allowed_classes - set(_CLASS_NAME_ALIASES.values())
        if unsupported:
            raise ValueError(f"Unsupported YOLO classes: {sorted(unsupported)}")
        self._model = self._load_model(model_path)

    def detect(self, frame: "np.ndarray") -> list[DetectionResult]:
        """No detected vehicle is normal and returns an empty list."""
        if frame is None:
            raise DetectionError("Frame must not be None")
        try:
            predictions = self._model(frame, conf=self._confidence_threshold, device=self._device, imgsz=self._image_size, verbose=False)
        except Exception as error:
            raise DetectionError("YOLO inference failed") from error

        detections: list[DetectionResult] = []
        for prediction in predictions:
            if prediction.boxes is None:
                continue
            for box in prediction.boxes:
                class_id = int(box.cls[0].item())
                raw_class_name = str(prediction.names.get(class_id, "")).strip().lower()
                class_name = _CLASS_NAME_ALIASES.get(raw_class_name)
                if class_name is None or class_name not in self._allowed_classes:
                    continue
                confidence = float(box.conf[0].item())
                if confidence < self._confidence_threshold:
                    continue
                x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
                detections.append(DetectionResult(BoundingBox(x1, y1, x2, y2), class_name, confidence))
        return detections

    @staticmethod
    def _load_model(model_path: str):
        try:
            from ultralytics import YOLO
            return YOLO(model_path)
        except ImportError as error:
            raise DetectionError("Ultralytics is not installed") from error
        except Exception as error:
            raise DetectionError(f"Cannot load YOLO model: {model_path}") from error
