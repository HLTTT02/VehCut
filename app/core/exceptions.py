from __future__ import annotations
from typing import Any

class AppError(Exception):
    code = "APPLICATION_ERROR"
    status_code = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

class VideoNotFoundError(AppError):
    code, status_code = "VIDEO_NOT_FOUND", 404

class InvalidVideoError(AppError):
    code, status_code = "INVALID_VIDEO", 422

class VideoProcessingError(AppError):
    code, status_code = "VIDEO_PROCESSING_FAILED", 500

class DetectionError(AppError):
    code, status_code = "DETECTION_FAILED", 500

class TrackingError(AppError):
    code, status_code = "TRACKING_FAILED", 500

class ClipGenerationError(AppError):
    code, status_code = "CLIP_GENERATION_FAILED", 500

class StorageError(AppError):
    code, status_code = "STORAGE_FAILED", 500

class ProcessingJobError(AppError):
    code, status_code = "PROCESSING_JOB_FAILED", 500

class RepositoryError(AppError):
    code, status_code = "REPOSITORY_FAILED", 500

class ResourceNotFoundError(AppError):
    code, status_code = "RESOURCE_NOT_FOUND", 404

