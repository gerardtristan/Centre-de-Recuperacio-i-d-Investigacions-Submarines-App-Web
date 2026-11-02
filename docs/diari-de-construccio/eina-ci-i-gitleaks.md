# Eina · CI i cerca de secrets amb gitleaks

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 02/11/2026 23:29 – 23:43 | 383c0df (excepció), 2a381b5 (diari), d1dab31 (permís) | 722 (sense canvis) | [A comprovar] |

No és una tasca del pla: és el manteniment del pipeline que revisa cada canvi.

**En tres línies:** el pipeline va sortir vermell tres vegades, però no per cap filtració. La cerca de secrets confonia una contrasenya inventada de les proves amb una de real. Ara aquest valor exacte és l'única excepció, i la feina de secrets té el permís que li faltava per revisar les PR.

## Què s'ha fet
- `.gitleaks.toml` a l'arrel: les regles per defecte de gitleaks i una sola excepció, a la regla `generic-api-key`, per al valor exacte `contrasenya-de-proves-1954`.
- Regla al `CLAUDE.md`: les proves fan servir sempre aquest valor; qualsevol altre valor que sembli un secret porta `gitleaks:allow` i un comentari. Cap secret real en proves.
- A `.github/workflows/ci.yml`, la feina `secrets` té permís de lectura de pull requests, a més de lectura del contingut. Els permisos globals i les altres feines no canvien.

## Decisions i perquè
- **Una excepció pel valor, no per fitxer ni per ruta:** si algun dia hi hagués un secret real al mateix fitxer, gitleaks el continuaria trobant.
- **Excepció dins la regla, no global:** l'acció `gitleaks/gitleaks-action@v2` fa servir gitleaks 8.24.3, que no té les llistes globals `[[allowlists]]` ni el camp `targetRules`, que són de la 8.25.0. El format `[[rules.allowlists]]` dins la regla funciona a la 8.24.3 i a les versions posteriors. No canvia ni l'expressió ni la descripció de la regla per defecte.
- **Sense `.gitleaksignore`:** l'excepció hauria de cobrir els tres avisos; només s'afegirien avisos concrets si no els cobrís.
- **El permís, només a la feina que el necessita:** la resta del pipeline continua només amb lectura del contingut.

## Problemes trobats
- Execucions #2, #3 i #5 en vermell: la feina `secrets` (regla `generic-api-key`) marcava la contrasenya inventada de les proves a tres llocs de dos commits antics (a2babcd i d5abc59). La feina de proves no tenia errors. Detall a la [T-M01-04](T-M01-04.md), la [T-M01-05](T-M01-05.md) i la [T-M01-07](T-M01-07.md).
- No es va poder provar gitleaks en local. Que l'excepció funcioni es va deduir del codi de la 8.24.3, no d'una execució.
- En un push, l'acció normalment només revisa els commits nous, i per això un verd no demostrava que l'excepció cobrís els commits antics. Per comprovar-ho es va obrir una PR en esborrany (#4) cap a `master`, on l'acció revisa tots els commits de la PR.
- A la PR, l'execució #12 va fallar a la feina `secrets` per un error de permisos (403, «Resource not accessible by integration»): l'acció demana la llista de commits de la PR a l'API, i el workflow només tenia permís de lectura del contingut. Corregit a d1dab31.

## Com se sap que funciona
- Execució #12 (PR #4): proves i captures en verd; `secrets` va fallar pel permís, no per cap filtració.
- Pendent: execució nova de la PR #4 amb el permís corregit. [A comprovar]

## Evidències
- `.github/workflows/ci.yml · commit d1dab31 · 02/11/2026`
  ```yaml
  secrets:
    runs-on: ubuntu-latest
    # A les PR, l'acció de gitleaks llegeix la llista de commits de la PR per l'API.
    permissions:
      contents: read
      pull-requests: read
  ```

## Termes nous
- **Pipeline o CI** (*continuous integration*, integració contínua): les comprovacions automàtiques que GitHub fa a cada canvi.
- **gitleaks**: eina que busca secrets (contrasenyes, claus) als commits.
- **Fals positiu**: avís d'un problema que no ho és.
- **Excepció** (*allowlist*): llista del que l'eina ha de deixar passar.
- **PR en esborrany** (*draft pull request*): proposta de canvi que no es pot fusionar fins que deixa de ser esborrany.
