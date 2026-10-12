from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.vehicle_track import VehicleTrack
from app.repositories.utils import repository_class
@repository_class
class VehicleTrackRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def create(self, **values: object) -> VehicleTrack: return self._persist(VehicleTrack(**values))
    def get_by_id(self, track_id: str) -> VehicleTrack | None: return self._session.scalar(select(VehicleTrack).where(VehicleTrack.id == track_id))
    def list(self, *, video_id: str | None = None, offset: int = 0, limit: int = 100) -> list[VehicleTrack]:
        statement = select(VehicleTrack).order_by(VehicleTrack.id).offset(offset).limit(limit)
        if video_id is not None: statement = statement.where(VehicleTrack.video_id == video_id)
        return list(self._session.scalars(statement))
    def update(self, entity: VehicleTrack, **values: object) -> VehicleTrack:
        for field, value in values.items(): setattr(entity, field, value)
        return self._persist(entity)
    def delete(self, entity: VehicleTrack) -> None: self._session.delete(entity); self._session.commit()
    def _persist(self, entity: VehicleTrack) -> VehicleTrack: self._session.add(entity); self._session.commit(); self._session.refresh(entity); return entity
