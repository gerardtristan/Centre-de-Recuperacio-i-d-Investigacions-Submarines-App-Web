# E4 · Seguiment d'errors sense dades personals

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 17/11/2026 15:00 | b8c3ee5c, a0757f78 (revisió) | 6514 (sense e2e); 29 noves | [A comprovar] |

**En tres línies:** quan la plataforma falli a producció, l'error es podrà enviar a un servei de seguiment (GlitchTip o Sentry) perquè l'equip ho sàpiga. Els informes no porten dades de socis: ni el que s'ha escrit als formularis, ni l'usuari, ni IBAN, targetes, correus, DNI, telèfons o IP. I només poden anar a un servei que el propietari hagi posat a la llista de permesos (dades a la UE).

## Què s'ha fet
- `apps/core/error_tracking.py`: inicia `sentry-sdk` (l'SDK que entenen GlitchTip i Sentry) només des de `config/settings/prod.py` i només si hi ha `ERROR_TRACKING_DSN`. Sense DSN, res i cap connexió (local, proves, CI).
- Filtres abans d'enviar: de la petició només queden el mètode i quatre capçaleres segures; fora l'usuari, els `extra`, les variables locals, els paràmetres dels registres i les consultes SQL. Als missatges, un patró per a cada dada personal ho tapa amb «[tapat]».
- Si el DSN no és `https` o el host no és a `ERROR_TRACKING_ALLOWED_HOSTS`, producció no arrenca. La llista és una constant del codi, buida fins a la P-294: el host s'hi afegeix amb una PR.
- Documentació: variables a l'[arquitectura](../arquitectura-integracions.md#observabilitat), fila E4 de les [portes del nivell 2](../estat/portes-nivell-2.md), fila a l'[estat del 00](../estat/M00.md) i pregunta [P-294](../decisions/pendents.md#oberts) (quin servei; per defecte, GlitchTip al VPS).

## Decisions i perquè
- **El control del host és a l'arrencada, no una comprovació de `manage.py check`:** les comprovacions de `check` no corren amb el servidor web (ho diu `apps/payments/checks.py`). Si el DSN apunta a un host no permès, cap procés no arrenca.
- **L'URL de la petició tampoc s'envia:** un enllaç de convidat porta el testimoni al camí. La ruta, sense valors, ja surt com a nom de la transacció.
- **Patrons amples:** és millor tapar de més (per exemple, un número de nou xifres que no és un telèfon) que deixar passar una dada. Els identificadors interns (el número d'un compte) sí que hi poden sortir.

## Problemes trobats
- La revisió de la #183 va trobar fuites: un telèfon enganxat a «+34», un DNI o NIE amb guió o espai, una IPv6 comprimida («fe80::1», «::1»), un IBAN enganxat a una paraula («iban_GB00…»), un testimoni al camí de la transacció quan la ruta no es resol, un DSN `http` i la llista de hosts a la mateixa configuració que el DSN. Per a cada una, primer una prova que fallava (17 en total) i després l'arreglo (a0757f78).
- L'ajudant que carrega producció en un procés a part era repetit a `test_mail_limit.py`: ara és un de sol a `conftest.py`, amb la clau del mandat explícita i un temps màxim de 60 s.
- La cobertura no mira els subprocessos: la prova que carrega la configuració de producció en un procés a part no compta. S'hi ha afegit una prova en el mateix procés que substitueix `sentry_sdk.init`.

## Com se sap que funciona
- `apps/core/tests/test_error_tracking.py`: sense DSN no s'activa; amb un host no permès producció no arrenca; amb un host permès s'activa amb `send_default_pii` fals, sense variables locals, sense cos i sense traça de rendiment; un esdeveniment inventat surt sense cos, galetes, consulta, usuari ni `extra`, i amb l'IBAN, la targeta, el DNI, el NIE, el telèfon, el correu i les IP tapats; les miges de pa de SQL no es guarden.
- Sortida de proves · commit b8c3ee5c · executada el 17/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q -m "not e2e"
  6499 passed, 115 deselected   (a b8c3ee5c; a a0757f78 només test_error_tracking, test_mail_limit i test_files: 103 passed)
  ```

## Termes nous
- **DSN** (adreça del projecte): l'URL que diu a l'SDK a quin servidor i projecte ha d'enviar els errors.
- **Breadcrumb** (en català: miga de pa): el rastre curt del que ha passat abans d'un error (registres, consultes).
