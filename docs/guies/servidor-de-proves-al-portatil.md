# Servidor de proves al portàtil

Guia per al propietari ([decisió 099](../decisions/099-servidor-de-proves-al-portatil.md)). Fa córrer la plataforma en un portàtil amb Windows perquè tu i la junta la pugueu provar des de qualsevol lloc: socis, quotes, canvis de dades, tresoreria i pagaments ficticis.

> **Només dades inventades.** Mai no s'hi entren dades reals de socis. Els pagaments, el banc i el correu són ficticis: no es cobra res i cap correu no surt a fora (tots van a la bústia de proves).

## Com funciona

- **Docker Desktop** fa córrer, dins el portàtil, la base de dades, l'aplicació, la cua de tasques, la bústia de proves i una porta amb contrasenya (Caddy).
- **Cloudflare Tunnel** dona una adreça pública amb HTTPS (`https://….trycloudflare.com`) que apunta al portàtil, sense obrir cap port del router. **No cal cap compte**: l'adreça canvia cada vegada que s'arrenca. Si vols una adreça fixa, mira l'apartat [Adreça fixa](#adreça-fixa-opcional).
- Tot va darrere d'una **contrasenya del davant** (usuari `proves`), i els cercadors no l'indexen.
- Només funciona mentre el portàtil està **encès, connectat a internet i sense entrar en repòs**.

Cloudflare és una empresa dels EUA. S'accepta com a excepció només per a proves i amb dades inventades (17/11/2026). Producció, mai.

## Primera vegada (al portàtil que farà de servidor)

1. **Activa la virtualització a la BIOS.** Engega el portàtil prement **F1**; a *Security → Virtualization*, posa *Intel Virtualization Technology* (i VT-d, si hi és) a *Enabled* i desa amb **F10**. Sense això Docker no arrenca. Comprova que el Windows 10 és la versió 22H2 (*Configuració → Sistema → Quant a*) i que està al dia.
2. **Limita la memòria de Docker** (portàtils de 4 GB, com el ThinkPad 11e). Crea amb el Bloc de notes el fitxer `C:\Users\EL_TEU_USUARI\.wslconfig` (tria «Tots els fitxers» perquè no hi afegeixi `.txt`) amb aquest contingut:
   ```
   [wsl2]
   memory=2GB
   processors=2
   swap=2GB
   ```
   El servidor ja està ajustat per gastar poc: un sol procés de l'aplicació i poca memòria per a la base de dades.
3. **Instal·la Docker Desktop** des de <https://www.docker.com/products/docker-desktop/>. Accepta l'opció WSL 2 i reinicia si t'ho demana. Obre'l i espera que digui «Engine running». A *Settings → General*, marca «Start Docker Desktop when you sign in».
4. **Instal·la Git** des de <https://git-scm.com/download/win> (les opcions per defecte ja van bé).
5. **Baixa el repositori.** Obre PowerShell i escriu:
   ```powershell
   git clone https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-INvestigacions-Submarines-App-Web.git C:\cris
   ```
6. **Arrenca'l.** Obre la carpeta `C:\cris\deploy\proves` i fes doble clic a **`arrenca.cmd`**. La primera vegada triga entre 5 i 20 minuts, segons el portàtil. Genera els secrets del portàtil (es desen a `deploy\proves\local\` i mai no van al repositori), carrega les dades inventades i, al final, mostra:
   - l'**adreça per compartir** i la **contrasenya del davant**;
   - els **comptes de l'administració** (`admin-demo`, `secretaria-demo`, `tresorer-demo`, `president-demo` i `instructor-demo`), amb la contrasenya `contrasenya-de-proves-1954`;
   - el **secret del doble factor**, que és el mateix per a tots els comptes. Afegeix-lo a Google Authenticator, Aegis o una app semblant com a «clau de configuració».
7. **Deixa'l encès.** A *Configuració → Sistema → Energia*, posa «Quan estigui connectat, posa en repòs després de» a **Mai**. Si el tens amb la tapa tancada: *Tauler de control → Opcions d'energia → Tria què fa el tancament de la tapa → No fer res* (amb el portàtil endollat).

La finestra mostra també com entrar a la **bústia de proves** (`/bustia/`). Hi arriben tots els correus de la plataforma, i també un correu titulat «Entorn de proves: com s'hi entra» amb els mateixos accessos.

## Què passes a la junta

- L'adreça (`https://….trycloudflare.com`), l'usuari `proves` i la contrasenya del davant.
- Per entrar com un rol de l'administració: el compte, la contrasenya de proves i el secret del doble factor.
- Per entrar com a soci: l'àrea personal (`/entrar/`) amb la mateixa contrasenya de proves i un d'aquests socis inventats: `ple.dret.pagat@example.org` (al corrent, carnet vàlid), `canvi.pendent@example.org` (canvi de tipus pendent), `suplement.pendent@example.org` (suplement per pagar) o `baixa.pendent@example.org` (baixa pendent).

Amb el túnel ràpid, l'adreça canvia cada vegada que s'arrenca el servidor: torna-la a passar.

## Actualitzar a l'última versió

Quan s'hagin fusionat millores a `master`, fes doble clic a **`actualitza.cmd`**. L'script:

1. baixa l'última versió de `master` (`git pull`);
2. reconstrueix l'aplicació;
3. aplica els canvis de la base de dades (les migracions) en arrencar;
4. torna a arrencar el servidor. Si el túnel ja estava obert, l'adreça no canvia.

Les dades inventades i el que hi hagi canviat la junta **es conserven**. Les dades inventades de les funcions noves només apareixen si comences de zero: obre PowerShell a `C:\cris\deploy\proves` i escriu `.\arrenca.cmd -Reinicia` (et demana que escriguis `SI`).

## Aturar-lo

Doble clic a **`atura.cmd`**. L'adreça pública deixa de funcionar. Les dades es conserven fins a la propera arrencada.

## Opcions

| Ordre (a PowerShell, dins `C:\cris\deploy\proves`) | Què fa |
|---|---|
| `.\arrenca.cmd` | Arrenca amb el túnel ràpid de Cloudflare (adreça nova a cada arrencada) |
| `.\arrenca.cmd -Tunel cap` | Sense túnel: només aquest portàtil (`http://localhost:8080`) o Tailscale |
| `.\arrenca.cmd -Tunel fix` | Amb l'adreça fixa del teu compte de Cloudflare |
| `.\arrenca.cmd -Reinicia` | Esborra la base de dades de proves i torna a carregar les dades inventades |
| `.\actualitza.cmd` | Baixa l'última versió i torna a arrencar (accepta `-Tunel` igual) |
| `.\atura.cmd` | Atura el servidor |

### Alternativa privada: Tailscale

Només hi entren els dispositius que convidis, però cadascú ha d'instal·lar l'app de Tailscale.

1. Arrenca amb `.\arrenca.cmd -Tunel cap`.
2. Instal·la Tailscale al portàtil (<https://tailscale.com/download>) i entra-hi amb el teu compte.
3. A PowerShell: `tailscale serve --bg 8080`. L'adreça serà `https://<nom-del-portàtil>.<la-teva-xarxa>.ts.net`.
4. Convida la junta a la teva xarxa de Tailscale des de la seva web.

### Adreça fixa (opcional)

Cal un compte gratuït de Cloudflare **i un domini gestionat per Cloudflare**. Fer servir un subdomini de `cris1954.cat` voldria dir moure'n els DNS a Cloudflare, i no està decidit [A validar].

1. A Cloudflare: *Zero Trust → Networks → Tunnels → Create a tunnel* (tipus «Cloudflared»). Copia'n el testimoni (*token*).
2. Al túnel, afegeix un *Public hostname* (per exemple, `proves.el-teu-domini.cat`) amb el servei `http://caddy:80`.
3. Crea el fitxer `C:\cris\deploy\proves\local\tunel-fix.env` amb dues línies:
   ```
   TUNNEL_TOKEN=el-testimoni-copiat
   ADRECA=https://proves.el-teu-domini.cat
   ```
4. Arrenca amb `.\arrenca.cmd -Tunel fix`.

## Si alguna cosa no va

| Què passa | Què fer |
|---|---|
| «Docker Desktop no està en marxa» | Obre Docker Desktop, espera «Engine running» i torna-ho a provar |
| «No he rebut l'adreça del túnel» | Comprova la connexió i torna a arrencar. Mentrestant, funciona a `http://localhost:8080` |
| «L'aplicació no respon» | A PowerShell, dins la carpeta: `docker compose logs web`. Envia'n les últimes línies |
| El navegador demana usuari i contrasenya | És la contrasenya del davant: usuari `proves` i la contrasenya que mostra `arrenca.cmd` (també és a `local\secrets.env`, línia `ACCES_CONTRASENYA`) |
| En desar una factura, un comprovant o una foto de titulació surt un error de «FILE_ENCRYPTION_KEYS» | El portàtil va generar els secrets abans que existís aquesta clau. Genera'n una a PowerShell, dins la carpeta: `docker compose run --rm web python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`, afegeix a `local\secrets.env` la línia `FILE_ENCRYPTION_KEYS=` amb el valor i torna a arrencar. No la canviïs després: els fitxers ja desats només es llegeixen amb aquesta clau |
| «Hi ha fitxers del repositori modificats» en actualitzar | A PowerShell, a `C:\cris`: `git checkout -- .` i torna a actualitzar |

## Què hi ha al repositori

- [`deploy/proves/`](../../deploy/proves/): `docker-compose.yml`, `Caddyfile`, els scripts (`arrenca`, `actualitza` i `atura`, en `.cmd` i `.ps1`), `entrypoint.sh`, `genera_secrets.py` i `credencials.py`.
- [`Dockerfile`](../../Dockerfile) i [`config/settings/staging.py`](../../config/settings/staging.py): la imatge i la configuració de proves (DEBUG apagat, pagaments ficticis i correu a la bústia).
