# 041 — Web instal·lable i avisos dins l'app i per correu, sense push

- **Data:** 27/10/2026
- **Estat:** Acceptada com a camí per defecte. La renúncia a les botigues d'apps, pendent de la junta amb el pressupost ([037](037-pressupost-amb-web-installable.md)). Origen: decisió 0011 del repositori anterior (històric).

## Context
- CLAUDE.md i el context v4 ja diuen «primer web (PWA); app nativa més endavant».
- Una petició anterior demanava publicar l'app a App Store i Play Store.
- Amb la [035](035-dades-nomes-dins-ue.md) hi ha dos conflictes: les notificacions push d'iPhone i Android passen sempre per Apple i Google (EUA), i les botigues tracten el compte del club i les descàrregues.

## Alternatives
1. Botigues i notificacions push: incompleix la 035.
2. Push «buida» (sense contingut, «Tens novetats al C.R.I.S.»): Apple i Google continuen rebent l'identificador del dispositiu.
3. **Web instal·lable (PWA) amb avisos dins l'app i per correu.**

## Decisió
- L'app es publica com a **web instal·lable** des de cris1954.cat, sense botigues.
- Els avisos arriben **dins l'app** (safata d'avisos) i **per correu** amb un servei dins la UE.
- **Cap notificació push.** La push «buida» només s'accepta si el responsable del projecte l'aprova per escrit.

## Conseqüències
- No cal compte de desenvolupador d'Apple ni de Google ni número D-U-N-S.
- A iPhone s'instal·la des de Safari amb «Afegeix a la pantalla d'inici»: cal una pàgina d'ajuda amb captures.
- El service worker guarda el carnet amb QR i la pantalla «sense connexió».
- Els avisos urgents (per exemple, una sortida anul·lada) també surten per correu.

## Fonts
- Decisió comunicada per l'equip el 27/10/2026
- `docs/proveidors-i-dades-ue.md`, conflictes C1 i C2
