self.addEventListener('install', e => e.waitUntil(caches.open('admin-v1').then(c => c.addAll(['/agross-sos/AGROSS_SOS_ADMIN.html']))));
self.addEventListener('fetch', e => e.respondWith(fetch(e.request).catch(() => caches.match(e.request))));
