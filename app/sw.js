const CACHE_NAME = 'truthlens-v1';
const SHARED_CACHE = 'truthlens-shared-v1';
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
  const url = new URL(event.request.url);

  // Handle Web Share Target POST to /verify by redirecting to main app with params and caching shared image
  if (url.pathname === '/verify' && event.request.method === 'POST') {
    event.respondWith((async () => {
      try {
        const formData = await event.request.formData();
        const text = formData.get('text') || formData.get('title') || formData.get('url') || '';
        const file = formData.get('image');

        let query = `?text=${encodeURIComponent(text || '')}`;

        if (file && typeof file === 'object' && 'size' in file && file.size > 0) {
          const id = `${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
          const path = `/shared/${id}`;
          const cache = await caches.open(SHARED_CACHE);
          const headers = { 'Content-Type': file.type || 'application/octet-stream', 'Cache-Control': 'no-store' };
          // Response can take a Blob/File directly
          await cache.put(path, new Response(file, { headers }));
          query += `&sharedImage=${encodeURIComponent(path)}`;
        }

        const redirectUrl = `/${query}`;
        return Response.redirect(redirectUrl, 303);
      } catch (e) {
        // Fallback to home
        return Response.redirect('/', 303);
      }
    })());
    return;
  }

  // Default: cache-first, then network
  event.respondWith(
    caches.match(event.request)
      .then((response) => response || fetch(event.request))
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
