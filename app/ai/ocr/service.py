from typing import Protocol


class PlateOcrService(Protocol):
    """Port for reading a cropped plate image; no DB, controller, or video dependency."""

    def read(self, plate_roi: object) -> str | None: ...
