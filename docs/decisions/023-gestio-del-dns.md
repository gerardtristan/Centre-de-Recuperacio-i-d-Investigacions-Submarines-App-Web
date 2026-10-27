# 023 — Gestió del DNS i de les credencials dels dominis

- **Data:** 27/10/2026
- **Estat:** Proposada (recomanació de l'equip). Dada confirmada: el club controla el DNS de cris1954.cat i de cris.es. Qui té l'accés concret està [A validar].

## Context
La [019](019-domini-i-correu.md) deixava [A validar] el control del DNS (P-25). L'equip ha confirmat que el control és del club, però no se sap quina persona té les credencials del registrador i de la zona DNS.

## Alternatives
- Mantenir el DNS de cris1954.cat al registrador actual: cada canvi s'hi fa a mà, i no permet Cloudflare Pages amb el domini arrel de manera senzilla ni Email Routing.
- Delegar el DNS de cris1954.cat a Cloudflare (pla gratuït): una sola consola per a la web, l'API, el correu (SPF, DKIM, DMARC) i els àlies futurs.

## Recomanació
1. **Delegar el DNS de cris1954.cat a Cloudflare**, després de fer inventari dels registres actuals.
2. **No tocar el DNS de cris.es**: només rep les respostes a cris@cris.es.
3. Guardar les credencials del registrador i de Cloudflare en un **gestor de contrasenyes compartit amb dues persones** del club, amb doble factor.
4. Anotar a la documentació interna (fora del repositori) qui té l'accés [A validar].

## Conseqüències
- Si es perd l'accés al registrador, es pot perdre el domini: el gestor compartit amb dues persones evita la dependència d'una sola.
- Cloudflare passa a ser crític per a la resolució del domini; la via de sortida és exportar la zona i tornar a apuntar els servidors de noms.

## Fonts
- Confirmació del control del DNS comunicada per l'equip el 27/10/2026
- [019](019-domini-i-correu.md); `docs/arquitectura-integracions.md`, §2 i §7
