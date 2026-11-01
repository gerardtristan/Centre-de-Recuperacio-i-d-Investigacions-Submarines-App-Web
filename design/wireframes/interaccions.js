/* ==========================================================================
   Interaccions compartides dels prototips C.R.I.S. (JavaScript propi, sense
   dependències ni CDN: decisió 046).

     CRIS.tema()                       selector Sistema / Clar / Fosc
     CRIS.anuncia(text)                regió viva per al lector de pantalla
     CRIS.botoDinamic(boto)            botó que canvia de text i d'amplada
     CRIS.subratllat(contenidor, o)    ratlla elàstica i píndola que segueix el cursor
     CRIS.pestanyes(llista, o)         pestanyes ARIA amb subratllat i relleu de panells
     CRIS.zonaMagnetica(zona, o)       pujar fitxers arrossegant-los, amb imant
     CRIS.impressora(arrel)            justificant que s'imprimeix
     CRIS.icona(nom)                   icones SVG pròpies

   Patrons de referència (l'equip els va passar com a experiments): Dynamic
   Button, Receipt Printer, Magnetic Drop Zone i Tactile Button (React + Motion)
   i «Subrayado» de Moxen. Aquí no se'n copia codi: es reimplementen amb els
   tokens del club. Tot respecta «reduir moviment».
   ========================================================================== */
(function () {
  'use strict';

  const redueix = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const CORBA = 'cubic-bezier(.23, 1, .32, 1)';
  const ns = 'http://www.w3.org/2000/svg';
  const espera = ms => new Promise(r => setTimeout(r, ms));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const el = (etiqueta, classe, html) => { const e = document.createElement(etiqueta); if (classe) e.className = classe; if (html != null) e.innerHTML = html; return e; };
  const pf = v => parseFloat(v) || 0;

  /* ---------- Icones: traç de 2 px sobre una graella de 24 ---------- */
  const ICONES = {
    copia: '<rect x="8.5" y="8.5" width="11" height="11" rx="2.5"/><path d="M15.5 8.5V6.5a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
    fet: '<circle cx="12" cy="12" r="9"/><path d="m8 12.4 2.7 2.6L16 9.6"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7"/>',
    carrega: '<path d="M12 3a9 9 0 1 0 9 9"/>',
    targeta: '<rect x="3" y="5.5" width="18" height="13" rx="2.5"/><path d="M3 10h18M7 14.5h3"/>',
    fletxa: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    puja: '<path d="M12 15.5V4.5M7.5 9 12 4.5 16.5 9M5 19.5h14"/>',
    fitxer: '<path d="M14 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5z"/><path d="M14 3.5v5h5"/>',
    pdf: '<path d="M14 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5z"/><path d="M14 3.5v5h5M8.5 16.5v-4h1.2a1.2 1.2 0 0 1 0 2.4H8.5M13 12.5v4h.8a1.6 1.6 0 0 0 1.6-1.6v-.8a1.6 1.6 0 0 0-1.6-1.6z"/>',
    taula: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10"/>',
    imatge: '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.6"/><path d="m20.5 16-4.5-4.5L6 19.5"/>',
    creu: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
    menys: '<path d="M7.5 12h9"/>',
    cadenat: '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    rebut: '<path d="M6 3.5h12v17l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4-2 1.4z"/><path d="M9 8.5h6M9 12h6M9 15.5h3"/>',
    gira: '<path d="M4 12a8 8 0 0 1 13.7-5.6L20 8.5M20 4v4.5h-4.5M20 12a8 8 0 0 1-13.7 5.6L4 15.5M4 20v-4.5h4.5"/>',
    persona: '<circle cx="12" cy="8.5" r="3.8"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
    escut: '<path d="M12 3.5 5 6.5v5c0 4.4 3 7.8 7 9 4-1.2 7-4.6 7-9v-5z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
    ona: '<path d="M3 14c2 0 2-2 4.5-2S10 14 12 14s2-2 4.5-2S19 14 21 14M3 18.5c2 0 2-2 4.5-2s2.5 2 4.5 2 2-2 4.5-2 2.5 2 4.5 2"/>',
    rellotge: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    banc: '<path d="M3.5 9.5 12 4.5l8.5 5M5.5 10v7M10 10v7M14 10v7M18.5 10v7M3.5 19.5h17"/>',
    mobil: '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 17.5h2"/>',
    casa: '<path d="M4 11 12 4.5 20 11M6.5 9.5v10h11v-10"/>',
    llista: '<path d="M9 7h11M9 12h11M9 17h11M4.5 7h.01M4.5 12h.01M4.5 17h.01"/>'
  };
  function icona(nom, classe) {
    return '<svg class="icona-svg' + (classe ? ' ' + classe : '') + '" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + (ICONES[nom] || '') + '</svg>';
  }

  /* ---------- Regió viva compartida ---------- */
  let regio = null;
  function anuncia(text) {
    if (!regio) {
      regio = el('div', 'anunci');
      regio.setAttribute('role', 'status');
      regio.setAttribute('aria-live', 'polite');
      document.body.append(regio);
    }
    regio.textContent = '';
    setTimeout(() => { regio.textContent = text; }, 60);
  }

  /* ---------- Tema: Sistema / Clar / Fosc, desat a localStorage («cris-tema») ---------- */
  function tema() {
    const arrel = document.documentElement;
    const actual = () => arrel.getAttribute('data-theme') || 'sistema';
    function aplica(t) {
      try {
        if (t === 'sistema') { arrel.removeAttribute('data-theme'); localStorage.removeItem('cris-tema'); }
        else { arrel.setAttribute('data-theme', t); localStorage.setItem('cris-tema', t); }
      } catch (e) { if (t !== 'sistema') arrel.setAttribute('data-theme', t); }
      document.querySelectorAll('.selector-tema input').forEach(i => { i.checked = i.value === t; });
    }
    document.querySelectorAll('.selector-tema input').forEach(i => {
      i.addEventListener('change', () => { if (i.checked) aplica(i.value); });
    });
    aplica(actual());
  }

  /* ---------- Molla: un resort amortit (posició, velocitat, destí, rigidesa) ---------- */
  function molla(k, fre, massa) { return { x: 0, v: 0, meta: 0, k, fre, m: massa || 1 }; }
  function avanca(m, h) {
    m.v += ((-m.k * (m.x - m.meta) - m.fre * m.v) / m.m) * h;
    m.x += m.v * h;
  }
  const quieta = m => Math.abs(m.x - m.meta) < 0.1 && Math.abs(m.v) < 0.1;

  /* ======================================================================
     Botó dinàmic
     El text i la icona antics surten cap amunt i els nous entren de sota;
     l'amplada del botó segueix el text nou sense salts.
     ====================================================================== */
  function botoDinamic(boto) {
    if (boto._dinamic) return boto._dinamic;
    const text0 = boto.textContent.trim();
    const icona0 = boto.dataset.icona || 'fletxa';
    boto.classList.add('boto-dinamic');
    boto.textContent = '';
    const cos = el('span', 'bd-cos');
    const caixaIcona = el('span', 'bd-icona');
    const caixaText = el('span', 'bd-text');
    cos.append(caixaIcona, caixaText);
    const mesura = el('span', 'bd-mesura');
    mesura.setAttribute('aria-hidden', 'true');
    boto.append(cos, mesura);
    const estat = { text: text0, icona: icona0, gira: false };
    caixaIcona.append(el('span', 'bd-capa', icona(icona0)));
    caixaText.append(el('span', 'bd-capa', esc(text0)));

    function relleva(caixa, html) {
      const nova = el('span', 'bd-capa', html);
      const velles = Array.from(caixa.children);
      caixa.append(nova);
      const mou = !redueix();
      velles.forEach(v => {
        const a = v.animate(
          [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: mou ? 'translateY(-8px)' : 'none' }],
          { duration: mou ? 150 : 120, easing: CORBA, fill: 'forwards' });
        a.onfinish = () => v.remove();
        setTimeout(() => v.remove(), 400);   // per si la pestanya no anima (en segon pla)
      });
      nova.animate(
        [{ opacity: 0, transform: mou ? 'translateY(8px)' : 'none' }, { opacity: 1, transform: 'translateY(0)' }],
        { duration: mou ? 180 : 160, easing: CORBA });
    }

    function amplada() {
      if (boto.dataset.amplada === 'plena') return;
      // si el botó no es pinta (diàleg tancat, panell amagat), no es pot mesurar: amplada automàtica
      if (!boto.getClientRects().length) { boto.style.width = ''; return; }
      const abans = boto.getBoundingClientRect().width;
      const cs = getComputedStyle(boto);
      const extra = pf(cs.paddingLeft) + pf(cs.paddingRight) + pf(cs.borderLeftWidth) + pf(cs.borderRightWidth);
      const despres = Math.ceil(mesura.scrollWidth + extra);
      boto.style.width = abans + 'px';
      void boto.offsetWidth;            // fixa l'amplada de partida abans de canviar-la
      boto.style.width = despres + 'px';
    }

    function posa(text, nomIcona, opcions) {
      opcions = opcions || {};
      nomIcona = nomIcona || estat.icona;
      boto.classList.toggle('es-fet', !!opcions.fet);
      if (text === estat.text && nomIcona === estat.icona && !!opcions.gira === estat.gira) return;
      mesura.innerHTML = '<span class="bd-icona-mesura"></span><span>' + esc(text) + '</span>';
      amplada();
      if (nomIcona !== estat.icona || !!opcions.gira !== estat.gira) relleva(caixaIcona, icona(nomIcona, opcions.gira ? 'gira' : ''));
      if (text !== estat.text) relleva(caixaText, esc(text));
      estat.text = text; estat.icona = nomIcona; estat.gira = !!opcions.gira;
    }
    function ocupat(si) {
      if (si) { boto.setAttribute('aria-busy', 'true'); boto.setAttribute('aria-disabled', 'true'); }
      else { boto.removeAttribute('aria-busy'); boto.removeAttribute('aria-disabled'); }
    }
    /* Seqüència de passos: [{ text, icona, gira, fet, ms }] */
    async function flux(passos) {
      ocupat(true);
      for (const p of passos) {
        posa(p.text, p.icona, p);
        if (p.anunci) anuncia(p.anunci);
        if (p.ms) await espera(p.ms);
      }
      ocupat(false);
    }
    const api = { posa, ocupat, flux, get estaOcupat() { return boto.getAttribute('aria-busy') === 'true'; }, get text() { return estat.text; }, inicial: { text: text0, icona: icona0 } };
    boto._dinamic = api;
    return api;
  }

  /* ======================================================================
     Subratllat elàstic
     Cada extrem de la ratlla és un resort. El que va cap al destí és rígid
     i surt disparat; el de darrere és tou i el segueix tard: la ratlla
     s'estira i s'aprima pel camí (conserva el volum) i s'escurça en arribar.
     Es dibuixa amb SVG perquè les puntes rodones no es deformin.
     ====================================================================== */
  function subratllat(cont, opcions) {
    const o = Object.assign({ elements: '[role="tab"]', grossor: 3, davant: 340, darrere: 105, fre: 1.45, ratlla: 'base', separacio: 7, pindola: true, farciment: 10 }, opcions);
    cont.classList.add('subratllat');
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'sr-capa');
    svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = '<rect class="sr-pindola" rx="999"/><line class="sr-vora"/><line class="sr-ratlla"/>';
    cont.prepend(svg);
    const pind = svg.querySelector('rect'), vora = svg.querySelector('.sr-vora'), ratlla = svg.querySelector('.sr-ratlla');

    const esq = molla(o.davant, 0), dre = molla(o.davant, 0), pe = molla(260, 0), pd = molla(260, 0);
    [esq, dre, pe, pd].forEach(m => { m.fre = o.fre * Math.sqrt(m.k); });
    let actiu = null, sobre = null, visible = 0, metaVisible = 0, raf = 0, ultim = null;
    let base = 1, y = 0, pindY = 0, pindH = 0;

    const elements = () => Array.from(cont.querySelectorAll(o.elements));
    const esVisible = e => !!(e && e.getClientRects().length);
    function bordes(e) {
      const c = cont.getBoundingClientRect(), r = e.getBoundingClientRect();
      return { esq: r.left - c.left + cont.scrollLeft, dre: r.right - c.left + cont.scrollLeft, dalt: r.top - c.top, alt: r.height, baix: r.bottom - c.top };
    }
    function calculaY(b) {
      y = o.ratlla === 'base' ? cont.clientHeight - o.grossor / 2 : b.baix - o.separacio;
    }
    function pinta() {
      const llarg = Math.max(1, dre.x - esq.x);
      const g = o.grossor * Math.max(0.45, Math.min(1.35, Math.sqrt(base / llarg)));
      const yy = (y - (g - o.grossor) / 2).toFixed(2);
      const x1 = (esq.x + g / 2).toFixed(2), x2 = Math.max(esq.x + g / 2, dre.x - g / 2).toFixed(2);
      [vora, ratlla].forEach(l => { l.setAttribute('x1', x1); l.setAttribute('x2', x2); l.setAttribute('y1', yy); l.setAttribute('y2', yy); });
      ratlla.style.strokeWidth = g.toFixed(2);
      vora.style.strokeWidth = (g + 2).toFixed(2);
      const amagada = !esVisible(actiu);
      ratlla.style.opacity = vora.style.opacity = amagada ? 0 : 1;
      if (o.pindola) {
        pind.setAttribute('x', (pe.x - o.farciment).toFixed(2));
        pind.setAttribute('width', Math.max(0, pd.x - pe.x + o.farciment * 2).toFixed(2));
        pind.setAttribute('y', pindY.toFixed(2));
        pind.setAttribute('height', pindH.toFixed(2));
        pind.style.opacity = visible.toFixed(3);
      }
    }
    function coloca() {
      if (!esVisible(actiu)) { pinta(); return; }
      const b = bordes(actiu);
      calculaY(b);
      esq.x = esq.meta = b.esq; dre.x = dre.meta = b.dre;
      esq.v = dre.v = 0;
      base = b.dre - b.esq;
      pinta();
    }
    function pas(ts) {
      if (ultim === null) ultim = ts;
      let dt = Math.min(1 / 30, (ts - ultim) / 1000);
      ultim = ts;
      for (; dt > 0; dt -= 1 / 240) {
        const h = Math.min(dt, 1 / 240);
        [esq, dre, pe, pd].forEach(m => avanca(m, h));
        visible += (metaVisible - visible) * Math.min(1, h * 10);
      }
      pinta();
      if ([esq, dre, pe, pd].every(quieta) && Math.abs(visible - metaVisible) < 0.01) {
        visible = metaVisible; pinta(); raf = 0; ultim = null; return;
      }
      raf = requestAnimationFrame(pas);
    }
    const anda = () => { if (!raf) raf = requestAnimationFrame(pas); };

    function activa(e, anima) {
      if (!e) return;
      const abans = actiu;
      actiu = e;
      if (!esVisible(e)) { pinta(); return; }
      const b = bordes(e);
      calculaY(b);
      if (anima === false || redueix() || !esVisible(abans)) { coloca(); return; }
      const dreta = b.esq > esq.x;
      esq.meta = b.esq; dre.meta = b.dre;
      base = b.dre - b.esq;
      dre.k = dreta ? o.davant : o.darrere;
      esq.k = dreta ? o.darrere : o.davant;
      [esq, dre].forEach(m => { m.fre = o.fre * Math.sqrt(m.k); });
      anda();
    }
    function hover(e) {
      if (!o.pindola) return;
      const b = bordes(e);
      pe.meta = b.esq; pd.meta = b.dre; pindY = b.dalt; pindH = b.alt;
      if (!sobre || redueix()) { pe.x = pe.meta; pd.x = pd.meta; pe.v = pd.v = 0; }
      sobre = e; metaVisible = 1;
      if (redueix()) { visible = 1; pinta(); return; }
      anda();
    }
    cont.addEventListener('pointerover', ev => {
      if (ev.pointerType !== 'mouse') return;
      const e = ev.target.closest(o.elements);
      if (e && cont.contains(e) && e !== sobre) hover(e);
    });
    cont.addEventListener('pointerleave', () => {
      sobre = null; metaVisible = 0;
      if (redueix()) { visible = 0; pinta(); return; }
      anda();
    });
    if ('ResizeObserver' in window) new ResizeObserver(() => { if (!raf) coloca(); }).observe(cont);
    addEventListener('resize', () => { if (!raf) coloca(); });
    if (document.fonts) document.fonts.ready.then(() => { if (!raf) coloca(); });
    cont.addEventListener('scroll', () => { if (!raf) coloca(); }, { passive: true });
    return { activa, refresca: coloca, elements };
  }

  /* ======================================================================
     Pestanyes ARIA amb subratllat. El panell nou entra des del costat cap al
     qual s'ha mogut la ratlla, línia a línia; el vell surt de pressa.
     ====================================================================== */
  function pestanyes(llista, opcions) {
    const o = Object.assign({ enCanvi: null }, opcions);
    const totes = () => Array.from(llista.querySelectorAll('[role="tab"]'));
    const visibles = () => totes().filter(t => !t.hidden && t.getClientRects().length);
    const panell = t => document.getElementById(t.getAttribute('aria-controls'));
    const sr = subratllat(llista, Object.assign({ elements: '[role="tab"]' }, o.subratllat));
    let actiu = totes().find(t => t.getAttribute('aria-selected') === 'true') || totes()[0];

    function releva(vell, nou, dir) {
      if (!vell || !nou || vell === nou) { if (nou) nou.hidden = false; return; }
      if (redueix()) { vell.hidden = true; nou.hidden = false; return; }
      vell.getAnimations({ subtree: true }).forEach(a => a.cancel());
      vell.animate([{ transform: 'none', opacity: 1 }, { transform: 'translateX(' + (-dir * 24) + 'px)', opacity: 0 }],
        { duration: 150, easing: 'cubic-bezier(.4, 0, 1, 1)', fill: 'forwards' }).onfinish = () => {
        vell.hidden = true; vell.getAnimations().forEach(a => a.cancel());
      };
      nou.hidden = false;
      Array.from(nou.children).forEach((fill, k) => fill.animate(
        [{ transform: 'translateX(' + (dir * 48) + 'px)', opacity: 0 }, { transform: 'none', opacity: 1 }],
        { duration: 620, delay: 150 + k * 60, easing: CORBA, fill: 'backwards' }));
    }
    function ves(t, focus, anima) {
      if (!t) return;
      const abans = actiu;
      const llistaT = totes();
      const dir = llistaT.indexOf(t) >= llistaT.indexOf(abans) ? 1 : -1;
      llistaT.forEach(x => {
        const si = x === t;
        x.setAttribute('aria-selected', String(si));
        x.tabIndex = si ? 0 : -1;
      });
      actiu = t;
      if (anima === false) { llistaT.forEach(x => { const p = panell(x); if (p) p.hidden = x !== t; }); }
      else if (abans !== t) releva(panell(abans), panell(t), dir);
      if (focus) t.focus();
      sr.activa(t, anima);
      if (o.enCanvi) o.enCanvi(t);
    }
    llista.addEventListener('click', e => { const t = e.target.closest('[role="tab"]'); if (t && llista.contains(t)) ves(t); });
    llista.addEventListener('keydown', e => {
      const v = visibles(); const i = v.indexOf(actiu);
      let n = null;
      if (e.key === 'ArrowRight') n = v[(i + 1) % v.length];
      else if (e.key === 'ArrowLeft') n = v[(i - 1 + v.length) % v.length];
      else if (e.key === 'Home') n = v[0];
      else if (e.key === 'End') n = v[v.length - 1];
      if (!n) return;
      e.preventDefault(); ves(n, true);
    });
    function refresca() {
      // si un permís amaga la pestanya activa, passa a la primera visible
      if (!visibles().includes(actiu)) ves(visibles()[0], false, false);
      else sr.refresca();
    }
    ves(actiu, false, false);
    return { ves, refresca, get actiu() { return actiu; } };
  }

  /* ======================================================================
     Zona d'arrossegament magnètica
     Quan un fitxer s'acosta (a menys de 180 px), la zona s'hi inclina una
     mica i s'hi encén una llum; a sobre, creix un 2,5 %. Clic o Intro per
     triar el fitxer amb el selector del sistema.
     ====================================================================== */
  const DISTANCIA = 180, DESPLACAMENT = 10;
  const zones = new Set();
  const esFitxer = dt => !!dt && Array.from(dt.types || []).includes('Files');
  function midaLlegible(b) {
    if (b === 0) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(b) / Math.log(1024)), u.length - 1);
    const v = b / Math.pow(1024, i);
    return (v >= 10 || i === 0 ? Math.round(v) : v.toFixed(1)).toLocaleString('ca') + ' ' + u[i];
  }
  function accepta(f, regles) {
    if (!regles.trim()) return true;
    const nom = f.name.toLowerCase(), tipus = (f.type || '').toLowerCase();
    return regles.split(',').map(r => r.trim().toLowerCase()).some(r =>
      r.startsWith('.') ? nom.endsWith(r) : r.endsWith('/*') ? tipus.startsWith(r.slice(0, -1)) : tipus === r);
  }
  function iconaFitxer(f) {
    const n = f.name.toLowerCase();
    if ((f.type || '').startsWith('image/')) return 'imatge';
    if (f.type === 'application/pdf' || n.endsWith('.pdf')) return 'pdf';
    if (n.endsWith('.csv') || f.type === 'text/csv') return 'taula';
    return 'fitxer';
  }
  /* Import d'una cel·la de CSV a cèntims (enter), sense coma flotant */
  function centims(text) {
    let t = String(text).trim().replace(/["\s€]/g, '');
    if (/,\d{1,2}$/.test(t)) t = t.replace(/\./g, '').replace(',', '.');
    else t = t.replace(/,/g, '');
    const m = /^([-+])?(\d+)(?:\.(\d{1,2}))?$/.exec(t);
    if (!m) return null;
    const c = parseInt(m[2], 10) * 100 + parseInt(((m[3] || '') + '00').slice(0, 2), 10);
    return m[1] === '-' ? -c : c;
  }
  const euros = c => (c < 0 ? '−' : '') + (Math.abs(c) / 100).toLocaleString('ca', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
  async function resumCsv(f) {
    const text = await f.text();
    const linies = text.split(/\r?\n/).filter(l => l.trim());
    if (!linies.length) return 'El fitxer és buit.';
    const cap = linies[0];
    const sep = [';', '\t', ','].sort((a, b) => cap.split(b).length - cap.split(a).length)[0];
    const columnes = cap.split(sep).map(c => c.trim().replace(/^"|"$/g, ''));
    const files = linies.length - 1;
    const iImport = columnes.findIndex(c => /import|amount|quantitat/i.test(c));
    let suma = 0, errors = 0;
    if (iImport >= 0) linies.slice(1).forEach(l => { const v = centims(l.split(sep)[iImport] || ''); if (v === null) errors++; else suma += v; });
    const nomSep = sep === ';' ? 'punt i coma' : sep === ',' ? 'coma' : 'tabulador';
    let r = files + (files === 1 ? ' moviment' : ' moviments') + ' · ' + columnes.length + ' columnes · separador: ' + nomSep + '.';
    if (iImport >= 0) r += ' Suma de «' + columnes[iImport] + '»: ' + euros(suma) + (errors ? ' (' + errors + ' imports il·legibles)' : '') + '.';
    return r;
  }
  function prepara() {
    if (prepara.fet) return; prepara.fet = true;
    // Evita que el navegador obri el fitxer si es deixa anar fora d'una zona
    addEventListener('dragover', e => {
      if (!esFitxer(e.dataTransfer)) return;
      e.preventDefault();
      if (!e.target.closest || !e.target.closest('.zona-magnetica')) e.dataTransfer.dropEffect = 'none';
      zones.forEach(z => z._imant(e));
    });
    addEventListener('drop', e => { if (esFitxer(e.dataTransfer)) e.preventDefault(); zones.forEach(z => z._reposa()); });
    addEventListener('dragend', () => zones.forEach(z => z._reposa()));
    document.addEventListener('dragleave', e => { if (!e.relatedTarget) zones.forEach(z => z._reposa()); });
  }

  function zonaMagnetica(zona, opcions) {
    const o = Object.assign({
      accepta: zona.dataset.accepta || '',
      midaMax: +zona.dataset.midaMax || 10 * 1024 * 1024,
      tipus: zona.dataset.tipus || 'PDF o imatge',
      titol: zona.dataset.titol || 'Arrossega un fitxer aquí',
      csv: zona.hasAttribute('data-csv'),
      enCanvi: null
    }, opcions);
    prepara();
    const input = el('input');
    input.type = 'file'; input.hidden = true; input.accept = o.accepta;
    const llum = el('div', 'zm-llum'); llum.setAttribute('aria-hidden', 'true');
    const cos = el('div', 'zm-cos');
    const error = el('p', 'zm-error'); error.setAttribute('aria-live', 'polite'); error.hidden = true;
    zona.append(input, llum, cos, error);
    const idAjuda = 'zm-ajuda-' + Math.random().toString(36).slice(2, 8);
    let fitxer = null, aProp = false, aSobre = false;

    const tx = molla(280, 24, 0.65), ty = molla(280, 24, 0.65), ts = molla(280, 24, 0.65), lx = molla(280, 24, 0.65), ly = molla(280, 24, 0.65);
    ts.x = ts.meta = 1;
    let raf = 0, ultim = null;
    function pas(t) {
      if (ultim === null) ultim = t;
      let dt = Math.min(1 / 30, (t - ultim) / 1000); ultim = t;
      for (; dt > 0; dt -= 1 / 240) { const h = Math.min(dt, 1 / 240); [tx, ty, ts, lx, ly].forEach(m => avanca(m, h)); }
      zona.style.transform = 'translate3d(' + tx.x.toFixed(2) + 'px,' + ty.x.toFixed(2) + 'px,0) scale(' + ts.x.toFixed(4) + ')';
      llum.style.transform = 'translate3d(' + lx.x.toFixed(1) + 'px,' + ly.x.toFixed(1) + 'px,0)';
      if ([tx, ty, lx, ly].every(quieta) && Math.abs(ts.x - ts.meta) < 0.0005 && Math.abs(ts.v) < 0.001) { raf = 0; ultim = null; return; }
      raf = requestAnimationFrame(pas);
    }
    const anda = () => { if (!raf) raf = requestAnimationFrame(pas); };

    function titol() { return aSobre ? 'Deixa\'l anar per afegir-lo' : aProp ? 'Acosta\'l una mica més' : o.titol; }
    function marca() {
      zona.classList.toggle('a-prop', aProp);
      zona.classList.toggle('a-sobre', aSobre);
      const t = cos.querySelector('.zm-titol');
      if (t && !fitxer) t.textContent = titol();
    }
    function pintaBuit() {
      cos.innerHTML =
        '<button class="zm-tria" type="button" aria-describedby="' + idAjuda + '">' +
          '<span class="zm-rajola">' + icona('puja') + '</span>' +
          '<span class="zm-titol">' + esc(titol()) + '</span>' +
          '<span class="zm-ajuda" id="' + idAjuda + '">o fes clic per triar-lo · ' + esc(o.tipus) + ' · fins a ' + midaLlegible(o.midaMax) + '</span>' +
        '</button>';
      cos.querySelector('.zm-tria').addEventListener('click', () => input.click());
    }
    async function pintaFitxer() {
      cos.innerHTML =
        '<div class="zm-fitxer">' +
          '<span class="zm-rajola">' + icona(iconaFitxer(fitxer)) + '</span>' +
          '<span class="zm-llest">' + icona('fet') + 'Llest per pujar</span>' +
          '<span class="zm-nom">' + esc(fitxer.name) + '</span>' +
          '<span class="zm-mida">' + midaLlegible(fitxer.size) + '</span>' +
          (o.csv ? '<p class="zm-resum" aria-live="polite">Llegint el fitxer…</p>' : '') +
          '<div class="zm-accions">' +
            '<button class="boto boto-petit" type="button" data-zm="substitueix">' + icona('puja') + 'Substitueix</button>' +
            '<button class="boto boto-petit" type="button" data-zm="treu" aria-label="Treu ' + esc(fitxer.name) + '">' + icona('creu') + 'Treu</button>' +
          '</div>' +
        '</div>';
      cos.querySelector('[data-zm="substitueix"]').addEventListener('click', () => input.click());
      cos.querySelector('[data-zm="treu"]').addEventListener('click', () => { buida(); cos.querySelector('.zm-tria').focus(); });
      if (o.csv) {
        const r = cos.querySelector('.zm-resum');
        try { r.textContent = await resumCsv(fitxer); } catch (e) { r.textContent = 'No s\'ha pogut llegir el fitxer.'; }
      }
    }
    function mostraError(t) { error.textContent = t; error.hidden = !t; zona.classList.toggle('te-error', !!t); }
    function rep(llista) {
      const f = llista[0];
      if (!f) return;
      if (!accepta(f, o.accepta)) { fitxer = null; pintaBuit(); mostraError('«' + f.name + '» no és d\'un tipus admès (' + o.tipus + ').'); if (o.enCanvi) o.enCanvi(null); return; }
      if (f.size > o.midaMax) { fitxer = null; pintaBuit(); mostraError('«' + f.name + '» passa de ' + midaLlegible(o.midaMax) + '.'); if (o.enCanvi) o.enCanvi(null); return; }
      fitxer = f; mostraError('');
      zona.classList.add('te-fitxer');
      pintaFitxer();
      anuncia('Fitxer afegit: ' + f.name);
      if (o.enCanvi) o.enCanvi(f);
    }
    function buida() {
      fitxer = null; zona.classList.remove('te-fitxer'); mostraError(''); pintaBuit();
      anuncia('Fitxer tret'); if (o.enCanvi) o.enCanvi(null);
    }
    zona._reposa = () => {
      tx.meta = ty.meta = lx.meta = ly.meta = 0; ts.meta = 1;
      aProp = aSobre = false; marca(); anda();
    };
    zona._imant = e => {
      if (!zona.getClientRects().length) return;
      const r = zona.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const dx = Math.max(Math.abs(e.clientX - cx) - r.width / 2, 0);
      const dy = Math.max(Math.abs(e.clientY - cy) - r.height / 2, 0);
      const prop = Math.max(0, 1 - Math.hypot(dx, dy) / DISTANCIA);
      if (prop === 0) { if (aProp) zona._reposa(); return; }
      const sobreZona = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
      const ddx = e.clientX - cx, ddy = e.clientY - cy, d = Math.max(Math.hypot(ddx, ddy), 1);
      const desp = sobreZona ? 0 : prop * DESPLACAMENT;
      const quiet = redueix();
      tx.meta = quiet ? 0 : (ddx / d) * desp;
      ty.meta = quiet ? 0 : (ddy / d) * desp;
      ts.meta = quiet ? 1 : sobreZona ? 1.025 : 1.01;
      lx.meta = quiet ? 0 : ddx; ly.meta = quiet ? 0 : ddy;
      if (!aProp) { lx.x = lx.meta; ly.x = ly.meta; }
      aProp = true; aSobre = sobreZona; marca(); anda();
    };
    zona.addEventListener('dragover', e => { if (!esFitxer(e.dataTransfer)) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; });
    zona.addEventListener('drop', e => { e.preventDefault(); e.stopPropagation(); rep(Array.from(e.dataTransfer.files)); zona._reposa(); });
    input.addEventListener('change', () => { rep(Array.from(input.files || [])); input.value = ''; });
    zones.add(zona);
    pintaBuit();
    return { get fitxer() { return fitxer; }, buida };
  }

  /* ======================================================================
     Impressora de justificants
     Etapes: «processant» (esperant el proveïdor), «imprimint» (el paper surt
     a batzegades) i «complet». En producció, «complet» només arriba amb la
     notificació verificada del proveïdor, mai pel navegador (CLAUDE.md).
     ====================================================================== */
  const AVANC = ['translateY(calc(-100% + 2px))', 'translateY(-91%)', 'translateY(-91%)', 'translateY(-81%)', 'translateY(-81%)',
    'translateY(-70%)', 'translateY(-70%)', 'translateY(-58%)', 'translateY(-58%)', 'translateY(-45%)', 'translateY(-45%)',
    'translateY(-32%)', 'translateY(-32%)', 'translateY(-20%)', 'translateY(-20%)', 'translateY(-10%)', 'translateY(-10%)',
    'translateY(-3%)', 'translateY(-3%)', 'translateY(0%)'];
  const TEMPS = [0, .075, .105, .18, .21, .285, .315, .39, .42, .495, .525, .6, .63, .705, .735, .81, .84, .915, .945, 1];
  function vora(paper) {
    // vora inferior en ona (en lloc de les dents d'un tiquet): 22 ones de 4 px
    const punts = [], n = 88, ones = 22, a = 2.2;
    for (let i = 0; i <= n; i++) {
      const x = 100 - (i * 100) / n;
      const yy = (a + a * Math.cos((i / n) * ones * 2 * Math.PI)).toFixed(2);
      punts.push(x.toFixed(3) + '% calc(100% - ' + yy + 'px)');
    }
    paper.style.clipPath = 'polygon(0 0, 100% 0, ' + punts.join(', ') + ')';
  }
  function impressora(arrel) {
    if (arrel._imp) return arrel._imp;
    const paper = arrel.querySelector('.imp-paper');
    const mov = arrel.querySelector('.imp-moviment');
    const etiqueta = arrel.querySelector('.imp-etiqueta');
    const indicador = arrel.querySelector('.imp-indicador');
    const textos = {
      processant: arrel.dataset.textProcessant || 'Esperant la confirmació del proveïdor',
      imprimint: arrel.dataset.textImprimint || 'Imprimint el justificant',
      complet: arrel.dataset.textComplet || 'Pagament confirmat'
    };
    vora(paper);
    indicador.innerHTML = '<span class="treballant">' + icona('carrega', 'gira') + '</span>';
    etiqueta.innerHTML = '<span>' + esc(textos.processant) + '</span>';
    etiqueta.setAttribute('role', 'status');
    etiqueta.setAttribute('aria-live', 'polite');
    let etapaActual = null, anim = null;

    function relleva(caixa, html, dy) {
      const mou = !redueix();
      const velles = Array.from(caixa.children);
      const nova = el('span', null, html);
      if (caixa === indicador) nova.className = html.indexOf('icona-svg gira') > -1 ? 'treballant' : 'fet';
      caixa.append(nova);
      velles.forEach(v => { const a = v.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: mou ? (dy ? 'translateY(-' + dy + 'px)' : 'scale(.96)') : 'none' }], { duration: 160, easing: CORBA, fill: 'forwards' }); a.onfinish = () => v.remove(); setTimeout(() => v.remove(), 400); });
      nova.animate([{ opacity: 0, transform: mou ? (dy ? 'translateY(' + dy + 'px)' : 'scale(.94)') : 'none' }, { opacity: 1, transform: 'none' }], { duration: 180, easing: CORBA });
    }
    function etapa(nom) {
      if (nom === etapaActual) return;
      const abans = etapaActual;
      etapaActual = nom;
      arrel.dataset.etapa = nom;
      const mou = !redueix();
      if (abans !== null) relleva(etiqueta, esc(textos[nom]), 4);
      const fet = nom === 'complet';
      const eraFet = indicador.querySelector('.fet');
      if (fet && !eraFet) relleva(indicador, icona('fet'), 0);
      if (!fet && eraFet) relleva(indicador, icona('carrega', 'gira'), 0);
      paper.setAttribute('aria-hidden', String(!fet));
      if (anim) anim.cancel();
      if (nom === 'processant') {
        mov.style.opacity = '0';
        mov.style.transform = mou ? 'translateY(calc(-100% + 2px))' : 'none';
      } else if (nom === 'imprimint') {
        mov.style.opacity = '1';
        if (mou) {
          anim = mov.animate(AVANC.map((t, i) => ({ transform: t, offset: TEMPS[i] })), { duration: 1750, easing: 'linear', fill: 'forwards' });
          anim.onfinish = () => { mov.style.transform = 'none'; };
        } else mov.style.transform = 'none';
      } else {
        mov.style.opacity = '1'; mov.style.transform = 'none';
        anuncia(textos.complet + '. El justificant està a punt.');
      }
    }
    /* Seqüència completa: processa (fins que el proveïdor confirma), imprimeix i acaba */
    async function imprimeix(opcions) {
      opcions = opcions || {};
      if (!opcions.directe) { etapa('processant'); await espera(opcions.ms || 1500); }
      etapa('imprimint');
      await espera(redueix() ? 200 : 1800);
      etapa('complet');
    }
    etapa(arrel.dataset.etapa || 'processant');
    const api = { etapa, imprimeix, get etapa_actual() { return etapaActual; } };
    arrel._imp = api;
    return api;
  }

  window.CRIS = { tema, anuncia, botoDinamic, subratllat, pestanyes, zonaMagnetica, impressora, icona, espera, euros, centims, redueix };
})();
