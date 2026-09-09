import logging
import os

from pywebpush import WebPushException, webpush
from supabase import Client

from pipeline.models import RunSummary

logger = logging.getLogger("pipeline.web_push")

TABLE_NAME = "push_subscriptions"
GONE_STATUS_CODES = {404, 410}  # subscription no longer valid on the push service


class WebPushNotifier:
    """Notifier: sends a native Web Push notification (VAPID, no third-party
    service) to every subscription stored in Supabase, summarizing the
    daily run. A subscription the push service reports as gone (404/410)
    is deleted so future runs stop trying it.
    """

    def __init__(self, client: Client, vapid_private_key: str, vapid_subject: str):
        self._client = client
        self._vapid_private_key = vapid_private_key
        self._vapid_claims = {"sub": vapid_subject}

    @classmethod
    def from_env(cls, supabase_client: Client) -> "WebPushNotifier":
        return cls(
            client=supabase_client,
            vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
            vapid_subject=os.environ["VAPID_SUBJECT"],
        )

    def notify(self, summary: RunSummary) -> None:
        subscriptions = self._client.table(TABLE_NAME).select("*").execute().data
        message = (
            f"Rodada diária: {summary.processed} vídeo(s) processado(s), "
            f"{summary.failed} falha(s), {summary.skipped} pulado(s)."
        )

        for sub in subscriptions:
            self._send_one(sub, message)

    def _send_one(self, sub: dict, message: str) -> None:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=message,
                vapid_private_key=self._vapid_private_key,
                vapid_claims=dict(self._vapid_claims),
            )
        except WebPushException as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in GONE_STATUS_CODES:
                logger.info("Push subscription gone, removing: %s", sub["endpoint"])
                self._client.table(TABLE_NAME).delete().eq("id", sub["id"]).execute()
            else:
                logger.warning("Push send failed for %s: %s", sub["endpoint"], exc)
