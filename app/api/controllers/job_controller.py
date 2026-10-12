from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.dependencies import get_query_service
from app.schemas.job import JobStatusResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, service: Annotated[QueryService, Depends(get_query_service)]) -> JobStatusResponse:
    return JobStatusResponse.model_validate(service.get_job(job_id))
