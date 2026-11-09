/* Llista emergent «Exporta» del llistat de socis (T-M01-15). Millora progressiva d'un <details>
   natiu: sense JavaScript, s'obre i es tanca amb el botó, com fins ara. Amb JavaScript, també es
   tanca amb Esc (el focus torna a «Exporta»), amb un clic fora i quan el focus en surt amb Tab o
   Maj+Tab. Fitxer propi, cap codi en línia ni cap petició externa. */
(function () {
  'use strict';
  document.querySelectorAll('details.menu-exporta').forEach(function (menu) {
    var boto = menu.querySelector('summary');

    menu.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && menu.open) {
        event.preventDefault();
        menu.open = false;
        boto.focus();
      }
    });

    // El focus surt de la llista (Tab, Maj+Tab o un clic en un altre element): es tanca.
    menu.addEventListener('focusout', function (event) {
      if (menu.open && event.relatedTarget && !menu.contains(event.relatedTarget)) {
        menu.open = false;
      }
    });

    // Un clic fora (també en una zona que no pot rebre el focus): es tanca.
    document.addEventListener('click', function (event) {
      if (menu.open && !menu.contains(event.target)) {
        menu.open = false;
      }
    });
  });
})();
