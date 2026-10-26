# 011 — Monitoratge de disponibilitat i seguiment d'errors

- **Data:** 27/10/2026
- **Estat:** Acceptada; el proveïdor de seguiment d'errors depèn de confirmar la regió de la UE [A validar]

## Context
La checklist demana monitoratge extern (E3), seguiment d'errors amb traça (E2) i registres sense dades personals (E1). Un monitor instal·lat al mateix VPS no avisaria si el servidor cau.

## Alternatives
- Monitor autoallotjat al mateix VPS: descartat.
- UptimeRobot gratuït: només comprova URL públiques; no rep dades de socis.
- Seguiment d'errors: Sentry (pla gratuït amb regió de dades a Frankfurt, segons la documentació de Sentry consultada el 27/10/2026) o GlitchTip (de codi obert, amb instància a la UE segons la seva pàgina de preus; pla gratuït de 1.000 esdeveniments/mes).

## Decisió
- Disponibilitat: UptimeRobot gratuït, avís per correu.
- Errors: GlitchTip o Sentry, **només** si es confirma per escrit que les dades es guarden a la UE [A validar]. La regió de Sentry es tria en crear l'organització i no es pot canviar després.
- Cap dada de socis als registres ni als esdeveniments d'error: s'envien sense dades personals (sense correus, noms, DNI, IBAN ni cos de les peticions).

## Conseqüències
- Segons la documentació de Sentry, algunes dades de comprovació de disponibilitat es poden guardar fora de la regió triada, i l'empresa no té entitat jurídica a la UE per contractar: cal valorar-ho.
- Si cap dels dos compleix, es pot autoallotjar GlitchTip en un altre servidor (més cost i manteniment).

## Fonts
- `docs/checklist-produccio.md`, E1-E4
- Decisió de l'equip del 27/10/2026
