// Service Worker for aggressive avatar caching
const CACHE_NAME = 'agent-avatars-v2';
const FAL_MEDIA_PATTERN = /^https:\/\/v3\.fal\.media\/files\//;

// Install event - cache critical resources immediately
self.addEventListener('install', (event) => {
  self.skipWaiting();
  console.log('Service Worker: Installing and caching critical resources');
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      // Clear old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName.startsWith('agent-avatars-')) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
    ])
  );
});

self.addEventListener('fetch', (event) => {
  // Aggressively cache all fal.media avatar images
  if (FAL_MEDIA_PATTERN.test(event.request.url) && event.request.method === 'GET') {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            console.log('Service Worker: Serving from cache', event.request.url);
            return cachedResponse;
          }
          
          // Network first, then cache
          return fetch(event.request.clone()).then((response) => {
            // Cache successful responses immediately
            if (response.status === 200 && response.type === 'basic') {
              console.log('Service Worker: Caching new avatar', event.request.url);
              cache.put(event.request, response.clone());
            }
            return response;
          }).catch((error) => {
            console.log('Service Worker: Network failed, returning fallback avatar');
            // Return a default avatar SVG if network fails
            const size = event.request.url.includes('w=64') ? 64 : 48;
            const svg = `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="${size/2}" cy="${size/2}" r="${size/2}" fill="#E5E7EB"/>
              <circle cx="${size/2}" cy="${size/2*0.8}" r="${size/4}" fill="#9CA3AF"/>
              <path d="M${size*0.2} ${size*0.9}c0-${size*0.3} ${size*0.15}-${size*0.4} ${size*0.3}-${size*0.4}s${size*0.3} ${size*0.1} ${size*0.3} ${size*0.4}" fill="#9CA3AF"/>
            </svg>`;
            
            return new Response(svg, {
              headers: { 
                'Content-Type': 'image/svg+xml',
                'Cache-Control': 'no-cache'
              }
            });
          });
        });
      })
    );
  }
});

// Preload avatars when requested by the main app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'PRELOAD_AVATARS') {
    const avatarUrls = event.data.urls;
    console.log('Service Worker: Preloading', avatarUrls.length, 'avatars');
    
    caches.open(CACHE_NAME).then((cache) => {
      const preloadPromises = avatarUrls.map(url => {
        return fetch(url).then(response => {
          if (response.status === 200) {
            cache.put(url, response.clone());
            console.log('Service Worker: Preloaded avatar', url);
          }
          return response;
        }).catch(error => {
          console.warn('Service Worker: Failed to preload avatar', url, error);
        });
      });
      
      return Promise.all(preloadPromises);
    });
  }
});