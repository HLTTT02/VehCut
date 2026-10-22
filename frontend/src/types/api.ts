export type VehicleClass = "person" | "car" | "motorcycle" | "bus" | "truck";
export type JobState = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
export type ClipState = "READY" | "NEEDS_REVIEW" | "REJECTED" | "FAILED";
export interface Video { id: string; filename: string; original_path: string; duration: number | null; fps: number | null; width: number | null; height: number | null; status: string; created_at: string; }
export interface UploadedVideo { id: string; filename: string; original_path: string; status: string; }
export interface ProcessOptions { confidence_threshold: number; vehicle_classes: VehicleClass[]; padding_before: number; padding_after: number; min_clip_duration: number; }
export interface JobStatus { id: string; video_id: string; status: JobState; progress: number; started_at: string | null; completed_at: string | null; error_message: string | null; }
export interface VehicleTrack { id: string; video_id: string; track_id: number; vehicle_class: VehicleClass; start_time: number; end_time: number; avg_confidence: number; review_required: boolean; }
export interface Clip { id: string; vehicle_track_id: string; full_clip_path: string; roi_clip_path: string | null; duration: number; status: ClipState; created_at: string; }
export interface ReviewRequest { status: "PENDING" | "APPROVED" | "REJECTED"; reason?: string; note?: string; }
export interface VehicleClassCounts { person: number; car: number; motorcycle: number; truck: number; bus: number; }
export interface Statistics { total_videos: number; total_vehicles: number; total_clips: number; pending_review: number; completed_jobs: number; failed_jobs: number; vehicle_classes: VehicleClassCounts; }
export interface JobHistory { id: string; video_id: string; filename: string | null; status: JobState; progress: number; started_at: string | null; completed_at: string | null; error_message: string | null; }
export interface DetectionBox { vehicle_class: VehicleClass; confidence: number; x1: number; y1: number; x2: number; y2: number; }
export interface FrameDetections { time_seconds: number; detections: DetectionBox[]; }
export interface RoiPoint { x: number; y: number; }
export interface RoiZone { id: string; video_id: string; name: string; points: RoiPoint[]; enabled: boolean; created_at: string; updated_at: string; }
export interface RoiZoneCreate { name: string; points: RoiPoint[]; enabled?: boolean; }
export interface SuspiciousEvent { id: string; video_id: string; vehicle_track_id: string; event_type: string; severity: string; screenshot_path: string | null; message: string; created_at: string; }
