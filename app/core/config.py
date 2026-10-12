from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    storage_root: str
    storage_public_base_url: str
    celery_broker_url: str
    celery_result_backend: str
    yolo_model_path: str
    yolo_device: str = "cpu"
    yolo_confidence_threshold: float = 0.5
    yolo_image_size: int = 640
    processing_frame_stride: int = 1
    celery_task_soft_time_limit_seconds: int = 3600
    celery_task_time_limit_seconds: int = 3660
    celery_task_max_retries: int = 3

settings = Settings()
