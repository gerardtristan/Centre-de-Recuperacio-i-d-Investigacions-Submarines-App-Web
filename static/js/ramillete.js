/* Ramillete (T-DX-08 i T-DX-59): la navegació de l'àrea del soci.
   - Barra (fins a 1023 px): el botó central obre i tanca el ventall. Focus atrapat dins del ventall,
     Esc i tocar fora el tanquen, i les fletxes recorren les opcions.
   - Panell (a partir de 1024 px): els botons amb `data-desplega` obren i tanquen la llista que
     controlen (la fletxa de «Mostra el QR» i «Més»). Esc la tanca i torna el focus al botó; el menú
     flotant (`data-desplega="flotant"`) porta el focus a la primera opció, les fletxes el recorren i
     tocar fora el tanca.
   Sense JavaScript no surt res d'això: hi ha la navegació de la capçalera i els enllaços de sempre. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var nav = document.querySelector('[data-ramillete]');
    if (!nav) return;
    var boto = nav.querySelector('.ramillete-boto');
    var opcions = function () { return Array.prototype.slice.call(nav.querySelectorAll('.ramillete-item')); };
    document.documentElement.classList.add('ramillete-actiu');

    function obre() {
      nav.classList.add('es-obert');
      boto.setAttribute('aria-expanded', 'true');
      var primera = opcions()[0];
      if (primera) primera.focus();
    }
    function tanca(tornaAlBoto) {
      nav.classList.remove('es-obert');
      boto.setAttribute('aria-expanded', 'false');
      if (tornaAlBoto) boto.focus();
    }
    boto.addEventListener('click', function () {
      if (nav.classList.contains('es-obert')) tanca(true); else obre();
    });
    nav.addEventListener('keydown', function (e) {
      if (!nav.classList.contains('es-obert')) return;
      var llista = opcions().concat(boto);
      var i = llista.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        llista[(i + (e.key === 'ArrowDown' ? 1 : llista.length - 1)) % llista.length].focus();
      }
      if (e.key === 'Tab') {  // focus atrapat: del botó a la primera opció i de l'última al botó
        e.preventDefault();
        llista[(i + (e.shiftKey ? llista.length - 1 : 1)) % llista.length].focus();
      }
    });

    // Panell: els desplegables.
    var desplegables = Array.prototype.slice.call(nav.querySelectorAll('[data-desplega]'));
    function llistaDe(b) { return document.getElementById(b.getAttribute('aria-controls')); }
    function enllacos(b) { return Array.prototype.slice.call(llistaDe(b).querySelectorAll('a')); }
    function obert(b) { return b.getAttribute('aria-expanded') === 'true'; }
    function posa(b, obrir) {
      b.setAttribute('aria-expanded', obrir ? 'true' : 'false');
      llistaDe(b).hidden = !obrir;
      if (obrir && b.dataset.desplega === 'flotant') enllacos(b)[0].focus();
    }
    desplegables.forEach(function (b) {
      b.addEventListener('click', function () { posa(b, !obert(b)); });
      if (b.dataset.desplega !== 'flotant') return;
      // El menú flotant es tanca quan el focus en surt (Tab), perquè no tapi les entrades.
      b.parentNode.addEventListener('focusout', function (e) {
        if (obert(b) && !b.parentNode.contains(e.relatedTarget)) posa(b, false);
      });
      llistaDe(b).addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
        e.preventDefault();
        var llista = enllacos(b);
        var i = llista.indexOf(document.activeElement);
        llista[(i + (e.key === 'ArrowDown' ? 1 : llista.length - 1)) % llista.length].focus();
      });
    });

    // Esc tanca el ventall encara que el focus sigui fora, o el desplegable on és el focus.
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape') return;
      if (nav.classList.contains('es-obert')) { e.preventDefault(); tanca(true); return; }
      desplegables.forEach(function (b) {
        if (obert(b) && (b === document.activeElement || llistaDe(b).contains(document.activeElement))) {
          e.preventDefault();
          posa(b, false);
          b.focus();
        }
      });
    });
    document.addEventListener('pointerdown', function (e) {
      if (nav.classList.contains('es-obert') && !e.target.closest('.ramillete-accio')) tanca(false);
      desplegables.forEach(function (b) {
        if (b.dataset.desplega === 'flotant' && obert(b) && !b.parentNode.contains(e.target)) posa(b, false);
      });
    });
  });
})();
