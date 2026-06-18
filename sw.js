// Service Worker pro A-GROSS SOS
// Umožňuje offline režim a caching

const CACHE_VERSION = 'agross-v1';
const CACHE_FILES = [
  '/',
  '/A_GROSS_SOS.html',
  '/A_GROSS_SOS_VI.html',
  '/index.html',
  '/manifest.json',
  '/icon.svg',
  'https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap',
];

// Install: cache files
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_VERSION).then(cache => {
      console.log('[SW] Caching files');
      return cache.addAll(CACHE_FILES).catch(err => {
        console.log('[SW] Some files not available (ok for PWA):', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_VERSION) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: try network first, fallback to cache
self.addEventListener('fetch', event => {
  const {request} = event;
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // For HTML/CSS/JS, use network-first
  // For images/fonts, use cache-first
  const url = new URL(request.url);
  const isNavigate = request.mode === 'navigate';
  const isHTML = request.headers.get('accept')?.includes('text/html');
  const isResource = /\.(js|css|json|woff|woff2|ttf|eot|svg)$/.test(url.pathname);
  
  if (isNavigate || isHTML) {
    // Network-first for navigation/HTML
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful responses
          if (response.ok) {
            const cloned = response.clone();
            caches.open(CACHE_VERSION).then(cache => {
              cache.put(request, cloned);
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache
          return caches.match(request).then(cachedResponse => {
            return cachedResponse || new Response('Offline - stránka není k dispozici', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({'Content-Type': 'text/html'})
            });
          });
        })
    );
  } else if (isResource) {
    // Cache-first for resources
    event.respondWith(
      caches.match(request)
        .then(cachedResponse => {
          if (cachedResponse) return cachedResponse;
          
          return fetch(request)
            .then(response => {
              if (!response || response.status !== 200 || response.type === 'error') {
                return response;
              }
              const cloned = response.clone();
              caches.open(CACHE_VERSION).then(cache => {
                cache.put(request, cloned);
              });
              return response;
            })
            .catch(() => {
              console.log('[SW] Resource not available:', request.url);
              return new Response('Resource not available', {status: 404});
            });
        })
    );
  } else {
    // Default: network with fallback
    event.respondWith(
      fetch(request)
        .then(response => {
          if (response.ok) {
            const cloned = response.clone();
            caches.open(CACHE_VERSION).then(cache => {
              cache.put(request, cloned);
            });
          }
          return response;
        })
        .catch(() => caches.match(request))
    );
  }
});

// Background sync (když se vrátí online)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-orders') {
    console.log('[SW] Background sync triggered');
    event.waitUntil(syncOfflineOrders());
  }
});

async function syncOfflineOrders() {
  try {
    // Otevřít IndexedDB a synchronizovat všechny offline objednávky
    const db = await openDB();
    const orders = await getAllOrdersFromDB(db);
    
    for (const order of orders) {
      if (!order.synced) {
        // Poslat na server
        const response = await fetch('/api/orders/sync', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(order)
        });
        
        if (response.ok) {
          // Označit jako synchronizovanou
          await markOrderSynced(db, order.id);
        }
      }
    }
    
    console.log('[SW] Sync complete');
  } catch (error) {
    console.error('[SW] Sync failed:', error);
    throw error; // Retry
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('AGrossSOS', 1);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllOrdersFromDB(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('orders', 'readonly');
    const store = tx.objectStore('orders');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function markOrderSynced(db, orderId) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('orders', 'readwrite');
    const store = tx.objectStore('orders');
    const req = store.get(orderId);
    req.onsuccess = () => {
      const order = req.result;
      order.synced = true;
      const updateReq = store.put(order);
      updateReq.onsuccess = resolve;
      updateReq.onerror = () => reject(updateReq.error);
    };
    req.onerror = () => reject(req.error);
  });
}
