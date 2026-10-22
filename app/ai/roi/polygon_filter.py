from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.ai.detection.models import BoundingBox, DetectionResult


@dataclass(frozen=True)
class RoiPolygon:
    """Polygon points normalized to the source frame's 0..1 coordinate system."""

    points: tuple[tuple[float, float], ...]


class PolygonRoiFilter:
    """Pure geometry module. It has no DB, HTTP, model, or video dependency."""

    def filter_detections(
        self,
        detections: Iterable[DetectionResult],
        polygons: Iterable[RoiPolygon],
        frame_width: int,
        frame_height: int,
    ) -> list[DetectionResult]:
        zones = tuple(polygons)
        if not zones:
            return list(detections)
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("Frame dimensions must be positive")
        return [
            detection
            for detection in detections
            if any(self._contains_bbox_center(zone, detection.bbox, frame_width, frame_height) for zone in zones)
        ]

    @classmethod
    def _contains_bbox_center(cls, zone: RoiPolygon, bbox: BoundingBox, width: int, height: int) -> bool:
        center = ((bbox.x1 + bbox.x2) / (2 * width), (bbox.y1 + bbox.y2) / (2 * height))
        return cls._contains_point(zone.points, center)

    @staticmethod
    def _contains_point(points: tuple[tuple[float, float], ...], point: tuple[float, float]) -> bool:
        # Ray-casting algorithm. Boundary behavior is acceptable for a configured monitoring zone.
        x, y = point
        inside = False
        previous = len(points) - 1
        for current, (current_x, current_y) in enumerate(points):
            previous_x, previous_y = points[previous]
            crosses = (current_y > y) != (previous_y > y)
            if crosses and x < (previous_x - current_x) * (y - current_y) / (previous_y - current_y) + current_x:
                inside = not inside
            previous = current
        return inside
