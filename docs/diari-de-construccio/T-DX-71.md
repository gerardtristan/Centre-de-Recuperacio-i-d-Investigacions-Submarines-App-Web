# T-DX-71 · La prova del carnet sense connexió que fallava de tant en tant (P-315)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 19/11/2026 12:46 | 44691474 | 1 nova, sense navegador; `test_pwa_079.py`: 3 passen, 3 vegades seguides | [A comprovar] |

**En tres línies:** `test_081_copy_expires_after_30_days_or_the_valid_until_and_refreshes_online` fallava alguna vegada al CI, també a master, amb el missatge de consola «Failed to load resource: net::ERR_INTERNET_DISCONNECTED». En local passava sempre. El propietari va demanar trobar la manera de reproduir-la i arreglar-la, mai saltant la prova (19/11/2026). Era un error de la prova: els errors esperats sense connexió només es treien d'una de les dues llistes on poden arribar.

## Què s'ha fet
- `apps/core/tests/e2e/conftest.py`: `PageChecks.ignore(*textos)`. Els errors que contenen aquests textos no compten a `final_problems()`, ni a `problems` ni a la consola, encara que arribin després de cridar-ho.
- `apps/core/tests/e2e/test_pwa_079.py`: les dues proves sense connexió criden `page_checks.ignore(*OFFLINE_ERRORS)`. Abans, en acabar, filtraven només `page_checks.problems`.
- La prova que reprodueix l'error: `test_offline_errors_are_ignored_also_when_chromium_logs_them_to_the_console`. Fa servir un `PageChecks` amb una pàgina falsa, sense navegador, i li passa el missatge de consola que sortia al CI.
- `docs/decisions/pendents.md`: la P-315 passa a resoltes.

## Decisions i perquè
- **La causa.** Des de la #61 (16/11/2026), `PageChecks` guarda els missatges de consola «Failed to load resource» en una llista a part, i els resol en acabar la prova: així pot descartar els de les consultes automàtiques que troben la sessió tancada. La prova de la 081 es va escriure abans i filtrava només `problems`. Quan Chromium escrivia el missatge a la consola mentre la prova era sense connexió, cosa que depèn de com caigui el temps, el missatge sobrevivia i la prova fallava en acabar. Lliga amb el que diu la P-315: dos missatges de consola i cap petició fallida de la pàgina.
- **Una prova sense navegador.** Amb el navegador, que Chromium escrigui el missatge o no depèn del temps, i una prova així fallaria només de vegades, com l'original. Amb la pàgina falsa, el missatge arriba sempre.
- **`ignore` al moment de llegir els problemes, no un filtre a la llista.** També cobreix els missatges que arriben entre el filtre i el final de la prova, una altra porta a fallades de tant en tant.
- **No hi ha cap recurs que falti a la còpia del carnet.** La P-315 suggeria buscar un fitxer que el service worker no desés. No cal: els missatges són els de les peticions que el navegador fa sense connexió, i la prova ja els esperava.
- **Cap prova saltada, sense reintents ni temps més llargs.**

## Problemes trobats
- Cap més.

## Com se sap que funciona
- La prova nova falla sense l'arreglo (`'PageChecks' object has no attribute 'ignore'`) i passa amb l'arreglo.
- `test_pwa_079.py`: 3 passen, 3 vegades seguides en local.
- Ruff net.

## Comprovació §15.5
- Cap pantalla tocada: no calen captures ni axe.
