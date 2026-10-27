# 021 — Persones no sòcies com a convidades

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-23)

## Context
La [018](018-perfil-comptes-i-rols.md) estableix un perfil únic per persona i descriu comptes de soci i d'administrador. Alumnes, assistents i persones amb llicència d'un dia participen amb dades mínimes (funcionalitats §2 i §8.1), però no estava decidit si havien de tenir compte.

## Alternatives
- Compte obligatori per a tothom: més fricció i més dades guardades.
- Sense compte, amb un enllaç segur per a cada inscripció o pagament.

## Decisió
- Les persones no sòcies **no tenen compte d'accés per defecte**. Tenen perfil (dades mínimes i consentiment).
- S'inscriuen i paguen **com a convidades**, amb un **enllaç segur**: d'un sol ús o de durada limitada, lligat a la inscripció o al càrrec, i sense revelar dades d'altres persones.
- El compte és **opcional**: una persona no sòcia en pot crear un (amb les regles dels comptes de soci: correu únic, verificació i recuperació per correu).
- **A incloure a la spec 00** (`specs/00-base-comuna/spec.md`, encara no creada): perfil sense compte, enllaços segurs de convidat (generació, caducitat, revocació, limitació d'intents) i pas opcional de convidat a compte.

## Conseqüències
- Els pagaments de convidats segueixen les mateixes regles (formulari de Stripe, webhook verificat); el càrrec queda lligat al perfil.
- L'enllaç segur és un secret: no es pot registrar sencer als logs i ha de caducar.
- Detecció de duplicats de perfil (per correu o DNI) quan un convidat torna o es fa soci [A validar el criteri a la spec 00].

## Fonts
- Resolució de P-23 comunicada per l'equip el 27/10/2026
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §2 i §8.1
