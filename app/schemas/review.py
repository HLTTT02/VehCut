from pydantic import BaseModel, Field
from typing import Literal

ReviewDecision = Literal["PENDING", "APPROVED", "REJECTED"]

class ReviewClipRequest(BaseModel):
    status: ReviewDecision
    reason: str | None = Field(default=None, max_length=255)
    note: str | None = Field(default=None, max_length=5000)
