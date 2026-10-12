# VehCut

Web application upload video giao thông, phát hiện và theo dõi `car`, `motorcycle`, `bus`, `truck`, tạo clip/crop ROI, hỗ trợ review và tải kết quả. Dự án không bao gồm OCR biển số, payment, barrier hoặc nghiệp vụ parking.

## Stack

- Frontend: React + Vite
- Backend: FastAPI (Python), Pydantic, SQLAlchemy, PostgreSQL
- AI/video: Ultralytics YOLO, ByteTrack, OpenCV, FFmpeg
- Async: Celery + Redis
- Storage: Local qua abstraction; có thể thay MinIO/S3
- Deploy: Docker, hỗ trợ NVIDIA CUDA nếu có

## Kiến trúc

```text
React + Vite Web UI
        │ HTTP / WebSocket
        ▼
FastAPI Controller
        ▼
Pydantic DTO Validation
        ▼
Application Service
        ▼
Repository
        ▼
PostgreSQL (metadata/path)
```

Pipeline chạy nền bằng Celery:

```text
ProcessingService
 ├── DetectionService → Ultralytics YOLO
 ├── TrackingService  → ByteTrack
 ├── ClipService      → OpenCV + FFmpeg
 └── StorageService   → LocalStorage / MinIO / S3
```

`ProcessingService` điều phối pipeline, dùng repository để lưu trạng thái. Các module AI/video chỉ nhận input domain cần thiết; không phụ thuộc Controller, ORM hay database.

## Luồng nghiệp vụ

1. UI upload video và cấu hình lớp xe, confidence, ROI, padding, clip length.
2. `VideoController` validate DTO, gọi `ProcessingService.create_job`.
3. Service lưu file bằng `StorageService`, lưu metadata/path bằng repository, enqueue Celery task.
4. Worker gọi `ProcessingService.run`; service gọi detect → tracking → cắt/crop.
5. Service lưu tracks, clip, thumbnail, review status qua repository; UI nhận tiến độ qua WebSocket/SSE và tải kết quả qua API.

## Quy tắc phân lớp

| Layer | Được làm | Không được làm | Phụ thuộc |
| --- | --- | --- | --- |
| Controller | Routing, auth, HTTP status, nhận/trả DTO | Business logic, query DB | DTO, Service |
| DTO | Validate và serialize request/response | Là ORM entity | Pydantic |
| Service | Nghiệp vụ, orchestration, transaction boundary | SQL trực tiếp | Repository/service interfaces |
| Repository | CRUD/query với SQLAlchemy | Business rule, AI/video | Entity, session |
| Entity | Mapping bảng PostgreSQL | Trả trực tiếp cho frontend | SQLAlchemy |
| AI/Video | Inference, tracking, time range, cut/crop | Controller/DB access | Domain value objects |
| Storage adapter | Đọc/ghi file theo storage key | Logic job/clip | Storage interface |

Entity luôn được Service chuyển thành response DTO. File video không lưu binary trong PostgreSQL: DB chỉ lưu metadata, path/storage key.

## Module dependency

```text
api/controllers ──► api/dtos ──► application/services ──► repositories ──► database
                                      │
                                      ├──► ai/detection + ai/tracking
                                      ├──► video/clip
                                      └──► storage
workers/celery_tasks ─────────────────► application/services
```

| Module | Cung cấp | Phụ thuộc trực tiếp |
| --- | --- | --- |
| `api.controllers` | Endpoint FastAPI | DTO, service interface |
| `api.dtos` | Pydantic request/response | Không phụ thuộc ORM/controller |
| `application.processing_service` | Tạo/chạy/cập nhật job | Repository, Detection/Tracking/Clip/Storage interfaces |
| `application.review_service` | Quyết định review | Clip/Review repositories |
| `infrastructure.ai` | YOLO và ByteTrack implementations | Thư viện AI, domain models |
| `infrastructure.video` | Cut/crop bằng OpenCV/FFmpeg | Domain models, OpenCV/FFmpeg |
| `infrastructure.storage` | Local/MinIO/S3 adapter | Storage interface |
| `infrastructure.repositories` | SQLAlchemy repositories | Entity, DB session |
| `workers` | Celery task | Service interface, Celery/Redis |

Dependency chỉ đi theo mũi tên. Ví dụ Detection/Tracking không import controller, repository hay SQLAlchemy; repository không gọi service; controller không import entity/session.

## Interface cốt lõi

```python
from typing import Protocol, Iterable

class DetectionService(Protocol):
    def detect(self, video_path: str, config: "ProcessingConfig") -> Iterable["FrameDetections"]: ...

class TrackingService(Protocol):
    def track(self, detections: Iterable["FrameDetections"]) -> list["VehicleTrack"]: ...

class ClipService(Protocol):
    def create_clips(self, video_path: str, tracks: list["VehicleTrack"], config: "ProcessingConfig") -> list["ClipArtifact"]: ...

class StorageService(Protocol):
    def save_upload(self, source: object, key: str) -> str: ...
    def save_artifact(self, local_path: str, key: str) -> str: ...
    def open(self, key: str) -> object: ...

class ProcessingJobRepository(Protocol):
    def create(self, job: "ProcessingJob") -> "ProcessingJob": ...
    def get_by_id(self, job_id: str) -> "ProcessingJob | None": ...
    def update_status(self, job_id: str, status: str, progress: int) -> None: ...
```

FastAPI dependency injection cung cấp implementation: `YoloDetectionService`, `ByteTrackTrackingService`, `FfmpegClipService`, `LocalStorageService` và SQLAlchemy repositories. Đổi sang MinIO/S3 chỉ thay `StorageService` implementation.

## Entity và repository

| Entity / Repository | Dữ liệu |
| --- | --- |
| `Video` / `VideoRepository` | filename, MIME type, size, duration, storage key, upload time |
| `ProcessingJob` / `ProcessingJobRepository` | video, config JSON, `PENDING/PROCESSING/COMPLETED/FAILED`, progress, error |
| `VehicleTrack` / `TrackRepository` | track ID, vehicle type, first/last seen, confidence, review flag |
| `Clip` / `ClipRepository` | start/end, output/crop/thumbnail keys, review status |
| `ReviewDecision` / `ReviewRepository` | decision, note, reviewer, reviewed time |

Detection frame-level chỉ lưu khi cần audit/debug; dữ liệu lớn nên lưu JSON/Parquet trên storage và lưu key tại DB.

## API

| Endpoint | Chức năng |
| --- | --- |
| `POST /api/videos` | Upload, trả `VideoResponse` |
| `POST /api/videos/{video_id}/processing-jobs` | Tạo job từ `ProcessingConfigRequest` |
| `GET /api/processing-jobs/{job_id}` | Trạng thái/tiến độ (`ProcessingJobResponse`) |
| `GET /api/videos/{video_id}/clips` | Danh sách `ClipResponse` |
| `GET /api/clips/{clip_id}/download` | Tải clip/crop artifact |
| `PATCH /api/clips/{clip_id}/review` | `OK`, `NEEDS_REVIEW`, `REJECTED` |
| `WS /api/processing-jobs/{job_id}/progress` | Đẩy tiến độ worker |

```json
{
  "confidence_threshold": 0.5,
  "vehicle_classes": ["car", "motorcycle", "bus", "truck"],
  "padding_before_seconds": 2,
  "padding_after_seconds": 3,
  "minimum_clip_seconds": 1,
  "roi": {"type": "polygon", "points": [[0.1, 0.2], [0.9, 0.2], [0.9, 0.9], [0.1, 0.9]]}
}
```

## Quy tắc xử lý

- Giữ detection đúng lớp xe và confidence đạt ngưỡng.
- ByteTrack liên kết detection thành `VehicleTrack`.
- Khoảng clip là `first_seen - padding_before` đến `last_seen + padding_after`, clamp theo duration video; gộp range chồng lấn và bỏ clip ngắn hơn mức cấu hình.
- `ClipService` crop ROI theo bounding box xe, padding crop tùy cấu hình và không vượt khung hình.
- Gắn `NEEDS_REVIEW` khi confidence thấp, track ngắn/gián đoạn, bbox bất thường hoặc crop/FFmpeg lỗi. Không tự xóa artifact cần review.

## Cấu trúc thư mục

```text
backend/app/
  api/controllers/       # FastAPI, không business logic
  api/dtos/              # Pydantic schemas
  application/services/  # ProcessingService, ReviewService
  domain/                # Value objects và protocols
  infrastructure/
    database/            # entities, session, migrations
    repositories/        # SQLAlchemy implementations
    storage/             # Local / MinIO / S3
    ai/                  # YOLO, ByteTrack
    video/               # OpenCV, FFmpeg
  workers/               # Celery tasks
frontend/src/
  pages/ components/ services/ stores/ types/
docker-compose.yml
```

## Deploy

Docker Compose chạy `frontend`, `api`, `worker`, `postgres`, `redis`. Mount volume cho local storage. API và worker dùng cùng backend image, nhưng chỉ worker thực thi inference/FFmpeg. Worker chọn `cuda` khi NVIDIA runtime/CUDA khả dụng, nếu không chạy CPU.
