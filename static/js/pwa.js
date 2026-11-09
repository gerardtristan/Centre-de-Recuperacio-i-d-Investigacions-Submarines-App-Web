/* Web instal·lable (T-M01-21; decisió 041): registra el service worker. Fitxer propi, sense
   codi en línia (066). La ruta ve de la plantilla base (data-service-worker). Sense suport
   o amb un error, el lloc funciona igual, només sense el carnet sense connexió. */
(function () {
  'use strict';
  var script = document.currentScript;
  if (!script || !('serviceWorker' in navigator)) return;
  var ruta = script.getAttribute('data-service-worker');
  window.addEventListener('load', function () {
    navigator.serviceWorker.register(ruta).catch(function () { /* sense carnet sense connexió */ });
  });
})();
