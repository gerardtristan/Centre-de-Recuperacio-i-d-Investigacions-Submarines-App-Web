# Registre de decisions

Un fitxer per decisió, numerat (`NNN-nom.md`). Format: data, estat, context, alternatives, decisió, conseqüències i fonts.

Estats: **Acceptada** (es pot aplicar), **Proposada** (pendent de validació de la junta; no s'implementa la part afectada), **Substituïda** (indica per quina), **Descartada** (s'ha valorat i no es fa; es registra perquè no es torni a plantejar sense motius nous).

Una decisió no s'edita per canviar-la: se'n crea una de nova que la substitueix, i a l'antiga es marca l'estat «Substituïda per NNN».

| Núm. | Decisió | Estat |
|---|---|---|
| [001](001-construir-en-lloc-de-comprar.md) | Construir una plataforma pròpia en lloc de comprar | Acceptada (el cost de servidor l'actualitza la 016) |
| [002](002-pila-tecnologica.md) | Pila tecnològica | Acceptada (substituïda en part per 042 i 046) |
| [003](003-autenticacio-doble-factor.md) | Autenticació i doble factor | Substituïda per 015 |
| [004](004-correu.md) | Correu transaccional i butlletí amb Brevo | Acceptada |
| [005](005-fitxers.md) | Fitxers a Scaleway Object Storage | Acceptada |
| [006](006-copies-de-seguretat.md) | Còpies de seguretat creuades i xifrades | Acceptada |
| [007](007-pagaments-stripe.md) | Pagaments amb Stripe més transferència i registre manual | Substituïda per 014 i 017 |
| [008](008-metodologia-sdd.md) | Metodologia Spec-Driven Development | Acceptada |
| [009](009-sistema-de-disseny.md) | Sistema de disseny | Substituïda per 030 |
| [010](010-entorns.md) | Tres entorns i VPS de proves separat | Acceptada |
| [011](011-monitoratge-i-errors.md) | Monitoratge de disponibilitat i seguiment d'errors | Acceptada (regió del seguiment d'errors [A validar]) |
| [012](012-cua-de-tasques.md) | Cua de tasques sobre PostgreSQL | Acceptada |
| [013](013-imputacio-comissions.md) | Imputació de comissions per departament | Acceptada (llicències [A validar]) |
| [014](014-migracio-cluber-i-entrada-en-produccio.md) | Migració única de Cluber i criteri d'entrada en producció | Acceptada (concretada per 020; refinada per 025) |
| [015](015-doble-factor-i-comptes-administrador.md) | Doble factor i comptes d'administrador separats | Acceptada (concretada per 018; domini per 019) |
| [016](016-pressupost-produccio-minima.md) | Pressupost: començar amb la producció mínima | Acceptada |
| [017](017-pagaments-metodes-i-domiciliacions.md) | Pagaments: mètodes per cobrament i domiciliacions | Acceptada (registre manual [A validar]) |
| [018](018-perfil-comptes-i-rols.md) | Perfil únic, comptes i doble factor per entrada | Acceptada |
| [019](019-domini-i-correu.md) | Domini de la plataforma (cris1954.cat) i adreces de correu | Acceptada (control del DNS [A validar]) |
| [020](020-baixa-de-cluber-sense-restriccio-de-data.md) | Baixa de Cluber sense restricció de data | Acceptada |
| [021](021-persones-no-socies-com-a-convidades.md) | Persones no sòcies com a convidades | Acceptada |
| [022](022-mandats-sepa-escenari-base-b.md) | Mandats SEPA: escenari base B (mandats nous) | Acceptada provisionalment (creditor [A validar]) |
| [023](023-gestio-del-dns.md) | Gestió del DNS i de les credencials dels dominis | Proposada |
| [024](024-abast-minim-i-ordre-per-deixar-cluber.md) | Abast mínim i ordre de construcció per deixar Cluber (05a/05b) | Acceptada (mode real del 05a: vegeu 025) |
| [025](025-dos-nivells-de-produccio.md) | Dos nivells de producció: mandats (05a) i producció completa (05b) | Acceptada (porta 3 per nivells fixada; clau del nivell 1 [A validar amb Stripe]) |
| [026](026-duplicar-activitats-al-modul-02.md) | Duplicar activitats es construeix al mòdul 02 | Acceptada |
| [027](027-estructura-basica-de-carrec-i-pagament.md) | Estructura bàsica de càrrec i pagament a la 00; la 04 hi construeix al damunt | Acceptada |
| [028](028-esborrat-rgpd-i-registre-d-activitat.md) | Esborrat RGPD: anonimitzar, bloquejar el que obliga la llei i referència anònima al registre | Acceptada (terminis [A validar amb la gestoria]) |
| [029](029-compte-personal.md) | «Compte personal» en lloc de «compte de soci» | Acceptada |
| [030](030-sistema-de-disseny.md) | Sistema de disseny: tokens en dos temes, colors per zona, tipografia, punts de canvi i logotips | Acceptada (ampliada per 031 i 032; fletxes, logotip, fonts i pila del frontend [A validar]) · ampliada per 034 |
| [031](031-estil-neumorfic-limitat.md) | Estil neumòrfic limitat (selector de tema, avatars, carnet i pastilla de navegació pública) | Acceptada (amplia la 030; abast als socis ajustat per 032) · ampliada per 034 |
| [032](032-immersio-socis-i-centre.md) | Immersió al compte personal, logotip més gran i secció del Centre a la web pública | Acceptada (amplia la 030; bitàcola, carnet i textos del Centre [A validar]) · ampliada per 034 |
| [033](033-migracio-nextjs-once-ui.md) | Migrar els wireframes a Next.js i Once UI Core | Descartada (es mantenen HTML i CSS plans; vegeu 034) |
| [034](034-patrons-magic-portfolio.md) | Patrons de Magic Portfolio com a referència visual (sense codi): sortida destacada, memòries de projectes, notícies amb data, galeria i butlletí | Acceptada (amplia la 030, 031 i 032; contingut, fotos, butlletí i manteniment [A validar]) |
| [035](035-dades-nomes-dins-ue.md) | Totes les dades personals es tracten només dins la UE | Acceptada (afecta 002, 004, 007, 011, 017, 022, 023, 024 i 025; vegeu 042) |
| [036](036-fecdas-alia.md) | La FECDAS és un aliat, sense acord d'integració ni de finançament | Acceptada |
| [037](037-pressupost-amb-web-installable.md) | Pressupost amb web instal·lable i proveïdors dins la UE (≈160 €/any sense IVA) | Proposada, pendent de la junta (amplia 016) |
| [038](038-planificar-sense-dates.md) | Planificar per dependències i valor, sense dates | Acceptada |
| [039](039-numeros-de-soci-no-es-reutilitzen.md) | Els números de soci no es reutilitzen | Acceptada de manera provisional |
| [040](040-impagat-es-marca-a-ma.md) | L'impagat es marca a mà | Acceptada de manera provisional |
| [041](041-web-installable-i-avisos-sense-push.md) | Web instal·lable i avisos dins l'app i per correu, sense push | Acceptada com a camí per defecte (botigues: pendent de la junta) |
| [042](042-proveidors-substituits-pel-requisit-ue.md) | Proveïdors substituïts pel requisit UE: Cloudflare, Sentry, Brevo (condicional) i Stripe | Acceptada (substitueix en part 002, 007, 011, 017 i 023) |
| [043](043-proveidor-de-pagaments-dins-la-ue.md) | Proveïdor de pagaments dins la UE i pagament sense sortir de l'app | Acceptat l'ordre de recomanació; proveïdor pendent de verificar (P-44, P-45) |
| [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md) | Domiciliació SEPA pròpia: IBAN i mandat xifrats, només per a aquest ús | Acceptada com a camí per defecte, revisable si el banc o el proveïdor ofereixen custòdia de mandats (excepció a RN-70 de la spec 00) |
| [045](045-correccio-transferencia-conciliada-per-error.md) | Corregir una transferència conciliada amb el càrrec equivocat (pagat → pendent) | Acceptada (amplia RN-67 de la spec 00) |
| [046](046-interficie-django-htmx-servida-des-del-vps.md) | Interfície amb plantilles de Django i HTMX, servida des del VPS (HTMX sense CDN) | Acceptada (substitueix la part de frontend de la 002; resol la pila del frontend de la 030) |
| [047](047-planning-font-unica-de-l-especificacio.md) | `docs/planning.md` és la font única de l'especificació de cada mòdul | Acceptada (amplia la 008) |
| [048](048-reobrir-carrec-retornat.md) | Reobrir un càrrec retornat (retornat → pendent) en reintentar-lo o oferir l'alternativa | Acceptada (amplia RN-67 de la spec 00) |
| [049](049-peces-noves-a-moduls-aprovats-per-al-02.md) | Dues peces noves a mòduls aprovats per al 02: lectura de la llicència (01) i esdeveniment «càrrec pagat» (05b) | Acceptada (amplia el M01 i el M05b sense canviar-ne les regles) |
| [050](050-addenda-tresoreria-despeses-ingressos-i-periodes.md) | Addenda de la 04: despeses, altres ingressos, anul·lació i bloqueig de període tancat | Acceptada (addenda del M04 sense canviar-ne les regles) |
| [051](051-abast-de-la-044-i-documents-de-justificacio.md) | Abast de la 044 i documents de justificació amb IBAN (còpia emmascarada) | Acceptada (aclareix la 044 sense modificar-la) |
| [052](052-llicencia-font-unica-al-06.md) | La llicència té una sola font, el 06; el 01 en guarda una còpia de lectura | Acceptada (addenda del M01 sense canviar-ne les regles) |
| [053](053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md) | Addenda a la 050: el bloqueig de període tancat només afecta els moviments del 09; els d'origen extern entren al període obert | Acceptada (precisa RN-T28 sense canviar cap altra regla) |
| [054](054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md) | Addenda a la 052: versió dels esdeveniments de llicència i comprovació diària de la còpia del 01 | Acceptada (addenda del M01 sense canviar-ne les regles) |
| [055](055-ajustos-configurables-i-addendes.md) | Valors configurables: peça comuna d'ajustos a la 00, addendes al 01, 05a i 05b, avís dels canvis de diners i prova de la durada del període | Acceptada (addendes sense canviar cap regla aprovada) |

Contradiccions i decisions que ha de validar la junta: [pendents.md](pendents.md).
