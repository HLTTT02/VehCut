from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.clip import Clip
from app.repositories.utils import repository_class
@repository_class
class ClipRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def create(self, **values: object) -> Clip: return self._persist(Clip(**values))
    def get_by_id(self, clip_id: str) -> Clip | None: return self._session.scalar(select(Clip).where(Clip.id == clip_id))
    def list(self, *, vehicle_track_id: str | None = None, offset: int = 0, limit: int = 100) -> list[Clip]:
        statement = select(Clip).order_by(Clip.created_at.desc()).offset(offset).limit(limit)
        if vehicle_track_id is not None: statement = statement.where(Clip.vehicle_track_id == vehicle_track_id)
        return list(self._session.scalars(statement))
    def update(self, entity: Clip, **values: object) -> Clip:
        for field, value in values.items(): setattr(entity, field, value)
        return self._persist(entity)
    def delete(self, entity: Clip) -> None: self._session.delete(entity); self._session.commit()
    def _persist(self, entity: Clip) -> Clip: self._session.add(entity); self._session.commit(); self._session.refresh(entity); return entity
