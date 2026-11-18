/* Service worker de la web instal·lable (T-M01-21; decisió 041). Es serveix des de
   /service-worker.js (apps/core/views/pwa.py) perquè el seu abast sigui tot el lloc.

   Privacitat (dispositius compartits): només guarda la pàgina «El meu carnet» del compte
   personal i els estils, per veure el carnet sense connexió. Cap altra pàgina, ni de
   l'administració ni de cap altra persona. La còpia del carnet s'esborra en entrar o sortir
   per qualsevol de les dues entrades i quan el servidor ja no la dona (sessió caducada,
   sense soci). El control d'accés el fa el servidor; això només decideix què es guarda al
   navegador. Les rutes són les de Django: una prova comprova que coincideixen.

   Caducitat de la còpia (decisió 081, punt 15; RN-M01-101): es mostra com a màxim DIES_COPIA
   dies després de desar-la i mai després del dia «vàlid fins al» del carnet, si en té: la còpia
   no allarga la vigència real. Una còpia caducada (o d'una versió anterior, sense les dades de
   caducitat) s'esborra i no es mostra. La pàgina en línia la torna a desar a cada visita, i
   carnet-copia.js la recarrega quan torna la connexió. */
'use strict';

var CARNET = '/socis/carnet/';             // members:card
var INICI = '/';                           // start_url del manifest
var MEMORIA_CARNET = 'cris-carnet-v1';
var MEMORIA_ESTILS = 'cris-estils-v1';
var DIES_COPIA = 30;                       // decisió 081, punt 15 (cards.OFFLINE_COPY_DAYS)
var MS_DIA = 24 * 60 * 60 * 1000;
var CAP_DESADA = 'X-Cris-Copia-Desada';    // hora del dispositiu en desar-la (ms)
var CAP_VALID_FINS = 'X-Cris-Valid-Fins';  // «vàlid fins al» del carnet (AAAA-MM-DD) o buit
var VALID_FINS = /data-valid-fins="(\d{4}-\d{2}-\d{2})"/;
// Estils i les fonts que fa servir fonts.css (079, A-28; T-M01-45): sense connexió, el carnet es
// veu amb la lletra correcta. Són fitxers públics, sense cap dada. Des de la T-DX-61, també els estils i el
// JavaScript del carnet en 3D (disposició, segell, avatar, pista, gir i impressió).
var ESTILS = ['/static/css/fonts.css', '/static/css/tokens.css', '/static/css/comptes.css', '/static/js/tema.js',
  '/static/fonts/barlow-condensed/BarlowCondensed-SemiBold.woff2', '/static/fonts/barlow-condensed/BarlowCondensed-Bold.woff2',
  '/static/fonts/source-sans-3/SourceSans3-Regular.ttf.woff2', '/static/fonts/source-sans-3/SourceSans3-Semibold.ttf.woff2',
  '/static/fonts/source-sans-3/SourceSans3-Bold.ttf.woff2',
  '/static/fonts/jetbrains-mono/JetBrainsMono-Regular.woff2', '/static/fonts/jetbrains-mono/JetBrainsMono-Medium.woff2',
  '/static/js/carnet-copia.js',
  '/static/css/disposicio.css', '/static/css/autentico.css', '/static/css/monograma.css', '/static/css/baliza.css',
  '/static/css/carnet.css', '/static/js/carnet.js', '/static/js/imprimeix.js'];
var ENTRAR_O_SORTIR = /\/(entrar|sortir)\//;  // les dues entrades, també la d'administració
// Marca de l'avís que la pàgina del carnet porta amagat; la còpia el mostra.
var AVIS_AMAGAT = ' data-sense-connexio hidden';
var AVIS_VISIBLE = ' data-sense-connexio';

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(MEMORIA_ESTILS)
      .then(function (memoria) { return memoria.addAll(ESTILS); })
      .catch(function () { /* sense estils desats, el carnet es veu igualment */ })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  // Memòries d'una versió anterior d'aquest fitxer: fora.
  event.waitUntil(
    caches.keys().then(function (noms) {
      return Promise.all(noms.filter(function (nom) {
        return nom !== MEMORIA_CARNET && nom !== MEMORIA_ESTILS;
      }).map(function (nom) { return caches.delete(nom); }));
    }).then(function () { return self.clients.claim(); })
  );
});

function esborraCarnet() {
  return caches.delete(MEMORIA_CARNET);
}

function desaCarnet(resposta) {
  return resposta.text().then(function (html) {
    var copia = html.replace(AVIS_AMAGAT, AVIS_VISIBLE);
    // Sense l'avís «pot no estar al dia» no es desa res: millor cap còpia que una que sembli actual.
    if (copia === html) return esborraCarnet();
    var fins = VALID_FINS.exec(html);
    var capcaleres = { 'Content-Type': 'text/html; charset=utf-8' };
    capcaleres[CAP_DESADA] = String(Date.now());
    capcaleres[CAP_VALID_FINS] = fins ? fins[1] : '';
    return caches.open(MEMORIA_CARNET).then(function (memoria) {
      return memoria.put(CARNET, new Response(copia, { headers: capcaleres }));
    });
  });
}

// Cert si la còpia ja no es pot mostrar: massa antiga o passat el «vàlid fins al».
function copiaCaducada(copia, ara) {
  var desada = Number(copia.headers.get(CAP_DESADA));
  if (!desada || ara - desada > DIES_COPIA * MS_DIA) return true;
  var fins = copia.headers.get(CAP_VALID_FINS);
  if (fins) {
    var parts = fins.split('-');
    // L'endemà del «vàlid fins al», a les 00:00 del dispositiu.
    var final = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]) + 1).getTime();
    if (ara >= final) return true;
  }
  return false;
}

function copiaDelCarnet() {
  return caches.open(MEMORIA_CARNET)
    .then(function (memoria) { return memoria.match(CARNET); })
    .then(function (copia) {
      if (!copia) return Response.error();
      if (copiaCaducada(copia, Date.now())) {
        return esborraCarnet().then(function () { return Response.error(); });
      }
      return copia;
    });
}

self.addEventListener('fetch', function (event) {
  var peticio = event.request;
  var url = new URL(peticio.url);
  if (url.origin !== self.location.origin) return;

  if (peticio.method !== 'GET') {
    // Entrar o sortir: el carnet d'aquest dispositiu era d'una altra sessió.
    if (ENTRAR_O_SORTIR.test(url.pathname)) event.waitUntil(esborraCarnet());
    return;
  }

  if (ESTILS.indexOf(url.pathname) !== -1) {
    event.respondWith(fetch(peticio).catch(function () {
      return caches.match(url.pathname).then(function (r) { return r || Response.error(); });
    }));
    return;
  }

  if (peticio.mode !== 'navigate') return;

  if (url.pathname === CARNET) {
    event.respondWith(fetch(peticio).then(function (resposta) {
      if (resposta.ok && resposta.type === 'basic' && !resposta.redirected) {
        event.waitUntil(desaCarnet(resposta.clone()));
      } else if (resposta.status < 500) {
        // Redirecció a l'entrada (estat 0, «opaqueredirect»), 401 o 404: ja no és seu.
        event.waitUntil(esborraCarnet());
      }
      return resposta;
    }, copiaDelCarnet));
    return;
  }

  // L'app instal·lada s'obre a l'inici: sense connexió, hi surt el carnet desat, si n'hi ha.
  if (url.pathname === INICI) {
    event.respondWith(fetch(peticio).catch(copiaDelCarnet));
  }
});
