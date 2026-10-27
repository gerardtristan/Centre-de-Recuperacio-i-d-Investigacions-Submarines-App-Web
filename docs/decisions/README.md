# Registre de decisions

Un fitxer per decisió, numerat (`NNN-nom.md`). Format: data, estat, context, alternatives, decisió, conseqüències i fonts.

Estats: **Acceptada** (es pot aplicar), **Proposada** (pendent de validació de la junta; no s'implementa la part afectada), **Substituïda** (indica per quina).

Una decisió no s'edita per canviar-la: se'n crea una de nova que la substitueix, i a l'antiga es marca l'estat «Substituïda per NNN».

| Núm. | Decisió | Estat |
|---|---|---|
| [001](001-construir-en-lloc-de-comprar.md) | Construir una plataforma pròpia en lloc de comprar | Acceptada (el cost de servidor l'actualitza la 016) |
| [002](002-pila-tecnologica.md) | Pila tecnològica | Acceptada |
| [003](003-autenticacio-doble-factor.md) | Autenticació i doble factor | Substituïda per 015 |
| [004](004-correu.md) | Correu transaccional i butlletí amb Brevo | Acceptada |
| [005](005-fitxers.md) | Fitxers a Scaleway Object Storage | Acceptada |
| [006](006-copies-de-seguretat.md) | Còpies de seguretat creuades i xifrades | Acceptada |
| [007](007-pagaments-stripe.md) | Pagaments amb Stripe més transferència i registre manual | Substituïda per 014 i 017 |
| [008](008-metodologia-sdd.md) | Metodologia Spec-Driven Development | Acceptada |
| [009](009-sistema-de-disseny.md) | Sistema de disseny | Proposada (sense document d'origen) |
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

Contradiccions i decisions que ha de validar la junta: [pendents.md](pendents.md).
