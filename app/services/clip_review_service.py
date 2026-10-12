from app.entities.enums import ClipStatus, ReviewStatus
from app.repositories.clip_repository import ClipRepository
from app.repositories.review_repository import ReviewRepository
from app.services.errors import ResourceNotFoundError

class ClipReviewService:
    """Persists a human review decision; no HTTP and no AI behavior."""

    def __init__(self, clip_repository: ClipRepository, review_repository: ReviewRepository) -> None:
        self._clip_repository = clip_repository
        self._review_repository = review_repository

    def review_clip(self, clip_id: str, review_status: str, reason: str | None, note: str | None):
        clip = self._clip_repository.get_by_id(clip_id)
        if clip is None:
            raise ResourceNotFoundError("Clip not found")
        status = ReviewStatus(review_status)
        clip_status = {
            ReviewStatus.PENDING: ClipStatus.NEEDS_REVIEW,
            ReviewStatus.APPROVED: ClipStatus.READY,
            ReviewStatus.REJECTED: ClipStatus.REJECTED,
        }[status]
        self._clip_repository.update(clip, status=clip_status)
        self._review_repository.create(clip_id=clip.id, status=status, reason=reason, note=note)
        return clip

