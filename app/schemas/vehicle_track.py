from pydantic import BaseModel, ConfigDict, Field
from app.schemas.process import VehicleClass

class VehicleTrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    video_id: str
    track_id: int
    vehicle_class: VehicleClass
    start_time: float = Field(ge=0)
    end_time: float = Field(ge=0)
    avg_confidence: float = Field(ge=0, le=1)
    review_required: bool

