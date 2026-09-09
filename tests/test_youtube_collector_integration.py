import os

import pytest

from pipeline.collectors.youtube import YouTubeCollector

pytestmark = pytest.mark.skipif(
    not os.environ.get("YOUTUBE_API_KEY"),
    reason="requires YOUTUBE_API_KEY to hit the real YouTube Data API",
)


def test_collects_real_short_candidates_for_default_search_term():
    collector = YouTubeCollector.from_env(results_per_term=5)

    outcomes = list(collector.collect())

    assert len(outcomes) > 0
    errors = [o for o in outcomes if o.error]
    assert not errors, f"unexpected collection errors: {errors}"
    for outcome in outcomes:
        assert outcome.candidate.platform == "youtube"
        assert outcome.candidate.url.startswith("https://www.youtube.com/watch?v=")
        assert outcome.candidate.raw_metadata["duration_seconds"] <= 60
        assert outcome.candidate.raw_metadata["title"]


def test_unknown_search_term_yields_no_error_just_empty_results():
    collector = YouTubeCollector.from_env(
        search_terms=["asdkjaslkdjaslkdjqwoieqwoiejqwoiejasdkjhasdlkjh12345"],
        results_per_term=5,
    )

    outcomes = list(collector.collect())

    assert all(o.error is None for o in outcomes)
