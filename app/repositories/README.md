# Repository layer

Repositories are the only layer importing SQLAlchemy select, Session, or entity persistence details. Each provides create, get_by_id, list, update, delete, and commits a small database transaction.

Services call meaningful repository methods, for example:
    video = video_repository.get_by_id(video_id)

This keeps services focused on business orchestration, without SQL syntax, query construction, session lifecycle, or persistence mapping. Repositories never call AI, FFmpeg, tracking, HTTP, or business policies.

