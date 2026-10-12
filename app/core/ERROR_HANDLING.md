# Error handling

All public application failures inherit AppError and are mapped by FastAPI to this response shape:

    {"code": "VIDEO_PROCESSING_FAILED", "message": "...", "details": {}}

The API never returns Python stack traces. The global handler writes the exception chain to server logs; errors are raised with "raise ... from error", preserving the original module failure for developers.

- Invalid/corrupt source file: InvalidVideoError (422)
- FFmpeg/OpenCV failure: VideoProcessingError
- YOLO/ByteTrack failure: DetectionError / TrackingError
- Full/ROI artifact failure: ClipGenerationError
- Local/S3 storage failure: StorageError
- DB driver/transaction failure: RepositoryError. The repository decorator rolls back its session before raising it.
- Pipeline failure: ProcessingJobError. ProcessingService catches the root error, marks the ProcessingJob and Video FAILED, then rethrows a chained processing error.

Request Pydantic validation is also normalized to VALIDATION_FAILED with HTTP 422.

