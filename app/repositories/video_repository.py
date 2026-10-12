from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.video import Video
from app.repositories.utils import repository_class

@repository_class
class VideoRepository:
    """The only Video SQL access point."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, filename: str, original_path: str, duration: float | None) -> Video:
        video = Video(filename=filename, original_path=original_path, duration=duration)
        self._session.add(video)
        self._session.commit()
        self._session.refresh(video)
        return video

    def get_by_id(self, video_id: str) -> Video | None:
        return self._session.scalar(select(Video).where(Video.id == video_id))

    def list(self, *, offset: int = 0, limit: int = 100) -> list[Video]:
        statement = select(Video).order_by(Video.created_at.desc()).offset(offset).limit(limit)
        return list(self._session.scalars(statement))

    def update(self, entity: Video, **values: object) -> Video:
        for field, value in values.items():
            setattr(entity, field, value)
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def delete(self, entity: Video) -> None:
        self._session.delete(entity)
        self._session.commit()
