# 074 — Respostes del responsable al diagnòstic del 10/11/2026 (T-M01-16, 17, 36, 41, 27 i T-M00-05)

- **Data:** 10/11/2026
- **Estat:** Acceptada pel responsable del projecte el 10/11/2026 (respostes escrites a les preguntes 1–22 del diagnòstic de la tanda del 10/11/2026). Les validacions externes de la secció «Validacions que continuen pendents» es mantenen.
- **Abast:** precisa P-M01-B, P-M01-C, L-M01-04, RN-M01-20, RN-M01-56, RN-M01-57, la Q-088 de la [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md) i les tasques T-M01-16, T-M01-17, T-M01-22, T-M01-27, T-M01-36, T-M01-41 i T-M00-05. **No** valida cap dels set punts oberts de la [073](073-pas-de-ple-dret-a-simpatitzant-a-la-renovacio.md). Regles i criteris al [pla](../planning.md#M01-addenda-074).

## Context
Abans d'executar la tanda del 10/11/2026, el diagnòstic va llistar què faltava perquè cada tasca quedés completa i ho va agrupar en 22 preguntes. Aquesta decisió en recull les respostes. Les decisions ja acceptades (072, 073) no s'editen.

## Decisió

### Canvi de tipus i baixa (T-M01-17)
1. **Baixa amb data futura: es permet.** Validar una baixa amb una data efectiva posterior a avui la deixa programada: l'estat del soci, el carnet i les quotes no canvien fins aquell dia. Una tasca diària de la cua l'aplica el dia efectiu (estat «baixa», carnet revocat, correu de confirmació i quotes de la RN-M01-20). La tasca és idempotent: tornar-la a executar no duplica cap efecte.
2. **L-M01-04: es rebutja el canvi a ple dret mentre hi hagi una quota pendent.** Resolta pel responsable del projecte; es manté l'advertència [A validar: junta] que tenia el pla.
3. **El suplement es crea en aprovar el canvi, no en demanar-lo.** Corregeix el pas 2 de P-M01-B, que deia que el sistema crea el càrrec del suplement en demanar-lo. L'efecte econòmic definitiu el valida el tresorer.
4. **Termini del suplement: una setmana.** El suplement aprovat venç una setmana després de l'aprovació. Si passa sense pagar-se, **l'anul·la la secretaria** (anul·lació amb motiu, mai esborrat); **no s'anul·la automàticament**. El termini és configurable si el model d'ajustos actual ho permet sense la pantalla d'ajustos (T-AJ-02); si no, és una sola constant documentada. L'efecte econòmic definitiu el valida el tresorer.
5. **Canvi de tipus pendent i baixa:** en validar una baixa, un canvi de tipus pendent de la mateixa persona es cancel·la amb el motiu «baixa».
6. **Ruta i President (Q-052):** es confirma `/gestio/socis/sollicituds/`. El President no rep P4 de consulta (hi resol amb P3a i P7).
7. **Motius per rebutjar una baixa (resta de la P-50):** text lliure obligatori. Resolt pel responsable del projecte; es manté l'advertència de la junta que tenia el pla.
8. **Textos de la baixa i de l'explicació prèvia al soci:** els textos provisionals queden validats per a la revisió del responsable. El text definitiu continua pendent de la secretaria (Q-058).

### Llicència declarada pel soci (T-M01-36)
9. **On es desa:** a `expires_on`, amb una marca «declarada». Mentre la secretaria no l'ha confirmada, la marca impedeix que el 02 o qualsevol altre consumidor la tracti com a llicència vigent.
10. **Confirmació:** individual, a la fitxa, acceptant o corregint la data. La llista de confirmació en bloc no mostra les caducitats declarades.
11. **Validació de la data:** la mateixa que la fitxa actual.
12. **Enllaç a la confirmació en bloc:** a l'inici de l'administració, amb P19 i P4, comprovats també al servidor.

### Formulari d'alta i comunicacions d'un menor (T-M01-41)
13. **Menor de 14 anys:** totes les comunicacions van al representant (rebut, avisos, rebuig, aprovació, recordatoris, canvis i baixa).
14. **Menor de 14 a 17 anys sense correu propi:** les comunicacions van al representant.
15. **Consentiments d'un menor de 14 a 17 anys:** els dona el mateix menor. És la posició del responsable del projecte; abans de posar-ho en servei l'ha de confirmar l'assessor de protecció de dades.
16. **Textos del butlletí i de les imatges:** els redacta l'equip com a textos provisionals marcats [A validar] i els valida el responsable. No serveixen per recollir consentiments reals ni són textos definitius.

### Àrea del soci (T-M01-16)
17. **Canvi de correu des del perfil:** enllaç de confirmació a l'adreça nova; el correu d'entrada canvia quan es confirma; l'adreça antiga rep un avís; límits de la RN-M01-58 i registre d'activitat. Aquesta resposta autoritza tocar el `login` del compte personal per fer-ho.
18. **Rebut (CA-M01-12):** la T-M01-16 queda «feta en part» fins que existeixi la T-M05b-07. El criteri no es redueix ni es mou.

### Reautenticació i esborrat (T-M00-05, T-M01-22)
19. **Q-088:** «compte bloquejat» cobreix el bloqueig per intents i la desactivació. La T-M00-05 tanca les sessions del compte quan queda bloquejat per intents. La part de la desactivació és de la peça corresponent de la T-M01-22 i no es fa a la T-M00-05.
20. **Peça mínima de la T-M01-22:** autoritzada. Model de sol·licitud d'esborrat a `core`, amb migració, i pantalla `/socis/perfil/esborrar`, que només crea la sol·licitud (sense pantalla de gestió, anonimització ni exportació).

### Dades de prova i CI
21. **TOTP de prova fix a les dades de prova (T-M01-27):** permès amb un secret públic i inequívocament de prova, marcat `gitleaks:allow` si cal, només quan l'ordre de dades de prova pot executar-se (desenvolupament amb `DEBUG`). Fora d'aquest entorn no funciona.
22. **CI:** push de la branca `night/2026-11-10` a `origin` només per executar el CI. Cap PR ni fusió, i cap push d'`integracio/2026-11-09`.

## Validacions que continuen pendents
- **Tresorer:** l'efecte econòmic definitiu dels punts 3 i 4 (quan es crea el suplement i el termini d'una setmana).
- **Junta:** L-M01-04 i els motius de rebuig de la P-50 queden resolts pel responsable del projecte, amb l'advertència de la junta que ja hi havia.
- **Assessor de protecció de dades:** consentiments d'un menor de 14 a 17 anys (punt 15; Q-016), abans de posar-ho en servei.
- **Textos definitius:** baixa i explicació prèvia (secretaria, Q-058); butlletí i imatges (gestoria i assessor, Q-16 i Q-028).
- **073:** els set punts oberts continuen sense aprovar.

## Conseqüències
- **Pla:** [addenda de la 074](../planning.md#M01-addenda-074), amb les regles RN-M01-74 a RN-M01-80 i els criteris CA-M01-72 a CA-M01-80; remissions des de les files de les tasques afectades i des de P-M01-B.
- **pendents.md:** P-50 (motius de rebuig) resolta pel responsable del projecte.

## Fonts
- Respostes escrites del responsable del projecte, 10/11/2026, a les preguntes 1–22 del diagnòstic de la tanda del 10/11/2026 (fora del repositori).
- [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md), [073](073-pas-de-ple-dret-a-simpatitzant-a-la-renovacio.md), [064](064-una-baixa-es-pot-rebutjar-amb-motiu.md), [pendents.md](pendents.md) (P-50) i P-M01-B, P-M01-C, L-M01-04, RN-M01-20, RN-M01-56 i RN-M01-57 del [pla](../planning.md).
