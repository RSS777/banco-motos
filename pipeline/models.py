from dataclasses import dataclass


@dataclass(frozen=True)
class VideoCandidate:
    platform: str
    url: str
    raw_metadata: dict


@dataclass(frozen=True)
class CollectionOutcome:
    """Result of attempting to collect a single candidate.

    Exactly one of `candidate` or `error` is set. A collector yields one
    outcome per item it attempted, so a blocked/captcha'd item can be
    reported and skipped without losing the rest of the batch.
    """

    candidate: VideoCandidate | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if (self.candidate is None) == (self.error is None):
            raise ValueError("exactly one of candidate or error must be set")


@dataclass(frozen=True)
class ProcessedResult:
    theme: str
    hook: str
    format: str
    script_pt_br: str


@dataclass(frozen=True)
class ContentRecord:
    platform: str
    video_url: str
    metadata: dict
    script_pt_br: str
    collected_at: str


@dataclass(frozen=True)
class RunSummary:
    candidates_seen: int
    processed: int
    failed: int
    skipped: int
