# Registre de proveïdors i dades dins la UE

- **Data:** 27/10/2026
- **Aplica:** la [decisió 035](decisions/035-dades-nomes-dins-ue.md) (totes les dades personals, només dins la UE) i la [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) (proveïdors substituïts).
- **Origen:** registre del repositori anterior (històric), adaptat a la pila d'aquest repositori ([002](decisions/002-pila-tecnologica.md)).

## Com es llegeix
- **Compleix:** seu a la UE, servidors a la UE i sense transferències fora de la UE segons el que se'n sap. Abans de contractar, cal confirmar-ho amb la llista de subencarregats i el contracte d'encarregat del tractament (RGPD, art. 28).
- **A verificar:** candidat amb seu a la UE al qual falta confirmar servidors o subencarregats. No es fa servir fins que estigui verificat.
- **CONFLICTE:** no compleix la 035. No es fa servir; hi ha alternativa.
- **Sense dades personals:** el servei no rep dades personals si es fa servir com s'indica.

Cap proveïdor d'aquesta llista no està contractat. Tot s'ha de tornar a comprovar el dia de contractar.

## 1. Registre

### Infraestructura
| Servei | Proveïdor | Seu | Servidors | Dades que rep | Contracte art. 28 | Estat |
|---|---|---|---|---|---|---|
| Servidor de l'aplicació, base de dades i cua (Coolify) | Hetzner (VPS) | Alemanya | Alemanya o Finlàndia (no triar regions dels EUA ni de Singapur) | Totes | Sí | Compleix (triar regió UE) |
| Web pública i PWA | El mateix VPS de Hetzner (042) | Alemanya | UE | IP dels visitants | Sí | Compleix |
| Fitxers privats | Scaleway Object Storage ([005](decisions/005-fitxers.md)) | França | París | Documents i fotos | Sí | Compleix |
| Còpies de seguretat | Còpies de Hetzner, Storage Box i Scaleway, xifrades amb restic ([006](decisions/006-copies-de-seguretat.md)) | Alemanya / França | UE | Totes (xifrades) | Sí | Compleix |
| DNS de cris1954.cat | Registrador del domini o Hetzner DNS (042) | [A verificar] | [A verificar] | Cap dada de socis | — | A verificar ([023](decisions/023-gestio-del-dns.md), P-25) |
| CDN i web estàtica (abans) | Cloudflare | EUA | Global | IP i peticions | — | **CONFLICTE** (substituït, 042) |

### Pagaments i banc
| Servei | Proveïdor | Seu | Servidors | Dades que rep | Contracte art. 28 | Estat |
|---|---|---|---|---|---|---|
| Banc del club | **CaixaGuissona** [A verificar que és el banc del club] | Espanya | [A verificar] | Remeses, extractes, pagaments | Contracte bancari | A verificar |
| TPV virtual, targeta i Bizum | **PaynoPain** (plataforma Paylands), via CaixaGuissona [A verificar] | Espanya [A verificar entitat i llicència] | [A verificar] | Import, referència, identificador intern del client; la targeta l'escriu el soci a la pàgina o `iframe` de Paylands | [A verificar] | A verificar ([043](decisions/043-proveidor-de-pagaments-dins-la-ue.md), P-45) |
| Bizum (xarxa) | Redsys, a través del TPV | Espanya | Espanya [A verificar] | Dades del pagament | Amb el TPV | A verificar |
| Targeta i Bizum (alternativa) | PAYCOMET | Espanya [A verificar grup] | [A verificar] | Les mateixes | [A verificar] | A verificar |
| Targeta i Bizum (alternativa) | MONEI | Espanya (Màlaga); entitat de pagament núm. 6911 segons la seva web | La web diu «Powered by … AWS» [A verificar regió] | Les mateixes | [A verificar] | **Probable CONFLICTE** (AWS, empresa dels EUA) |
| Targeta, Bizum i SEPA (alternativa) | Mollie | Països Baixos | [A verificar subencarregats] | Les mateixes | Sí [A verificar] | A verificar |
| Targeta, Bizum i SEPA (abans) | Stripe | EUA (entitat contractant a Irlanda) | Transferències als EUA | Nom, correu, import, IBAN | — | **CONFLICTE** (descartat, 042) |
| Domiciliació SEPA de quotes | Remesa `pain.008` generada per l'app i enviada pel banc | — | Servidor propi i banc | Nom, IBAN (xifrat, [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)), mandat, import | Amb el banc | Compleix si el banc ho confirma |
| Domiciliació SEPA (alternativa) | GoCardless | Regne Unit | — | Nom, IBAN, mandat | — | **CONFLICTE** |
| Transferència amb referència | Conciliació amb l'extracte (spec 04) | — | Servidor propi | Línies de l'extracte | — | Compleix |
| Extracte bancari | Fitxer CSV o Norma 43 descarregat del banc | — | Servidor propi | Moviments del compte | — | Compleix |
| Pagaments sortints | Fitxer `pain.001` que el tresorer signa al banc | — | Servidor propi i banc | Beneficiari, IBAN, import | Amb el banc | Compleix (fase 2) |

L'app no guarda mai dades de targeta ni credencials del banc.

### Facturació
| Servei | Proveïdor | Seu | Servidors | Dades que rep | Contracte art. 28 | Estat |
|---|---|---|---|---|---|---|
| Facturació homologada (Verifactu) | B2Brouter (API) o el programa de la gestoria | Espanya | [A verificar] | Nom, NIF i adreça, línies i imports | Sí | A verificar (P-02) |
| Enviament a l'Agència Tributària | AEAT | Espanya | Espanya | Registres de facturació | Obligació legal | Compleix |

### Comunicació
| Servei | Proveïdor | Seu | Servidors | Dades que rep | Contracte art. 28 | Estat |
|---|---|---|---|---|---|---|
| Correu transaccional i butlletí | Brevo ([004](decisions/004-correu.md), [062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)) | França | Afirmat pel responsable del projecte el 03/11/2026 | Nom, correu i contingut | Sí | Es manté ([062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)) |
| Correu (alternativa) | Scaleway Transactional Email | França | França | Les mateixes | Sí | A verificar |
| Bústia de la junta | Gmail (ús actual) | EUA | Global | Tot el que s'hi escriu | — | **CONFLICTE** |
| Bústia (alternativa) | mailbox.org o correu d'OVHcloud | Alemanya / França | Alemanya / França | Tot el que s'hi escriu | Sí | A verificar |
| Missatges i xat | Mòdul propi | — | Servidor propi | Missatges i adjunts | — | Compleix |
| Xat actual | WhatsApp | Irlanda (grup Meta, EUA) | Transferències als EUA | Telèfon, noms, missatges | — | **CONFLICTE** |
| Notificacions push | Apple (APNs) i Google (FCM) | EUA | Global | Identificador del dispositiu i text | — | **CONFLICTE** (no es fan, [041](decisions/041-web-installable-i-avisos-sense-push.md)) |

### App i distribució
| Servei | Proveïdor | Seu | Dades que rep | Estat |
|---|---|---|---|---|
| App Store i Play Store | Apple i Google | EUA | Compte del club i descàrregues | **CONFLICTE** (no es fan servir, 041) |
| Web instal·lable (PWA) | Servidor propi | UE | Les de l'app | Compleix |

### Identitat
| Servei | Proveïdor | Seu | Dades que rep | Estat |
|---|---|---|---|---|
| «Continua amb Google» (OpenID Connect, opcional, només comptes personals) | Google | EUA | Google sap que la persona entra a la plataforma; la plataforma només en rep el nom i el correu verificat, i les dades continuen desades a la UE | **Excepció acotada** ([108](decisions/108-respostes-del-propietari-del-27-11-2026-web-butlleti-i-compte-rapid.md), D.2): opció voluntària de la persona; apagat fins que hi hagi la clau |
| Clau d'accés (WebAuthn) i codi pel correu | Servidor propi (el codi surt per Brevo) | UE | Clau pública del dispositiu; correu | Compleix |

### Contingut i web
| Servei | Proveïdor | Seu | Dades que rep | Estat |
|---|---|---|---|---|
| Vídeos tutorials | Fitxers a Scaleway amb el reproductor del navegador | UE | IP de qui el mira | Compleix |
| Vídeos (opció habitual) | YouTube o Vimeo | EUA | IP i navegació | **CONFLICTE** |
| Tipografies | Fitxers servits des del servidor propi ([030](decisions/030-sistema-de-disseny.md): allotjament de les fonts [A validar]) | — | Cap | Compleix |
| Tipografies (opció habitual) | Google Fonts | EUA | IP de cada visitant | **CONFLICTE** |

### Observabilitat
| Servei | Proveïdor | Seu | Dades que rep | Estat |
|---|---|---|---|---|
| Errors | GlitchTip o Bugsink al servidor propi (042) | UE | Errors, sense dades de socis ([011](decisions/011-monitoratge-i-errors.md)) | Compleix |
| Errors (abans) | Sentry | EUA | Errors | **CONFLICTE** (substituït, 042) |
| Disponibilitat | UptimeRobot ([011](decisions/011-monitoratge-i-errors.md)) | [A verificar] | Només l'URL pública; cap dada personal | Sense dades personals [A verificar seu] |
| Analítica | Cap, o Matomo propi | UE | Visites | Compleix |

### Eines de desenvolupament
| Servei | Proveïdor | Seu | Dades que rep | Estat |
|---|---|---|---|---|
| Repositori | GitHub | EUA | Només codi i dades inventades | Sense dades personals si es compleix la norma |
| Assistent de desenvolupament | Claude (Anthropic) | EUA | Només codi i documentació | Sense dades personals si es compleix la norma |

**Norma:** al repositori, a la integració contínua i a les eines d'IA no hi entra mai cap dada personal real ni cap còpia de la base de dades ([010](decisions/010-entorns.md)).

### Tercers que reben dades
| Destinatari | Seu | Dades | Estat |
|---|---|---|---|
| FECDAS (llicències, [036](decisions/036-fecdas-alia.md)) | Catalunya | Dades de tramitació | Compleix (cal informar-ne els titulars) |
| Gestoria | Espanya [A verificar] | Factures i comptabilitat | A verificar |
| Centres de busseig | Espanya [A verificar cadascun] | Participants i material | A verificar |

## 2. Conflictes i com queden
| # | Conflicte | Alternativa | Estat |
|---|---|---|---|
| C1 | Notificacions push | Avisos dins l'app i per correu | Resolt (041). Push «buida» només amb aprovació escrita del responsable del projecte |
| C2 | Botigues d'apps | Web instal·lable | Resolt (041); la junta ho ha d'acceptar amb el pressupost (037) |
| C3 | Gmail | mailbox.org o OVHcloud | Pendent de la junta |
| C4 | Google Fonts | Fonts servides des del servidor | Es fa directament |
| C5 | WhatsApp | Missatges propis | Pendent de la junta (quan es deixa) |
| C6 | Stripe | TPV de CaixaGuissona via PaynoPain; si no, PAYCOMET, MONEI o Mollie verificats | Stripe descartat (042); proveïdor a la 043 |
| C7 | GoCardless | Remesa `pain.008` pel banc (044) | Resolt |
| C8 | YouTube o Vimeo | Vídeos propis | Es fa directament |
| C9 | Sentry | GlitchTip o Bugsink | Resolt (042) |
| C10 | Google Analytics | Cap, o Matomo | Es fa directament |
| C11 | Cloudflare | Servir des de Hetzner | Resolt (042) |
| C12 | MONEI (AWS) | Les altres opcions de la 043 | Pendent de verificar |

## 3. Pendents d'aquest registre
- Respostes del banc i de PaynoPain: [pendents.md](decisions/pendents.md), P-45.
- Programa de facturació de la gestoria (P-02).
- Registrador del domini i DNS (P-25).
