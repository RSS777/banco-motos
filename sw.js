const CACHE_NAME = "banco-motos-v2";
const SHELL = ["./", "./index.html", "./style.css", "./app.js", "./manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  // Never cache the data itself — the shell is offline-installable, but
  // the content list should always reflect the latest daily run.
  if (event.request.url.includes("/rest/v1/")) return;
  // Network-first for the shell: this project ships changes often and a
  // stale cached app.js silently shadowing new deploys is worse than the
  // occasional extra network round-trip. Cache is only the offline fallback.
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

self.addEventListener("push", (event) => {
  const text = event.data ? event.data.text() : "Rodada diária concluída.";
  event.waitUntil(
    self.registration.showNotification("banco-motos", {
      body: text,
      icon: "icons/icon-192.png",
    })
  );
});
