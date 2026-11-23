# T-M09A-06 i T-M09A-15 (nucli) · Plantilles dels avisos dels ajuts

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 13:56 | (vegeu la PR) | 5 noves | [A comprovar] |

**En tres línies:** quatre plantilles de correu noves per als avisos dels ajuts: el tancament d'una convocatòria, la resposta prevista, la justificació i els requeriments d'esmena. Les fan servir els avisos de la cua de l'app d'ajuts (T-M09A-06 i T-M09A-15). Text provisional.

## Què s'ha fet
- `templates/emails/avis-ajut-tancament`, `avis-ajut-resposta`, `avis-ajut-justificacio` i `avis-ajut-requeriment` (assumpte i text) i la seva prioritat («recordatori») a `apps/core/mail.py`.

## Decisions i perquè
- Només l'organisme, la convocatòria, les dates i la referència de la sol·licitud; mai la descripció del requeriment, que és text lliure.
- Una sola plantilla per als requeriments: sense `days`, el primer avís (immediat); amb `days`, el de 7 i 2 dies abans.

## Problemes trobats
Cap.

## Com se sap que funciona
`apps/core/tests/test_mail_templates_09a.py` (les quatre plantilles, i el requeriment amb i sense dies) i `apps/core/tests/test_mail.py` (la llista de prioritats coincideix amb la carpeta).

## Termes nous
Cap.
