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
    // Carril de la tauleta (T-DX-62): tocar la icona d'un grup n'obre les entrades al costat, d'un en
    // un; Esc, tocar fora o triar una altra icona el tanca. Fora del carril, els grups són <details>.
    var carril = window.matchMedia('(min-width: 600px) and (max-width: 1023.98px)');
    function enCarril() { return carril.matches && !barra.classList.contains('oberta'); }
    function tancaGrups(excepte) {
      barra.querySelectorAll('.lateral-grup.desplegat').forEach(function (grup) {
        if (grup !== excepte) {
          grup.classList.remove('desplegat');
          grup.querySelector('summary').setAttribute('aria-expanded', 'false');
        }
      });
    }
    barra.querySelectorAll('.lateral-grup summary').forEach(function (resum) {
      resum.addEventListener('click', function (event) {
        if (!enCarril()) return;
        event.preventDefault();
        var grup = resum.closest('.lateral-grup');
        var obre = !grup.classList.contains('desplegat');
        tancaGrups(grup);
        grup.classList.toggle('desplegat', obre);
        resum.setAttribute('aria-expanded', obre ? 'true' : 'false');
        if (obre) {
          grup.querySelector('details').open = true;
          var primer = grup.querySelector('details > ul a');
          if (primer) primer.focus();
        }
      });
    });
    document.addEventListener('pointerdown', function (event) {
      if (!event.target.closest('.lateral-grup')) tancaGrups(null);
    });
    document.addEventListener('keydown', function (event) {
      var obert = barra.querySelector('.lateral-grup.desplegat');
      if (event.key === 'Escape' && obert) {
        tancaGrups(null);
        obert.querySelector('summary').focus();
        return;
      }
      if (event.key === 'Escape' && boto.getAttribute('aria-expanded') === 'true') {
        posa(false);
        boto.focus();
      }
    });
  });
})();
