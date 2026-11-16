/* Duermevela: motor de tema Sistema / Clar / Fosc (T-DX-04; recurs a design/extern/; abans,
   decisions 030, 031 i 066). Fitxer propi, sense codi en línia.
   - Es carrega al <head> sense «defer»: el tema desat s'aplica abans de pintar (cap destell).
   - La mateixa tria a totes les pestanyes obertes (esdeveniment «storage»).
   - La barra del navegador (<meta name="theme-color">) pren el color de fons del tema actiu,
     també quan el sistema canvia de tema amb «Sistema».
   - El canvi es revela amb una cortina circular que surt del control (View Transitions), de
     --m-panell i amb --m-corba-entra-surt. Amb moviment reduït o sense l'API, canvi directe.
   El color dels controls natius (color-scheme) el posa tokens.css segons el tema.
   Clau i valors com abans: «cris-tema» = light | dark; amb «Sistema», sense clau. */
(function () {
  'use strict';
  var arrel = document.documentElement;
  var CLAU = 'cris-tema';
  var menysMoviment = window.matchMedia('(prefers-reduced-motion: reduce)');

  function llegeix() {
    try {
      var v = localStorage.getItem(CLAU);
      return v === 'light' || v === 'dark' ? v : 'sistema';
    } catch (e) { return 'sistema'; }  // sense localStorage: el del sistema
  }
  function posa(t) {
    if (t === 'sistema') arrel.removeAttribute('data-theme');
    else arrel.setAttribute('data-theme', t);
  }
  var actual = llegeix();
  posa(actual);

  function token(nom) { return getComputedStyle(arrel).getPropertyValue(nom).trim(); }
  function barra() {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'theme-color');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', token('--c-fons'));
    // Avisa els controls (Eclipse) que el tema que es veu pot haver canviat.
    document.dispatchEvent(new CustomEvent('cris:tema'));
  }
  function marca(t) {
    document.querySelectorAll('.selector-tema input').forEach(function (i) { i.checked = i.value === t; });
  }
  function desa(t) {
    try {
      if (t === 'sistema') localStorage.removeItem(CLAU);
      else localStorage.setItem(CLAU, t);
    } catch (e) { /* mode privat: la tria val mentre la pàgina és oberta */ }
  }

  /* La cortina: el tema nou creix en cercle des del control triat. */
  function cortina(origen, canvia) {
    var ms = parseFloat(token('--m-panell')) || 0;
    if (menysMoviment.matches || !ms || !document.startViewTransition || document.hidden || !origen) {
      canvia();
      return;
    }
    var r = origen.getBoundingClientRect();
    var x = r.left + r.width / 2, y = r.top + r.height / 2;
    var radi = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    var transicio = document.startViewTransition(canvia);
    transicio.ready.then(function () {
      arrel.animate(
        { clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + radi + 'px at ' + x + 'px ' + y + 'px)'] },
        { duration: ms, easing: token('--m-corba-entra-surt') || 'ease-in-out', pseudoElement: '::view-transition-new(root)' }
      );
    }).catch(function () {});
    transicio.finished.catch(function () {});
  }

  function tria(t, origen) {
    var abans = token('--c-fons');
    desa(t);
    marca(t);
    posa(t);
    var canvia = token('--c-fons') !== abans;  // «Sistema» pot no canviar cap color: llavors, sense cortina
    if (canvia) {
      posa(actual);  // la cortina necessita la imatge del tema d'abans
      cortina(origen, function () { posa(t); barra(); });
    } else {
      barra();
    }
    actual = t;
  }

  // Per als altres controls de tema (Eclipse, T-DX-05): triar i saber quin tema es veu.
  window.CrisTema = {
    tria: tria,
    fosc: function () {
      var t = arrel.getAttribute('data-theme');
      return t ? t === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.selector-tema input').forEach(function (i) {
      i.addEventListener('change', function () { if (i.checked) tria(i.value, i.closest('label')); });
    });
    marca(actual);
    barra();
    // Sense JavaScript el selector no faria res: només es mostra quan funciona.
    document.querySelectorAll('.selector-tema[hidden]').forEach(function (s) { s.hidden = false; });
  });

  // Una altra pestanya ha canviat el tema: s'aplica aquí, sense cortina.
  window.addEventListener('storage', function (e) {
    if (e.key !== CLAU && e.key !== null) return;
    actual = llegeix();
    posa(actual);
    marca(actual);
    barra();
  });
  // Amb «Sistema», si el sistema canvia de tema, la barra el segueix (el CSS ja ho fa sol).
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', barra);
})();
