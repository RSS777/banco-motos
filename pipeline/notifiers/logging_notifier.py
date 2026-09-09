import logging

from pipeline.models import RunSummary

logger = logging.getLogger("pipeline.daily_run")


class LoggingNotifier:
    """Placeholder Notifier: logs the run summary. Real push notifications
    (#9/#10, Web Push/VAPID) replace this once built; the orchestrator's
    Notifier interface doesn't change either way.
    """

    def notify(self, summary: RunSummary) -> None:
        logger.info(
            "Daily pipeline run finished: %s candidates seen, %s processed, "
            "%s failed, %s skipped",
            summary.candidates_seen,
            summary.processed,
            summary.failed,
            summary.skipped,
        )
