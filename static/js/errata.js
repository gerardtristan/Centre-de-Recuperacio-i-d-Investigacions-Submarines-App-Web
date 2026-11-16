/* Errata (T-DX-06): si el servidor ha tornat el formulari amb errors, el focus va al resum
   (el lector de pantalla llegeix «Hi ha N errors») i cada enllaç porta al seu camp i hi posa
   el focus. Sense JavaScript, el resum es veu igual i els enllaços salten al camp. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    var resum = document.querySelector('[data-errata]');
    if (!resum) return;
    resum.focus();
    resum.querySelectorAll('a[href^="#"]').forEach(function (enllac) {
      enllac.addEventListener('click', function (e) {
        var camp = document.getElementById(enllac.getAttribute('href').slice(1));
        if (!camp) return;
        e.preventDefault();
        camp.focus();
        camp.scrollIntoView({ block: 'center' });
      });
    });
  });
})();
