from dataclasses import dataclass


@dataclass(frozen=True)
class VideoCandidate:
    platform: str
    url: str
    raw_metadata: dict
    # Set by a download step (e.g. the TikTok transitory download in #7)
    # before the candidate reaches the processor. The file at this path is
    # expected to still exist when Processor.process() runs; the caller
    # that set it owns deleting it afterwards.
    local_video_path: str | None = None


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
    # True when the processor (Gemini, comparing against recently stored
    # themes) judged this candidate's idea a near-duplicate of one already
    # saved, even though it's a different video. The orchestrator skips
    # storing it rather than treating this as a failure.
    is_duplicate: bool = False
    duplicate_reason: str = ""


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
    duplicates: int = 0
