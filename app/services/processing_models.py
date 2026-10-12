from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessingConfig:
    padding_before: float = 2.0
    padding_after: float = 3.0

    def __post_init__(self) -> None:
        if self.padding_before < 0 or self.padding_after < 0:
            raise ValueError("Clip padding must be non-negative")

@dataclass(frozen=True)
class ProcessingOutcome:
    job_id: str
    processed_tracks: int
    created_clips: int

from app.core.exceptions import ProcessingJobError

ProcessingError = ProcessingJobError
