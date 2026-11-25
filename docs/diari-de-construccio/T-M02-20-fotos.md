# T-M02-20 (fotos) · Fotos d'una sortida de medi ambient, apagades fins a la P-41

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 25/11/2026 04:47 | (vegeu la PR) | 11 noves i 1 e2e | [A comprovar] |

**En tres línies:** la peça per guardar les fotos d'una sortida de medi ambient ja hi és, però és apagada. Quan la junta respongui la P-41 (autor, permís i drets d'imatge), es podrà encendre. Mentrestant ningú no pot pujar ni obrir cap foto.

## Què s'ha fet
- **Nucli:** un tipus nou de fitxer privat, `environment_photo` (`core/0083`), xifrat a l'aplicació amb la clau que ja hi havia (cap clau ni dependència nova), sense adreça pública, que només obre un compte d'administrador amb AC14 (la junta, consulta). Qui l'ha pujat no l'obre amb el compte personal.
- **02:** `EnvironmentalPhoto` i l'interruptor `activities.environment_photos_enabled`, apagat (`activities/0026`), i `environment_photos.py`: pujar (JPEG o PNG, sense metadades, amb l'autor i el permís d'ús obligatoris), retirar amb motiu sense esborrar, i marcar-ne una de publicable només si compleix CA-M02-22.
- **Pantalla:** la secció «Fotos de la sortida» a «Resultats ambientals», només amb l'interruptor encès.

## Decisions i perquè
- **L'opció més conservadora (D2):** la P-41 és oberta i afecta imatges de persones: ús intern, mai públiques, i l'interruptor apagat. Cap permís per encendre'l des de l'app: l'apartat d'ajustos del 02 és «Cons.» per a tothom.
- **Una foto retirada no s'obre:** el guarda d'accés del tipus mira l'interruptor i que la foto sigui activa, també per l'adreça directa.
- **Marcar publicable no publica res** (RN-M02-23): només deixa escrit que compleix CA-M02-22, per quan el 07 en pugui publicar. No té pantalla.

## Com se sap que funciona
- Apagat: no es puja ni s'obre res, tampoc per l'adreça directa.
- La foto es desa xifrada, sense la geolocalització ni el comentari, sense adreça signada i amb registre. Sense autor o sense permís d'ús, es rebutja.
- CA-M02-22: amb persones i sense consentiment, no es pot marcar com a publicable; amb consentiment, sí.
- AC14 puja i retira; la junta veu la foto però no la puja ni la retira; el tresorer no l'obre. Retirada, la fila i el fitxer es queden i ningú no l'obre.

## Evidències
- Sortida de proves · executada el 25/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q apps/activities apps/core/tests/test_files.py apps/core/tests/test_encrypted_files.py apps/core/tests/test_verificacio_t_m00_07.py apps/accounts/tests/test_navigation_subpages.py
  1030 passed
  $ pytest -m e2e apps/core/tests/e2e/test_activitats_fotos_medi_ambient.py apps/core/tests/e2e/test_activitats_medi_ambient.py
  2 passed
  ```
- Captures a 1280, 390 i 320 px (clar i fosc) a `.e2e-captures/`, mirades. El camp de fitxer surt en anglès («Choose File»), com a la T-DX-120.
