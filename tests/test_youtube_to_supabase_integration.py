import os

import pytest

from pipeline.collectors.youtube import YouTubeCollector
from pipeline.orchestrator import run_daily_pipeline
from pipeline.stores.supabase_store import SupabaseStore
from tests.fakes import FakeNotifier, FakeProcessor

pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("YOUTUBE_API_KEY")
        and os.environ.get("SUPABASE_URL")
        and os.environ.get("SUPABASE_SERVICE_KEY")
    ),
    reason="requires YOUTUBE_API_KEY, SUPABASE_URL and SUPABASE_SERVICE_KEY",
)


def test_real_youtube_candidates_flow_into_real_supabase():
    collector = YouTubeCollector.from_env(results_per_term=3)
    store = SupabaseStore.from_env()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], FakeProcessor(), store, notifier, max_items=3)

    assert summary.processed > 0
    result = (
        store._client.table("content_records")
        .select("*")
        .eq("platform", "youtube")
        .order("created_at", desc=True)
        .limit(summary.processed)
        .execute()
    )
    assert len(result.data) == summary.processed
    saved_urls = {row["video_url"] for row in result.data}

    # Clean up: this run's records are test noise, not real curated content.
    for url in saved_urls:
        store._client.table("content_records").delete().eq("video_url", url).execute()
