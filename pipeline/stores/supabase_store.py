import os
from datetime import datetime, timedelta, timezone

from supabase import Client, create_client

from pipeline.models import ContentRecord

TABLE_NAME = "content_records"


class SupabaseStore:
    """Store implementation backed by Supabase Postgres.

    Writes use the service/secret key so they bypass row-level security;
    the anon key (used by the PWA) only ever gets read access, per the
    "public read access" policy in supabase/migrations/0001_content_records.sql.
    """

    def __init__(self, client: Client):
        self._client = client

    @classmethod
    def from_env(cls) -> "SupabaseStore":
        url = os.environ["SUPABASE_URL"]
        service_key = os.environ["SUPABASE_SERVICE_KEY"]
        return cls(create_client(url, service_key))

    def save(self, record: ContentRecord) -> None:
        self._client.table(TABLE_NAME).insert(
            {
                "platform": record.platform,
                "video_url": record.video_url,
                "metadata": record.metadata,
                "script_pt_br": record.script_pt_br,
                "collected_at": record.collected_at,
            }
        ).execute()

    def exists(self, video_url: str) -> bool:
        result = (
            self._client.table(TABLE_NAME)
            .select("id", count="exact")
            .eq("video_url", video_url)
            .limit(1)
            .execute()
        )
        return (result.count or 0) > 0

    def recent_themes(self, days: int = 30, limit: int = 200) -> list[str]:
        """Theme + hook of recently stored records, for the processor to
        compare a new candidate's idea against before saving it.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self._client.table(TABLE_NAME)
            .select("metadata")
            .gte("collected_at", since)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        themes = []
        for row in result.data:
            meta = row.get("metadata") or {}
            theme = meta.get("theme")
            if theme:
                hook = meta.get("hook", "")
                themes.append(f"{theme} — {hook}" if hook else theme)
        return themes
