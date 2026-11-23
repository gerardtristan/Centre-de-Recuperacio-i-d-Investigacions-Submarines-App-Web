# T-M03-22 i T-M09-13 (nucli) · Permisos dels ajustos del material i avisos del 09

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 11:38 | a38cce77 | 3 noves (plantilles i permisos del 03) | [A comprovar] |

**En tres línies:** el responsable de material ja pot editar quants dies després d'una activitat surt l'avís de material no retornat, i el tresorer, el cost d'ús de cada tipus de material, que toca diners i porta data d'entrada en vigor i avís. El tresorer veu l'apartat «Material» dels ajustos. El nucli té també les dues plantilles de correu que el 09 necessita: marge baix i reobertura d'un període.

## Què s'ha fet
- `apps/core/permission_catalog.py`: `settings.edit.equipment.unreturned_after_days` (VC-29, responsable de material), `settings.edit.equipment.usage_rates` (VC-28, tresorer, `touches_money`) i el tresorer a `settings.section.equipment` (lectura).
- `core/0071_equipment_settings_more_permissions`: les cel·les a la matriu amb una versió nova (060), reversible.
- `apps/core/mail.py` i `templates/emails/`: `avis-marge-baix` (CA-M09-12) i `avis-reobertura-periode` (S-M09-13), amb prioritat de confirmació.

## Decisions i perquè
- Les plantilles només porten el nom de l'activitat, el període, els imports i el motiu: cap dada personal. El text és provisional [A validar: tresorer].
- Feina començada pel carril A2 (aturat pel límit setmanal) i acabada pel PILOT; migració renumerada de la 0070 a la 0071 després de la #457 i de la T-M03-17a.

## Problemes trobats
- Cap.

## Com se sap que funciona
`apps/core/tests/test_mail_templates_09.py` i `apps/core/tests/test_permissions_03.py`; `makemigrations --check` net.
