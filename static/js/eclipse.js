/* Eclipse (T-DX-05; recurs a design/extern/): l'interruptor de dia i nit de la part pública.
   El sol creua el carril amb una molla mentre la lluna el va tapant; en tancar-se, l'anell de
   diamant i la corona; les núvols s'enfonsen i surten les estrelles. Al tope, l'astre s'aixafa.
   El tema el tria tema.js (window.CrisTema), amb la cortina de Duermevela que surt del botó.
   En obrir la pàgina, l'interruptor mostra el tema que es veu (el del sistema si no s'ha triat
   res). «Com el sistema» torna a seguir el sistema. Amb moviment reduït, sense animació. */
(function () {
  'use strict';
  var HZ = 240, PAS = 1 / HZ;  // les molles, a passos fixos: igual a qualsevol velocitat de pantalla
  function acota(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function suau(t) { return t * t * (3 - 2 * t); }

  function Eclipse(boto) {
    var menysMoviment = window.matchMedia('(prefers-reduced-motion: reduce)');
    var tema = window.CrisTema;
    var diamant = boto.querySelector('.eclipse-diamant');
    var esNit = tema.fosc();
    // Dues molles: p mou l'astre (es passa un 7 % i torna) i q la lluna, més lenta.
    var p = esNit ? 1 : 0, vp = 0, q = p, vq = 0;
    var raf = 0, previ = null, resta = 0, qAbans = q;

    function pinta() {
      // Els valors van a variables de CSS (eclipse.css), no a estils escrits a mà.
      var x = acota(p, 0, 1), l = acota(q, 0, 1);
      var cop = p > 1 ? p - 1 : p < 0 ? -p : 0;
      var estira = Math.min(0.07, Math.abs(vp) * 0.014);
      var v = {
        '--eclipse-x': x.toFixed(4),
        '--eclipse-sx': ((1 + estira) * (1 - 1.5 * cop)).toFixed(4),
        '--eclipse-sy': ((1 - estira * 0.6) * (1 + 0.9 * cop)).toFixed(4),
        '--eclipse-lluna': l.toFixed(4),
        '--eclipse-nit': suau(x).toFixed(3),
        '--eclipse-corona': suau(acota((l - 0.82) / 0.18, 0, 1)).toFixed(3)
      };
      for (var nom in v) boto.style.setProperty(nom, v[nom]);
      boto.classList.toggle('eclipse-a-la-dreta', p > 0.5);
    }
    function destell() {
      if (menysMoviment.matches || !diamant.animate) return;
      diamant.animate(
        [{ opacity: 0, transform: 'scale(.3)' }, { opacity: 1, transform: 'scale(1.25)', offset: 0.3 }, { opacity: 0, transform: 'scale(.7)' }],
        { duration: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--m-llindar')) || 0, easing: 'ease-out' }
      );
    }
    function pas() {
      var meta = esNit ? 1 : 0;
      vp += (220 * (meta - p) - 19 * vp) * PAS; p += vp * PAS;
      vq += (130 * (meta - q) - 19 * vq) * PAS; q += vq * PAS;
      if ((qAbans - 0.93) * (q - 0.93) < 0) destell();  // la lluna creua el 93 % del sol
      qAbans = q;
    }
    function quadre(t) {
      if (previ !== null) resta += Math.min(100, t - previ);
      previ = t;
      var n = Math.floor(resta / (1000 / HZ));
      for (var k = 0; k < n; k++) pas();
      resta -= n * (1000 / HZ);
      pinta();
      var meta = esNit ? 1 : 0;
      if (Math.abs(p - meta) + Math.abs(vp) + Math.abs(q - meta) + Math.abs(vq) < 1e-4) {
        p = q = meta; vp = vq = 0; pinta(); raf = 0; previ = null; return;
      }
      raf = requestAnimationFrame(quadre);
    }
    function marca() {
      boto.classList.toggle('es-nit', esNit);
      boto.setAttribute('aria-checked', esNit ? 'true' : 'false');
    }
    function mou() {
      if (menysMoviment.matches) { p = q = esNit ? 1 : 0; vp = vq = 0; pinta(); return; }
      if (!raf) raf = requestAnimationFrame(quadre);
    }

    boto.addEventListener('click', function () {
      esNit = !esNit;
      marca();
      mou();
      tema.tria(esNit ? 'dark' : 'light', boto);
    });
    // El tema ha canviat per una altra via (una altra pestanya, el sistema, «Com el sistema»).
    document.addEventListener('cris:tema', function () {
      if (tema.fosc() === esNit) return;
      esNit = tema.fosc();
      marca();
      mou();
    });
    // L'estat inicial es pinta sense transicions: en obrir de nit no es veu un eclipse sencer.
    boto.classList.add('eclipse-quiet');
    marca();
    pinta();
    requestAnimationFrame(function () { requestAnimationFrame(function () { boto.classList.remove('eclipse-quiet'); }); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!window.CrisTema) return;
    document.querySelectorAll('[data-eclipse]').forEach(Eclipse);
    document.querySelectorAll('[data-tema-sistema]').forEach(function (b) {
      b.addEventListener('click', function () { window.CrisTema.tria('sistema', b); });
    });
    // Sense JavaScript l'interruptor no faria res: només es mostra quan funciona.
    document.querySelectorAll('.eclipse-tema[hidden]').forEach(function (e) { e.hidden = false; });
  });
})();
