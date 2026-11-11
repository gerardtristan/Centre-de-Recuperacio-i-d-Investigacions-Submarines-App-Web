/* Còpia del carnet sense connexió (T-M01-21; decisió 081, punt 15). Quan la pàgina que es veu és
   la còpia (l'avís [data-sense-connexio] és visible), en tornar la connexió es comprova primer que
   el servidor respon i llavors es torna a carregar, per tenir el carnet actual.

   L'esdeveniment «online» pot arribar abans que la xarxa funcioni: si es recarregués de seguida,
   el service worker tornaria a donar la còpia i ja no hi hauria cap altre «online». Per això es
   prova amb una petició (que el service worker no respon: no és una navegació) i, si falla, es
   torna a provar més tard, un nombre limitat de vegades: cap bucle. Qualsevol resposta del
   servidor (també una redirecció a l'entrada) recarrega la pàgina. També es prova en carregar la
   còpia si el navegador ja diu que hi ha connexió (el servidor no responia).
   Fitxer propi, sense codi en línia (066). */
(function () {
  'use strict';
  var ESPERES = [1000, 2000, 4000, 8000, 15000, 30000];
  var provant = false;

  function prova(intent) {
    fetch(window.location.pathname, { cache: 'no-store', credentials: 'same-origin', redirect: 'manual' })
      .then(function () { window.location.reload(); })
      .catch(function () {
        if (intent + 1 < ESPERES.length) {
          window.setTimeout(function () { prova(intent + 1); }, ESPERES[intent + 1]);
        } else {
          provant = false;
        }
      });
  }

  function comenca() {
    if (provant) return;
    provant = true;
    window.setTimeout(function () { prova(0); }, ESPERES[0]);
  }

  function prepara() {
    var avis = document.querySelector('[data-sense-connexio]');
    if (!avis || avis.hidden) return;
    window.addEventListener('online', comenca);
    if (navigator.onLine) comenca();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', prepara);
  else prepara();
})();
