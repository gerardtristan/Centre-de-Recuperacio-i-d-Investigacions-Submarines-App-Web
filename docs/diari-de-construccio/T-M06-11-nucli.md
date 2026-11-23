# T-M06-11 (nucli) · Plantilles dels avisos de venciment de llicència

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 23/11/2026 13:09 | 43e3360b | 1 nova (plantilles) | [A comprovar] |

**En tres línies:** el nucli ja té les dues plantilles de correu que el 06 necessita per avisar dels venciments: l'avís al titular d'una llicència que caduca i el resum diari per a qui tramita. El resum només porta recomptes per data i categoria, sense noms ni enllaç. La mida del lot d'enviament és una variable d'entorn tècnica.

## Què s'ha fet
- `apps/core/mail.py`: prioritats de `avis-venciment-llicencia` i `resum-venciments-llicencies`.
- `templates/emails/`: les quatre plantilles (assumpte i cos).
- `LICENCE_REMINDER_BATCH_SIZE` (VC-43, 50 per defecte) a `config/settings/base.py` i `.env.example`: el pla la deixa a l'entorn perquè és d'informàtica.

## Decisions i perquè
- P-501 (irreversible: RGPD i seguretat): el resum va sense noms ni enllaç a l'administració, perquè la ruta d'administració és configurable i l'adreça de notificació pot no ser del club. És l'opció més conservadora fins que respongui la secretaria.
- Feina del carril A5; el PILOT l'obre al torn del nucli, després de la #462 (que també tocava `mail.py`).

## Problemes trobats
- Cap.

## Com se sap que funciona
`apps/core/tests/test_licences_core.py` (les dues plantilles es renderitzen amb el context esperat).
