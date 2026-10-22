from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.ai.detection.yolo_detection_service import YoloDetectionService
from app.ai.roi.polygon_filter import PolygonRoiFilter, RoiPolygon
from app.core.dependencies import get_live_detection_service, get_processing_service, get_query_service, get_roi_service, get_storage_service, get_video_service
from app.storage.service import StorageService
from app.video.video_service import VideoService as FrameVideoService
from app.schemas.clip import ClipResponse
from app.schemas.job import JobStatusResponse
from app.schemas.process import ProcessVideoRequest
from app.schemas.vehicle_track import VehicleTrackResponse
from app.schemas.video import VideoResponse, VideoUploadResponse
from app.services.processing_models import ProcessingError
from app.services.processing_service import ProcessingService
from app.services.query_service import QueryService
from app.services.roi_service import RoiService
from app.services.video_service import VideoService
from app.workers.tasks import process_video_job

router = APIRouter(prefix="/videos", tags=["videos"])

_SUPPORTED_SUFFIXES = {".mp4", ".mov", ".avi", ".jpg", ".jpeg", ".png", ".webp"}

class DetectionBoxResponse(BaseModel):
    vehicle_class: str
    confidence: float = Field(ge=0, le=1)
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)
    x2: float = Field(ge=0, le=1)
    y2: float = Field(ge=0, le=1)

class FrameDetectionResponse(BaseModel):
    time_seconds: float = Field(ge=0)
    detections: list[DetectionBoxResponse]

@router.get("", response_model=list[VideoResponse])
def list_videos(service: Annotated[VideoService, Depends(get_video_service)]) -> list[VideoResponse]:
    return [VideoResponse.model_validate(video) for video in service.list_videos()]

@router.post("", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: Annotated[UploadFile, File(...)],
    service: Annotated[VideoService, Depends(get_video_service)],
) -> VideoUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Filename is required")
    if Path(file.filename).suffix.lower() not in _SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported uploads: MP4, MOV, AVI, JPG, JPEG, PNG, WEBP",
        )
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

@router.get("/{video_id}/detections", response_model=FrameDetectionResponse)
def detect_frame(
    video_id: str,
    service: Annotated[VideoService, Depends(get_video_service)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
    detector: Annotated[YoloDetectionService, Depends(get_live_detection_service)],
    roi_service: Annotated[RoiService, Depends(get_roi_service)],
    time_seconds: float = Query(default=0, ge=0),
) -> FrameDetectionResponse:
    """Return normalized boxes for one preview frame; the browser draws them over the media."""
    video = service.get_video(video_id)
    source_path = storage.get_file(video.original_path)
    frame_service = FrameVideoService()
    if source_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
        frame = frame_service.read_image(source_path)
        actual_time = 0.0
    else:
        metadata = frame_service.validate_video(source_path)
        frame_index = min(metadata.frame_count - 1, int(time_seconds * metadata.fps))
        frame = frame_service.extract_frame(source_path, frame_index)
        actual_time = frame_index / metadata.fps
    height, width = frame.shape[:2]
    zones = roi_service.list_zones(video_id)
    polygons = [
        RoiPolygon(points=tuple((float(point["x"]), float(point["y"])) for point in zone.points))
        for zone in zones if zone.enabled
    ]
    # Preview uses the same strict event-zone contract as ProcessingService.
    detections = PolygonRoiFilter().filter_detections(detector.detect(frame), polygons, width, height) if polygons else []
    return FrameDetectionResponse(
        time_seconds=actual_time,
        detections=[DetectionBoxResponse(
            vehicle_class=item.class_name, confidence=item.confidence,
            x1=max(0, min(1, item.bbox.x1 / width)), y1=max(0, min(1, item.bbox.y1 / height)),
            x2=max(0, min(1, item.bbox.x2 / width)), y2=max(0, min(1, item.bbox.y2 / height)),
        ) for item in detections],
    )

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
