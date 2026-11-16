/* Solapas (T-DX-07; recurs a design/extern/; design-system §6.11): pestanyes de les fitxes obertes
   a l'administració, per anar d'una fitxa a l'altra sense perdre-les.
   - Una fitxa que es vol a les pestanyes ho diu amb <meta name="cris-solapa" content="Soci 12">.
   - P-96 (B): la llista (adreça i etiqueta, sense noms) va a sessionStorage, que només viu en
     aquesta pestanya del navegador; el contingut no es desa enlloc. «Surt» la buida.
   - Arrossegar per ordenar (també Alt+← i Alt+→), × per tancar (en tancar l'activa, s'obre la de
     la dreta o, si era l'última, la de l'esquerra), un punt si la fitxa té canvis sense desar i,
     quan no hi caben, les que menys s'han fet servir passen al menú «+N».
   Cada pestanya és un enllaç: el servidor torna a comprovar el permís en obrir la fitxa. */
(function () {
  'use strict';
  var CLAU = 'cris-solapes';

  function llegeix() {
    try { return JSON.parse(sessionStorage.getItem(CLAU)) || { llista: [], torn: 0 }; }
    catch (e) { return { llista: [], torn: 0 }; }
  }
  function desa(estat) {
    try { sessionStorage.setItem(CLAU, JSON.stringify(estat)); } catch (e) { /* sense sessionStorage: només la pàgina actual */ }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var tira = document.querySelector('[data-solapes]');
    // «Surt»: la llista se'n va amb la sessió.
    document.querySelectorAll('.lateral-compte form').forEach(function (f) {
      f.addEventListener('submit', function () { try { sessionStorage.removeItem(CLAU); } catch (e) { /* res */ } });
    });
    if (!tira) return;
    // El menú «+N» el crea el guió: sense JavaScript no faria res.
    var mes = document.createElement('div');
    mes.className = 'solapes-mes';
    mes.hidden = true;
    mes.innerHTML = '<button class="boto-solapes" type="button" aria-expanded="false" aria-haspopup="menu"><span class="solapes-mes-n">+0</span></button><ul role="menu" hidden></ul>';
    mes.querySelector('button').setAttribute('aria-label', tira.dataset.mes);
    tira.append(mes);
    var estat = llegeix();
    var aqui = location.pathname;
    var meta = document.querySelector('meta[name="cris-solapa"]');
    if (meta && !estat.llista.some(function (s) { return s.url === aqui; })) {
      estat.llista.push({ url: aqui, etiqueta: meta.content });
    }
    estat.llista.forEach(function (s) { if (s.url === aqui) s.us = ++estat.torn; });
    desa(estat);
    var bruta = false;

    function tanca(url) {
      var i = estat.llista.findIndex(function (s) { return s.url === url; });
      if (i < 0) return;
      if (url === aqui && bruta && !window.confirm(tira.dataset.avisCanvis)) return;
      estat.llista.splice(i, 1);
      desa(estat);
      if (url !== aqui) { pinta(); return; }
      var seguent = estat.llista[i] || estat.llista[i - 1];
      bruta = false;
      location.href = seguent ? seguent.url : tira.dataset.inici;
    }
    function mou(url, pas) {
      var i = estat.llista.findIndex(function (s) { return s.url === url; });
      var j = i + pas;
      if (i < 0 || j < 0 || j >= estat.llista.length) return;
      estat.llista.splice(j, 0, estat.llista.splice(i, 1)[0]);
      desa(estat);
      pinta();
    }

    function pestanya(s) {
      var li = document.createElement('li');
      li.className = 'solapa' + (s.url === aqui ? ' es-activa' + (bruta ? ' es-bruta' : '') : '');
      li.dataset.url = s.url;
      var a = document.createElement('a');
      a.href = s.url;
      a.textContent = s.etiqueta;
      a.draggable = false;  // l'arrossegament natiu de l'enllaç es menjaria el de la pestanya
      if (s.url === aqui) a.setAttribute('aria-current', 'page');
      a.addEventListener('keydown', function (e) {
        if (!e.altKey || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;
        e.preventDefault();
        mou(s.url, e.key === 'ArrowLeft' ? -1 : 1);
        var enllac = tira.querySelector('.solapa[data-url="' + CSS.escape(s.url) + '"] a');
        if (enllac) enllac.focus();
      });
      var punt = document.createElement('span');
      punt.className = 'solapa-punt';
      punt.setAttribute('aria-hidden', 'true');
      var x = document.createElement('button');
      x.type = 'button';
      x.className = 'solapa-tanca';
      x.setAttribute('aria-label', tira.dataset.tanca.replace('%s', s.etiqueta));
      x.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m7 7 10 10M17 7 7 17"/></svg>';
      x.addEventListener('click', function () { tanca(s.url); });
      li.append(punt, a, x);
      arrossega(li, s.url);
      return li;
    }

    /* Arrossegar: en passar per sobre del centre d'una veïna, s'intercanvien. */
    function arrossega(li, url) {
      li.addEventListener('pointerdown', function (e) {
        if (e.button !== 0 || e.target.closest('.solapa-tanca')) return;
        var x0 = e.clientX, mogut = false, actual = li;
        function aquesta() { return tira.querySelector('.solapes-llista .solapa[data-url="' + CSS.escape(url) + '"]'); }
        function moviment(ev) {
          if (!mogut && Math.abs(ev.clientX - x0) < 6) return;
          mogut = true;
          actual.classList.add('es-arrossega');
          var germanes = Array.prototype.slice.call(tira.querySelectorAll('.solapes-llista .solapa'));
          var i = germanes.indexOf(actual);
          var dreta = germanes[i + 1], esquerra = germanes[i - 1];
          var pas = 0;
          if (dreta && ev.clientX > dreta.getBoundingClientRect().left + dreta.offsetWidth / 2) pas = 1;
          else if (esquerra && ev.clientX < esquerra.getBoundingClientRect().left + esquerra.offsetWidth / 2) pas = -1;
          if (!pas) return;
          mou(url, pas);  // torna a pintar: es continua amb l'element nou
          actual = aquesta() || actual;
          actual.classList.add('es-arrossega');
        }
        function fi() {
          document.removeEventListener('pointermove', moviment);
          document.removeEventListener('pointerup', fi);
          actual.classList.remove('es-arrossega');
          // Després d'arrossegar, el clic de deixar anar no obre la fitxa.
          if (mogut) actual.addEventListener('click', function para(ev) { ev.preventDefault(); actual.removeEventListener('click', para, true); }, true);
        }
        document.addEventListener('pointermove', moviment);
        document.addEventListener('pointerup', fi);
      });
    }

    function pinta() {
      var llista = tira.querySelector('.solapes-llista');
      var mes = tira.querySelector('.solapes-mes');
      var menu = mes.querySelector('ul');
      llista.textContent = '';
      menu.textContent = '';
      estat.llista.forEach(function (s) { llista.append(pestanya(s)); });
      tira.hidden = estat.llista.length === 0;
      // Si no hi caben, les que fa més que no s'obren van al menú «+N» (mai l'activa).
      var amagades = 0;
      var perUs = estat.llista.slice().sort(function (a, b) { return (a.us || 0) - (b.us || 0); });
      mes.hidden = false;
      while (llista.scrollWidth > llista.clientWidth && amagades < perUs.length) {
        var s = perUs[amagades++];
        if (s.url === aqui) continue;
        var li = llista.querySelector('.solapa[data-url="' + CSS.escape(s.url) + '"]');
        if (!li) continue;
        li.remove();
        var item = document.createElement('li');
        var a = document.createElement('a');
        a.href = s.url;
        a.setAttribute('role', 'menuitem');
        a.textContent = s.etiqueta;
        item.append(a);
        menu.append(item);
      }
      var n = menu.children.length;
      mes.hidden = n === 0;
      mes.querySelector('.solapes-mes-n').textContent = '+' + n;
    }

    var boto = tira.querySelector('.solapes-mes button');
    boto.addEventListener('click', function () {
      var obert = boto.getAttribute('aria-expanded') === 'true';
      boto.setAttribute('aria-expanded', obert ? 'false' : 'true');
      tira.querySelector('.solapes-mes ul').hidden = obert;
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Escape' || boto.getAttribute('aria-expanded') !== 'true') return;
      boto.setAttribute('aria-expanded', 'false');
      tira.querySelector('.solapes-mes ul').hidden = true;
      boto.focus();
    });
    // Canvis sense desar a la fitxa activa: el punt de la pestanya (no es desen enlloc).
    var cos = document.getElementById('contingut');
    cos.addEventListener('input', function (e) {
      if (!e.target.closest('form') || bruta) return;
      bruta = true;
      var activa = tira.querySelector('.solapa.es-activa');
      if (activa) activa.classList.add('es-bruta');
    });
    cos.addEventListener('submit', function () { bruta = false; });
    pinta();
    window.addEventListener('resize', pinta);
  });
})();
