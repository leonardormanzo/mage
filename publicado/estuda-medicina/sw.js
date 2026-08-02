// Service worker mínimo do Estuda Medicina.
//
// Existe só para habilitar `registration.showNotification()` — no Chrome
// Android (e outros navegadores móveis), notificações disparadas via
// `new Notification()` sem um service worker registrado costumam falhar
// silenciosamente. Não faz cache, não intercepta requisições (sem
// `fetch` handler) e não funciona offline — é puramente um requisito
// técnico para a notificação real do cronograma de estudos.

self.addEventListener("install", function (event) {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});
