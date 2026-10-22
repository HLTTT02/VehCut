from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SuspiciousEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    video_id: str
    vehicle_track_id: str
    event_type: str
    severity: str
    screenshot_path: str | None
    message: str
    created_at: datetime
