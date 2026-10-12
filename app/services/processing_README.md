# Processing orchestration

ProcessingService is the only application-level coordinator for the video pipeline.

1. It loads ProcessingJob and Video using repositories.
2. It gets the original file through StorageService, then validates and reads frames through VideoService.
3. For each frame it delegates detection and tracking.
4. When ByteTrack finalizes a state (or EOF finalizes all states), it delegates full/ROI clip creation to ClipService.
5. It sends tracking and clip facts to ReviewService, then persists VehicleTrack and Clip metadata with repositories.
6. It updates job progress during the frame loop. Any pipeline exception updates job and video to FAILED, then raises ProcessingError.

The service has no SQL select statements, YOLO implementation, FFmpeg command, or HTTP response logic. Those responsibilities remain in repositories, detection, video/clip, and controller layers.

