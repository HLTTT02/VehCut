from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from app.video.errors import InvalidVideoError, VideoProcessingError
from app.video.models import TrackBox, VideoMetadata

class VideoService:
    """OpenCV/FFmpeg adapter. It has no database, controller, AI, or tracking dependency."""

    def __init__(self, ffmpeg_binary: str = "ffmpeg") -> None:
        self._ffmpeg_binary = ffmpeg_binary

    def validate_video(self, video_path: str | Path) -> VideoMetadata:
        path = self._require_file(video_path)
        capture = self._open_capture(path)
        try:
            metadata = self._metadata_from_capture(path, capture)
            if metadata.frame_count <= 0 or metadata.fps <= 0 or metadata.width <= 0 or metadata.height <= 0:
                raise InvalidVideoError(f"Corrupt or unsupported video: {path}")
            if metadata.codec is None:
                raise InvalidVideoError(f"Unsupported video codec: {path}")
            return metadata
        finally:
            capture.release()

    def get_metadata(self, video_path: str | Path) -> VideoMetadata:
        return self.validate_video(video_path)

    def extract_frame(self, video_path: str | Path, frame_index: int):
        if frame_index < 0:
            raise VideoProcessingError("frame_index must be non-negative")
        capture = self._open_capture(self._require_file(video_path))
        try:
            frame_count = int(capture.get(self._cv2().CAP_PROP_FRAME_COUNT))
            if frame_index >= frame_count:
                raise VideoProcessingError(f"Frame index {frame_index} is outside the video")
            capture.set(self._cv2().CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok or frame is None:
                raise VideoProcessingError(f"Cannot read frame {frame_index}")
            return frame
        finally:
            capture.release()

    def iter_frames(self, video_path: str | Path):
        """Yield (frame_index, frame) and surface unexpected read failures."""
        path = self._require_file(video_path)
        capture = self._open_capture(path)
        cv2 = self._cv2()
        expected_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_index = 0
        try:
            while frame_index < expected_frames:
                ok, frame = capture.read()
                if not ok or frame is None:
                    raise VideoProcessingError(f"Cannot read frame {frame_index}")
                yield frame_index, frame
                frame_index += 1
        finally:
            capture.release()

    @staticmethod
    def time_to_frame(time_seconds: float, fps: float) -> int:
        if time_seconds < 0 or fps <= 0:
            raise VideoProcessingError("time_seconds must be >= 0 and fps must be > 0")
        return int(time_seconds * fps)

    @staticmethod
    def frame_to_time(frame_index: int, fps: float) -> float:
        if frame_index < 0 or fps <= 0:
            raise VideoProcessingError("frame_index must be >= 0 and fps must be > 0")
        return frame_index / fps

    def cut_video(self, video_path: str | Path, output_path: str | Path, start_time: float, end_time: float) -> Path:
        source = self._require_file(video_path)
        if start_time < 0 or end_time <= start_time:
            raise VideoProcessingError("Cut range must satisfy 0 <= start_time < end_time")
        duration = self.get_metadata(source).duration
        if end_time > duration:
            raise VideoProcessingError("Cut end_time exceeds video duration")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        self._run_ffmpeg([
            "-y", "-ss", str(start_time), "-to", str(end_time), "-i", str(source),
            "-c:v", "libx264", "-c:a", "aac", str(output),
        ])
        if not output.is_file() or output.stat().st_size == 0:
            raise VideoProcessingError("FFmpeg did not produce an output file")
        return output

    def crop_roi_video(
        self, video_path: str | Path, output_path: str | Path, track_boxes: Sequence[TrackBox]
    ) -> Path:
        """Crop a frame-aligned ROI that follows the nearest track bounding box."""

        if not track_boxes:
            raise VideoProcessingError("track_boxes must not be empty")
        source = self._require_file(video_path)
        metadata = self.get_metadata(source)
        crop_width = min(metadata.width, max(box.width for box in track_boxes))
        crop_height = min(metadata.height, max(box.height for box in track_boxes))
        if crop_width <= 0 or crop_height <= 0:
            raise VideoProcessingError("Track boxes do not create a valid crop ROI")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        intermediate_output = output.with_name(f"{output.stem}.intermediate.mp4")
        cv2 = self._cv2()
        capture = self._open_capture(source)
        writer = cv2.VideoWriter(
            str(intermediate_output), cv2.VideoWriter_fourcc(*"mp4v"), metadata.fps, (crop_width, crop_height)
        )
        if not writer.isOpened():
            capture.release()
            raise VideoProcessingError(f"Cannot create ROI output: {output}")
        processed_frames = 0
        boxes_by_frame = {box.frame_index: box for box in track_boxes}
        known_indices = sorted(boxes_by_frame)
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                box = boxes_by_frame.get(processed_frames)
                if box is None:
                    nearest_index = min(known_indices, key=lambda index: abs(index - processed_frames))
                    box = boxes_by_frame[nearest_index]
                center_x = box.x + box.width / 2
                center_y = box.y + box.height / 2
                x1 = max(0, min(metadata.width - crop_width, round(center_x - crop_width / 2)))
                y1 = max(0, min(metadata.height - crop_height, round(center_y - crop_height / 2)))
                crop = frame[y1:y1 + crop_height, x1:x1 + crop_width]
                if crop.size == 0:
                    raise VideoProcessingError("Cannot crop video frame")
                writer.write(crop)
                processed_frames += 1
        finally:
            writer.release()
            capture.release()
        if processed_frames != metadata.frame_count:
            raise VideoProcessingError("Frame read failed while creating ROI crop")
        # OpenCV's mp4v output is not consistently supported by browsers.
        # Re-encode the temporary crop to H.264/YUV420P for HTML video playback.
        try:
            self._run_ffmpeg([
                "-y", "-i", str(intermediate_output), "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
            ])
        finally:
            intermediate_output.unlink(missing_ok=True)
        if not output.is_file() or output.stat().st_size == 0:
            raise VideoProcessingError("ROI crop did not produce an output file")
        return output

    def _run_ffmpeg(self, args: list[str]) -> None:
        if shutil.which(self._ffmpeg_binary) is None:
            raise VideoProcessingError(f"FFmpeg executable not found: {self._ffmpeg_binary}")
        result = subprocess.run(
            [self._ffmpeg_binary, *args], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            message = result.stderr.strip() or "Unknown FFmpeg error"
            raise VideoProcessingError(f"FFmpeg failed: {message}")

    def _open_capture(self, path: Path):
        capture = self._cv2().VideoCapture(str(path))
        if not capture.isOpened():
            raise InvalidVideoError(f"Cannot open video (corrupt or unsupported codec): {path}")
        return capture

    def _metadata_from_capture(self, path: Path, capture) -> VideoMetadata:
        cv2 = self._cv2()
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        codec_value = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(chr((codec_value >> 8 * index) & 0xFF) for index in range(4)).strip() or None
        return VideoMetadata(
            path=path, fps=fps, frame_count=frame_count,
            duration=frame_count / fps if fps > 0 else 0,
            width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            codec=codec,
        )

    @staticmethod
    def _require_file(video_path: str | Path) -> Path:
        path = Path(video_path)
        if not path.is_file():
            raise VideoProcessingError(f"Video file does not exist: {path}")
        return path

    @staticmethod
    def _cv2():
        try:
            import cv2
            return cv2
        except ImportError as error:
            raise VideoProcessingError("OpenCV is not installed") from error
