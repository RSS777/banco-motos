-- Content records: one row per video collected + analyzed by the daily pipeline.
-- Never stores the video file itself, only the permanent source link.
create table if not exists content_records (
    id uuid primary key default gen_random_uuid(),
    platform text not null,
    video_url text not null,
    metadata jsonb not null default '{}'::jsonb,
    script_pt_br text not null,
    collected_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);

create index if not exists content_records_collected_at_idx
    on content_records (collected_at desc);

create index if not exists content_records_platform_idx
    on content_records (platform);

-- PWA has no login: anon key gets read-only access.
-- Writes come only from the GitHub Actions pipeline using the service/secret key,
-- which bypasses RLS by design (Supabase service_role always bypasses RLS).
alter table content_records enable row level security;

create policy "public read access"
    on content_records
    for select
    to anon
    using (true);
