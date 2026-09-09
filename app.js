const SUPABASE_URL = "https://lfnncwknrmtifezxiqnd.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_-FltxZra7lwIbk1OpsAJrg_EK1mDxXv";

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

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

loadRecords();
