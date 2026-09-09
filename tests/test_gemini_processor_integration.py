import os

import pytest

from pipeline.models import CollectionOutcome
from pipeline.orchestrator import run_daily_pipeline
from pipeline.processors.gemini_processor import GeminiProcessor
from pipeline.stores.supabase_store import SupabaseStore
from tests.fakes import FakeCollector, FakeNotifier, candidate

pytestmark = pytest.mark.skipif(
    not (
        os.environ.get("GEMINI_API_KEY")
        and os.environ.get("SAMPLE_VIDEO_PATH")
        and os.environ.get("SUPABASE_URL")
        and os.environ.get("SUPABASE_SERVICE_KEY")
    ),
    reason="requires GEMINI_API_KEY, SAMPLE_VIDEO_PATH, SUPABASE_URL and SUPABASE_SERVICE_KEY",
)


def test_orchestrator_with_real_gemini_and_store_produces_full_record():
    sample_video_path = os.environ["SAMPLE_VIDEO_PATH"]
    marker_url = "https://example.com/gemini-integration-test-marker"

    collector = FakeCollector(
        [CollectionOutcome(candidate=candidate(marker_url, local_video_path=sample_video_path))]
    )
    processor = GeminiProcessor.from_env()
    store = SupabaseStore.from_env()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert summary.processed == 1
    assert summary.failed == 0

    result = (
        store._client.table("content_records")
        .select("*")
        .eq("video_url", marker_url)
        .execute()
    )
    assert len(result.data) == 1
    record = result.data[0]
    assert record["script_pt_br"]
    assert record["metadata"]["theme"]
    assert record["metadata"]["hook"]
    assert record["metadata"]["format"]

    store._client.table("content_records").delete().eq("video_url", marker_url).execute()
