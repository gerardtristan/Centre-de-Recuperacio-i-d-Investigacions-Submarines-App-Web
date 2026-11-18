/* Activitats (T-DX-63; design-system §16, T-DX-63): les pestanyes per tipus (patró ARIA, amb les
   fletxes, Inici i Fi), els filtres sobre el contingut d'exemple de la pàgina, el panell de filtres a
   pantalla sencera del mòbil i el comptador del carril «Activitats per a tu». Res no surt del
   navegador: cap petició, cap desat i cap eval. Els textos venen de la plantilla (traduïbles). */
(function () {
  'use strict';

  // Carril «per a tu»: el comptador «1 / 3» segueix la posició real (sense avanç automàtic, D20)
  document.querySelectorAll('[data-carril]').forEach(function (carril) {
    const comptador = document.getElementById(carril.dataset.carril);
    const n = carril.children.length;
    if (!comptador || !n) return;
    carril.addEventListener('scroll', function () {
      const pas = carril.children[0].getBoundingClientRect().width + (parseFloat(getComputedStyle(carril).columnGap) || 0);
      comptador.textContent = Math.min(n, Math.round(carril.scrollLeft / pas) + 1) + ' / ' + n;
    }, { passive: true });
  });

  const arrel = document.querySelector('[data-activitats]');
  if (!arrel) return;

  /* ---------- Pestanyes ---------- */
  const pestanyes = Array.from(arrel.querySelectorAll('[role="tab"]'));
  function tria(pestanya, enfoca) {
    pestanyes.forEach(function (p) {
      const activa = p === pestanya;
      p.setAttribute('aria-selected', String(activa));
      p.tabIndex = activa ? 0 : -1;
      document.getElementById(p.getAttribute('aria-controls')).hidden = !activa;
    });
    if (enfoca) pestanya.focus();
  }
  pestanyes.forEach(function (p, i) {
    p.addEventListener('click', function () { tria(p); });
    p.addEventListener('keydown', function (e) {
      const j = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: pestanyes.length - 1 }[e.key];
      if (j === undefined) return;
      e.preventDefault();
      tria(pestanyes[(j + pestanyes.length) % pestanyes.length], true);
    });
  });
  arrel.querySelectorAll('[data-mostra]').forEach(function (boto) {
    boto.addEventListener('click', function () { tria(document.getElementById('pest-' + boto.dataset.mostra), true); });
  });

  /* ---------- Filtres ---------- */
  const puc = arrel.querySelector('[data-filtre="puc"]');
  const places = arrel.querySelector('[data-filtre="places"]');
  const lloc = arrel.querySelector('[data-filtre="lloc"]');
  const quan = function () { return arrel.querySelector('input[name="activitats-quan"]:checked'); };
  const actiu = function (interruptor) { return interruptor.getAttribute('aria-checked') === 'true'; };

  function passa(t) {
    const mes = Number(t.dataset.mes);
    const q = quan().value;
    return (!actiu(puc) || t.dataset.puc === '1')
      && (q === 'tot' || (q === 'mes' ? mes === 0 : mes <= 2))
      && (!lloc.value || t.dataset.lloc === lloc.value)
      && (!actiu(places) || t.dataset.places === '1');
  }

  // El que diu cada filtre actiu als botons de l'estat buit: «Quan: Aquest mes», «On: Cadaqués»
  function etiquetes() {
    return {
      puc: actiu(puc),
      quan: quan().value !== 'tot' && document.getElementById('f-quan').textContent + ': ' + quan().closest('label').querySelector('[data-nom]').textContent,
      lloc: !!lloc.value && lloc.labels[0].textContent + ': ' + lloc.selectedOptions[0].textContent,
      places: actiu(places),
    };
  }

  function aplica() {
    const actius = etiquetes();
    arrel.querySelectorAll('[role="tabpanel"]').forEach(function (panell) {
      let total = 0;
      panell.querySelectorAll('[data-grup]').forEach(function (grup) {
        const limit = Number(grup.dataset.limit) || Infinity;
        let n = 0;
        grup.querySelectorAll('[data-targeta]').forEach(function (t) {
          const ok = passa(t);
          if (ok) n += 1;
          t.hidden = !ok || n > limit;
        });
        grup.hidden = n === 0;
        const compte = grup.querySelector('[data-n]');
        if (compte) compte.textContent = n;
        total += n;
      });
      arrel.querySelector('[aria-controls="' + panell.id + '"] [data-n]').textContent = total;
      if (panell.id === 'panell-totes') arrel.querySelector('[data-recompte]').textContent = total;
      const buit = panell.querySelector('[data-buit]');
      buit.hidden = total > 0;
      buit.querySelectorAll('[data-treu]').forEach(function (li) {
        const text = actius[li.dataset.treu];
        li.hidden = !text;
        const etiqueta = li.querySelector('[data-etiqueta]');
        if (etiqueta && text) etiqueta.textContent = text;
      });
    });
  }

  function commuta(interruptor, si) {
    interruptor.setAttribute('aria-checked', String(si));
    interruptor.querySelector('.int-estat').textContent = si ? interruptor.dataset.si : interruptor.dataset.no;
  }
  [puc, places].forEach(function (interruptor) {
    interruptor.addEventListener('click', function () { commuta(interruptor, !actiu(interruptor)); aplica(); });
  });
  arrel.querySelectorAll('input[name="activitats-quan"]').forEach(function (r) { r.addEventListener('change', aplica); });
  lloc.addEventListener('change', aplica);

  // «Treu el filtre» de l'estat buit
  const treu = {
    puc: function () { commuta(puc, false); },
    places: function () { commuta(places, false); },
    quan: function () { arrel.querySelector('input[name="activitats-quan"][value="tot"]').checked = true; },
    lloc: function () { lloc.value = ''; },
  };
  arrel.querySelectorAll('[data-treu] button').forEach(function (boto) {
    boto.addEventListener('click', function () {
      treu[boto.closest('[data-treu]').dataset.treu]();
      aplica();
      arrel.querySelector('[role="tab"][aria-selected="true"]').focus();
    });
  });

  /* ---------- Mòbil: els filtres a pantalla sencera ---------- */
  const panell = document.getElementById('activitats-filtres');
  const obre = arrel.querySelector('[data-obre]');
  const fet = panell.querySelector('[data-fet]');
  const fons = arrel.querySelectorAll('[data-fons]');
  function obert(si) {
    panell.classList.toggle('es-obert', si);
    obre.setAttribute('aria-expanded', String(si));
    fons.forEach(function (el) { el.inert = si; });
    (si ? fet : obre).focus();
  }
  obre.addEventListener('click', function () { obert(true); });
  fet.addEventListener('click', function () { obert(false); });
  panell.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panell.classList.contains('es-obert')) obert(false);
  });
  // Si la finestra s'eixampla amb el panell obert, es tanca (a la tauleta i a l'escriptori no ho és)
  matchMedia('(min-width: 600px)').addEventListener('change', function (e) {
    if (e.matches && panell.classList.contains('es-obert')) obert(false);
  });
}());
