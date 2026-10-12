# Chạy VehCut bằng Docker (CPU)

Thiết lập này dành cho laptop không có GPU. Worker dùng `yolov8n` (YOLO Nano)
và chỉ xử lý **một job một lúc**, phù hợp để kiểm tra video giao thông 30 giây,
60 giây hoặc khoảng 2 phút.

## 1. Chuẩn bị

- Cài và mở Docker Desktop.
- Kiểm tra Docker đang hoạt động:

  ```powershell
  docker version
  ```

- File `.env` đã được tạo cho môi trường local. Nếu clone lại dự án, tạo nó từ
  `.env.example`, sau đó thay đổi `POSTGRES_PASSWORD`.

## 2. Khởi động đầy đủ hệ thống

Tại thư mục gốc dự án, chạy:

```powershell
docker compose up --build -d
docker compose ps
```

Lần build đầu có thể mất lâu vì Docker tải Python, FFmpeg, PyTorch CPU và YOLO.
Sau khi các service có trạng thái `running`/`healthy`, mở:

- Web UI: http://localhost:5173
- API docs: http://localhost:8001/docs
- API health: http://localhost:8001/health

Xem log khi cần:

```powershell
docker compose logs -f backend worker
```

Trong lần worker chạy đầu tiên, YOLO có thể tải file `yolov8n.pt`; hãy chờ log
model tải xong trước khi gửi job đầu tiên.

## 3. Kịch bản kiểm tra CPU

1. Dùng video MP4 H.264 720p, dài 30 giây trước.
2. Trong UI đặt confidence `0.50`, bật các lớp cần thử và padding `0` hoặc `1`.
3. Upload rồi bấm xử lý; UI polling job thông qua API/worker.
4. Theo dõi worker bằng `docker compose logs -f worker`.
5. Kiểm tra kết quả, clip và trạng thái review trên UI.
6. Sau khi ổn định, thử 60 giây và cuối cùng 2 phút.

Khuyến nghị để laptop CPU dễ phản hồi: bắt đầu 720p/30fps; nếu video 1080p hoặc
quá chậm, hạ xuống 720p và thử `PROCESSING_FRAME_STRIDE=2` trong `.env`.
Stride 2 bỏ qua một nửa frame nên nhanh hơn nhưng có thể bỏ sót xe xuất hiện rất
ngắn; chỉ dùng khi đánh đổi này chấp nhận được. Sau khi đổi `.env`, chạy:

```powershell
docker compose up -d --force-recreate backend worker
```

## 4. Dừng hoặc khởi động lại

```powershell
docker compose stop
docker compose start
```

`stop/start` giữ PostgreSQL và file video/clip trong Docker volumes. Không dùng
`docker compose down -v` nếu còn dữ liệu test muốn giữ vì lệnh đó xóa volumes.

## 5. Chạy frontend ngoài Docker (tuỳ chọn)

Sau khi `backend`, `worker`, `postgres`, `redis` chạy bằng Docker:

```powershell
Set-Location frontend
npm install
npm run dev
```

Vite sẽ chạy ở URL nó in ra (thường là http://localhost:5173) và tự proxy
`/api` sang backend ở cổng 8001. Không chạy frontend Docker cùng lúc trên cổng
5173 nếu muốn dùng cách này.

## Xử lý lỗi nhanh

- `Cannot connect to Docker daemon`: mở Docker Desktop và chờ nó báo Engine
  running.
- UI hiện HTML thay vì JSON khi gọi `/api`: backend chưa chạy hoặc đang mở Vite
  mà chưa có proxy; dùng Docker UI hoặc kiểm tra http://localhost:8001/health.
- Job `FAILED`: xem `docker compose logs --tail=200 worker`; lỗi FFmpeg/video
  corrupt sẽ được ghi nguyên nhân vào job và log.
- Port đã dùng: dừng tiến trình Vite cũ hoặc đổi mapping `5173:80` trong
  `docker-compose.yml`.
