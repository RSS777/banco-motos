import re
import time
import urllib.parse
from typing import Iterable

from scrapling.fetchers import StealthyFetcher

from pipeline.models import CollectionOutcome, VideoCandidate

DEFAULT_SEARCH_TERMS = [
    "moto elétrica",  # pt-BR
    "electric motorcycle",  # en
    "moto eléctrica",  # es
]
DEFAULT_RESULTS_PER_TERM = 12
DEFAULT_DELAY_BETWEEN_TERMS_SECONDS = 8
SEARCH_XHR_FILTER = "api/search/general/full"
FETCH_TIMEOUT_MS = 60_000
FETCH_WAIT_MS = 5_000


def build_candidate_from_search_entry(entry: dict, term: str) -> VideoCandidate | None:
    """Map one entry of TikTok's api/search/general/full response to a
    VideoCandidate, or None if the entry isn't a real video result (e.g.
    a "related search" suggestion) or is missing required fields.
    """
    item = entry.get("item")
    if not item or entry.get("type") != 1:
        return None

    author = item.get("author", {})
    unique_id = author.get("uniqueId")
    video_id = item.get("id")
    if not unique_id or not video_id:
        return None

    stats = item.get("stats", {})
    hashtags = [c.get("title") for c in item.get("challenges", []) if c.get("title")]

    return VideoCandidate(
        platform="tiktok",
        url=f"https://www.tiktok.com/@{unique_id}/video/{video_id}",
        raw_metadata={
            "description": item.get("desc", ""),
            "author": unique_id,
            "duration_seconds": item.get("video", {}).get("duration"),
            "hashtags": hashtags,
            "play_count": stats.get("playCount"),
            "digg_count": stats.get("diggCount"),
            "search_term": term,
            # Signed TikTok CDN URL — expires (see the x-expires query param),
            # typically within a day or two. Fine for a same-day review habit;
            # not a durable thumbnail source.
            "cover_url": item.get("video", {}).get("cover"),
        },
    )


class TikTokCollector:
    """Collector: discovers TikTok videos by hashtag/keyword search, without
    logging in. Loads the search page with a stealth browser (scrapling's
    StealthyFetcher/Camoufox) and reads the results from the same XHR call
    the page itself makes (api/search/general/full) — TikTok serves real
    search results to logged-out visitors this way, confirmed against the
    live site.

    Only discovers candidates; does not download video (that is #7's job).
    Conservative pacing: a fixed delay between search terms, no proxy.

    A failure fetching one term (network error, unparseable/blocked
    response) yields a single error outcome for that term; other terms
    still run — the daily round should not die over one bad search.
    """

    def __init__(
        self,
        search_terms: list[str] | None = None,
        results_per_term: int = DEFAULT_RESULTS_PER_TERM,
        delay_between_terms_seconds: float = DEFAULT_DELAY_BETWEEN_TERMS_SECONDS,
    ):
        self._search_terms = search_terms or DEFAULT_SEARCH_TERMS
        self._results_per_term = results_per_term
        self._delay_between_terms_seconds = delay_between_terms_seconds

    def collect(self) -> Iterable[CollectionOutcome]:
        for i, term in enumerate(self._search_terms):
            if i > 0:
                time.sleep(self._delay_between_terms_seconds)
            yield from self._collect_for_term(term)

    def _collect_for_term(self, term: str) -> Iterable[CollectionOutcome]:
        try:
            query = urllib.parse.quote(term)
            page = StealthyFetcher.fetch(
                f"https://www.tiktok.com/search?q={query}",
                headless=True,
                network_idle=True,
                wait=FETCH_WAIT_MS,
                timeout=FETCH_TIMEOUT_MS,
                capture_xhr=SEARCH_XHR_FILTER,
            )
            results = self._extract_results(page, term)
        except Exception as exc:  # noqa: BLE001 - any fetch/parse failure is a per-term skip
            yield CollectionOutcome(error=f"TikTok search failed for term '{term}': {exc}")
            return

        if results is None:
            yield CollectionOutcome(
                error=(
                    f"TikTok search blocked or returned no usable data for term '{term}' "
                    f"(diagnostic: {self._diagnose(page)})"
                )
            )
            return

        for entry in results[: self._results_per_term]:
            candidate = build_candidate_from_search_entry(entry, term)
            if candidate is not None:
                yield CollectionOutcome(candidate=candidate)

    def _diagnose(self, page) -> str:
        """Best-effort hint about *why* no search XHR was captured, for the
        error string only — never raises, since this runs in the failure path.
        """
        try:
            html = page.html_content or ""
            title_match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
            title = title_match.group(1).strip() if title_match else "?"
            xhr_count = len(page.captured_xhr or [])
            flags = [
                kw
                for kw in ("captcha", "verify", "unusual traffic", "blocked", "robot")
                if kw in html.lower()
            ]
            return (
                f"title={title!r} html_len={len(html)} xhr_captured={xhr_count} "
                f"flags={flags or 'none'}"
            )
        except Exception as exc:  # noqa: BLE001 - diagnostics must never mask the real error
            return f"diagnose failed: {exc}"

    def _extract_results(self, page, term: str) -> list[dict] | None:
        for xhr in page.captured_xhr or []:
            data = xhr.json()
            if not isinstance(data, dict):
                continue
            if data.get("status_code") != 0:
                return None
            return data.get("data", [])
        return None
