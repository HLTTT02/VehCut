from app.entities.roi_zone import RoiZone
from app.repositories.roi_zone_repository import RoiZoneRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.roi import RoiPoint, RoiZoneCreateRequest, RoiZoneUpdateRequest
from app.services.processing_models import ProcessingError


class RoiService:
    """ROI application logic; HTTP and SQL details remain outside this service."""

    def __init__(self, video_repository: VideoRepository, roi_repository: RoiZoneRepository) -> None:
        self._video_repository = video_repository
        self._roi_repository = roi_repository

    def list_zones(self, video_id: str) -> list[RoiZone]:
        self._require_video(video_id)
        return self._roi_repository.list_by_video_id(video_id)

    def create_zone(self, video_id: str, request: RoiZoneCreateRequest) -> RoiZone:
        self._require_video(video_id)
        return self._roi_repository.create(
            video_id=video_id,
            name=request.name.strip(),
            points=self._serialize_points(request.points),
            enabled=request.enabled,
        )

    def update_zone(self, zone_id: str, request: RoiZoneUpdateRequest) -> RoiZone:
        zone = self._require_zone(zone_id)
        values: dict[str, object] = request.model_dump(exclude_unset=True)
        if "name" in values:
            values["name"] = str(values["name"]).strip()
        if "points" in values:
            values["points"] = self._serialize_points(request.points or [])
        return self._roi_repository.update(zone, **values)

    def delete_zone(self, zone_id: str) -> None:
        self._roi_repository.delete(self._require_zone(zone_id))

    def _require_video(self, video_id: str) -> None:
        if self._video_repository.get_by_id(video_id) is None:
            raise ProcessingError(f"Video not found: {video_id}")

    def _require_zone(self, zone_id: str) -> RoiZone:
        zone = self._roi_repository.get_by_id(zone_id)
        if zone is None:
            raise ProcessingError(f"ROI zone not found: {zone_id}")
        return zone

    @staticmethod
    def _serialize_points(points: list[RoiPoint]) -> list[dict[str, float]]:
        return [{"x": point.x, "y": point.y} for point in points]
