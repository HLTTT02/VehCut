from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_suspicious_event_service
from app.schemas.suspicious_event import SuspiciousEventResponse
from app.services.suspicious_event_service import SuspiciousEventService

router=APIRouter(prefix="/alerts",tags=["alerts"])

@router.get("",response_model=list[SuspiciousEventResponse])
def list_alerts(service: Annotated[SuspiciousEventService, Depends(get_suspicious_event_service)]) -> list[SuspiciousEventResponse]:
    return [SuspiciousEventResponse.model_validate(item) for item in service.list_events()]
