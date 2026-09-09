const SUPABASE_URL = "https://lfnncwknrmtifezxiqnd.supabase.co";
// The legacy JWT anon key, not the newer sb_publishable_... key: the
// publishable key does not evaluate as Postgres role `anon` for RLS here
// (INSERT on push_subscriptions returned 42501 with it; the legacy key
// works for both the read-only content_records policy and this insert).
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxmbm5jd2tucm10aWZlenhpcW5kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5NTQ5ODgsImV4cCI6MjEwNDUzMDk4OH0.bd6lkh7T0QrG9fncpJbka0z4H--K9kogrf48cr7GFPs";

const PLATFORM_LABEL = { youtube: "YouTube", tiktok: "TikTok" };

const tileBank = document.getElementById("tile-bank");
const statusEl = document.getElementById("dash-status");
const readoutEl = document.getElementById("dash-readout");
const searchInput = document.getElementById("dash-search");
const chips = Array.from(document.querySelectorAll(".chip"));

let records = [];
let activePlatform = "all";

function timeAgo(iso) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diffMs / 86400000);
  if (days <= 0) return "hoje";
  if (days === 1) return "há 1 dia";
  return `há ${days} dias`;
}

function escapeHtml(str) {
  return (str || "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function renderTile(record) {
  const meta = record.metadata || {};
  const theme = meta.theme || "—";
  const hook = meta.hook || "";
  const format = meta.format || "—";
  const platform = record.platform;
  const platformLabel = PLATFORM_LABEL[platform] || platform;
  const platformGlyph = platformLabel.slice(0, 2).toUpperCase();

  const tile = document.createElement("article");
  tile.className = "tile";
  tile.dataset.platform = platform;
  tile.innerHTML = `
    <div class="tile-head">
      <span class="platform-light">${escapeHtml(platformLabel)}</span>
      <div class="tile-head-right">
        <time datetime="${record.collected_at}">${timeAgo(record.collected_at)}</time>
        <span class="state-light" title="pronto"></span>
      </div>
    </div>
    <div class="gauge-triad">
      <div class="gauge">
        <span class="label">Tema / gancho / formato</span>
        <span class="value">${escapeHtml(theme)}</span>
        ${hook ? `<span class="value sub">${escapeHtml(hook)} — ${escapeHtml(format)}</span>` : `<span class="value sub">${escapeHtml(format)}</span>`}
      </div>
      <div class="gauge">
        <span class="label">Vídeo-fonte</span>
        <div class="source-swatch">
          <span class="glyph">${escapeHtml(platformGlyph)}</span>
          <a class="source-link" href="${escapeHtml(record.video_url)}" target="_blank" rel="noopener">abrir vídeo →</a>
        </div>
      </div>
      <div class="gauge">
        <span class="label">Roteiro</span>
        <span class="value">${escapeHtml(record.script_pt_br)}</span>
      </div>
    </div>
    <button type="button" class="tile-expand-btn">ler roteiro completo</button>
    <div class="tile-script">${escapeHtml(record.script_pt_br)}</div>
  `;

  tile.querySelector(".tile-expand-btn").addEventListener("click", () => {
    const isOpen = tile.classList.toggle("is-open");
    tile.querySelector(".tile-expand-btn").textContent = isOpen
      ? "recolher"
      : "ler roteiro completo";
  });

  return tile;
}

function matchesQuery(record, query) {
  if (!query) return true;
  const meta = record.metadata || {};
  const haystack = [meta.theme, meta.hook, meta.format, record.script_pt_br, record.platform]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.toLowerCase());
}

function render() {
  const query = searchInput.value.trim();
  const visible = records.filter(
    (r) => (activePlatform === "all" || r.platform === activePlatform) && matchesQuery(r, query)
  );

  tileBank.innerHTML = "";
  if (visible.length === 0) {
    statusEl.hidden = false;
    statusEl.innerHTML = records.length === 0
      ? `Painel vazio. <span class="accent">Aguardando a próxima rodada.</span>`
      : `Nenhum item bate com esse filtro.`;
    return;
  }
  statusEl.hidden = true;
  visible.forEach((r) => tileBank.appendChild(renderTile(r)));
}

async function loadRecords() {
  statusEl.hidden = false;
  statusEl.textContent = "Carregando painel…";

  const url = `${SUPABASE_URL}/rest/v1/content_records?select=*&order=created_at.desc&limit=200`;
  const resp = await fetch(url, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
  });

  if (!resp.ok) {
    statusEl.textContent = "Falha ao carregar o painel. Recarregue a página.";
    return;
  }

  records = await resp.json();
  readoutEl.textContent = `${records.length} ITEM${records.length === 1 ? "" : "S"} · ${new Date().toLocaleDateString("pt-BR")}`;
  render();
}

const tripComputer = document.getElementById("trip-computer");
const tripToggle = document.getElementById("trip-toggle");
tripToggle.addEventListener("click", () => {
  const expanded = tripComputer.classList.toggle("is-expanded");
  tripToggle.setAttribute("aria-expanded", String(expanded));
  if (expanded) searchInput.focus();
});

searchInput.addEventListener("input", render);
chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((c) => c.setAttribute("aria-pressed", "false"));
    chip.setAttribute("aria-pressed", "true");
    activePlatform = chip.dataset.platform;
    render();
  });
});

const VAPID_PUBLIC_KEY =
  "BAgsKO6Dkl2d799sY9Y9i7J3kuk58GC7thLoCpIKdMF9HQTeS_JftcAKmc9Df6gJO21nG8OuMLQnpki-RRAbMUE";

function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

async function saveSubscription(subscription) {
  const json = subscription.toJSON();
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/push_subscriptions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Prefer: "resolution=ignore-duplicates",
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
    body: JSON.stringify({
      endpoint: json.endpoint,
      p256dh: json.keys.p256dh,
      auth: json.keys.auth,
    }),
  });
  if (!resp.ok) {
    throw new Error(`Supabase insert failed: ${resp.status} ${await resp.text()}`);
  }
}

async function setupPush(registration) {
  const pushToggle = document.getElementById("push-toggle");
  const supported = "PushManager" in window && "Notification" in window;
  if (!supported) return;

  pushToggle.hidden = false;

  const existing = await registration.pushManager.getSubscription();
  if (existing) {
    // Re-save on every load (idempotent via ignore-duplicates): keeps
    // Supabase in sync even if an earlier save failed after the browser
    // already held the subscription.
    saveSubscription(existing).catch(() => {});
    pushToggle.textContent = "notificações ativas";
    pushToggle.dataset.state = "active";
  } else if (Notification.permission === "denied") {
    pushToggle.textContent = "notificações bloqueadas";
    pushToggle.dataset.state = "denied";
  }

  pushToggle.addEventListener("click", async () => {
    if (pushToggle.dataset.state === "active" || pushToggle.dataset.state === "denied") return;

    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      pushToggle.textContent = "notificações bloqueadas";
      pushToggle.dataset.state = "denied";
      return;
    }

    try {
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      });
      await saveSubscription(subscription);
      pushToggle.textContent = "notificações ativas";
      pushToggle.dataset.state = "active";
    } catch {
      pushToggle.textContent = "falha ao ativar — tentar de novo";
    }
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker
    .register("sw.js")
    .then((registration) => setupPush(registration))
    .catch(() => {});
}

loadRecords();
