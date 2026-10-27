# Context del projecte — Emprenedoria Digital · C.R.I.S.

> **Versió 4 · 27/10/2026.** Parteix del context v3 (20/10/2026), que es conserva a `docs/arxiu/context-projecte-v3-2026-10-20.pdf`, i hi incorpora les decisions [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md) a [019](decisions/019-domini-i-correu.md).
>
> **Canvis respecte a la v3:** abast dels cobraments i Cluber (§6-7), domini (§3 i §7), doble factor i comptes (§9), pressupost (§9) i forma de treballar per mòduls (§1 i §11).
>
> **Actualització del 27/10/2026 (dins la v4):** cobraments de Cluber i el seu cost (§4), mandats SEPA (§8), persones no sòcies com a convidades (§9), control del DNS (§3) i objectiu orientatiu de canvi de Cluber (§11). Decisions [021](decisions/021-persones-no-socies-com-a-convidades.md) a [023](decisions/023-gestio-del-dns.md).
>
> Les contradiccions amb altres documents que encara no s'han resolt són a [decisions/pendents.md](decisions/pendents.md).

## 1. Meta del projecte
Dissenyar i construir, per mòduls prioritzats i validats amb la junta, una plataforma web pròpia per al C.R.I.S. (Centre de Recuperació i Investigacions Submarines). La plataforma ha de centralitzar la gestió de socis, cursos, sortides, material, tresoreria i pagaments, i calcular automàticament el marge de cada activitat. S'ha de deixar documentada perquè el club en pugui continuar el desenvolupament i el manteniment.

El treball s'organitza per mòduls i passos (especificació, aclariment, pla, tasques, implementació), no per setmanes. El calendari de l'assignatura és una restricció acadèmica (§2), no el pla de construcció.

## 2. L'assignatura (restriccions acadèmiques)
- Emprenedoria Digital, Grau en Empresa i Tecnologia, UAB, curs 26-27: 15 setmanes lectives.
- Aprenentatge basat en reptes reals, format consultoria amb client real. Metodologia AS-IS / TO-BE.
- 8 lliuraments: proposta de repte (10 %), tria i justificació del repte (10 %), establiment d'objectiu i planificació (10 %), desenvolupament del pla (10 %), proposta de valor i pressupost (10 %), pla de millora d'aplicacions i processos (10 %), seguiment i control (10 %), memòria final i presentació (30 %).
- Competències: CM14 (proposta de valor), CM29 (impacte de la innovació), CM30 (pla d'empresa), KM27 (tecnologies), SM08 (presentacions orals), SM10 (impacte en sistemes de gestió).
- El lliurable principal és un business case (diagnòstic AS-IS, proposta TO-BE, cas pràctic comparatiu d'una sortida real, cost-benefici) amb una prova de concepte funcional i una presentació.
- El codi és la prova de concepte, no tota la nota: la part de consultoria (entrevistes, rànquing, cost-benefici, seguiment, memòria) pesa molt. Cal dedicar-hi temps.
- Document incremental: es revisa cada dijous. Es manté en versions (v3 a 20/10/2026). La propera versió ha de recollir els canvis d'aquest context v4 (vegeu P-14 a [pendents.md](decisions/pendents.md)).

## 3. El client: C.R.I.S.
- Club esportiu de busseig fundat el 26/04/1954 a Barcelona, pioner a la península. Entitat sense ànim de lucre gestionada per una junta. Seu: Moll de la Vela, 1, Sant Adrià de Besòs.
- Història: centre d'investigació i serveis subaquàtics amb departaments de biologia, enginyeria, escola, cinema, rescat, arqueologia i medicina. El departament mèdic es va constituir el 1986 en una societat independent, CRIS-UTH (no és «pròpia» del club; relació actual a confirmar).
- Ara: club de busseig esportiu i recreatiu amb cursos, sortides, sortides de medi ambient, conferències gratuïtes (branca històrica), llicències federatives (FECDAS) i carnet digital.
- Rumb: reposicionament cap a la conservació del medi marí (sortides ambientals, línia de ciència ciutadana Minka [A validar]) i modernització digital.
- Socis: simpatitzant 35 €/any; ple dret 90 €/any.
- Volum de referència: uns 150 socis i uns 300 subscriptors del butlletí [A validar amb dades reals].
- Contactes de la fitxa: tres persones de la junta. Els noms són a la font original i no es transcriuen per minimitzar dades personals al repositori; el càrrec de cadascuna està per confirmar.
- Dominis i correu ([019](decisions/019-domini-i-correu.md)):
  - **cris1954.cat**: domini de la plataforma i de la web nova, ja pagat pel club.
  - **cris@cris.es**: adreça de contacte del club.
  - **cris.barcelona**: web actual (WordPress). Redirecció cap a la web nova [A validar].
  - El club controla el DNS de cris1954.cat i de cris.es; qui té l'accés concret és [A validar]. Recomanació: delegar cris1954.cat a Cloudflare i guardar les credencials en un gestor compartit amb dues persones ([023](decisions/023-gestio-del-dns.md)).

## 4. Situació actual (AS-IS)
- Cluber: socis, quotes, alguns cobraments (inclosos els rebuts domiciliats actuals) i carnet. No hi ha contracte amb Cluber: el club el pot deixar quan vulgui.
  - Cluber cobra els rebuts domiciliats a través del seu compte i després ingressa al club l'import menys un percentatge (tresoreria, 27/10/2026; percentatge [A validar]). Per tant, el creditor dels mandats actuals seria Cluber [A validar amb un rebut o la documentació de Cluber].
  - Permet exportar les dades (socis, IBAN i referències); format [A validar].
  - Segons el document incremental §1.2, també intervé en les llicències federatives (P-28).
- App del banc, càlculs a mà i Excel: ingressos, despeses, marge de cada activitat, recompte de sortides i de material.
- Gmail i WhatsApp (grup per sortida i grup general de socis): comunicació.
- Web cris.barcelona (WordPress): informació i conferències.
- Problema: informació en 4-5 eines que es creuen a mà; errors, temps perdut, dependència de persones, sense visió del marge ni de la tresoreria.

## 5. Processos coneguts
- Tresoreria: comptabilitat (ingressos i despeses), factures, comptabilització de despeses per departament per demanar ajuts.
- Cursos: anunci, inscripcions, horari teòric i pràctic, control del material que usa cada participant (propi o llogat al centre de busseig).
- Sortides i sortides de medi ambient: igual que cursos sense teoria; programa del dia i control de material.
- Socis: llistat amb número de soci, carnet digital, altes, baixes, canvi de simpatitzant a ple dret.
- Llicències federatives: altes, baixes i renovacions anuals.
- Informàtica: Cluber, anuncis, butlletins, web, dashboard amb KPI.
- Branca històrica: conferències gratuïtes amb inscripció.
- Botiga de merchandising: fase futura, fora d'abast.

## 6. Abast i prioritats (MoSCoW, hipòtesi inicial)
1. Socis i carnet digital (Must)
2. Cursos i sortides (Must)
3. Material per participant i cost (Must)
4. Tresoreria: ingressos, despeses, marge per activitat i per departament, justificació d'ajuts (Must)
5. Pagaments integrats: domiciliació SEPA, targeta, Bizum i transferència (Must; és el criteri d'entrada en producció, [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md))
6. Web pública i anuncis (Should)
7. Llicències federatives: registre i recordatoris (Should)
8. Dashboard amb KPI (Should)
9. Facturació (Could; cal confirmar IVA i programa)
10. Conferències (Could)
11. Botiga en línia (Won't ara)

Fora d'abast: dades de salut i integració directa amb la federació.

**Cluber** ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md) i [020](decisions/020-baixa-de-cluber-sense-restriccio-de-data.md)):
- Es migra una sola vegada (socis, dates d'alta, rebuts i mandats si es poden exportar).
- Es deixa quan la plataforma estigui activa amb els pagaments inclosos, és a dir, amb el mòdul 05 acabat i provat. No hi ha restricció de data perquè no hi ha contracte.
- La campanya de quotes en paral·lel que preveu el document de funcionalitats (§9.13) és opcional.

> **⚠ Contradicció (facturació).** Aquí és «Could»; al document de funcionalitats (§7) la facturació via servei homologat Verifactu forma part de la tresoreria, que és imprescindible. Vegeu P-02.
>
> **⚠ Contradicció (numeració de mòduls).** CLAUDE.md i la metodologia fan servir 9 mòduls (0-8); el document de funcionalitats en fa servir 12 (0-11) amb una altra numeració. Vegeu P-03.

## 7. Arquitectura
- Una sola base de dades i un sol backend; tres zones: web pública, àrea de socis i panell d'administració (entrada separada, doble factor).
- Rols: soci, instructor, secretaria, responsable de cursos i sortides, responsable de material, tresorer, Departament d'Història, administrador. Permisos per rol (RBAC) i per objecte, i registre d'activitat. Els rols instructor i Departament d'Història surten del document de funcionalitats §2 (vegeu P-04).
- Primer web (responsive i instal·lable com a PWA); app d'escriptori només més endavant si cal.
- Cobraments dins la plataforma amb Stripe: domiciliació SEPA (quotes, per defecte), targeta i Bizum. Fora de Stripe: transferència amb referència i registre manual ([017](decisions/017-pagaments-metodes-i-domiciliacions.md)). La plataforma importa una sola vegada les dades de Cluber i, de manera periòdica, l'extracte bancari en CSV.
- Cap registre econòmic s'esborra: s'anul·la amb motiu. Numeració de factures correlativa.
- Marge d'activitat = ingressos menys despeses menys cost de material.
- Domini de la plataforma: cris1954.cat ([019](decisions/019-domini-i-correu.md)). Detall tècnic de la pila i les integracions: [arquitectura-integracions.md](arquitectura-integracions.md).

## 8. Decisions pendents (no programar sense confirmar)
- Canvi de simpatitzant a ple dret: diferència (55 €), import complet o prorrata.
- Número de soci: reutilitzar els de les baixes?
- Impagats: termini i conseqüències (inclosos els rebuts domiciliats retornats).
- Material llogat: el paga el club o el participant? Cost d'ús del material propi.
- Llicència no vigent: avís o bloqueig.
- Cancel·lacions i devolucions.
- IVA i programa de facturació.
- Mandats SEPA actuals: escenari base B, campanya de mandats nous ([022](decisions/022-mandats-sepa-escenari-base-b.md)); confirmar el creditor i el format d'exportació (P-21).
- En quin moment de l'any es cobren les quotes anuals: la campanya de mandats ha d'acabar abans de la propera remesa (P-29).
- Relació amb CRIS-UTH i abast de medicina hiperbàrica.

## 9. Requisits no funcionals
- RGPD: consentiments amb data i versió, exportar i esborrar dades d'un soci, mínim de dades, dades de salut fora d'abast.
- Seguretat ([015](decisions/015-doble-factor-i-comptes-administrador.md) i [018](decisions/018-perfil-comptes-i-rols.md)):
  - Cada persona té un únic perfil.
  - Un administrador té dos comptes: soci i administrador.
  - Doble factor obligatori per a qualsevol compte que entri per l'administració; opcional per als comptes de soci.
  - Els comptes d'administrador no recuperen la contrasenya per correu.
  - Comptes d'emergència amb doble factor, còpies de seguretat provades i secrets fora del repositori.
  - Les persones no sòcies no tenen compte per defecte: s'inscriuen i paguen com a convidades amb un enllaç segur; el compte és opcional ([021](decisions/021-persones-no-socies-com-a-convidades.md)).
- Dades de prova (inventades) fins que el tractament estigui resolt.
- Manteniment: responsable a la junta, documentació, repositori amb dos accessos, calendari de manteniment.
- Pressupost ([016](decisions/016-pressupost-produccio-minima.md)): zero en llicències.
  - La junta coneix el cost i s'ha començat amb la producció mínima: uns 160 €/any sense IVA (preus consultats el 27/10/2026), sense cost addicional de domini (cris1954.cat ja està pagat).
  - Les comissions de Stripe són la part variable: uns 53-110 €/any per a les quotes, més un 1,9 % aproximat del que es cobri per targeta o Bizum.
  - Referència: Cluber descompta un percentatge de cada ingrés que cobra [A validar el percentatge]; el preu publicat és des de 599 €/any (si el club el paga a més del percentatge, P-27).
  - Substitueix la previsió anterior de 100-120 €/any.

> **⚠ Dada de salut.** Funcionalitats §2 planteja guardar com a molt la data de validesa del certificat mèdic [A validar]. Cal confirmar si aquesta data es considera dada de salut. Vegeu P-07.

## 10. Anàlisi de mercat (resum)
- Alternatives: Cluber (des de 599 €/any), programari genèric per a clubs (Clupik, SportEasy, Playoff) i programari de busseig (Dive Admin, Anolla, Kananas). Les funcions de material per participant, marge per activitat i justificació d'ajuts per departament no consten a les ofertes consultades (a verificar amb demostració).
- Justificació de construir: encaix, una sola font de dades, propietat de dades i codi, cost sostenible, creixement per mòduls. Risc principal: manteniment i dependència de persones.

## 11. Com s'avança
Per mòduls i passos, seguint [metodologia-sdd.md](metodologia-sdd.md):
1. Entrevistes i mapa AS-IS (fet).
2. Rànquing i tall MoSCoW validats amb la junta.
3. Especificació de cada mòdul en l'ordre de CLAUDE.md, amb les preguntes obertes resoltes.
4. Pla, tasques i implementació de cada mòdul.
5. Cas pràctic amb una sortida real i comparació del marge.
6. Producció en dos nivells ([025](decisions/025-dos-nivells-de-produccio.md)). Nivell 1 (05a): campanya de mandats nous, sense cobraments reals. Nivell 2 (05b acabat i provat): producció completa i migració única de Cluber. Objectiu orientatiu: finals de gener o principis de febrer de 2027. No és una data compromesa: es pot posposar sense cost. L'abast mínim i l'ordre aprovats (00 → 01 → 04 mínim → 05a → 05b) són a l'[arquitectura, §9](arquitectura-integracions.md) i a la [decisió 024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md).
7. Business case, pla de manteniment, memòria i presentació (lliuraments de l'assignatura).

## 12. Convencions de treball
- Idioma: català per a documents i interfície; codi i noms tècnics en anglès o català coherent (decidir-ho una vegada).
- Cada mòdul és independent, té proves dels càlculs i un issue amb criteris d'acceptació.
- Tot el que no estigui confirmat es marca [A validar].
