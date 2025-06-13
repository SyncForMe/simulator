// Service Worker for caching agent avatars
const CACHE_NAME = 'agent-avatars-v1';
const FAL_MEDIA_PATTERN = /^https:\/\/v3\.fal\.media\/files\//;

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Only cache fal.media avatar images
  if (FAL_MEDIA_PATTERN.test(event.request.url) && event.request.method === 'GET') {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            // Return cached version immediately
            return cachedResponse;
          }
          
          // Fetch and cache
          return fetch(event.request).then((response) => {
            // Only cache successful responses
            if (response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          }).catch(() => {
            // Return a default avatar if network fails
            return new Response(
              `<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="24" cy="24" r="24" fill="#E5E7EB"/>
                <circle cx="24" cy="20" r="8" fill="#9CA3AF"/>
                <path d="M8 42c0-8.837 7.163-16 16-16s16 7.163 16 16" fill="#9CA3AF"/>
              </svg>`,
              { headers: { 'Content-Type': 'image/svg+xml' } }
            );
          });
        });
      })
    );
  }
});

// Clear old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('agent-avatars-')) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});