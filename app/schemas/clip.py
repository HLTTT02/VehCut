from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ClipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vehicle_track_id: str
    full_clip_path: str
    roi_clip_path: str | None
    duration: float = Field(gt=0)
    status: str
    created_at: datetime

