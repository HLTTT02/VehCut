# Backend dependency guide

- `api/controllers` depends only on schemas and services. It owns HTTP request/response, never SQL or business logic.
- `schemas` contains Pydantic DTOs. DTOs do not depend on SQLAlchemy entities; entities never return straight to the frontend.
- `services` owns business orchestration and depends on repository plus AI/video/storage interfaces, never direct SQL.
- `repositories` is the only PostgreSQL access layer and depends on entities plus a database session.
- `entities` maps SQLAlchemy tables. `db` provides Base, engine, and sessions.
- `core/dependencies.py` is the composition root, wiring implementations through FastAPI Depends.
- `ai/detection` and `ai/tracking` contain framework-neutral contracts and must not import controller, repository, entity, or DB modules.
- `video` contains OpenCV/FFmpeg contracts and never depends on controllers.
- `storage` hides Local/MinIO/S3 behind StorageService.
- `workers` contains Celery entry points; a worker calls application services rather than individual repositories or AI adapters.

