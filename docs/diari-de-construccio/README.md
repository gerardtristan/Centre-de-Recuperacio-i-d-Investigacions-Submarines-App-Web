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
