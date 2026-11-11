/* Menú de l'administració en pantalles estretes (T-M01-46; sistema de disseny §6.1). Fitxer
   propi, sense codi en línia (066) ni cap petició. Millora progressiva: sense JavaScript, la
   barra lateral es veu sempre. Amb JavaScript, per sota de 1024 px queda plegada i el botó
   «Menú» l'obre i la tanca (aria-expanded); Esc la tanca i torna el focus al botó. A partir de
   1024 px el full d'estils la mostra sempre i amaga el botó.
   Es carrega al <head> sense «defer» perquè la barra no es vegi oberta un instant. No decideix
   què hi surt: les entrades les posa el servidor segons els permisos del compte. */
(function () {
  'use strict';
  var arrel = document.documentElement;
  arrel.classList.add('menu-plegable');

  document.addEventListener('DOMContentLoaded', function () {
    var boto = document.querySelector('.boto-menu');
    var barra = document.getElementById('barra-lateral');
    if (!boto || !barra) { arrel.classList.remove('menu-plegable'); return; }

    function posa(oberta) {
      barra.classList.toggle('oberta', oberta);
      boto.setAttribute('aria-expanded', oberta ? 'true' : 'false');
    }
    boto.hidden = false;
    boto.addEventListener('click', function () {
      posa(boto.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && boto.getAttribute('aria-expanded') === 'true') {
        posa(false);
        boto.focus();
      }
    });
  });
})();
