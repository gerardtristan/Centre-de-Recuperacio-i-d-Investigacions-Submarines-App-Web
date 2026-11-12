# 075 — Respostes del responsable a l'informe de la tanda del 10/11/2026

- **Data:** 10/11/2026
- **Estat:** Acceptada pel responsable del projecte el 10/11/2026 (respostes escrites a les preguntes restants de l'informe de la tanda del 10/11/2026). Els punts pendents de la junta, la secretaria, el tresorer, l'assessor i la gestoria continuen oberts a [pendents.md](pendents.md#preguntes-de-la-tanda-del-10-11).
- **Abast:** precisa RN-M01-76 i RN-M01-79 de la [074](074-respostes-del-responsable-al-diagnostic-del-10-11.md), RN-M01-80 (Q-088), la matriu inicial de la [059](059-rols-i-permisos-editables.md) per a una acció nova i les tasques T-M01-14, T-M01-16, T-M01-17 i T-M01-27. Regles i criteris al [pla](../planning.md#M01-addenda-075).

## Context
L'informe de la tanda del 10/11/2026 va deixar preguntes obertes, una de seguretat i una contradicció amb la 074: el suplement vençut només el podia anul·lar qui tenia P8 amb edició (el tresorer), però la 074 (punt 4) diu que l'anul·la la secretaria.

## Decisió
1. **Canvi del correu d'entrada amb reautenticació.** Per demanar el canvi, el soci torna a escriure la contrasenya i, si el compte té TOTP, el codi, a la mateixa petició (`accounts.require_recent_auth` amb `minutes=0`, T-M00-05). Si falla, no s'envia cap enllaç i l'intent compta per a V-01.
2. **Sessions en confirmar el correu nou.** Es tanquen totes les altres sessions del compte i es conserva la sessió des de la qual es confirma (si n'hi ha cap del mateix compte).
3. **CI.** Push de la branca amb el nom `feature/night-2026-11-10` només per executar el CI. Cap PR ni fusió, i cap push d'`integracio/2026-11-09`.
4. **Suplement vençut: l'anul·la la secretaria.** Acció nova a la matriu de la 059, **P7a «Anul·lar el suplement vençut d'un canvi de tipus»**, assignada inicialment **només a la secretaria** (com la resta de la matriu, l'administrador la pot reassignar des de l'app). Qui té P8 amb edició (el tresorer) la continua podent fer per `fees.cancel_fee`. Només serveix per a aquest suplement i només quan ha vençut; no eixampla cap altre permís econòmic (P8 no canvia). El registre d'activitat guarda qui l'executa i el motiu.
5. **«Crea una baixa» exigeix també P4.** Per obrir la pantalla i veure el nom del soci cal P7 amb edició **i** P4. Si el President ha de poder crear baixes sense accedir a fitxes queda com a pregunta pendent.
6. **Resum de la baixa.** Només qui té P10 veu la llista de quotes sense pagar (venciment i import). La resta veu que s'aplicaran les conseqüències de la baixa (RN-M01-20), sense imports ni detall.
7. **Sessions tancades per intents (RN-M01-80).** S'accepta de moment amb el risc documentat: qui conegui el correu d'un soci li pot tancar totes les sessions amb cinc intents fallits. Es reconsidera quan es decideixi la [P-52](pendents.md).
8. **Secret TOTP de prova.** El servidor rebutja el secret de prova de `seed_demo_data` quan `DEBUG` no està actiu, amb una comprovació barata (comparació directa), sense sobrecarregar la validació.
9. **Menors sense correu del representant.** Tasca de recollida de dades amb la secretaria: obtenir el correu (i el telèfon) del representant dels menors donats d'alta abans de la `members/0017`. No s'implementa res més ara.
10. **Casella «He comprovat el document».** Pendent de la junta. Provisionalment, la casella no es mostra a qui no pot veure el document (sense C2) i aquesta comprovació no es dona per feta: sense C2, una alta que la necessita no es pot aprovar.
11. **Preguntes de la secretaria, el tresorer, l'assessor i la gestoria:** passen a [pendents.md](pendents.md#preguntes-de-la-tanda-del-10-11), agrupades per responsable.

## Conseqüències
- **Pla:** [addenda de la 075](../planning.md#M01-addenda-075), amb RN-M01-81 a RN-M01-84, CA-M01-81 a CA-M01-86 i la tasca T-M01-44 (recollida de dades del representant).
- **Matriu de la 059:** P7a, nova, inicialment només a la secretaria.
- **pendents.md:** secció «Preguntes de la tanda del 10/11/2026»; nota a la P-52.

## Fonts
- Respostes escrites del responsable del projecte, 10/11/2026, a l'informe de la tanda del 10/11/2026 (fora del repositori).
- [074](074-respostes-del-responsable-al-diagnostic-del-10-11.md), [059](059-rols-i-permisos-editables.md), [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md) (Q-088) i [pendents.md](pendents.md) (P-52).
