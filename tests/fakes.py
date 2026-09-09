from pipeline.interfaces import ProcessingError
from pipeline.models import CollectionOutcome, ProcessedResult, VideoCandidate


class FakeCollector:
    """Yields a fixed list of pre-built outcomes (candidates and/or errors)."""

    def __init__(self, outcomes: list[CollectionOutcome]):
        self._outcomes = outcomes

    def collect(self):
        return list(self._outcomes)


class FakeProcessor:
    """Returns a canned ProcessedResult, or raises ProcessingError for
    candidates whose URL is in `failing_urls`, or flags the result as a
    duplicate idea for candidates whose URL is in `duplicate_idea_urls`.
    """

    def __init__(
        self,
        failing_urls: set[str] | None = None,
        duplicate_idea_urls: set[str] | None = None,
    ):
        self._failing_urls = failing_urls or set()
        self._duplicate_idea_urls = duplicate_idea_urls or set()

    def process(self, candidate: VideoCandidate) -> ProcessedResult:
        if candidate.url in self._failing_urls:
            raise ProcessingError(f"gemini failed for {candidate.url}")
        return ProcessedResult(
            theme="tema fake",
            hook="gancho fake",
            format="formato fake",
            script_pt_br=f"roteiro fake para {candidate.url}",
            is_duplicate=candidate.url in self._duplicate_idea_urls,
            duplicate_reason="ideia repetida" if candidate.url in self._duplicate_idea_urls else "",
        )


class FakeStore:
    def __init__(self, existing_urls: set[str] | None = None):
        self.saved = []
        self._existing_urls = set(existing_urls or set())

    def save(self, record) -> None:
        self.saved.append(record)
        self._existing_urls.add(record.video_url)

    def exists(self, video_url: str) -> bool:
        return video_url in self._existing_urls


class FakeNotifier:
    def __init__(self):
        self.notifications = []

    def notify(self, summary) -> None:
        self.notifications.append(summary)


def candidate(
    url: str, platform: str = "youtube", local_video_path: str | None = None
) -> VideoCandidate:
    return VideoCandidate(
        platform=platform, url=url, raw_metadata={}, local_video_path=local_video_path
    )
