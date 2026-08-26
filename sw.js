const CACHE_NAME = 'auto-chah-cache-v1';
const urlsToCache = [
  '/auto-chah-/',
  '/auto-chah-/index.html'
];

// ئورنىتىش باسقۇچى
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

// قوزغىتىش ۋە كونا كىشلەرنى تازىلاش
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// تور ئۇلىنىشىنى بىر تەرەپ قىلىش
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request).catch(() => caches.match('/auto-chah-/index.html'));
    })
  );
});
