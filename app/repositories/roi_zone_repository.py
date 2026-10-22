from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.roi_zone import RoiZone
from app.repositories.utils import repository_class


@repository_class
class RoiZoneRepository:
    """Persistence-only access to ROI zone records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, video_id: str, name: str, points: list[dict[str, float]], enabled: bool) -> RoiZone:
        zone = RoiZone(video_id=video_id, name=name, points=points, enabled=enabled)
        self._session.add(zone)
        self._session.commit()
        self._session.refresh(zone)
        return zone

    def get_by_id(self, zone_id: str) -> RoiZone | None:
        return self._session.scalar(select(RoiZone).where(RoiZone.id == zone_id))

    def list_by_video_id(self, video_id: str, *, enabled_only: bool = False) -> list[RoiZone]:
        statement = select(RoiZone).where(RoiZone.video_id == video_id).order_by(RoiZone.created_at.asc())
        if enabled_only:
            statement = statement.where(RoiZone.enabled.is_(True))
        return list(self._session.scalars(statement))

    def update(self, zone: RoiZone, **values: object) -> RoiZone:
        for field, value in values.items():
            setattr(zone, field, value)
        self._session.add(zone)
        self._session.commit()
        self._session.refresh(zone)
        return zone

    def delete(self, zone: RoiZone) -> None:
        self._session.delete(zone)
        self._session.commit()
