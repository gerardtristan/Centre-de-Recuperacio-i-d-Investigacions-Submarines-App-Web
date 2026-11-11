/* Recorreguts dels wireframes (T-M01-48): pinta l'índex a partir de window.RECORREGUTS
   (dades.js, generat des de recorreguts.json). Sense dependències ni cap petició: funciona
   obert amb file://. Tot el text s'escriu amb textContent, mai com a HTML. */
(function () {
  'use strict';
  // El mateix tema desat que els wireframes
  try {
    var tema = localStorage.getItem('cris-tema');
    if (tema === 'light' || tema === 'dark') document.documentElement.setAttribute('data-theme', tema);
  } catch (e) { /* sense emmagatzematge: tema del sistema */ }

  var dades = window.RECORREGUTS;
  if (!dades) return;
  var WIREFRAMES = '../wireframes/';
  var ESTIL = {
    'sense-wireframe': 'estat-neutre',
    'aplicacio-difereix': 'estat-avis',
    'wireframe-sense-implementar': 'estat-info'
  };

  function el(nom, classe, text) {
    var node = document.createElement(nom);
    if (classe) node.className = classe;
    if (text) node.textContent = text;
    return node;
  }
  function distintiu(codi) {
    return el('span', 'estat ' + (ESTIL[codi] || 'estat-neutre'), dades.distintius[codi]);
  }
  function dada(llista, nom, valor) {
    var fila = el('div');
    fila.appendChild(el('dt', '', nom));
    var dd = el('dd');
    if (typeof valor === 'string') dd.textContent = valor; else dd.appendChild(valor);
    fila.appendChild(dd);
    llista.appendChild(fila);
  }
  function enllacos(wireframes) {
    var grup = document.createDocumentFragment();
    wireframes.forEach(function (w, i) {
      if (i) grup.appendChild(document.createTextNode(' · '));
      var a = el('a', 'codi', w.fitxer + '#' + w.ancora);
      a.href = WIREFRAMES + w.fitxer + '#' + w.ancora + (w.rol ? '&rol=' + w.rol : '');
      grup.appendChild(a);
    });
    return grup;
  }
  function pas(p) {
    var li = el('li', 'pas');
    var cap = el('div', 'pas-cap');
    cap.appendChild(el('strong', '', 'Pas ' + p.pas));
    cap.appendChild(el('span', '', p.actor));
    if (p.distintiu) cap.appendChild(distintiu(p.distintiu));
    li.appendChild(cap);
    li.appendChild(el('p', '', p.que));
    var dl = el('dl', 'pas-dades');
    dada(dl, 'Permís', p.permisos.length ? p.permisos.join(' i ') : 'Cap (pas del sistema)');
    if (p.pantalla) dada(dl, 'Pantalla', p.pantalla);
    dada(dl, 'Wireframe', p.wireframes.length ? enllacos(p.wireframes) : (p.pantalla ? 'No n\'hi ha' : 'Sense pantalla'));
    dada(dl, 'Tasca del pla', p.tasca);
    li.appendChild(dl);
    if (p.nota) li.appendChild(el('p', 'pas-nota text-2', p.nota));
    return li;
  }

  document.getElementById('titol').textContent = dades.titol;
  document.getElementById('font').textContent = dades.font;
  var index = document.getElementById('index');
  var llegenda = document.getElementById('llegenda');
  var contenidor = document.getElementById('recorreguts');
  var comptes = {};

  dades.recorreguts.forEach(function (r) {
    var entrada = el('li');
    var enllac = el('a', '', r.id + ' · ' + r.titol + ' (' + r.passos.length + ' passos)');
    enllac.href = '#' + r.id;
    entrada.appendChild(enllac);
    index.appendChild(entrada);

    var seccio = el('section', 'targeta recorregut');
    seccio.id = r.id;
    seccio.setAttribute('aria-labelledby', r.id + '-titol');
    var titol = el('h2', '', r.id + ' · ' + r.titol);
    titol.id = r.id + '-titol';
    seccio.appendChild(titol);
    var llista = el('ol', 'passos');
    r.passos.forEach(function (p) {
      if (p.distintiu) comptes[p.distintiu] = (comptes[p.distintiu] || 0) + 1;
      llista.appendChild(pas(p));
    });
    seccio.appendChild(llista);
    contenidor.appendChild(seccio);
  });

  Object.keys(dades.distintius).forEach(function (codi) {
    var li = el('li');
    li.appendChild(distintiu(codi));
    var n = comptes[codi] || 0;
    li.appendChild(el('span', 'text-2', n + (n === 1 ? ' pas' : ' passos')));
    llegenda.appendChild(li);
  });
})();
