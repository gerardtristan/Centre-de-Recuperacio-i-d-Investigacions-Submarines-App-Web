/* Ramillete (T-DX-08): el botó central de la barra de l'àrea del soci obre i tanca el ventall.
   Focus atrapat dins del ventall, Esc i tocar fora el tanquen, i les fletxes recorren les
   opcions. Sense JavaScript, el botó no surt i les opcions rares són a la seva pàgina. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var nav = document.querySelector('[data-ramillete]');
    if (!nav) return;
    var boto = nav.querySelector('.ramillete-boto');
    var opcions = function () { return Array.prototype.slice.call(nav.querySelectorAll('.ramillete-item')); };
    boto.hidden = false;
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
    // Esc el tanca encara que el focus sigui fora del ventall.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('es-obert')) { e.preventDefault(); tanca(true); }
    });
    document.addEventListener('pointerdown', function (e) {
      if (nav.classList.contains('es-obert') && !e.target.closest('.ramillete-accio')) tanca(false);
    });
  });
})();
