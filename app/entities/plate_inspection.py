import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlateInspection(Base):
    """Persistent output of the secondary plate detector and OCR for one vehicle track."""

    __tablename__ = "plate_inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_track_id: Mapped[str] = mapped_column(ForeignKey("vehicle_tracks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plate_detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    plate_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detector_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
