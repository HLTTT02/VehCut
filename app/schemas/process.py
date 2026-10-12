from typing import Literal
from pydantic import BaseModel, Field

VehicleClass = Literal["car", "motorcycle", "bus", "truck"]

class ProcessVideoRequest(BaseModel):
    confidence_threshold: float = Field(ge=0, le=1)
    vehicle_classes: list[VehicleClass] = Field(min_length=1)
    padding_before: float = Field(ge=0)
    padding_after: float = Field(ge=0)
    min_clip_duration: float = Field(gt=0)

