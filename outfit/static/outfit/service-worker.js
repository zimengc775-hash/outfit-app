// Service Worker — 缓存静态资源，离线也能看到界面
var CACHE_NAME = 'outfit-cache-v1';

// 要缓存的文件列表
var urlsToCache = [
    '/',
    '/static/outfit/manifest.json',
];

// 安装阶段：预缓存关键资源
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(urlsToCache);
        })
    );
});

// 拦截请求：缓存优先，没网时用缓存兜底
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            // 缓存有就用缓存，没有就走网络
            return response || fetch(event.request);
        })
    );
});

// 激活阶段：清理旧缓存
self.addEventListener('activate', function(event) {
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.filter(function(name) {
                    return name !== CACHE_NAME;
                }).map(function(name) {
                    return caches.delete(name);
                })
            );
        })
    );
});
