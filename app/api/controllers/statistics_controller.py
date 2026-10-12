from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_statistics_service
from app.schemas.statistics import StatisticsResponse
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("", response_model=StatisticsResponse)
def get_statistics(service: Annotated[StatisticsService, Depends(get_statistics_service)]) -> StatisticsResponse:
    return service.get_summary()

