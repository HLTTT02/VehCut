from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CreateVideoRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    original_path: str = Field(min_length=1)
    duration: float | None = Field(default=None, ge=0)


class VideoUploadResponse(BaseModel):
    """Response after the upload adapter has placed the original file in storage."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_path: str
    status: str


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    filename: str
    original_path: str
    duration: float | None
    fps: float | None
    width: int | None
    height: int | None
    status: str
    created_at: datetime
