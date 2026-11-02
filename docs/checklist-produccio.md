# Checklist de producció — Plataforma C.R.I.S.

Aquest fitxer és la llista de comprovació que ha de seguir qualsevol persona o assistent que desenvolupi la plataforma. Cap mòdul es dona per acabat fins que passa les portes que li corresponen.

## 1. Decisió: primer web, després app
Es construeix primer una app-web (web responsive instal·lable com a PWA). L'app nativa o d'escriptori no entra a l'abast actual.

Motius:
- Una sola base de codi per a ordinador, tauleta i mòbil, sense passar per botigues d'aplicacions.
- Les funcions que necessita el club (carnet digital amb QR, passar llista, assignar material, pagar, consultar) no exigeixen accés profund al dispositiu.
- Una PWA s'instal·la a Android i a iOS; a iOS les notificacions push només funcionen si l'usuari l'ha afegida a la pantalla d'inici i ha donat permís.
- Més endavant, la mateixa web es pot empaquetar per a les botigues si cal.

Quan reconsiderar-ho: si fan falta notificacions fiables a iOS sense instal·lació, funcions de maquinari (Bluetooth, NFC, càmera avançada) o presència a les botigues.

Requisits PWA: HTTPS, manifest, service worker, carnet i llista d'assistència disponibles amb poca cobertura (al moll sovint n'hi ha poca).

## 2. Portes (quan s'ha de complir cada cosa)
- Porta 0 — abans del primer codi: repositori, README, secrets, ambients, esquelet de CI.
- Porta 1 — abans d'ensenyar una demo a la junta: staging, domini i SSL, pàgines d'error, proves bàsiques, autenticació a cada endpoint, còpies.
- Porta 2 — abans de dades reals de socis: RGPD, política de privacitat, doble factor, prova de restauració, limitació de peticions, auditoria de dependències, registres, esborrat de compte.
- Porta 3 — abans d'obrir-ho als socis: monitoratge, alertes, SEO, proves en dispositius i xarxes lentes, pla de marxa enrere provat, cookies, accessibilitat, correu de confirmació del mandat (G3). SPF, DKIM, DMARC i plantilles (G1, G2) són de la porta 2.
- Continu: auditoria de dependències cada mes, prova de restauració cada trimestre, rotació de claus cada any o davant d'una filtració.

**Dos nivells de producció** (decisió 025):
- **Nivell 1, producció de mandats** (05a acabat i provat): Stripe en mode real només per recollir mandats, **sense cap cobrament real**. Requereix l'autorització expressa de la junta i les portes 0, 1 i 2 superades, en particular HTTPS (A7), secrets (A3), còpies i restauració (D1, D2), RGPD i consentiments (H1, H3, text del mandat) i registre d'activitat (C8). De la porta 3, només el que afecta el flux de signatura de mandats (marcat «N1» a la columna Porta):
  - A6 pla de marxa enrere;
  - E3 monitoratge de la web i l'API del flux;
  - E4 alertes de caiguda, errors, certificat i còpia fallida;
  - B5 flux en mòbil (Android, iOS) i navegadors habituals;
  - B8 accessibilitat bàsica del flux;
  - G3 correu de confirmació del mandat.
- **Nivell 2, producció completa** (05b acabat i provat): cobraments reals i baixa de Cluber. Requereix l'autorització expressa de la junta i les portes 0 a 3 completes: la resta de la porta 3 (B6, E5, E6, F1-F7, H2, H5) i la part de nivell 2 de B5, B8, E3 i E4.
- En tots dos nivells, la plataforma només guarda l'IBAN xifrat al mandat, per a la domiciliació (decisió 044, que substitueix la custòdia de Stripe després de la 042). Els documents de justificació d'ajuts que porten IBAN segueixen la decisió 051 (xifrats, només tresorer i junta, còpia emmascarada).

## 3. Llista per categories

### A. Repositori i lliurament
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| A1 | CI/CD | Pipeline que a cada canvi executa proves, anàlisi estàtica i auditoria de dependències; desplega a staging automàticament i a producció amb aprovació | El pipeline és verd abans de fusionar | 0 |
| A2 | Ambients | Local, staging (còpia de producció amb dades inventades) i producció | Tres configuracions separades i documentades | 0 |
| A3 | Secrets fora del repositori | Claus, contrasenyes i tokens en variables d'entorn o gestor de secrets | Escaneig de secrets al CI; cap secret a l'historial | 0 |
| A4 | Rotar claus filtrades | Procediment escrit; si una clau surt al repositori, es rota i es revisa l'historial | Simulacre una vegada | 2 |
| A5 | README | Com instal·lar, executar, provar, desplegar, fer una còpia i restaurar; qui és responsable | Una persona nova ho posa en marxa seguint-lo | 0 |
| A6 | Pla de marxa enrere | Cada desplegament es pot revertir; migracions de base de dades compatibles amb la versió anterior | Reversió provada a staging | 3 · N1 |
| A7 | Domini propi i SSL | Domini existent del club, certificat renovat automàticament, redirecció a HTTPS | Alerta de caducitat; prova externa de SSL | 1 |

### B. Proves
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| B1 | Proves unitàries | Prioritat màxima: càlcul del marge, quotes, canvi de simpatitzant a ple dret, preus de llicències, llista d'espera, imputació de material | Cobertura mínima dels càlculs econòmics del 100% | 1 |
| B2 | Proves de fum | Després de cada desplegament: inici de sessió, carnet, inscripció, pagament de prova, pàgina d'inici | S'executen automàticament a staging i producció | 1 |
| B3 | Proves de regressió | Cada error corregit deixa una prova que l'evita | Llista d'errors amb prova associada | 2 |
| B4 | Proves de permisos | Per a cada rol: què pot i què no pot; el soci només veu el seu, l'instructor només les seves sessions. Els permisos són editables des de l'app (decisió 059): cal provar la configuració inicial, el motor (unió de rols, abast, efecte a la petició següent), cada regla protegida i les garanties de l'editor | Proves per cel·la generades des de la configuració inicial (`docs/planning.md#rols-i-permisos-059-matriu`) i proves de CA-RP-01 a CA-RP-14 | 1 |
| B5 | Proves en diversos dispositius | Mòbil (Android i iOS), tauleta i ordinador; navegadors principals | Llista de dispositius provats i resultat | 3 · N1: flux de mandat en mòbil (Android, iOS) i navegadors habituals · N2: la resta de pantalles i la tauleta |
| B6 | Proves amb xarxa lenta | Carnet i llista d'assistència amb poca cobertura; estats de càrrega i errors clars | Emulació de 3G i mode sense connexió | 3 |
| B7 | Estats reals | Pàgines 404 i 500 pròpies, estats buits («encara no hi ha inscripcions») i estats de càrrega | Revisió de cada pantalla | 1 |
| B8 | Accessibilitat | Contrast, navegació amb teclat, etiquetes de formulari, text alternatiu, mida de lletra; objectiu WCAG 2.2 AA | Auditoria automàtica i revisió manual | 3 · N1: bàsica del flux de mandat (contrast, teclat, etiquetes, errors clars) · N2: WCAG 2.2 AA completa |
| B9 | Proves d'importació | Importació de socis i de l'extracte bancari amb casos incorrectes, duplicats i fitxers buits | Fitxers de prova | 2 |

### C. Seguretat
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| C1 | Autenticació a cada endpoint | Per defecte tot exigeix sessió i permís; només es marquen com a públics els endpoints que ho són | Prova automàtica que recorre totes les rutes sense sessió | 1 |
| C2 | Doble factor i comptes d'administrador | TOTP obligatori per a qualsevol compte que entri per l'administració (inclosos instructor i Departament d'Història) i per als comptes d'emergència; opcional per als comptes de soci. Cada persona té un únic perfil; un administrador té dos comptes: soci (correu únic) i administrador (nom d'usuari únic, entrada separada, diversos rols possibles, correu no únic només per a notificacions, sense recuperació per correu: la restableix un altre administrador o s'hi entra amb codis de recuperació fora de línia). El registre d'activitat guarda quin compte ha fet cada acció. Vegeu docs/decisions/015 i 018 | No es pot accedir a l'administració sense segon factor; el compte d'administrador no té cap enllaç de recuperació per correu; proves de restabliment per un altre administrador i amb codi de recuperació; l'editor de permisos demana el TOTP de nou per desar i rebutja qualsevol canvi que deixi menys d'un administrador operatiu (decisió 059) | 2 |
| C3 | Limitació de peticions | Inici de sessió, recuperació de contrasenya, formularis públics i API | Prova de càrrega i bloqueig temporal | 2 |
| C4 | Restabliment de contrasenya | **Comptes de soci:** enllaç per correu d'un sol ús amb caducitat, sense revelar si el correu existeix. **Comptes d'administrador:** cap restabliment per correu; el fa un altre administrador (queda al registre d'activitat) o s'entra amb un codi de recuperació d'un sol ús guardat fora de línia (decisió 018) | Prova de principi a fi per a cada tipus de compte; comprovar que l'entrada d'administració no ofereix cap enllaç de recuperació per correu | 1 |
| C5 | Verificació de correu | **Comptes de soci:** queden pendents fins a confirmar el correu. **Comptes d'administrador:** els crea un administrador i no es verifiquen per correu (el correu no és únic i només serveix per a notificacions) | Prova de principi a fi | 1 |
| C6 | Auditoria de dependències | Pipeline que falla amb vulnerabilitats greus; revisió mensual | Informe a cada execució | 2 |
| C7 | Configuració de producció | Mode de depuració desactivat, secret fora del repositori i capçaleres de seguretat; si es fa servir Django, executar la comprovació de desplegament | La comprovació no mostra avisos | 2 |
| C8 | Registre d'activitat | Qui, quan, què i valor anterior en dades de socis i diners | Es consulta des de l'administració | 1 |
| C9 | Pagaments | Verificar la firma de cada notificació del proveïdor, notificacions idempotents, mai donar un pagament per fet només pel navegador. Stripe en mode de proves fora dels dos nivells de producció (decisió 025). Al nivell 1 (05a), mode real només per a mandats i cap cobrament real; al nivell 2 (05b), producció completa. La plataforma no guarda l'IBAN, excepte xifrat al mandat (044) | Proves amb notificacions repetides i falsificades; proves de domiciliació fallida, reintent i rebut retornat; prova que al nivell 1 no es pot crear cap cobrament real; revisió del model de dades: l'únic camp amb IBAN és el xifrat del mandat (044) | 2 |
| C10 | Fitxers pujats | Tipus i mida limitats, emmagatzematge privat, enllaços temporals | Prova amb fitxers maliciosos | 2 |
| C11 | Usuaris de la base de dades | Dos usuaris de PostgreSQL: un per a les migracions (propietari de les taules) i un altre per a l'app en funcionament, sense ser propietari ni superusuari, de manera que no pugui desactivar els disparadors del registre d'activitat (T-M01-07) ni canviar l'estructura | Comprovar que l'usuari de l'app no pot fer `ALTER TABLE core_auditentry DISABLE TRIGGER` ni `DROP TRIGGER` | 1 |

### D. Dades i continuïtat
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| D1 | Còpies de la base de dades | Diàries, fora del servidor principal, també dels documents pujats | Alerta si falla una còpia | 1 |
| D2 | Prova de restauració | Restaurar l'última còpia en un entorn net i comprovar que es pot entrar i que les dades són coherents | Informe de cada prova, cada trimestre | 2 |
| D3 | Límits de despesa i alertes de facturació | Límit mensual al proveïdor d'allotjament, correu i pagaments, amb avís al responsable | Alerta configurada i provada | 1 |
| D4 | Allotjament a la UE | Servidor i còpies dins la UE | Documentat | 1 |
| D5 | Migracions | Les migracions es proven amb dades de staging abans de producció | Pipeline | 1 |

### E. Observabilitat
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| E1 | Registres | Estructurats, sense contrasenyes ni dades personals innecessàries | Revisió d'exemples | 2 |
| E2 | Seguiment d'errors | Avís amb la traça cada vegada que hi ha un error en producció | Error provocat a staging | 2 |
| E3 | Monitoratge de disponibilitat | Comprovació externa cada pocs minuts de la web i del carnet | Alerta quan cau | 3 · N1: web i API del flux de mandat · N2: carnet |
| E4 | Alertes | Qui rep què: errors, caiguda, còpia fallida, certificat a punt de caducar, despesa | Simulacre | 3 · N1: caiguda, errors, certificat, còpia fallida · N2: la resta (despesa) |
| E5 | Monitoratge de rendimiento | Temps de resposta i consultes lentes; objectiu de càrrega de pàgina raonable en mòbil | Informe mensual | 3 |
| E6 | Analítica | Només la que es pugui justificar. Segons l'AEPD, les cookies d'audiència només estan exemptes de consentiment si només mesuren l'audiència en nom de l'editor, donen dades anònimes i agregades i no es creuen amb altres tractaments ni permeten seguir l'usuari entre llocs. Una opció és una eina pròpia o sense cookies | Revisió de les quatre condicions | 3 |

### F. Web pública i SEO
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| F1 | Sitemap i robots.txt | Només pàgines públiques; l'àrea de socis i l'administració queden excloses | Prova automàtica | 3 |
| F2 | Dades estructurades | Organització, esdeveniments (cursos, sortides, conferències) i preguntes freqüents | Validador de dades estructurades | 3 |
| F3 | AEO (respostes de cercadors i assistents) | Pàgines de preguntes freqüents clares, textos que responen directament i dades de contacte coherents | Revisió manual | 3 |
| F4 | Imatges OG i favicon | Logotip del club per a previsualitzacions en xarxes i icona de l'app | Prova en xarxes | 3 |
| F5 | Optimització d'imatges | Formats moderns, mides adaptades i càrrega diferida | Informe de rendiment | 3 |
| F6 | Memòria cau | Memòria cau del navegador per a recursos estàtics i del servidor per a pàgines públiques | Capçaleres comprovades | 3 |
| F7 | Idioma | Català i, si es decideix, castellà i anglès amb etiquetes d'idioma | Revisió | 3 |

### G. Correu
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| G1 | SPF, DKIM i DMARC | Perquè els correus de la plataforma (rebuts, carnets, avisos, butlletins) no acabin a brossa. Es configuren a cris1954.cat (domini remitent); les respostes van a cris@cris.es (decisió 019) | Comprovador de correu | 2 |
| G2 | Plantilles i enllaç de baixa | Butlletins només amb consentiment i amb enllaç de baixa | Prova | 2 |
| G3 | Correu de confirmació del mandat | En signar un mandat, el soci rep un correu des de cris1954.cat (resposta a cris@cris.es) amb la referència del mandat, l'ID de creditor, la data de signatura i com revocar-lo. Si l'envia Stripe o la plataforma és [A validar] | Prova de principi a fi en mode de proves; revisió del text amb la junta | 3 · N1 |

### H. Legal i privacitat
| ID | Requisit | Com s'aplica al C.R.I.S. | Com es comprova | Porta |
|---|---|---|---|---|
| H1 | Política de privacitat i condicions | Redactades amb la junta; qui és el responsable, per a què es fan servir les dades i quant de temps es guarden | Publicades i enllaçades als formularis | 2 |
| H2 | Consentiment de cookies | Si hi ha cookies no tècniques: consentiment previ i opció de rebutjar tan visible com la d'acceptar | Revisió amb la pàgina oberta per primera vegada | 3 |
| H3 | Esborrat de compte i de dades | Un soci pot demanar l'esborrat i l'exportació de les seves dades; es conserven només les dades que obliga la llei (per exemple, factures) | Prova de principi a fi | 2 |
| H4 | Dades de salut | No es guarden a la plataforma | Revisió del model de dades | 1 |
| H5 | Protocol per a menors | Si hi ha menors, protocol i persona de referència fora de l'app. Si hi ha socis menors, el mandat SEPA de la seva quota l'ha de signar el titular del compte bancari. [A validar: el club té socis menors d'edat?] | Confirmar amb la junta | 3 · N2 |

### I. Funcions d'IA (només si s'afegeixen)
No aplica a l'abast actual. Si més endavant s'afegeix una funció amb un model d'IA (per exemple, identificar espècies), cal: avaluacions amb casos reals, proves contra injecció de prompts, alternativa quan el servei no respongui, gestió dels límits de context i límit de despesa.

## 4. Elements de la llista original que s'han descartat
- Les línies «ТОВ ЭНТАЗЯВ» i «rotate any keys that leaked C» eren text sobrant; la rotació de claus s'ha inclòs com a A4.

## 5. Extres propis del C.R.I.S.
- Carnet digital i llista d'assistència amb mode sense connexió.
- Càlcul del marge amb proves que comparin el resultat de la plataforma amb el càlcul manual d'una sortida real.
- Importació de Cluber i del banc amb previsualització i opció de desfer.
- Dades de prova inventades a staging; mai dades reals fora de producció.
- Responsable de manteniment nomenat a la junta i calendari de tasques periòdiques.

## 6. Com s'ha de treballar
- Abans de començar un mòdul, copiar les files que li afecten a un issue com a criteris d'acceptació.
- No es fusiona cap canvi si el pipeline falla.
- A cada porta, es revisa la llista i es deixa constància de què s'ha complert, què no i per què.
