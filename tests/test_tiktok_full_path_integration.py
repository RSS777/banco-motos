import os

import pytest

from pipeline.collectors.tiktok import TikTokCollector
from pipeline.orchestrator import run_daily_pipeline
from pipeline.processors.gemini_processor import GeminiProcessor
from pipeline.processors.tiktok_download_processor import TikTokDownloadingProcessor
from pipeline.stores.supabase_store import SupabaseStore
from tests.fakes import FakeNotifier

pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("RUN_TIKTOK_INTEGRATION") == "1"
        and os.environ.get("GEMINI_API_KEY")
        and os.environ.get("SUPABASE_URL")
        and os.environ.get("SUPABASE_SERVICE_KEY")
    ),
    reason="requires RUN_TIKTOK_INTEGRATION=1, GEMINI_API_KEY, SUPABASE_URL and "
    "SUPABASE_SERVICE_KEY; hits TikTok, Gemini and Supabase for real (slow)",
)


def test_discovery_download_analysis_and_storage_end_to_end():
    collector = TikTokCollector(search_terms=["moto elétrica"], results_per_term=3)
    processor = TikTokDownloadingProcessor(inner=GeminiProcessor.from_env())
    store = SupabaseStore.from_env()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier, max_items=3)

    assert summary.candidates_seen >= 1
    # A specific TikTok video can legitimately fail to download (removed,
    # region-locked, etc.) without that being a bug in this wiring, so we
    # only require that at least one candidate made it all the way through.
    assert summary.processed >= 1

    result = (
        store._client.table("content_records")
        .select("*")
        .eq("platform", "tiktok")
        .order("created_at", desc=True)
        .limit(summary.processed)
        .execute()
    )
    assert len(result.data) == summary.processed
    for record in result.data:
        assert record["video_url"].startswith("https://www.tiktok.com/@")
        assert record["script_pt_br"]
        assert "local_video_path" not in record
        assert "local_video_path" not in record["metadata"]
        store._client.table("content_records").delete().eq(
            "video_url", record["video_url"]
        ).execute()
