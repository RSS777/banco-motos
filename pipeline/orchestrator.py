import logging
from datetime import datetime, timezone
from typing import Callable, Sequence

from pipeline.interfaces import Collector, Notifier, ProcessingError, Processor, Store
from pipeline.models import ContentRecord, RunSummary

DEFAULT_MAX_ITEMS = 15

logger = logging.getLogger("pipeline.orchestrator")


def run_daily_pipeline(
    collectors: Sequence[Collector],
    processor: Processor,
    store: Store,
    notifier: Notifier,
    max_items: int = DEFAULT_MAX_ITEMS,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> RunSummary:
    candidates = []
    skipped = 0
    duplicates = 0
    for collector in collectors:
        for outcome in collector.collect():
            if outcome.error is not None:
                skipped += 1
                logger.warning("Collection error: %s", outcome.error)
                continue
            # Same video URL already stored: skip before it ever reaches the
            # processor, so a repeat costs nothing (no Gemini call) and
            # doesn't eat into the volume cap below. A transient store
            # failure here (e.g. a Supabase gateway timeout) must not crash
            # the whole round — worst case we reprocess a duplicate, which
            # is far cheaper than losing every other candidate in the batch.
            try:
                is_duplicate_url = store.exists(outcome.candidate.url)
            except Exception as exc:  # noqa: BLE001 - any store failure degrades, never crashes
                logger.warning(
                    "store.exists() failed for %s, proceeding as new: %s",
                    outcome.candidate.url,
                    exc,
                )
                is_duplicate_url = False
            if is_duplicate_url:
                duplicates += 1
                continue
            candidates.append(outcome.candidate)

    candidates = candidates[:max_items]

    processed = 0
    failed = 0
    for candidate in candidates:
        try:
            result = processor.process(candidate)
        except ProcessingError as exc:
            failed += 1
            logger.warning("Processing error for %s: %s", candidate.url, exc)
            continue

        # Different video, but the processor judged the idea itself a
        # near-duplicate of something already stored (see GeminiProcessor's
        # recent_themes comparison) — don't save it either.
        if result.is_duplicate:
            duplicates += 1
            continue

        record = ContentRecord(
            platform=candidate.platform,
            video_url=candidate.url,
            metadata={
                "theme": result.theme,
                "hook": result.hook,
                "format": result.format,
                **candidate.raw_metadata,
            },
            script_pt_br=result.script_pt_br,
            collected_at=now().isoformat(),
        )
        try:
            store.save(record)
        except Exception as exc:  # noqa: BLE001 - a save failure shouldn't end the whole round
            failed += 1
            logger.warning("store.save() failed for %s: %s", candidate.url, exc)
            continue
        processed += 1

    summary = RunSummary(
        candidates_seen=len(candidates),
        processed=processed,
        failed=failed,
        skipped=skipped,
        duplicates=duplicates,
    )
    notifier.notify(summary)
    return summary
