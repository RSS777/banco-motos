import os

import pytest

from pipeline.collectors.youtube import YouTubeCollector
from pipeline.orchestrator import run_daily_pipeline
from pipeline.processors.gemini_processor import GeminiProcessor
from pipeline.stores.supabase_store import SupabaseStore
from tests.fakes import FakeNotifier

pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("YOUTUBE_API_KEY")
        and os.environ.get("GEMINI_API_KEY")
        and os.environ.get("SUPABASE_URL")
        and os.environ.get("SUPABASE_SERVICE_KEY")
    ),
    reason="requires YOUTUBE_API_KEY, GEMINI_API_KEY, SUPABASE_URL and SUPABASE_SERVICE_KEY",
)


def test_youtube_candidates_analyzed_via_native_url_no_download():
    """The real path #8 wires up: Gemini receives the YouTube URL directly
    (no yt-dlp download for this platform, see GeminiProcessor._video_part).
    """
    collector = YouTubeCollector.from_env(results_per_term=2)
    processor = GeminiProcessor.from_env()
    store = SupabaseStore.from_env()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier, max_items=1)

    assert summary.processed == 1
    assert summary.failed == 0

    result = (
        store._client.table("content_records")
        .select("*")
        .eq("platform", "youtube")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    assert len(result.data) == 1
    record = result.data[0]
    assert record["script_pt_br"]
    assert record["metadata"]["theme"]

    store._client.table("content_records").delete().eq("id", record["id"]).execute()
