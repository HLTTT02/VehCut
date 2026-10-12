from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import get_processing_service, get_query_service, get_video_service
from app.schemas.clip import ClipResponse
from app.schemas.job import JobStatusResponse
from app.schemas.process import ProcessVideoRequest
from app.schemas.vehicle_track import VehicleTrackResponse
from app.schemas.video import VideoResponse, VideoUploadResponse
from app.services.processing_models import ProcessingError
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.services.video_service import VideoService
from app.workers.tasks import process_video_job

router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    service: Annotated[VideoService, Depends(get_video_service)],
) -> VideoUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Filename is required")
    try:
        return VideoUploadResponse.model_validate(service.upload_video(file.file, file.filename))
    finally:
        await file.close()

@router.post("/{video_id}/process", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def start_processing(
    video_id: str,
    payload: ProcessVideoRequest,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> JobStatusResponse:
    """DTO is validated before this controller delegates creation of the queued job."""
    job = service.create_job(video_id)
    try:
        process_video_job.delay(job.id)
    except Exception as error:
        service.mark_enqueue_failed(job.id, "Cannot enqueue processing job")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Processing queue unavailable") from error
    return JobStatusResponse.model_validate(job)

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: str, service: Annotated[VideoService, Depends(get_video_service)]
) -> VideoResponse:
    return VideoResponse.model_validate(service.get_video(video_id))

@router.get("/{video_id}/tracks", response_model=list[VehicleTrackResponse])
def list_tracks(
    video_id: str, service: Annotated[QueryService, Depends(get_query_service)]
) -> list[VehicleTrackResponse]:
    return [VehicleTrackResponse.model_validate(track) for track in service.list_tracks(video_id)]

@router.get("/{video_id}/clips", response_model=list[ClipResponse])
def list_clips(
    video_id: str, service: Annotated[QueryService, Depends(get_query_service)]
) -> list[ClipResponse]:
    return [ClipResponse.model_validate(clip) for clip in service.list_clips(video_id)]
