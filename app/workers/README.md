# Background processing

POST /api/videos/{video_id}/process creates a ProcessingJob with PENDING status, enqueues process_video_job(job_id), and returns HTTP 202 immediately. The frontend polls GET /api/jobs/{job_id}; values progress through PENDING, PROCESSING, COMPLETED, or FAILED.

The Celery task contains no YOLO, ByteTrack, OpenCV, FFmpeg, SQL, or pipeline logic. It builds ProcessingService once for the worker invocation and calls process(job_id).

Celery uses Redis as broker/result backend. Late acknowledgement and reject-on-worker-lost make an unacknowledged task requeue after a worker crash. Soft/hard time limits are configurable. Exceptions retry with backoff up to the configured limit; ProcessingService records FAILED and the error message for each failed pipeline attempt. A hard kill cannot write DB state at that instant, but Celery requeues the task because task_reject_on_worker_lost is enabled.

