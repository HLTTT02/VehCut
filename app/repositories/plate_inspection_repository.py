from sqlalchemy import select
from sqlalchemy.orm import Session

from app.entities.plate_inspection import PlateInspection
from app.repositories.utils import repository_class


@repository_class
class PlateInspectionRepository:
    """Persistence-only repository for secondary plate inspection results."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **values: object) -> PlateInspection:
        entity = PlateInspection(**values)
        self._session.add(entity)
        self._session.commit()
        self._session.refresh(entity)
        return entity

    def get_by_track_id(self, vehicle_track_id: str) -> PlateInspection | None:
        return self._session.scalar(select(PlateInspection).where(PlateInspection.vehicle_track_id == vehicle_track_id))
