from pipeline.models import CollectionOutcome
from pipeline.orchestrator import run_daily_pipeline
from tests.fakes import FakeCollector, FakeNotifier, FakeProcessor, FakeStore, candidate


def test_happy_path_processes_saves_and_notifies_once():
    collector = FakeCollector(
        [
            CollectionOutcome(candidate=candidate("https://youtube.com/1")),
            CollectionOutcome(candidate=candidate("https://youtube.com/2")),
        ]
    )
    processor = FakeProcessor()
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert len(store.saved) == 2
    assert summary.processed == 2
    assert summary.failed == 0
    assert summary.skipped == 0
    assert len(notifier.notifications) == 1
    assert notifier.notifications[0] == summary


def test_blocked_candidate_is_skipped_and_round_continues():
    collector = FakeCollector(
        [
            CollectionOutcome(error="captcha bloqueado"),
            CollectionOutcome(candidate=candidate("https://tiktok.com/1", platform="tiktok")),
        ]
    )
    processor = FakeProcessor()
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert len(store.saved) == 1
    assert store.saved[0].video_url == "https://tiktok.com/1"
    assert summary.skipped == 1
    assert summary.processed == 1


def test_processing_failure_creates_no_partial_record_and_round_continues():
    ok_url = "https://youtube.com/ok"
    bad_url = "https://youtube.com/bad"
    collector = FakeCollector(
        [
            CollectionOutcome(candidate=candidate(bad_url)),
            CollectionOutcome(candidate=candidate(ok_url)),
        ]
    )
    processor = FakeProcessor(failing_urls={bad_url})
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert len(store.saved) == 1
    assert store.saved[0].video_url == ok_url
    assert summary.failed == 1
    assert summary.processed == 1


def test_empty_round_still_notifies():
    collector = FakeCollector([])
    processor = FakeProcessor()
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert summary.candidates_seen == 0
    assert summary.processed == 0
    assert len(store.saved) == 0
    assert len(notifier.notifications) == 1


def test_volume_cap_is_respected_across_collectors():
    youtube = FakeCollector(
        [CollectionOutcome(candidate=candidate(f"https://youtube.com/{i}")) for i in range(10)]
    )
    tiktok = FakeCollector(
        [
            CollectionOutcome(candidate=candidate(f"https://tiktok.com/{i}", platform="tiktok"))
            for i in range(10)
        ]
    )
    processor = FakeProcessor()
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([youtube, tiktok], processor, store, notifier, max_items=12)

    assert summary.candidates_seen == 12
    assert summary.processed == 12
    assert len(store.saved) == 12
