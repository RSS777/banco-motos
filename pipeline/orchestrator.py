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
            # doesn't eat into the volume cap below.
            if store.exists(outcome.candidate.url):
                duplicates += 1
                continue
            candidates.append(outcome.candidate)

    candidates = candidates[:max_items]

    processed = 0
    failed = 0
    for candidate in candidates:
        try:
            result = processor.process(candidate)
        except ProcessingError:
            failed += 1
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
        store.save(record)
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
