from datetime import datetime, timezone
from typing import Callable, Sequence

from pipeline.interfaces import Collector, Notifier, ProcessingError, Processor, Store
from pipeline.models import ContentRecord, RunSummary

DEFAULT_MAX_ITEMS = 15


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
    for collector in collectors:
        for outcome in collector.collect():
            if outcome.error is not None:
                skipped += 1
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
    )
    notifier.notify(summary)
    return summary
