/* Conciliació a l'escriptori (T-DX-72; design-system §6.22). Amb el panell de la línia triada a la vista
   (el CSS el mostra quan el cos fa 56rem o més), «Casa a mà…», «Casa amb moviments…» i «Revisa i
   confirma…» es carreguen amb HTMX al panell des de la mateixa vista, amb l'esquelet mentre carrega.
   Esc o «Tanca» el tanquen i el focus torna a l'enllaç. J i K (de Teletipo) passen de línia, sense
   modificadors i mai dins d'un camp. Amb el panell amagat (mòbil i tauleta) o sense JavaScript,
   l'enllaç porta a la pàgina com abans. El panell no és cap control: la vista torna a comprovar el
   permís i l'estat. */
(function () {
  'use strict';
  const graella = document.querySelector('[data-conciliacio]');
  const panell = graella && graella.querySelector('[data-panell]');
  if (!panell || !window.htmx) return;
  const cos = panell.querySelector('[data-panell-cos]');
  const tanca = panell.querySelector('button[data-panell-tanca]');
  const taula = graella.querySelector('table');
  const files = Array.from(taula.tBodies[0].rows);
  const inicial = cos.innerHTML;
  let origen = null;  // l'enllaç que ha obert el panell: hi torna el focus

  panell.hidden = false;
  taula.setAttribute('aria-keyshortcuts', 'J K');
  files.forEach(function (fila) { fila.tabIndex = -1; });

  function visible() { return getComputedStyle(panell).display !== 'none'; }
  function obert() { return !tanca.hidden; }
  function titol() { const t = cos.querySelector('#panell-linia-titol'); if (t) t.focus(); }
  function mostra(selector) {
    cos.replaceChildren(graella.querySelector(selector).content.cloneNode(true));
  }

  function tria(fila) {
    files.forEach(function (f) {
      f.classList.toggle('es-triada', f === fila);
      if (f === fila) f.setAttribute('aria-current', 'true'); else f.removeAttribute('aria-current');
    });
  }

  function obre(enllac) {
    origen = enllac;
    tria(enllac.closest('tr'));
    tanca.hidden = false;
    mostra('[data-panell-esquelet]');
    cos.setAttribute('aria-busy', 'true');
    htmx.ajax('GET', enllac.href, { source: enllac, target: cos, swap: 'innerHTML' }).then(function () {
      if (origen !== enllac || !obert()) return;
      cos.removeAttribute('aria-busy');
      titol();
    });
  }

  function tancaPanell() {
    tanca.hidden = true;
    cos.innerHTML = inicial;
    cos.removeAttribute('aria-busy');
    if (origen && document.contains(origen)) origen.focus();
  }

  graella.addEventListener('click', function (e) {
    const enllac = e.target.closest('a[data-panell-enllac]');
    if (enllac) {
      // Ctrl, Maj o el botó del mig: on el navegador diu (una pestanya nova, la pàgina)
      if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || !visible()) return;
      e.preventDefault();
      obre(enllac);
    } else if (e.target.closest('[data-panell-tanca]') && panell.contains(e.target)) {
      e.preventDefault();
      tancaPanell();
    }
  });

  // Error, accés denegat o sense xarxa: ho diu al panell i ofereix la pàgina. La sessió caducada no
  // arriba aquí: el servidor respon amb HX-Redirect i HTMX porta tota la pàgina (middleware).
  function error() {
    mostra('[data-panell-error]');
    cos.querySelector('[data-panell-pagina]').href = origen.href;
    cos.removeAttribute('aria-busy');
    titol();
  }

  document.body.addEventListener('htmx:beforeSwap', function (e) {
    if (e.detail.target !== cos) return;
    const elt = e.detail.requestConfig && e.detail.requestConfig.elt;
    // Una resposta que arriba tard (el panell ja és tancat o s'ha obert una altra línia) no s'hi posa
    if (!obert() || (elt && elt.matches('a[data-panell-enllac]') && elt !== origen)) {
      e.detail.shouldSwap = false;
      e.detail.isError = false;
    } else if (e.detail.isError) {
      e.detail.isError = false;  // el panell ja ho explica: HTMX no ho torna a escriure a la consola
      error();
    }
  });
  document.body.addEventListener('htmx:sendError', function (e) {
    if (e.detail.target === cos && obert()) error();
  });

  document.addEventListener('keydown', function (e) {
    if (e.defaultPrevented || !visible()) return;
    if (e.key === 'Escape') {
      if (obert()) { e.preventDefault(); tancaPanell(); }
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey || e.isComposing) return;
    if (e.target.closest && e.target.closest('input, textarea, select, [contenteditable]')) return;
    const pas = { j: 1, k: -1 }[e.key.toLowerCase()];
    if (!pas) return;
    e.preventDefault();
    const ara = files.findIndex(function (f) { return f.classList.contains('es-triada'); });
    const fila = files[ara < 0 ? 0 : Math.min(files.length - 1, Math.max(0, ara + pas))];
    const enllac = fila.querySelector('a[data-panell-enllac]');
    if (obert() && enllac) {
      obre(enllac);  // el focus va al títol del panell quan arriba
      return;
    }
    if (obert()) tancaPanell();
    tria(fila);
    origen = enllac;
    (enllac || fila).focus();
  });
}());
