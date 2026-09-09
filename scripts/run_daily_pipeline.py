import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.collectors.tiktok import TikTokCollector
from pipeline.collectors.youtube import YouTubeCollector
from pipeline.notifiers.web_push_notifier import WebPushNotifier
from pipeline.orchestrator import run_daily_pipeline
from pipeline.processors.gemini_processor import GeminiProcessor
from pipeline.processors.tiktok_download_processor import TikTokDownloadingProcessor
from pipeline.stores.supabase_store import SupabaseStore

DEFAULT_MAX_ITEMS = 12  # within the 10-15/day target agreed for the MVP


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    collectors = [
        YouTubeCollector.from_env(),
        TikTokCollector(),
    ]
    processor = TikTokDownloadingProcessor(inner=GeminiProcessor.from_env())
    store = SupabaseStore.from_env()
    notifier = WebPushNotifier.from_env(supabase_client=store._client)
    max_items = int(os.environ.get("DAILY_PIPELINE_MAX_ITEMS", DEFAULT_MAX_ITEMS))

    summary = run_daily_pipeline(
        collectors, processor, store, notifier, max_items=max_items
    )

    logging.getLogger(__name__).info("Run summary: %s", summary)


if __name__ == "__main__":
    main()
