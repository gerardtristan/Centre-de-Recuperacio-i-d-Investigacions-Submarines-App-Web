/* Textos legals del formulari d'alta en una finestra integrada (T-M01-13). Fitxer propi, cap
   codi en línia (066). Sense JavaScript (o sense <dialog>), els textos es veuen sencers a la
   mateixa pàgina i els enllaços hi porten. El <dialog> natiu reté el focus i tanca amb Esc;
   en tancar, el focus torna a l'enllaç que l'ha obert. Les caselles no depenen de res d'això. */
(function () {
  'use strict';
  var CREU = '<svg class="icona-svg" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/></svg>';

  function finestra(article, tanca) {
    var titol = article.querySelector('h3');
    var cos = article.querySelector('.text-legal-cos');
    var dialeg = document.createElement('dialog');
    dialeg.className = 'dialeg dialeg-text';
    dialeg.id = article.id;
    dialeg.setAttribute('aria-labelledby', titol.id);
    article.removeAttribute('id');

    var cap = document.createElement('div');
    cap.className = 'dialeg-cap';
    var boto = document.createElement('button');
    boto.type = 'button';
    boto.className = 'boto boto-text boto-tanca';
    boto.setAttribute('aria-label', tanca);
    boto.innerHTML = CREU;
    boto.addEventListener('click', function () { dialeg.close(); });
    cap.appendChild(titol);
    cap.appendChild(boto);

    // Regió amb focus perquè el text llarg es pugui desplaçar amb el teclat.
    cos.classList.add('dialeg-cos');
    cos.tabIndex = 0;
    cos.setAttribute('role', 'region');
    cos.setAttribute('aria-labelledby', titol.id);

    dialeg.appendChild(cap);
    dialeg.appendChild(cos);
    document.body.appendChild(dialeg);
    return dialeg;
  }

  document.addEventListener('DOMContentLoaded', function () {
    var seccio = document.querySelector('[data-textos-legals]');
    if (!seccio || typeof HTMLDialogElement !== 'function') return;
    var tanca = seccio.getAttribute('data-tanca');
    seccio.querySelectorAll('article[id]').forEach(function (article) { finestra(article, tanca); });
    seccio.hidden = true;

    function marca() {
      document.querySelectorAll('a[data-obre-text]').forEach(function (enllac) {
        enllac.setAttribute('aria-haspopup', 'dialog');
      });
    }
    marca();
    // La part del formulari que depèn de l'edat arriba de nou amb HTMX: els enllaços nous
    // també s'han de marcar, i els clics s'escolten al document.
    document.body.addEventListener('htmx:afterSettle', marca);
    document.addEventListener('click', function (e) {
      var enllac = e.target.closest('a[data-obre-text]');
      if (!enllac) return;
      var dialeg = document.getElementById(enllac.getAttribute('href').slice(1));
      if (!dialeg || dialeg.tagName !== 'DIALOG') return;
      e.preventDefault();
      dialeg.showModal();
      dialeg.addEventListener('close', function () { enllac.focus(); }, { once: true });
    });
  });
})();
