import uuid
from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class VehicleTrack(Base):
    __tablename__ = "vehicle_tracks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(nullable=False, index=True)
    vehicle_class: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    video: Mapped["Video"] = relationship(back_populates="vehicle_tracks")
    clips: Mapped[list["Clip"]] = relationship(back_populates="vehicle_track", cascade="all, delete-orphan")

