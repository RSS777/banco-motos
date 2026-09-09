import os
import re
from typing import Iterable

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pipeline.models import CollectionOutcome, VideoCandidate

DEFAULT_SEARCH_TERMS = ["moto elétrica"]
SHORTS_MAX_DURATION_SECONDS = 60
DEFAULT_RESULTS_PER_TERM = 10

_ISO8601_DURATION_RE = re.compile(
    r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def _parse_iso8601_duration_seconds(duration: str) -> int:
    match = _ISO8601_DURATION_RE.fullmatch(duration)
    if not match:
        return 0
    parts = match.groupdict(default="0")
    return int(parts["hours"]) * 3600 + int(parts["minutes"]) * 60 + int(parts["seconds"])


class YouTubeCollector:
    """Collector: searches the YouTube Data API for short videos matching
    the configured search terms, keeping only results at or under
    SHORTS_MAX_DURATION_SECONDS (the classic Shorts cap), since the API has
    no dedicated Shorts filter.

    A failure on one search term yields a single error outcome for that
    term; other terms still run.
    """

    def __init__(
        self,
        api_key: str,
        search_terms: list[str] | None = None,
        results_per_term: int = DEFAULT_RESULTS_PER_TERM,
    ):
        self._api_key = api_key
        self._search_terms = search_terms or DEFAULT_SEARCH_TERMS
        self._results_per_term = results_per_term

    @classmethod
    def from_env(cls, **kwargs) -> "YouTubeCollector":
        return cls(api_key=os.environ["YOUTUBE_API_KEY"], **kwargs)

    def collect(self) -> Iterable[CollectionOutcome]:
        youtube = build("youtube", "v3", developerKey=self._api_key)
        for term in self._search_terms:
            yield from self._collect_for_term(youtube, term)

    def _collect_for_term(self, youtube, term: str) -> Iterable[CollectionOutcome]:
        try:
            search_response = (
                youtube.search()
                .list(
                    q=term,
                    part="snippet",
                    type="video",
                    videoDuration="short",
                    maxResults=self._results_per_term,
                )
                .execute()
            )
            video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
            if not video_ids:
                return
            details_response = (
                youtube.videos()
                .list(part="contentDetails,snippet", id=",".join(video_ids))
                .execute()
            )
        except HttpError as exc:
            yield CollectionOutcome(error=f"YouTube API error for term '{term}': {exc}")
            return

        for item in details_response.get("items", []):
            duration_seconds = _parse_iso8601_duration_seconds(
                item["contentDetails"]["duration"]
            )
            if duration_seconds > SHORTS_MAX_DURATION_SECONDS:
                continue

            snippet = item["snippet"]
            yield CollectionOutcome(
                candidate=VideoCandidate(
                    platform="youtube",
                    url=f"https://www.youtube.com/watch?v={item['id']}",
                    raw_metadata={
                        "title": snippet["title"],
                        "description": snippet["description"],
                        "channel": snippet["channelTitle"],
                        "duration_seconds": duration_seconds,
                        "search_term": term,
                    },
                )
            )
