# Diari de construcció

Un sol diari de com es construeix la plataforma, tasca a tasca, per preparar després explicacions, presentacions i un documental. Cada tasca acabada té una entrada d'una pàgina com a màxim (unes 50 línies), feta amb la [plantilla](_plantilla.md).

Una tasca no està acabada sense la seva entrada (definició de «fet» del `CLAUDE.md`). L'entrada va en un commit propi, just després del de la tasca, amb el missatge «Diari: T-XXX-NN». L'estat del CI l'afegeix el responsable quan el coneix; mentrestant, hi diu [A comprovar].

L'entrada no copia el pla: resumeix i enllaça la secció de [`docs/planning.md`](../planning.md) i les decisions de [`docs/decisions/`](../decisions/). Els termes tècnics en anglès s'expliquen a l'apartat «Termes nous» de l'entrada on surten per primera vegada.

## Regles de contingut
S'apliquen a tot: entrades, captures, fragments de codi i vídeos.

- Cap dada real de socis ni de cap persona. Només dades inventades.
- Cap secret: ni claus, ni contrasenyes, ni secrets o QR del doble factor, ni codis de recuperació.
- Cap captura amb persones reals, ni amb noms, correus o fotos reals.
- Cap detall que ajudi un atacant: ni la ruta de l'administració, ni els llindars i temps de bloqueig, ni noms d'usuari d'administració reals, ni claus.
- Cap captura de terminal que mostri contrasenyes generades.

## Captures
- **Només per a tasques amb pantalla.** Si la tasca no en té, l'evidència és la sortida de les proves i fragments de codi.
- **Què es captura:** només la finestra del navegador, amb un perfil net (sense extensions, marcadors ni historial a la vista), sense la barra de tasques ni notificacions.
- **Pantalles d'administració:** sense la barra d'adreces, perquè no se'n vegi la ruta.
- **No es capturen mai:** l'alta del doble factor (QR i clau) ni la pantalla dels codis de recuperació.
- **Dades:** les de l'ordre de dades inventades (vegeu el `README.md` del projecte), amb una base de dades local i separada.
- **Carpeta i nom:** `captures/AAAA-MM-DD_HHMM_tasca_pantalla.png`, per exemple `2026-11-02_1255_T-M01-09_llista-carrecs.png`. L'hora és la de la captura (Europa/Madrid).
- **Mida:** uns 300 KB i 1.600 px d'amplada com a màxim. El CI rebutja qualsevol fitxer de `captures/` de més de 500 KB.
- **Peu**, sota la imatge:
  `*02/11/2026 12:55 (Europa/Madrid) · local, dades inventades (llavor 1954) · commit 8cb6dc5*`

## Vídeos
Fora de Git (el `.gitignore` ja exclou `*.mp4`). A l'entrada hi va el nom del fitxer, on és guardat, la durada i el commit que mostra.

## Fragments de codi i sortida de proves
Com a text, mai com a imatge, amb una línia a sobre: `apps/core/charges.py · commit 8cb6dc5 · 02/11/2026`. Curts: només el que s'explica.

La sortida de proves porta el commit, la data d'execució i l'entorn: `Sortida de proves · commit 8cb6dc5 · executada el 02/11/2026 en local (PostgreSQL 16)`. Només la línia de resum (`692 passed`), sense temps ni rutes locals.

## Índex
«Proves» és el total de proves de la suite en aquell commit (comptades amb `pytest --collect-only`), no les proves noves.

| Tasca | Títol | Data i hora | Commit | Proves | CI |
|---|---|---|---|---|---|
| [T-M01-03](T-M01-03.md) | Esquelet del projecte | 01/11/2026 00:04 | ee78d4b, 82332bc | 10 | verd (#1) |
| [T-M01-04](T-M01-04.md) | Persona i model d'usuari | 01/11/2026 00:16 | a2babcd | 66 | vermell (#2) |
| [T-M01-05](T-M01-05.md) | Entrades separades i doble factor (en part) | 01/11/2026 00:31 | d5abc59 | 133 | vermell (#3) |
| [T-M01-06](T-M01-06.md) | Rols i permisos | 01/11/2026 07:28 | 3b9f947 | 561 | verd (#4) |
| [T-M01-07](T-M01-07.md) | Registre d'activitat immutable | 02/11/2026 00:33 | a8ff23d | 616 | vermell (#5) |
| [T-M01-08](T-M01-08.md) | Textos legals i consentiments | 02/11/2026 12:24 | f14ed71 | 636 | verd (#6) |
| [T-M01-09](T-M01-09.md) | Càrrec, pagament i departament | 02/11/2026 12:55 | 8cb6dc5 | 692 | verd (#7) |
| [T-M01-09b](T-M01-09b.md) | Preparada per traduir-se | 02/11/2026 13:46 | b7996f5, 18b8a73, b6cc76c, 4dc17e2 | 707 | verd (#8) |
| [T-M01-10](T-M01-10.md) | Correu mínim i fitxers privats | 03/11/2026 00:40 | ba27a1e, d70f300, d67ea3b, 93279ff | 795 | verd (a 4c8c143) |
| [T-M01-02](T-M01-02.md) | Wireframes que falten del mòdul 01 (en part: falta la revisió) | 03/11/2026 02:13 | 994c200, 28402de, 961117b, f37c182, 2d86a35, 2ab6390, a1c9adc, ac5aaf6, 6c0ba5b, 9b69ff9 | 795 | verd (PR #4, dues execucions) |

### Eines
Peces que no són tasques del pla però que fan servir les entrades (per exemple, per fer captures).

| Eina | Títol | Data i hora | Commit | Proves | CI |
|---|---|---|---|---|---|
| [seed_demo_data](eina-seed_demo_data.md) | Dades inventades per a captures | 02/11/2026 14:07 | e69793d, 942b752 | 722 | verd (#9) |
| [CI i gitleaks](eina-ci-i-gitleaks.md) | Cerca de secrets: excepció i permisos | 02/11/2026 23:43 | 383c0df, 2a381b5, d1dab31 | 722 | verd (#14 a la PR #4; el push de d7cd1c3 també en verd) |
