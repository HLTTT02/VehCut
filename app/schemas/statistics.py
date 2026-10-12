from pydantic import BaseModel

class VehicleClassCounts(BaseModel):
    car: int = 0
    motorcycle: int = 0
    truck: int = 0
    bus: int = 0

class StatisticsResponse(BaseModel):
    total_videos: int
    total_vehicles: int
    total_clips: int
    pending_review: int
    completed_jobs: int
    failed_jobs: int
    vehicle_classes: VehicleClassCounts

