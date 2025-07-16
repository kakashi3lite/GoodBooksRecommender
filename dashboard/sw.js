// GoodBooks Recommender Dashboard - Service Worker
// Provides offline functionality and caching

const CACHE_NAME = 'goodbooks-dashboard-v1';
const CACHE_URLS = [
  '/',
  '/index.html',
  '/css/dashboard.css',
  '/css/components.css',
  '/css/responsive.css',
  '/js/utils.js',
  '/js/api.js',
  '/js/components.js',
  '/js/charts.js',
  '/js/app.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.js'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(CACHE_URLS);
      })
      .then(() => {
        console.log('[SW] Service worker installed successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Failed to cache app shell:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request)
          .then((fetchResponse) => {
            // Don't cache API responses or external resources
            if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type !== 'basic') {
              return fetchResponse;
            }

            // Cache successful responses for static assets
            const responseToCache = fetchResponse.clone();
            const url = new URL(event.request.url);
            
            // Only cache our own assets
            if (url.origin === location.origin && 
                (url.pathname.endsWith('.css') || 
                 url.pathname.endsWith('.js') || 
                 url.pathname.endsWith('.html'))) {
              
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseToCache);
                });
            }

            return fetchResponse;
          })
          .catch(() => {
            // If both cache and network fail, return offline page for HTML requests
            if (event.request.destination === 'document') {
              return caches.match('/offline.html');
            }
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('[SW] Background sync triggered');
    
    event.waitUntil(
      // Handle offline actions here
      syncOfflineActions()
    );
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body,
      icon: '/assets/icon-192.png',
      badge: '/assets/badge-72.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: data.primaryKey
      },
      actions: [
        {
          action: 'explore',
          title: 'Explore',
          icon: '/assets/checkmark.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/assets/xmark.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification click received.');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Helper function to sync offline actions
async function syncOfflineActions() {
  try {
    // Get offline actions from IndexedDB or localStorage
    const offlineActions = await getOfflineActions();
    
    for (const action of offlineActions) {
      try {
        // Attempt to sync each action
        await syncAction(action);
        
        // Remove successfully synced action
        await removeOfflineAction(action.id);
        
      } catch (error) {
        console.error('[SW] Failed to sync action:', error);
      }
    }
    
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// Placeholder functions for offline functionality
async function getOfflineActions() {
  // In a real implementation, this would read from IndexedDB
  return [];
}

async function syncAction(action) {
  // In a real implementation, this would replay the action
  return Promise.resolve();
}

async function removeOfflineAction(actionId) {
  // In a real implementation, this would remove from IndexedDB
  return Promise.resolve();
}

// Message handling from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('[SW] Service worker script loaded');
