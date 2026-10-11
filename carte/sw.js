// Worker-ul cărții: o ține disponibilă fără internet (ultima versiune văzută) și deschide cartea când atingi o notificare de cronometru.
// Fișier static, nu e generat de build.py.
const CACHE = "carte-v3";
const FONTURI = /^https:\/\/fonts\.(googleapis|gstatic)\.com$/;
const ASTEPT_RETEAUA_MS = 3000;  // pe un Wi-Fi slab din bucătărie, după 3 secunde se deschide ce e salvat
// Încă de la prima vizită se salvează cartea, ca să meargă fără internet chiar dacă n-o mai deschizi online.
self.addEventListener("install", e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "index.html", "manifest.webmanifest", "icon.svg"])).catch(() => {})); });
// Versiunile vechi ale cache-ului se șterg.
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim())));
const pastreaza = (cerere, r) => { if (r.ok || r.type === "opaque") { const copie = r.clone(); caches.open(CACHE).then(c => c.put(cerere, copie)); } return r; };
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const origine = new URL(e.request.url).origin;
  // fonturile nu se schimbă: întâi din cache, ca să arate la fel și fără internet
  if (FONTURI.test(origine)) return e.respondWith(caches.match(e.request).then(c => c || fetch(e.request).then(r => pastreaza(e.request, r))));
  if (origine !== location.origin) return;
  // cartea și pozele: întâi rețeaua (ca să vezi rețetele noi); dacă nu răspunde în 3 secunde sau nu e internet, ce s-a salvat ultima dată
  const salvat = () => caches.match(e.request, {ignoreSearch: true});
  e.respondWith(new Promise(gata => {
    let raspuns = false;
    const da = r => { if (!raspuns && r) { raspuns = true; gata(r); } };
    const retea = fetch(e.request).then(r => pastreaza(e.request, r));
    setTimeout(() => salvat().then(da), ASTEPT_RETEAUA_MS);
    retea.then(da, () => salvat().then(r => { da(r); if (!raspuns) { raspuns = true; gata(Response.error()); } }));
  }));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true})
    .then(l => l.length ? l[0].focus() : self.clients.openWindow("./#gatit")));
});
