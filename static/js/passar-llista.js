/* Passar llista des del mòbil (T-M02-16b; CA-M02-17).
   Cada marca s'envia sola amb fetch. Si no hi ha cobertura, la fila diu «Pendent d'enviar» i la
   marca es reenvia en tornar la connexió (esdeveniment «online» i, per si de cas, cada 15 s). El
   servidor la desa una sola vegada encara que arribi dues vegades (és idempotent). Sense
   JavaScript, els botons envien el formulari normal. */
(function () {
  'use strict';
  var taula = document.querySelector('[data-passar-llista]');
  if (!taula) return;
  var textos = document.querySelector('template[data-textos]');
  var anunci = document.querySelector('[data-llista-anunci]');
  var pendents = {}; // inscripció → FormData per reenviar

  function text(clau) {
    var node = textos.content.querySelector('[data-text="' + clau + '"]');
    return node ? node.innerHTML : '';
  }

  function pinta(fila, clau) {
    var lloc = fila.querySelector('[data-estat]');
    if (lloc) lloc.innerHTML = text(clau);
    if (anunci) anunci.textContent = fila.querySelector('th').textContent.trim() + ': ' + lloc.textContent.trim();
  }

  // El comptador «N presents de M · K sense marcar» només compta el que el servidor ha desat.
  function compta() {
    var files = taula.querySelectorAll('[data-fila]');
    var presents = taula.querySelectorAll('[data-fila][data-marca="1"]').length;
    var sense = taula.querySelectorAll('[data-fila][data-marca=""]').length;
    var comptador = document.querySelector('[data-comptador]');
    if (!comptador) return;
    comptador.querySelector('[data-presents]').textContent = presents;
    comptador.querySelector('[data-total]').textContent = files.length;
    comptador.querySelector('[data-sense]').textContent = sense;
  }

  function envia(form, dades) {
    var fila = form.closest('[data-fila]');
    var clau = fila.getAttribute('data-fila');
    return fetch(form.action || window.location.href, {
      method: 'POST',
      body: dades,
      headers: { Accept: 'application/json' },
      credentials: 'same-origin'
    }).then(function (resposta) {
      delete pendents[clau];
      if (resposta.ok) {
        fila.setAttribute('data-marca', dades.get('present'));
        compta();
        pinta(fila, dades.get('present'));
      } else {
        pinta(fila, 'error'); // un error del servidor no es reintenta: cal tornar a marcar
      }
    }).catch(function () {
      pendents[clau] = { form: form, dades: dades };
      pinta(fila, 'pendent');
    });
  }

  function reintenta() {
    Object.keys(pendents).forEach(function (clau) {
      envia(pendents[clau].form, pendents[clau].dades);
    });
  }

  taula.addEventListener('submit', function (e) {
    var form = e.target;
    var boto = e.submitter;
    if (!boto || boto.name !== 'present') return;
    e.preventDefault();
    var dades = new FormData(form);
    dades.set('present', boto.value);
    envia(form, dades);
  });
  window.addEventListener('online', reintenta);
  window.setInterval(function () {
    if (Object.keys(pendents).length) reintenta();
  }, 15000);
})();
