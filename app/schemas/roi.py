from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoiPoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class RoiZoneCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    points: list[RoiPoint] = Field(min_length=3, max_length=50)
    enabled: bool = True

    @field_validator("points")
    @classmethod
    def points_must_be_distinct(cls, points: list[RoiPoint]) -> list[RoiPoint]:
        if len({(point.x, point.y) for point in points}) < 3:
            raise ValueError("ROI must contain at least three distinct points")
        return points


class RoiZoneUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    points: list[RoiPoint] | None = Field(default=None, min_length=3, max_length=50)
    enabled: bool | None = None


class RoiZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    video_id: str
    name: str
    points: list[RoiPoint]
    enabled: bool
    created_at: datetime
    updated_at: datetime
