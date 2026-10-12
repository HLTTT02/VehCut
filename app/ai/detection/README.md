# Vehicle detection

YoloDetectionService is constructed once in Celery worker startup or dependency composition. Its constructor loads YOLO once and detect(frame) reuses that model for every frame.

Only COCO IDs 2, 3, 5, 7 are requested and returned as car, motorcycle, bus, truck. confidence_threshold is checked at construction and applied during inference. device accepts cpu, cuda, cuda:0, or None for Ultralytics automatic selection.

The module accepts a NumPy frame and returns DetectionResult values. It does not import database, repositories, controllers, video cutting, or tracking. No vehicle found is normal and returns an empty list. DetectionError is for setup/inference failures only.

