# API controller boundary

Controllers only bind HTTP input, invoke application services, convert returned entities/results into Pydantic response DTOs, and map service errors to HTTP status codes.

Request flow for processing is:
request -> VideoController -> ProcessingService.create_job -> JobRepository/VideoRepository

Controllers never import repository classes, SQLAlchemy sessions, YOLO, OpenCV, ByteTrack, FFmpeg, or storage implementations. The queued job is executed later by a worker that builds the full ProcessingService pipeline.

