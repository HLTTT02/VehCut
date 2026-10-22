from app.entities.suspicious_event import SuspiciousEvent
from app.repositories.suspicious_event_repository import SuspiciousEventRepository


class SuspiciousEventService:
    def __init__(self, repository: SuspiciousEventRepository) -> None: self._repository = repository
    def list_events(self, limit: int = 100) -> list[SuspiciousEvent]: return self._repository.list(limit)
