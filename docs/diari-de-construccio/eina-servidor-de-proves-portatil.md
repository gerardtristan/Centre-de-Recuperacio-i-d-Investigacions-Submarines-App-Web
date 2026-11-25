# Eina · Servidor de proves al portàtil

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 19/11/2026 01:13 – 01:35 | 2b17994 | 32 (3 noves i 29 de `seed_demo_data`) | [A comprovar] |

No és una tasca del pla: és l'eina perquè el propietari i la junta provin la fase 1 des de fora ([decisió 099](../decisions/099-servidor-de-proves-al-portatil.md)).

**En tres línies:** un doble clic a `arrenca.cmd` fa córrer la plataforma al portàtil amb Docker, amb dades inventades, pagaments ficticis i els correus a una bústia de proves. Un túnel de Cloudflare li dona una adreça pública amb HTTPS, darrere d'una contrasenya. `actualitza.cmd` la posa al dia amb `master` i conserva les dades.

## Què s'ha fet
- Partint de l'esborrany del servidor de Hetzner (090): `config/settings/staging.py`, el `Dockerfile` i `seed_demo_data` amb el secret del doble factor propi del servidor.
- Adaptat al portàtil: el Caddy només escolta a `127.0.0.1:8080` (l'HTTPS el fa el túnel); hosts `.trycloudflare.com` i `.ts.net`; dos salts de proxy; sense redirecció HTTPS ni HSTS, perquè les adreces són provisionals.
- `genera_secrets.py` crea els secrets a `deploy/proves/local/`, que no van ni al repositori ni a la imatge (`.dockerignore`).
- Scripts per a Windows (`arrenca`, `actualitza` i `atura`) i la [guia](../guies/servidor-de-proves-al-portatil.md).

## Decisions i perquè
- **Túnel ràpid sense compte per defecte:** el propietari no ha de crear res per començar. L'adreça canvia a cada arrencada; el túnel fix queda com a opció.
- **`.gitattributes`:** a Windows, Git convertiria `entrypoint.sh` a CRLF i el contenidor no arrencaria. Els `.ps1` porten BOM perquè Windows PowerShell 5.1 en llegeixi bé els accents.
- **`$ErrorActionPreference = 'Continue'`** als scripts: amb `Stop`, PowerShell 5.1 tracta com a error el progrés que Docker escriu a stderr.

## Problemes trobats
- Cap a l'aplicació. Al contenidor de proves de Claude, `pip` no confia en el certificat del servidor intermediari: la imatge s'ha construït amb un `Dockerfile` local que hi afegeix el certificat, i que no és al repositori.

## Com se sap que funciona
- `test_servidor_proves_portatil.py` (3): la configuració no cobra ni envia correus a fora; només accepta els túnels i el portàtil; els secrets generats són vàlids i Docker Compose els pot llegir tal qual.
- `test_seed_demo_data_staging.py` i `test_seed_demo_data.py` (29) en verd.
- Prova manual amb Docker (19/11/2026): els cinc serveis arrenquen; les dades inventades es carreguen; sense contrasenya del davant, 401; entrada a l'administració amb `admin-demo` i el doble factor del servidor, amb els estils carregats (captura a 1280 px, mirada); simulant el túnel (`X-Forwarded-Proto: https` i un host `.trycloudflare.com`), la galeta CSRF és segura i l'entrada funciona, i un origen estrany rep 403; en reiniciar, les migracions s'apliquen i les dades es conserven.
- No provat aquí: el túnel real de Cloudflare (el contenidor no pot publicar adreces) ni els scripts de PowerShell (no hi ha Windows). [A comprovar] al portàtil.

## Ajust per a 4 GB (25/11/2026)
- El portàtil servidor és un ThinkPad 11e (Celeron N4100, 4 GB) amb Windows 10. gunicorn passa a un procés amb quatre fils i PostgreSQL a `shared_buffers=64MB`; la guia afegeix la BIOS (VT-x), el Windows 22H2 i el `.wslconfig` que limita Docker a 2 GB.
- Provat amb Docker sobre `master` (#607): els cinc serveis ocupen uns 280 MB i l'entrada a l'administració amb el doble factor funciona.
