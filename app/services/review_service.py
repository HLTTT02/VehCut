from app.services.review_models import (
    ReviewConfig,
    ReviewDecision,
    ReviewInput,
    ReviewReason,
    ReviewSeverity,
)

class ReviewService:
    """Config-driven quality evaluation. It consumes tracking/clip results only."""

    def __init__(self, config: ReviewConfig | None = None) -> None:
        self._config = config or ReviewConfig()
        self._validate_config()

    def evaluate(self, payload: ReviewInput) -> ReviewDecision:
        self._validate_input(payload)
        reasons: list[ReviewReason] = []
        track = payload.track
        config = self._config

        if track.average_confidence < config.min_average_confidence:
            reasons.append(ReviewReason.LOW_CONFIDENCE)
        if self._has_track_gap(track, config.max_gap_frames):
            reasons.append(ReviewReason.TRACK_GAP)
        if self._track_duration(track, payload.fps) < config.min_track_duration_seconds:
            reasons.append(ReviewReason.SHORT_TRACK)
        if self._has_partial_vehicle(track, payload.frame_width, payload.frame_height, config.edge_margin_pixels):
            reasons.append(ReviewReason.PARTIAL_VEHICLE)
        if self._has_small_box(track, config.min_box_width, config.min_box_height):
            reasons.append(ReviewReason.SMALL_BOUNDING_BOX)
        if payload.id_switch_count > config.max_id_switches:
            reasons.append(ReviewReason.UNSTABLE_TRACK_ID)
        if payload.clip_duration < config.min_clip_duration_seconds:
            reasons.append(ReviewReason.SHORT_CLIP)
        if payload.max_overlap_iou >= config.strong_overlap_iou:
            reasons.append(ReviewReason.STRONG_TRACK_OVERLAP)

        severity = self._severity(reasons)
        return ReviewDecision(
            required=bool(reasons),
            reasons=[reason.value for reason in reasons],
            severity=severity,
        )

    @staticmethod
    def _has_track_gap(track, max_gap_frames: int) -> bool:
        return any(
            next_frame - frame > max_gap_frames + 1
            for frame, next_frame in zip(track.frame_indices, track.frame_indices[1:])
        )

    @staticmethod
    def _track_duration(track, fps: float) -> float:
        return (track.last_frame - track.first_frame + 1) / fps

    @staticmethod
    def _has_partial_vehicle(track, frame_width: int, frame_height: int, edge_margin: float) -> bool:
        return any(
            box.x1 <= edge_margin or box.y1 <= edge_margin
            or box.x2 >= frame_width - edge_margin or box.y2 >= frame_height - edge_margin
            for box in track.bounding_boxes
        )

    @staticmethod
    def _has_small_box(track, min_width: float, min_height: float) -> bool:
        return any(
            box.x2 - box.x1 < min_width or box.y2 - box.y1 < min_height
            for box in track.bounding_boxes
        )

    @staticmethod
    def _severity(reasons: list[ReviewReason]) -> ReviewSeverity:
        high_reasons = {
            ReviewReason.UNSTABLE_TRACK_ID,
            ReviewReason.STRONG_TRACK_OVERLAP,
        }
        medium_reasons = {
            ReviewReason.TRACK_GAP,
            ReviewReason.PARTIAL_VEHICLE,
            ReviewReason.SHORT_CLIP,
        }
        if any(reason in high_reasons for reason in reasons):
            return ReviewSeverity.HIGH
        if any(reason in medium_reasons for reason in reasons):
            return ReviewSeverity.MEDIUM
        return ReviewSeverity.LOW

    def _validate_config(self) -> None:
        config = self._config
        if not 0 <= config.min_average_confidence <= 1:
            raise ValueError("min_average_confidence must be between 0 and 1")
        if config.max_gap_frames < 0 or config.max_id_switches < 0:
            raise ValueError("Frame and ID thresholds must be non-negative")
        if min(
            config.min_track_duration_seconds,
            config.min_box_width,
            config.min_box_height,
            config.edge_margin_pixels,
            config.min_clip_duration_seconds,
        ) < 0:
            raise ValueError("Review thresholds must be non-negative")
        if not 0 <= config.strong_overlap_iou <= 1:
            raise ValueError("strong_overlap_iou must be between 0 and 1")

    @staticmethod
    def _validate_input(payload: ReviewInput) -> None:
        if payload.fps <= 0 or payload.frame_width <= 0 or payload.frame_height <= 0:
            raise ValueError("fps and frame dimensions must be positive")
        if payload.clip_duration < 0 or payload.id_switch_count < 0:
            raise ValueError("clip duration and ID switch count must be non-negative")
        if not 0 <= payload.max_overlap_iou <= 1:
            raise ValueError("max_overlap_iou must be between 0 and 1")

