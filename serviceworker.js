var cacheName = 'pwa';
var filesToCache = [
];

self.addEventListener('install', function(e) {
  console.log('Install begins');
  e.waitUntil(
    caches.open(cacheName).then(function(cache) {
      console.log('Caching app shell');
      return cache.addAll(filesToCache);
    })
  );
});

self.addEventListener('activate',  event => {
    console.log('PWA activated');
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request, {ignoreSearch:true}).then(response => {
            return response || fetch(event.request);
        })
    );
});
