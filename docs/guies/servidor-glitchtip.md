# Seguiment d'errors: instal·lar GlitchTip al servidor

**Per a qui és:** qui administra el servidor de producció (Coolify al VPS de Hetzner). **Estat:** preparat, **no encès** (17/11/2026). El propietari va triar GlitchTip autoallotjat al mateix servidor de la UE com a servei permanent de producció ([P-294](../decisions/pendents.md)). No s'encén fins que el servidor existeixi i el propietari ho confirmi per escrit.

**Per què aquí:** les dades dels errors no surten del servidor del club i no cal cap encarregat del tractament nou: Hetzner ja ho és. El codi de la plataforma ja és fet ([`apps/core/error_tracking.py`](../../apps/core/error_tracking.py)). Què no s'envia mai: [arquitectura, Observabilitat](../arquitectura-integracions.md#observabilitat).

## 1. Abans de començar
- **Memòria del servidor.** GlitchTip són uns quants contenidors més (web, tasques i la seva base de dades). Cal mirar que el pla del VPS hi arribi amb la plataforma en marxa [A verificar en triar el pla: CX23, 4 GB, o CX33, 8 GB; arquitectura §2].
- **Nom.** `errors.cris1954.cat` [A validar el nom, com la resta de subdominis: arquitectura §2]. Si canvia, cal una PR que canviï `ERROR_TRACKING_ALLOWED_HOSTS` al codi: sense, la plataforma no arrenca amb el DSN nou.
- **DNS.** Un registre `A` (i `AAAA` si n'hi ha) de `errors.cris1954.cat` cap a la IP del VPS ([P-25](../decisions/pendents.md): qui té l'accés al DNS).

## 2. Instal·lar-lo (quan el servidor existeixi)
1. A Coolify, crea un servei nou a partir de la plantilla de **GlitchTip** del catàleg de serveis de Coolify, al mateix projecte i servidor que la plataforma. Fes servir la versió estable del dia i apunta-la aquí [A verificar: requisits de la versió a la documentació d'instal·lació de GlitchTip; si la plantilla porta Redis o Valkey, és intern de GlitchTip i no canvia la cua de la plataforma, que continua sobre PostgreSQL].
2. Domini del servei: `https://errors.cris1954.cat` (Coolify en fa el certificat). El DSN ha de ser `https`: amb `http` la plataforma no arrenca.
3. Variables del servei (cap valor real al repositori; només a Coolify):
   - `SECRET_KEY`: una de nova i llarga, generada a Coolify.
   - `GLITCHTIP_DOMAIN=https://errors.cris1954.cat`.
   - `ENABLE_USER_REGISTRATION=False` (i, si la versió la té, `ENABLE_ORGANIZATION_CREATION=False`): ningú no s'hi pot registrar sol [A verificar el nom exacte de la variable a la versió instal·lada].
   - `GLITCHTIP_MAX_EVENT_LIFE_DAYS=30`: els errors s'esborren sols al cap de 30 dies (minimització) [A validar el termini: propietari].
   - Correu per a les alertes: `EMAIL_URL` amb les credencials SMTP de Brevo i `DEFAULT_FROM_EMAIL` amb el remitent del club (decisió 085). Les credencials, només a Coolify.
4. Còpies: les dades de GlitchTip són efímeres (30 dies) i no tenen dades de socis; **no** entren a les còpies de la plataforma. Si es perden, només es perden errors antics.

## 3. Configurar-lo
1. Crea el primer usuari (l'administrador de la plataforma) amb la comanda de creació de superusuari del contenidor web de GlitchTip [A verificar l'ordre exacta a la versió instal·lada].
2. Activa el **doble factor (TOTP)** a cada compte de GlitchTip, com a qualsevol entrada d'administració de la plataforma. Només hi entren els administradors de la plataforma.
3. Crea l'organització «C.R.I.S.» i un projecte Django, «Plataforma». Copia'n el DSN.
4. Alertes del projecte: correu als administradors de la plataforma quan apareix un error nou [A validar qui els rep: checklist E4].

## 4. Encendre-ho a producció (només amb el sí del propietari)
1. A Coolify, a les variables de la plataforma (no de GlitchTip): `ERROR_TRACKING_DSN=<el DSN del pas 3.3>` i, si es vol, `ERROR_TRACKING_ENVIRONMENT=production`.
2. Torna a desplegar la plataforma. Si el host del DSN no és `errors.cris1954.cat` o no és `https`, la plataforma no arrenca: és a propòsit.
3. Prova: des del terminal de Coolify del contenidor de la plataforma, `python manage.py shell -c "import sentry_sdk; sentry_sdk.capture_message('Prova del seguiment d errors'); sentry_sdk.flush()"`. El missatge ha d'arribar al projecte en uns segons, i l'alerta, per correu.
4. Mira l'esdeveniment de prova i un error real: no hi ha d'haver cos de petició, galetes, usuari, IBAN, correus ni IP (R11). Si en surt cap, apaga-ho (treu `ERROR_TRACKING_DSN` i torna a desplegar) i obre una incidència.
5. Apunta a la [checklist](../checklist-produccio.md#e-observabilitat) (E4) la data i qui ho ha comprovat.

## 5. Apagar-ho
Treure `ERROR_TRACKING_DSN` de les variables de la plataforma i tornar a desplegar. GlitchTip pot continuar en marxa sense rebre res.
