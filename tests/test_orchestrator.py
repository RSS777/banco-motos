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


def test_url_already_in_store_is_skipped_before_processing():
    already_stored_url = "https://youtube.com/already-there"
    collector = FakeCollector(
        [
            CollectionOutcome(candidate=candidate(already_stored_url)),
            CollectionOutcome(candidate=candidate("https://youtube.com/new")),
        ]
    )
    processor = FakeProcessor()
    store = FakeStore(existing_urls={already_stored_url})
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert summary.duplicates == 1
    assert summary.processed == 1
    assert summary.candidates_seen == 1  # the duplicate never reaches the cap/processing count
    assert len(store.saved) == 1
    assert store.saved[0].video_url == "https://youtube.com/new"


def test_idea_flagged_as_duplicate_by_processor_is_not_saved():
    duplicate_url = "https://youtube.com/same-idea-different-video"
    collector = FakeCollector(
        [
            CollectionOutcome(candidate=candidate(duplicate_url)),
            CollectionOutcome(candidate=candidate("https://youtube.com/original")),
        ]
    )
    processor = FakeProcessor(duplicate_idea_urls={duplicate_url})
    store = FakeStore()
    notifier = FakeNotifier()

    summary = run_daily_pipeline([collector], processor, store, notifier)

    assert summary.duplicates == 1
    assert summary.processed == 1
    assert len(store.saved) == 1
    assert store.saved[0].video_url == "https://youtube.com/original"
