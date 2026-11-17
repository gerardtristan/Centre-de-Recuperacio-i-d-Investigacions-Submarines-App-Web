# Línia cronològica del projecte

Genera una sola pàgina HTML, sense dependències ni peticions de xarxa, amb l'estat real de cada tasca de `docs/planning.md`: fases i mòduls, dependències, decisions, pendents, «què desbloqueja», camí crític i l'estat del CI. El workflow `.github/workflows/linia-cronologica.yml` la regenera sola, la **xifra** i la publica a GitHub Pages.

## Què llegeix
Només llegeix; no modifica cap fitxer del repositori.

- `docs/planning.md` (sencer), `docs/decisions/` i `docs/decisions/pendents.md`, `docs/preguntes-externes.md`, `docs/diari-de-construccio/`.
- El `git log` de la branca, per al commit i la data de cada tasca.
- Les execucions del workflow «CI» (número i resultat), per l'API de GitHub.

El que no troba surt com a «no trobat». Les regles amb què llegeix l'estat, el vincle entre preguntes i tasques i l'estimació del cost són a la vista «Fonts i criteris» de la mateixa pàgina.

## Quan s'actualitza
- Cada vegada que acaba el CI d'un push (a `master` o a `feature/**`).
- Amb un push a `master` que toqui el pla, les decisions, el diari o aquest generador.
- Un cop al dia, com a xarxa de seguretat, i a mà des de la pestanya «Actions» («Run workflow»).

Es llegeix la branca amb el commit més recent entre `master` i `feature/*`. Per fixar-ne una, crea la variable del repositori `TIMELINE_BRANCH` (Settings → Secrets and variables → Actions → Variables).

## Configuració, una sola vegada
1. **Contrasenya.** Settings → Secrets and variables → Actions → *New repository secret*, amb el nom `TIMELINE_PASSPHRASE`. Ha de tenir **16 caràcters o més**; si no, el workflow s'atura i no publica res. Una frase de quatre o cinc paraules a l'atzar va bé. No s'escriu mai al repositori, ni en cap issue, ni en cap missatge.
2. **Pages.** Settings → Pages → *Source*: **GitHub Actions**. Amb un repositori privat, GitHub Pages demana un pla de pagament (GitHub Pro o superior).
3. Executa el workflow a mà la primera vegada. L'adreça de la pàgina surt al resum de l'execució.

Per canviar la contrasenya, canvia el secret i torna a executar el workflow: la versió anterior deixa de servir-se.

## Seguretat: què protegeix i què no
- **Una pàgina de GitHub Pages és pública.** El que la protegeix és el xifratge: les dades viatgen xifrades amb AES-256-GCM i una clau derivada de la contrasenya (PBKDF2-HMAC-SHA256, 600.000 iteracions), i es desxifren al navegador. Sense la contrasenya, el fitxer publicat no conté cap text del pla.
- **Queda a la vista** el títol, el logotip i el codi de la pàgina (aquesta plantilla).
- Qui es baixi el fitxer pot provar contrasenyes sense límit al seu ordinador. Per això no val un PIN: quatre xifres cauen en menys d'una hora. La protecció és tan forta com la contrasenya.
- «Recorda-la en aquest dispositiu» desa la contrasenya al navegador (`localStorage`); «Bloqueja» l'esborra. No ho marquis en un ordinador compartit.
- Les dades són el pla intern (preguntes obertes, riscos, decisions). No hi ha dades de socis, i no n'hi ha d'haver mai.
- El workflow executa sempre el generador de la branca per defecte. De les altres branques només en llegeix el text.

## Ús en local
Sense xifrar, per obrir-la amb doble clic. El fitxer és al `.gitignore`: **no es puja mai sense xifrar**.

```
pip install pillow
python tools/linia-cronologica/generate.py --ref origin/master --out CRIS_linia_cronologica.html
```

Opcions: `--ref` (branca o commit que es llegeix; per defecte, `HEAD`), `--runs` (execucions del CI en JSON Lines; sense, el CI de GitHub surt com a «no trobat») i `--encrypt` (demana `TIMELINE_PASSPHRASE` a l'entorn i `pip install cryptography`).

## Fitxers
- `generate.py`: lectura de les fonts, vincles, estimació i xifratge.
- `template.html`: la pàgina (HTML, CSS i JavaScript en línia).
