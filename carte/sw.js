// Worker-ul cărții: o ține disponibilă fără internet (ultima versiune văzută) și deschide cartea când atingi o notificare de cronometru.
// Fișier static, nu e generat de build.py.
const CACHE = "carte-v1";
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  // întâi rețeaua (ca să vezi rețetele noi), iar fără internet ce s-a salvat ultima dată
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const copie = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copie)); }
    return r;
  }).catch(() => caches.match(e.request, {ignoreSearch: true})));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true})
    .then(l => l.length ? l[0].focus() : self.clients.openWindow("./#gatit")));
});
