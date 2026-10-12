# Storage abstraction

StorageService exposes save_original_video, save_clip, save_roi_clip, get_file, delete_file, and build_file_url. It does not depend on FastAPI controllers or repositories.

LocalStorageService stores bytes under storage/originals, storage/clips, and storage/roi. It returns a relative path, for example clips/<uuid>_vehicle.mp4. Entities/repositories persist only original_path, full_clip_path, and roi_clip_path. PostgreSQL never stores video bytes.

To adopt S3 or MinIO, implement these same methods in S3StorageService and replace the binding in core/dependencies.py. ProcessingService depends on StorageService, not LocalStorageService, so no ProcessingService code changes. The S3 adapter can keep the same key format and produce signed/public URLs in build_file_url.

