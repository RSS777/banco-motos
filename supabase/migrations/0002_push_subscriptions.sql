-- Web Push subscriptions (VAPID). The PWA (#11/#12) inserts its own
-- subscription directly from the browser using the anon key; the daily
-- pipeline (service key) reads all of them to send the end-of-run
-- notification and deletes ones that turn out to be expired/invalid.
create table if not exists push_subscriptions (
    id uuid primary key default gen_random_uuid(),
    endpoint text not null unique,
    p256dh text not null,
    auth text not null,
    created_at timestamptz not null default now()
);

alter table push_subscriptions enable row level security;

-- Anyone can subscribe (insert their own row); nobody but the service key
-- can read or delete — a subscription endpoint is bearer-token-like and
-- shouldn't be listable by other anonymous visitors.
create policy "anon can subscribe"
    on push_subscriptions
    for insert
    to anon
    with check (true);
