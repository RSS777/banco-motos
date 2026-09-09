import os

import pytest

from pipeline.collectors.tiktok import TikTokCollector

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_TIKTOK_INTEGRATION") != "1",
    reason="hits the real TikTok site with a real browser; opt in explicitly "
    "with RUN_TIKTOK_INTEGRATION=1 (slow, and subject to TikTok's own rate limiting)",
)


def test_collects_real_candidates_without_login_for_one_term():
    collector = TikTokCollector(search_terms=["moto elétrica"], results_per_term=5)

    outcomes = list(collector.collect())

    assert len(outcomes) > 0
    errors = [o for o in outcomes if o.error]
    assert not errors, f"unexpected collection errors: {errors}"
    for outcome in outcomes:
        assert outcome.candidate.platform == "tiktok"
        assert outcome.candidate.url.startswith("https://www.tiktok.com/@")
        assert "/video/" in outcome.candidate.url
        assert outcome.candidate.raw_metadata["description"] or outcome.candidate.raw_metadata[
            "hashtags"
        ]
