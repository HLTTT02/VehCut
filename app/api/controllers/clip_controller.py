from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_clip_review_service
from app.schemas.clip import ClipResponse
from app.schemas.review import ReviewClipRequest
from app.services.clip_review_service import ClipReviewService

router = APIRouter(prefix="/clips", tags=["clips"])

@router.patch("/{clip_id}/review", response_model=ClipResponse)
def review_clip(
    clip_id: str,
    payload: ReviewClipRequest,
    service: Annotated[ClipReviewService, Depends(get_clip_review_service)],
) -> ClipResponse:
    clip = service.review_clip(clip_id, payload.status, payload.reason, payload.note)
    return ClipResponse.model_validate(clip)
