/* Tema Sistema / Clar / Fosc (decisions 030, 031 i 066). Fitxer propi, sense codi en línia.
   Es carrega al <head> sense «defer» perquè el tema desat s'apliqui abans de pintar;
   el selector s'enllaça quan el document és llest. Mateixa clau que els prototips. */
(function () {
  'use strict';
  var arrel = document.documentElement;
  var CLAU = 'cris-tema';
  try {
    var desat = localStorage.getItem(CLAU);
    if (desat === 'light' || desat === 'dark') arrel.setAttribute('data-theme', desat);
  } catch (e) { /* sense localStorage: es queda el del sistema */ }

  function marca(t) {
    document.querySelectorAll('.selector-tema input').forEach(function (i) { i.checked = i.value === t; });
  }
  function aplica(t) {
    try {
      if (t === 'sistema') { arrel.removeAttribute('data-theme'); localStorage.removeItem(CLAU); }
      else { arrel.setAttribute('data-theme', t); localStorage.setItem(CLAU, t); }
    } catch (e) { if (t !== 'sistema') arrel.setAttribute('data-theme', t); }
    marca(t);
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.selector-tema input').forEach(function (i) {
      i.addEventListener('change', function () { if (i.checked) aplica(i.value); });
    });
    marca(arrel.getAttribute('data-theme') || 'sistema');
    // Sense JavaScript el selector no faria res: només es mostra quan funciona.
    document.querySelectorAll('.selector-tema[hidden]').forEach(function (s) { s.hidden = false; });
  });
})();
