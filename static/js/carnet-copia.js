/* Còpia del carnet sense connexió (T-M01-21; decisió 081, punt 15). Quan la pàgina que es veu és
   la còpia (l'avís [data-sense-connexio] és visible) i torna la connexió, es torna a carregar per
   tenir el carnet actual del servidor. Només amb l'esdeveniment «online», mai en carregar la
   pàgina: si el servidor no respon, el service worker torna a donar la còpia i no hi ha cap bucle.
   Fitxer propi, sense codi en línia (066). */
(function () {
  'use strict';
  function prepara() {
    var avis = document.querySelector('[data-sense-connexio]');
    if (!avis || avis.hidden) return;
    window.addEventListener('online', function () { window.location.reload(); }, { once: true });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', prepara);
  else prepara();
})();
