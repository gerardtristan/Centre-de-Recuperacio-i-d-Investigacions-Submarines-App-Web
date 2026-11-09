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
| [T-M01-02](T-M01-02.md) | Wireframes que falten del mòdul 01 (revisió aprovada el 03/11/2026) | 03/11/2026 02:13 | 994c200, 28402de, 961117b, f37c182, 2d86a35, 2ab6390, a1c9adc, ac5aaf6, 6c0ba5b, 9b69ff9 | 795 | verd (PR #4, dues execucions; també a 47d9b84; tancament a aca95cc) |
| [T-M01-05](T-M01-05.md) | Comptes: correu, doble factor personal, restabliment i càrrega (segona tanda, en part) | 03/11/2026 17:05 | 3e4b1ae, be08bed, cd80f9e, c5dc59f, 5b75d08, 43673af | 880 | verd (PR #4, sis feines, dues execucions; confirmat pel responsable) |
| [T-M01-05](T-M01-05.md) | Comptes: demanar els enllaços i restablir un altre compte (tercera tanda; pendent de revisió) | 03/11/2026 18:14 | a8fe478, cf5e7f3, 0802245, 2b671cd | 926 | verd (0bfcee8; confirmat pel responsable) |
| [T-M01-05](T-M01-05.md) | Comptes: revisió al navegador i correcció dels formularis dels enllaços (E1; en part) | 03/11/2026 21:15 | ad5d53d | 946 | verd (942b80a; confirmat pel responsable) |
| [T-M01-05](T-M01-05.md) | Comptes: ajustos de la decisió 066 (reenviament i límit d'origen; en part) | 04/11/2026 01:40 | fc49620, b56dc5e | 951 | verd (e316e40; confirmat pel responsable) |
| [T-M01-05](T-M01-05.md) | Comptes: reenviament múltiple, proves i comprovació al navegador (en part) | 04/11/2026 02:11 | 4e62231 | 956 | verd (e316e40, dues execucions; confirmat pel responsable) |
| [T-M01-05](T-M01-05.md) | Comptes: tancament, **Feta** (aprovada pel responsable el 04/11/2026; no tanca la T-M01-38, la T-M00-06, la T-M01-39 ni les comprovacions de desplegament) | 04/11/2026 02:31 | e316e40 (referència) | 956 | verd (e316e40; confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01 (en part: `avatar_seed` aturat; pendent de revisió) | 04/11/2026 03:03 | 19ba4c7, a501793 | 1014 | verd (d3d1064, dues execucions; confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: llavor de l'avatar, decisions pendents i neteja de les proves (segona tanda; pendent de revisió) | 04/11/2026 12:21 | a0e111e, ba89284 | 1017 | verd a 28cd481, que la inclou (confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: format de la llavor, prova de la quota i readmissió (tercera tanda; pendent de revisió) | 04/11/2026 12:35 | 0ca680a, a34f5a1 | 1025 | verd (28cd481, dues execucions; confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: readmissió i llavor de Cluber (quarta tanda, només documentació; pendent de revisió) | 04/11/2026 12:40 | 48d9ed6 | 1025 | verd (7b2c586, dues execucions; confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: decisió de la readmissió i pregunta de les quotes (cinquena tanda, només documentació; pendent de revisió) | 04/11/2026 12:48 | 1c87847 | 1025 | verd (b1b2ebc, dues execucions; confirmat pel responsable) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: pregunta de les quotes per a la junta (sisena tanda, només documentació; pendent de revisió) | 04/11/2026 12:52 | 1e0b2f4 | 1025 | sense CI propi; inclòs a a446ece, verd (referència) |
| [T-M01-11](T-M01-11.md) | Models del mòdul 01: tancament, **Feta** (aprovada pel responsable el 04/11/2026 dins l'abast actual; no tanca la P-54, les garanties de la quota, les transicions, la llavor de la importació ni les excepcions d'anonimització) | 04/11/2026 13:15 | a446ece (referència) i el commit del tancament | 1025 | verd a a446ece (referència); el commit del tancament: [A comprovar] |
| [T-M01-12](T-M01-12.md) | Estats del soci i transicions (en part: sense la part del carnet de CA-M01-09; pendent de revisió) | 04/11/2026 13:45 | f4624d0, 8653602 | 1102 | verd a 1647d72 (proves, secrets i captures, dues execucions; confirmat pel responsable) |
| [T-M01-12](T-M01-12.md) | Estats del soci i transicions: revisió (data de la readmissió, compte no actiu, bloqueig; segona tanda, en part; pendent de revisió) | 04/11/2026 14:13 | 812517f, 5447517, 0b5fa5d, 289277d | 1113 | verd a 081868b (confirmat pel responsable) |
| [T-M01-12](T-M01-12.md) | Estats del soci i transicions: tancament, **Feta** (aprovada pel responsable el 04/11/2026 dins l'abast actual; no tanca la validesa del carnet, l'historial dels importats, les proves de l'intent als punts d'entrada, el canvi de tipus ni la P-54) | 04/11/2026 | 081868b (referència) i el commit del tancament | 1113 | verd a 081868b (referència); el commit del tancament: [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber, fase de prova (en part: lector CSV i previsualització sense escriptures; sense `ImportBatch`, CA-20.8 ni pantalla; pendent de revisió) | 04/11/2026 17:50 | f7465a6, 5e078c7, 0389010, c710080 | 1188 | [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber, fase de prova: revisió (dades mínimes en memòria, resum segur, números molt llargs; segona tanda, en part; pendent de revisió) | 04/11/2026 18:06 | f879b95, 3cd9662, 57560df | 1200 | [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber, fase de prova: número d'un soci d'una persona anonimitzada (tercera tanda, en part; pendent de revisió) | 04/11/2026 18:14 | 66348b5, ce7bbaa | 1208 | verd a #89 (PR #4; comprovat visualment pel responsable); associació amb bf1eef6 [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: nucli compartit del lot i de la línia, procedència i CA-20.8 (quarta tanda, en part; pendent de revisió) | 04/11/2026 18:49 | bbdfb96, 3d64cff | 1282 | vermell a #92 (5add66b) i #93 (PR #4): dates dels lots de prova |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: correcció de la cronologia dels lots de prova (CI #92 i #93; en part) | 04/11/2026 | 366c1d4 | 1291 | verd a #94 (push de 26fae2f) i #95 (PR #4); comprovat visualment pel responsable |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: autorevisió ampliada (NUL, restriccions exactes i restauració de migracions; autorevisió; en part) | 04/11/2026 19:42 | 18a393b, 7adbf6d, b3f1276 | 1292 | verd a #96 (push de 6a18a75) i #97 (PR #4); comprovat visualment pel responsable |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: correccions de la segona revisió d'IA (capçaleres, llargades i conflicte; segona revisió d'IA; en part) | 04/11/2026 20:17 | 1874e4a, e878958 | 1310 | verd a #98 (push de e4c3620) i #99 (PR #4); comprovat visualment pel responsable |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: pantalla de la prova (P18, CSRF, pujada en memòria i registre; en part; comprovació manual pendent) | 04/11/2026 21:37 | 9e7f1c7, df37c51 | 1339 | [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber: validació funcional de la pantalla pel responsable (en part: falten el CI del codi actual i la porta de la checklist; Q-23 pendent) | 05/11/2026 | 29d8073 (referència) i el commit d'aquesta entrada | 1339 | [A comprovar] |
| [T-M01-24](T-M01-24.md) | Importació de Cluber, fase de prova: tancament, **Feta** (aprovada pel responsable el 05/11/2026; no tanca Q-23, les equivalències ni la T-M01-25) | 05/11/2026 | af5aaa5 (referència) i el commit del tancament | 1343 | verd a #104 i #105 sobre af5aaa5 (confirmat pel responsable); el commit del tancament: [A comprovar] |
| [T-M01-38](T-M01-38.md) | Plantilla base, fulls d'estil i pantalles de comptes (Feta el 05/11/2026; pantalles validades pel responsable) | 05/11/2026 01:54 | [sense commit] | 1382 | [A comprovar] |
| [T-M01-07b](T-M01-07b.md) | Consulta del registre d'activitat (Feta el 05/11/2026; pantalla validada pel responsable; pendents: lector de pantalla, altres navegadors i CI) | 05/11/2026 16:10 | [sense commit] | 1427 | [A comprovar] |
| [T-M01-13](T-M01-13.md) | Formulari «Fer-se soci» i alta presencial (**Feta**; P-57, P-61, P-33 i P-56 obertes) | 09/11/2026 | 7fa8b97 | 1572 | verd: #112 i #113 (710b15f) |

### Eines
Peces que no són tasques del pla però que fan servir les entrades (per exemple, per fer captures).

| Eina | Títol | Data i hora | Commit | Proves | CI |
|---|---|---|---|---|---|
| [seed_demo_data](eina-seed_demo_data.md) | Dades inventades per a captures | 02/11/2026 14:07 | e69793d, 942b752 | 722 | verd (#9) |
| [CI i gitleaks](eina-ci-i-gitleaks.md) | Cerca de secrets: excepció i permisos | 02/11/2026 23:43 | 383c0df, 2a381b5, d1dab31 | 722 | verd (#14 a la PR #4; el push de d7cd1c3 també en verd) |
