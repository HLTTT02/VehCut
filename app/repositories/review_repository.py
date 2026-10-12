from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.review import Review
from app.repositories.utils import repository_class
@repository_class
class ReviewRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def create(self, **values: object) -> Review: return self._persist(Review(**values))
    def get_by_id(self, review_id: str) -> Review | None: return self._session.scalar(select(Review).where(Review.id == review_id))
    def list(self, *, clip_id: str | None = None, offset: int = 0, limit: int = 100) -> list[Review]:
        statement = select(Review).order_by(Review.created_at.desc()).offset(offset).limit(limit)
        if clip_id is not None: statement = statement.where(Review.clip_id == clip_id)
        return list(self._session.scalars(statement))
    def update(self, entity: Review, **values: object) -> Review:
        for field, value in values.items(): setattr(entity, field, value)
        return self._persist(entity)
    def delete(self, entity: Review) -> None: self._session.delete(entity); self._session.commit()
    def _persist(self, entity: Review) -> Review: self._session.add(entity); self._session.commit(); self._session.refresh(entity); return entity
