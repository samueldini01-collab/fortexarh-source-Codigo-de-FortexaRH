// FortexaRH Service Worker - PWA Support
const CACHE_NAME = 'fortexarh-v2';
const STATIC_CACHE = 'fortexarh-static-v2';
const DYNAMIC_CACHE = 'fortexarh-dynamic-v2';

// Assets to cache immediately on install
const STATIC_ASSETS = [
  '/manifest.json',
  '/fortexarh-favicon.png',
  '/fortexarh-icon-128.png',
  '/fortexarh-logo-200.png',
  '/fortexarh-logo-300.png',
  '/fortexarh-logo-full.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker v2...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
      .catch((err) => console.log('[SW] Cache error:', err))
  );
});

// Activate event - clean up ALL old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker v2...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - NETWORK-FIRST for navigation, cache-first for static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip API calls - always go to network
  if (url.pathname.startsWith('/api')) return;

  // Skip external requests
  if (url.origin !== location.origin) return;

  // NETWORK-FIRST for navigation requests (HTML pages)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse.ok) {
            const responseToCache = networkResponse.clone();
            caches.open(DYNAMIC_CACHE)
              .then((cache) => cache.put(request, responseToCache));
          }
          return networkResponse;
        })
        .catch(() => {
          return caches.match(request)
            .then((cachedResponse) => cachedResponse || caches.match('/offline.html'))
            .catch(() => new Response('Offline', { status: 503 }));
        })
    );
    return;
  }

  // CACHE-FIRST for static assets (images, fonts, etc.)
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          event.waitUntil(updateCache(request));
          return cachedResponse;
        }
        return fetch(request)
          .then((networkResponse) => {
            if (networkResponse.ok) {
              const responseToCache = networkResponse.clone();
              caches.open(DYNAMIC_CACHE)
                .then((cache) => cache.put(request, responseToCache));
            }
            return networkResponse;
          })
          .catch(() => new Response('Offline', { status: 503 }));
      })
  );
});

// Update cache in background
async function updateCache(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      await cache.put(request, response);
    }
  } catch (error) {
    // Network error - ignore
  }
}

// Listen for messages from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(cacheNames.map((name) => caches.delete(name)));
    });
  }
});

// Push notifications support
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body || 'Nueva notificacion de FortexaRH',
    icon: '/fortexarh-logo-200.png',
    badge: '/fortexarh-icon-128.png',
    vibrate: [100, 50, 100],
    data: { url: data.url || '/' },
    actions: [
      { action: 'open', title: 'Abrir' },
      { action: 'close', title: 'Cerrar' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'FortexaRH', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'close') return;

  const urlToOpen = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        for (const client of clientList) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.navigate(urlToOpen);
            return client.focus();
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});
