# ROI filter

`PolygonRoiFilter` receives normalized polygons and model bounding boxes. It retains a box when its center is inside any enabled polygon. The module is pure geometry and depends only on AI DTOs; it does not depend on controllers, services, repositories, PostgreSQL, storage, or YOLO.
