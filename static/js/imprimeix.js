/* «Desa com a PDF» (T-M01-19; decisió 079, A-20): el PDF del carnet és la impressió del
   navegador. Fitxer propi, sense codi en línia (066).
   - Mostra els botons [data-imprimeix] (surten amagats: sense JavaScript no farien res) i hi
     lliga la impressió.
   - Mentre s'imprimeix, força el tema clar: amb el tema fosc el text sortiria clar sobre paper
     blanc. En acabar, torna a posar el que hi havia. També val per a Ctrl+P. */
(function () {
  'use strict';
  var arrel = document.documentElement;
  var anterior = null;
  window.addEventListener('beforeprint', function () {
    anterior = arrel.getAttribute('data-theme');
    arrel.setAttribute('data-theme', 'light');
  });
  window.addEventListener('afterprint', function () {
    if (anterior) arrel.setAttribute('data-theme', anterior);
    else arrel.removeAttribute('data-theme');
  });
  function prepara() {
    document.querySelectorAll('[data-imprimeix]').forEach(function (boto) {
      boto.hidden = false;
      boto.addEventListener('click', function () { window.print(); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', prepara);
  else prepara();
})();
