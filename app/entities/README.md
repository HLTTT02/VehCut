# Persistence model

Video 1 -- many ProcessingJob
Video 1 -- many VehicleTrack
VehicleTrack 1 -- many Clip
Clip 1 -- many Review

All foreign keys use ON DELETE CASCADE. original_path, full_clip_path, and roi_clip_path are references to local/object storage; PostgreSQL never stores video binary data.

Entity is a SQLAlchemy persistence model: it maps database columns, foreign keys, and relationships. A DTO is a Pydantic input/output contract for HTTP. Entities can evolve with the database and must never be serialized directly to clients; DTOs expose only fields and validation allowed by the API.

