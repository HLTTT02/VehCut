from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class JobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    video_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

