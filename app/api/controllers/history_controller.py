from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_query_service
from app.schemas.history import JobHistoryResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/jobs", response_model=list[JobHistoryResponse])
def list_job_history(service: Annotated[QueryService, Depends(get_query_service)]) -> list[JobHistoryResponse]:
    return service.list_job_history()

