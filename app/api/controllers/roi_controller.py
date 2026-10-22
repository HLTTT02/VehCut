from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.dependencies import get_roi_service
from app.schemas.roi import RoiZoneCreateRequest, RoiZoneResponse, RoiZoneUpdateRequest
from app.services.roi_service import RoiService

router = APIRouter(tags=["roi"])


@router.get("/videos/{video_id}/roi-zones", response_model=list[RoiZoneResponse])
def list_roi_zones(video_id: str, service: Annotated[RoiService, Depends(get_roi_service)]) -> list[RoiZoneResponse]:
    return [RoiZoneResponse.model_validate(zone) for zone in service.list_zones(video_id)]


@router.post("/videos/{video_id}/roi-zones", response_model=RoiZoneResponse, status_code=status.HTTP_201_CREATED)
def create_roi_zone(video_id: str, payload: RoiZoneCreateRequest, service: Annotated[RoiService, Depends(get_roi_service)]) -> RoiZoneResponse:
    return RoiZoneResponse.model_validate(service.create_zone(video_id, payload))


@router.patch("/roi-zones/{zone_id}", response_model=RoiZoneResponse)
def update_roi_zone(zone_id: str, payload: RoiZoneUpdateRequest, service: Annotated[RoiService, Depends(get_roi_service)]) -> RoiZoneResponse:
    return RoiZoneResponse.model_validate(service.update_zone(zone_id, payload))


@router.delete("/roi-zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roi_zone(zone_id: str, service: Annotated[RoiService, Depends(get_roi_service)]) -> Response:
    service.delete_zone(zone_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
