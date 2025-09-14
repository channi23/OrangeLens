const CACHE_NAME = 'truthlens-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Activate event - clean up old caches
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
});

// Background sync for offline verification requests
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-verify') {
    event.waitUntil(doBackgroundVerification());
  }
});

async function doBackgroundVerification() {
  // Handle offline verification requests when back online
  const offlineRequests = await getOfflineRequests();
  for (const request of offlineRequests) {
    try {
      await fetch('/api/v1/verify', {
        method: 'POST',
        body: request.data
      });
      await removeOfflineRequest(request.id);
    } catch (error) {
      console.error('Background sync failed:', error);
    }
  }
}
