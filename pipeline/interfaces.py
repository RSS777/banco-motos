from typing import Iterable, Protocol

from pipeline.models import CollectionOutcome, ProcessedResult, RunSummary, VideoCandidate


class ProcessingError(Exception):
    """Raised by a Processor when a candidate could not be analyzed/scripted."""


class Collector(Protocol):
    def collect(self) -> Iterable[CollectionOutcome]:
        """Yield one outcome per candidate attempted (success or error)."""
        ...


class Processor(Protocol):
    def process(self, candidate: VideoCandidate) -> ProcessedResult:
        """Analyze a candidate and return its metadata + pt-BR script.

        Raises ProcessingError if the candidate could not be processed.
        """
        ...


class Store(Protocol):
    def save(self, record) -> None:
        ...

    def exists(self, video_url: str) -> bool:
        """True if a record for this exact video URL is already stored."""
        ...


class Notifier(Protocol):
    def notify(self, summary: RunSummary) -> None:
        ...
