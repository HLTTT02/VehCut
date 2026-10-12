from sqlalchemy import select
from sqlalchemy.orm import Session
from app.entities.processing_job import ProcessingJob
from app.entities.enums import ProcessingJobStatus
from app.repositories.utils import repository_class
@repository_class
class JobRepository:
    def __init__(self, session: Session) -> None: self._session = session
    def create(self, *, video_id: str, status: ProcessingJobStatus = ProcessingJobStatus.PENDING) -> ProcessingJob: return self._persist(ProcessingJob(video_id=video_id, status=status))
    def get_by_id(self, job_id: str) -> ProcessingJob | None: return self._session.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))
    def list(self, *, video_id: str | None = None, offset: int = 0, limit: int = 100) -> list[ProcessingJob]:
        statement = select(ProcessingJob).order_by(ProcessingJob.id).offset(offset).limit(limit)
        if video_id is not None: statement = statement.where(ProcessingJob.video_id == video_id)
        return list(self._session.scalars(statement))
    def update(self, entity: ProcessingJob, **values: object) -> ProcessingJob:
        for field, value in values.items(): setattr(entity, field, value)
        return self._persist(entity)
    def delete(self, entity: ProcessingJob) -> None: self._session.delete(entity); self._session.commit()
    def _persist(self, entity: ProcessingJob) -> ProcessingJob: self._session.add(entity); self._session.commit(); self._session.refresh(entity); return entity
