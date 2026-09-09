import os

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
