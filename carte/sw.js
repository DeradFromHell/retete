// Worker-ul cărții: o ține disponibilă fără internet (ultima versiune văzută) și deschide cartea când atingi o notificare de cronometru.
// Fișier static, nu e generat de build.py.
const CACHE = "carte-v2";
const FONTURI = /^https:\/\/fonts\.(googleapis|gstatic)\.com$/;
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
const pastreaza = (cerere, r) => { if (r.ok || r.type === "opaque") { const copie = r.clone(); caches.open(CACHE).then(c => c.put(cerere, copie)); } return r; };
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const origine = new URL(e.request.url).origin;
  // fonturile nu se schimbă: întâi din cache, ca să arate la fel și fără internet
  if (FONTURI.test(origine)) return e.respondWith(caches.match(e.request).then(c => c || fetch(e.request).then(r => pastreaza(e.request, r))));
  if (origine !== location.origin) return;
  // cartea și pozele: întâi rețeaua (ca să vezi rețetele noi), iar fără internet ce s-a salvat ultima dată
  e.respondWith(fetch(e.request).then(r => pastreaza(e.request, r)).catch(() => caches.match(e.request, {ignoreSearch: true})));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true})
    .then(l => l.length ? l[0].focus() : self.clients.openWindow("./#gatit")));
});
