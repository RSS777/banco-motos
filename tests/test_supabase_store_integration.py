import os

import pytest

from pipeline.orchestrator import run_daily_pipeline
from pipeline.stores.supabase_store import SupabaseStore
from tests.fakes import FakeCollector, FakeNotifier, FakeProcessor, candidate
from pipeline.models import CollectionOutcome

pytestmark = pytest.mark.skipif(
    not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY")),
    reason="requires SUPABASE_URL and SUPABASE_SERVICE_KEY to hit the real project",
)


def test_orchestrator_with_real_store_persists_a_queryable_record():
    store = SupabaseStore.from_env()
    marker_url = "https://example.com/integration-test-marker"
    collector = FakeCollector([CollectionOutcome(candidate=candidate(marker_url))])

    run_daily_pipeline([collector], FakeProcessor(), store, FakeNotifier())

    result = (
        store._client.table("content_records")
        .select("*")
        .eq("video_url", marker_url)
        .execute()
    )
    assert len(result.data) == 1
    assert result.data[0]["script_pt_br"] == f"roteiro fake para {marker_url}"

    # Clean up: this table should only ever hold real pipeline output.
    store._client.table("content_records").delete().eq("video_url", marker_url).execute()
