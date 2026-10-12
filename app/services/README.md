# Application services

Services contain business orchestration and use repositories or external-service interfaces. They do not write SQL, accept HTTP requests, or expose ORM entities.

ReviewService is a pure, configurable quality engine. It receives tracking and clip measurements in ReviewInput; it does not call YOLO, ByteTrack, FFmpeg, storage, or repositories. All thresholds live in ReviewConfig, allowing per-environment or per-job policy without scattered rule constants.

ReviewInput.max_overlap_iou and id_switch_count are pipeline measurements. The tracking/pipeline layer calculates them; ReviewService only evaluates the supplied facts and returns ReviewDecision.

