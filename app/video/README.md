# Video processing

VideoService is a standalone OpenCV/FFmpeg adapter. It accepts paths and returns VideoMetadata, OpenCV frames, or output paths. It never imports controllers, services, repositories, entities, or database code.

ClipService composes VideoService and StorageService: it calculates the padded range of a finalized VehicleTrackState, creates a full clip, then creates a bbox-following ROI clip. It returns ClipResult with storage paths, duration, and track ID. It does not detect vehicles, access a database, or handle HTTP.

ROI crop follows the track per output frame. The crop window centers on the matching TrackBox; frames without a detection (including padding) use the nearest track box. Output dimensions are fixed to the largest bbox window so the MP4 encoder can write a valid stream.

- validate_video and get_metadata reject missing, corrupt, unreadable, or unsupported-codec files.
- extract_frame raises VideoProcessingError when a requested frame cannot be read.
- cut_video delegates to FFmpeg and exposes its error as VideoProcessingError.
- crop_roi_video accepts TrackBox values from a caller and does not detect or track vehicles.

ProcessingService may call ClipService, then persist ClipResult through repositories. Neither video module performs this persistence.

