// install app

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("rn360-cache").then(cache => {
      return cache.addAll([
        "/",
        "/static/css/bootstrap.min.css",
        "/static/js/bootstrap.bundle.min.js",
        "/static/img/default.jpeg"
      ]);
    })
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
