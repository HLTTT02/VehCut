from __future__ import annotations

import re

from app.ai.tracking.errors import TrackingError


class TesseractPlateOcrService:
    """Small local OCR adapter for Vietnamese-style alphanumeric licence plates."""

    def __init__(self, minimum_characters: int = 4) -> None:
        self._minimum_characters = minimum_characters
        try:
            import pytesseract
            self._pytesseract = pytesseract
        except ImportError as error:
            raise TrackingError("Plate OCR requires pytesseract") from error

    def read(self, plate_roi: object) -> str | None:
        if getattr(plate_roi, "size", 0) == 0:
            return None
        try:
            raw = self._pytesseract.image_to_string(
                plate_roi,
                config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.",
            )
        except Exception as error:
            raise TrackingError("Plate OCR failed") from error
        normalized = re.sub(r"[^A-Z0-9.-]", "", raw.upper())
        return normalized if len(re.sub(r"[^A-Z0-9]", "", normalized)) >= self._minimum_characters else None
