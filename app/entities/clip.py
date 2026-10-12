import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.entities.enums import ClipStatus

class Clip(Base):
    __tablename__ = "clips"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_track_id: Mapped[str] = mapped_column(ForeignKey("vehicle_tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    full_clip_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    roi_clip_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ClipStatus] = mapped_column(Enum(ClipStatus, name="clip_status"), nullable=False, default=ClipStatus.READY)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    vehicle_track: Mapped["VehicleTrack"] = relationship(back_populates="clips")
    reviews: Mapped[list["Review"]] = relationship(back_populates="clip", cascade="all, delete-orphan")

