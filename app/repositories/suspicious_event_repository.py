from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.suspicious_event import SuspiciousEvent
from app.repositories.utils import repository_class


@repository_class
class SuspiciousEventRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def create(self, **values: object) -> SuspiciousEvent:
        item=SuspiciousEvent(**values);self._session.add(item);self._session.commit();self._session.refresh(item);return item
    def list(self, limit: int = 100) -> list[SuspiciousEvent]:
        return list(self._session.scalars(select(SuspiciousEvent).order_by(SuspiciousEvent.created_at.desc()).limit(limit)))
