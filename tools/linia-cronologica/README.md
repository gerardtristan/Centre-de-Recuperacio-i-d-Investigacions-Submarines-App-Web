# Línia cronològica del projecte

Genera una sola pàgina HTML, sense dependències ni peticions de xarxa, amb l'estat real de cada tasca de `docs/planning.md`: fases i mòduls, dependències, decisions, pendents, «què desbloqueja», camí crític i l'estat del CI. El workflow `.github/workflows/linia-cronologica.yml` la regenera sola, la **xifra** i la publica a GitHub Pages.

## Què llegeix
Només llegeix; no modifica cap fitxer del repositori.

- `docs/planning.md` (sencer), `docs/decisions/` i `docs/decisions/pendents.md`, `docs/preguntes-externes.md`, `docs/diari-de-construccio/`.
- El `git log` de la branca, per al commit i la data de cada tasca.
- Les execucions del workflow «CI» (número i resultat), per l'API de GitHub.
- `docs/decisions/tauler-preguntes.yml` i els issues oberts del repositori, per al tauler de preguntes.

El que no troba surt com a «no trobat». Les regles amb què llegeix l'estat, el vincle entre preguntes i tasques i l'estimació del cost són a la vista «Fonts i criteris» de la mateixa pàgina.

## Quan s'actualitza
- Cada vegada que acaba el CI d'un push (a `master` o a `feature/**`).
- Amb un push a `master` que toqui el pla, les decisions, el diari o aquest generador.
- Quan s'obre, es tanca o s'edita un issue (una resposta del tauler obre un issue).
- Un cop al dia, com a xarxa de seguretat, i a mà des de la pestanya «Actions» («Run workflow»).

Es llegeix la branca amb el commit més recent entre `master` i `feature/*`. Per fixar-ne una, crea la variable del repositori `TIMELINE_BRANCH` (Settings → Secrets and variables → Actions → Variables).

## Configuració, una sola vegada
1. **Contrasenya.** Settings → Secrets and variables → Actions → *New repository secret*, amb el nom `TIMELINE_PASSPHRASE`. Ha de tenir **16 caràcters o més**; si no, el workflow s'atura i no publica res. Una frase de quatre o cinc paraules a l'atzar va bé. No s'escriu mai al repositori, ni en cap issue, ni en cap missatge.
2. **Pages.** Settings → Pages → *Source*: **GitHub Actions**. Amb un repositori privat, GitHub Pages demana un pla de pagament (GitHub Pro o superior).
3. Executa el workflow a mà la primera vegada. L'adreça de la pàgina surt al resum de l'execució.

Per canviar la contrasenya, canvia el secret i torna a executar el workflow: la versió anterior deixa de servir-se.

## Tauler de preguntes pendents (decisió 086)
Pestanya «Preguntes pendents», amb una **segona contrasenya**. Llista totes les preguntes obertes (pendents, apèndix del pla, tandes i preguntes noves dels fils), amb filtres per qui ha de respondre, mòdul i «només les que aturen una tasca». Les que aturen una tasca surten primer.

- **Opcions i recomanació.** Les opcions A a D i la recomanació de Claude (★) són a `docs/decisions/tauler-preguntes.yml`; les de les tandes de `pendents.md` es llegeixen de la columna «Opcions». Sense entrada, la pregunta només admet resposta lliure. El generador avisa de les entrades que ja no corresponen a cap pregunta oberta.
- **Enviar.** Es prepara una o més respostes (opció, o text propi, o opció i comentari) i «Envia les respostes». El navegador fa un `POST` (formulari, sense credencials) al webhook de Make; l'escenari «CRIS — Tauler de preguntes: resposta → issue» hi afegeix un resum amb la IA de Make, obre un issue amb la marca `<!-- tauler-id: ... -->` i torna el número.
- **Desaparèixer.** Una pregunta enviada desapareix a l'instant en aquest navegador; quan la pàgina es regenera (l'issue nou la dispara), surt a «Enviades, pendents que les incorpori» mentre l'issue és obert. En tancar l'issue, desapareix del tot si la font ja la dona per resolta, o torna a la llista si continua oberta.

### Configuració, una sola vegada
1. Secret `TAULER_PASSPHRASE`: 16 caràcters o més i **diferent** de `TIMELINE_PASSPHRASE` (el workflow s'atura si són iguals).
2. Secret `TAULER_WEBHOOK_URL`: l'adreça del webhook de Make (`https://hook.eu1.make.com/...`). No s'escriu mai al repositori; només viatja dins la part xifrada del tauler. Sense aquest secret, el tauler es pot consultar però no envia.
3. A Make, l'escenari ha d'estar actiu i amb la connexió de GitHub autoritzada.

Si l'adreça del webhook es filtra: crea'n una de nova a Make, assigna-la a l'escenari, canvia el secret i torna a executar el workflow.

## Seguretat: què protegeix i què no
- **Una pàgina de GitHub Pages és pública.** El que la protegeix és el xifratge: les dades viatgen xifrades amb AES-256-GCM i una clau derivada de la contrasenya (PBKDF2-HMAC-SHA256, 600.000 iteracions), i es desxifren al navegador. Sense la contrasenya, el fitxer publicat no conté cap text del pla.
- **Queda a la vista** el títol, el logotip i el codi de la pàgina (aquesta plantilla).
- Qui es baixi el fitxer pot provar contrasenyes sense límit al seu ordinador. Per això no val un PIN: quatre xifres cauen en menys d'una hora. La protecció és tan forta com la contrasenya.
- «Recorda-la en aquest dispositiu» desa la contrasenya al navegador (`localStorage`); «Bloqueja» l'esborra. No ho marquis en un ordinador compartit.
- El tauler es xifra a part, amb la seva contrasenya: qui té la de la línia no el pot obrir ni enviar respostes.
- Les dades són el pla intern (preguntes obertes, riscos, decisions). No hi ha dades de socis, i no n'hi ha d'haver mai.
- El workflow executa sempre el generador de la branca per defecte. De les altres branques només en llegeix el text.

## Ús en local
Sense xifrar, per obrir-la amb doble clic. El fitxer és al `.gitignore`: **no es puja mai sense xifrar**.

```
pip install pillow pyyaml
python tools/linia-cronologica/generate.py --ref origin/master --out CRIS_linia_cronologica.html
```

Opcions: `--ref` (branca o commit que es llegeix; per defecte, `HEAD`), `--runs` (execucions del CI en JSON Lines; sense, el CI de GitHub surt com a «no trobat») `--answers` (issues oberts en JSON, per marcar les preguntes ja respostes) i `--encrypt` (demana `TIMELINE_PASSPHRASE` i, per al tauler, `TAULER_PASSPHRASE` a l'entorn i `pip install cryptography`).

## Fitxers
- `generate.py`: lectura de les fonts, vincles, estimació i xifratge.
- `tauler.py`: dades del tauler de preguntes (opcions, preguntes noves i respostes enviades).
- `template.html`: la pàgina (HTML, CSS i JavaScript en línia).
