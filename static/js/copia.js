/* Botons «Copia» (T-M05b-06; CA-M05b-10): copien al porta-retalls el valor de [data-copia]
   (l'IBAN del club, l'import o la referència d'una transferència) i, durant uns segons, diuen
   el text de [data-copiat], que la regió viva de la pantalla anuncia. Surten amagats: sense
   JavaScript o sense porta-retalls no farien res, i el text es pot seleccionar igualment.
   Escolta al document, perquè HTMX pot tornar a dibuixar l'estat. Fitxer propi, sense codi en
   línia (066). */
(function () {
  'use strict';
  function mostra() {
    document.querySelectorAll('[data-copia]').forEach(function (boto) {
      boto.hidden = !(navigator.clipboard && window.isSecureContext);
    });
  }
  document.addEventListener('click', function (e) {
    var boto = e.target.closest('[data-copia]');
    if (!boto) return;
    if (!boto.dataset.text) boto.dataset.text = boto.textContent;
    navigator.clipboard.writeText(boto.dataset.copia).then(function () {
      boto.textContent = boto.dataset.copiat;
      setTimeout(function () { boto.textContent = boto.dataset.text; }, 2000);
    });
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mostra);
  else mostra();
  document.addEventListener('htmx:afterSwap', mostra);
})();
