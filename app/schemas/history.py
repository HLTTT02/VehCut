from datetime import datetime
from pydantic import BaseModel

class JobHistoryResponse(BaseModel):
    id: str
    video_id: str
    filename: str | None
    status: str
    progress: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

