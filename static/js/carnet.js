/* El carnet en 3D (T-DX-61; design-system §6.21). Fitxer propi, sense codi en línia (066), sense
   xarxa. Sense JavaScript, les dues cares es veuen una sota l'altra.
   - Gir: el botó [data-carnet-gira] o un clic al carnet. La cara amagada, «aria-hidden» i «inert».
     Un clic durant el gir el desfà (és una transició de CSS, B9). Amb #qr, obre pel darrere.
   - Inclinació: només amb ratolí, sense moviment reduït, fins a 6 graus (--rx i --ry).
   - Pista: només la primera vegada; el navegador en recorda només un identificador (P-98). */
(function () {
  'use strict';
  var PISTA = 'cris-pista-carnet';
  var MAX_GRAUS = 6;

  function prepara() {
    var escena = document.querySelector('[data-carnet]');
    var boto = document.querySelector('[data-carnet-gira]');
    if (!escena || !boto) return;
    var interior = escena.querySelector('.carnet-interior');
    var davant = escena.querySelector('.carnet-davant');
    var darrere = escena.querySelector('.carnet-darrere');
    var pista = document.querySelector('[data-carnet-pista]');
    var ratoli = window.matchMedia('(hover: hover) and (pointer: fine)');
    var redueix = window.matchMedia('(prefers-reduced-motion: reduce)');
    var girantFins = 0;

    function amaga(cara, amagada) {
      cara.inert = amagada;
      if (amagada) cara.setAttribute('aria-hidden', 'true');
      else cara.removeAttribute('aria-hidden');
    }

    function mostra(girat) {
      escena.classList.toggle('es-girat', girat);
      boto.setAttribute('aria-pressed', String(girat));
      amaga(davant, girat);
      amaga(darrere, !girat);
    }

    function reposa() {
      escena.classList.remove('es-inclinant');
      interior.style.setProperty('--rx', '0deg');
      interior.style.setProperty('--ry', '0deg');
    }

    function gira() {
      // Mentre gira, la inclinació no escurça la transició.
      girantFins = performance.now() + (parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--m-gir')) || 0);
      reposa();
      mostra(!escena.classList.contains('es-girat'));
      if (pista) pista.hidden = true;
    }

    // La cara inicial (també el darrere, amb #qr) es posa sense gir: la transició, després.
    interior.style.setProperty('transition', 'none');
    escena.classList.add('es-3d');
    mostra(window.location.hash === '#qr');
    interior.getBoundingClientRect();
    interior.style.removeProperty('transition');
    boto.hidden = false;
    boto.addEventListener('click', gira);
    escena.addEventListener('click', gira);
    window.addEventListener('hashchange', function () {
      if (window.location.hash === '#qr' && !escena.classList.contains('es-girat')) gira();
    });

    escena.addEventListener('pointermove', function (e) {
      if (!ratoli.matches || redueix.matches || performance.now() < girantFins) return;
      var r = escena.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      var signe = escena.classList.contains('es-girat') ? -1 : 1;
      escena.classList.add('es-inclinant');
      interior.style.setProperty('--ry', (x * 2 * MAX_GRAUS * signe).toFixed(2) + 'deg');
      interior.style.setProperty('--rx', (-y * 2 * MAX_GRAUS).toFixed(2) + 'deg');
    });
    escena.addEventListener('pointerleave', reposa);

    // La pista, una sola vegada. Sense poder-ho recordar, no surt (no es repetiria a cada visita).
    if (pista && !escena.classList.contains('es-girat')) {
      try {
        if (!window.localStorage.getItem(PISTA)) {
          window.localStorage.setItem(PISTA, 'vista');
          pista.hidden = false;
        }
      } catch (error) { /* sense emmagatzematge: sense pista */ }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', prepara);
  else prepara();
})();
