from __future__ import annotations


class SnapshotService:
    """OpenCV image encoding adapter; no HTTP, AI inference, or DB access."""

    def encode_jpeg(self, frame: object) -> bytes | None:
        if getattr(frame, "size", 0) == 0:
            return None
        try:
            import cv2
            ok, payload = cv2.imencode(".jpg", frame)
            return payload.tobytes() if ok else None
        except Exception:
            return None
