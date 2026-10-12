# Vehicle tracking

Detection answers: a vehicle is visible in this frame. Tracking answers: this visible vehicle is the same vehicle, for example track ID 17, across multiple frames.

ByteTrackTrackingService receives one frame's DetectionResult list through update(frame_index, detections) and returns TrackResult values. Its single instance owns the ByteTrack object and active VehicleTrackState objects for the pipeline lifetime.

VehicleTrackState records first_frame, last_frame, all bounding boxes, and confidence history. A track is moved to finalized_tracks when it has not appeared for more than max_missing_frames. Empty detection lists are valid and let ByteTrack/state aging continue.

The adapter imports only detection value objects plus numpy/supervision at runtime. It does not import or call DB, repositories, controllers, video cutting, or HTTP.

