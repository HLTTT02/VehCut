# Plate detection

`YoloPlateDetectionService` accepts a cropped vehicle ROI from the person/vehicle pipeline and returns zero or more `plate` bounding boxes in ROI-relative coordinates.

Dependencies: `app.ai.plate` → Ultralytics and shared AI DTOs only. It does not depend on HTTP, repositories, PostgreSQL, storage, tracking, or OCR. A later application-level service may combine its output across frames and invoke an OCR adapter.
