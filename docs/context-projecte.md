# Context del projecte — Emprenedoria Digital · C.R.I.S.

> **Font:** `docs/context/context-projecte.pdf` (context v3, 20/10/2026). Transcripció a Markdown del 27/10/2026.
> El contingut és el de l'original. Les notes marcades amb **⚠ Contradicció** no són a l'original: indiquen on un altre document diu una cosa diferent. No es resolen aquí; es llisten a [decisions/pendents.md](decisions/pendents.md).

## 1. Meta del projecte
Dissenyar i construir, per mòduls prioritzats i validats amb la junta, una plataforma web pròpia per al C.R.I.S. (Centre de Recuperació i Investigacions Submarines) que centralitzi la gestió de socis, cursos, sortides, material i tresoreria i calculi automàticament el marge de cada activitat, dins de les 15 setmanes de l'assignatura Emprenedoria Digital (Grau en Empresa i Tecnologia, UAB, curs 26-27), i deixar-la documentada perquè el club en pugui continuar el desenvolupament i el manteniment.

## 2. L'assignatura (restriccions acadèmiques)
- Aprenentatge basat en reptes reals, format consultoria amb client real. Metodologia AS-IS / TO-BE.
- 8 lliuraments: proposta de repte (10 %), tria i justificació del repte (10 %), establiment d'objectiu i planificació (10 %), desenvolupament del pla (10 %), proposta de valor i pressupost (10 %), pla de millora d'aplicacions i processos (10 %), seguiment i control (10 %), memòria final i presentació (30 %).
- Competències: CM14 (proposta de valor), CM29 (impacte de la innovació), CM30 (pla d'empresa), KM27 (tecnologies), SM08 (presentacions orals), SM10 (impacte en sistemes de gestió).
- El lliurable principal és un business case (diagnòstic AS-IS, proposta TO-BE, cas pràctic comparatiu d'una sortida real, cost-benefici) amb una prova de concepte funcional i una presentació.
- El codi és la prova de concepte, no tota la nota: la part de consultoria (entrevistes, rànquing, cost-benefici, seguiment, memòria) pesa molt. Cal dedicar-hi temps.
- Document incremental: es revisa cada dijous. Es manté en versions (v3 a 20/10/2026).

## 3. El client: C.R.I.S.
- Club esportiu de busseig fundat el 26/04/1954 a Barcelona, pioner a la península. Entitat sense ànim de lucre gestionada per una junta. Seu: Moll de la Vela, 1, Sant Adrià de Besòs.
- Història: centre d'investigació i serveis subaquàtics amb departaments de biologia, enginyeria, escola, cinema, rescat, arqueologia i medicina. El departament mèdic es va constituir el 1986 en una societat independent, CRIS-UTH (no és «pròpia» del club; relació actual a confirmar).
- Ara: club de busseig esportiu i recreatiu amb cursos, sortides, sortides de medi ambient, conferències gratuïtes (branca històrica), llicències federatives (FECDAS) i carnet digital.
- Rumb: reposicionament cap a la conservació del medi marí (sortides ambientals, línia de ciència ciutadana Minka [A validar]) i modernització digital.
- Socis: simpatitzant 35 €/any; ple dret 90 €/any.
- Contactes de la fitxa: tres persones de la junta (noms a la font original; no es transcriuen aquí per minimitzar dades personals al repositori; càrrec de cadascuna a confirmar).
- Volum de referència (encàrrec del 26/10/2026): uns 150 socis i uns 300 subscriptors del butlletí [A validar amb dades reals].

## 4. Situació actual (AS-IS)
- Cluber: socis, quotes, alguns cobraments, carnet.
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
5. Web pública i anuncis (Should)
6. Llicències federatives: registre i recordatoris (Should)
7. Dashboard amb KPI (Should)
8. Facturació (Could; cal confirmar IVA i programa)
9. Conferències (Could)
10. Botiga en línia (Won't ara)

Fora d'abast: substituir els cobraments de Cluber, dades de salut, integració directa amb la federació.

> **⚠ Contradicció (cobraments).** El context v3 i el document incremental (§2.3, §4.5) deixen fora d'abast substituir els cobraments de Cluber. El document de funcionalitats (§1, §2, §7) diu que «Cluber es deixa de fer servir» i que els pagaments (targeta, Bizum, rebut domiciliat) s'integren a l'app. L'encàrrec d'arquitectura del 26/10/2026 inclou Stripe. Vegeu P-01 a [pendents.md](decisions/pendents.md).
>
> **⚠ Contradicció (facturació).** Aquí és «Could»; al document de funcionalitats (§7) la facturació via servei homologat Verifactu forma part de la tresoreria, que és imprescindible. Vegeu P-02.
>
> **⚠ Contradicció (numeració de mòduls).** CLAUDE.md i la metodologia fan servir 9 mòduls (0-8); el document de funcionalitats en fa servir 12 (0-11) amb una altra numeració. Vegeu P-03.

## 7. Arquitectura
- Una sola base de dades i un sol backend; tres zones: web pública, àrea de socis i panell d'administració (entrada separada, doble factor).
- Rols: soci, tresorer, secretaria, responsable de cursos i sortides, responsable de material, administrador. Permisos per rol (RBAC) i registre d'activitat.
- Primer web (responsive i instal·lable com a PWA); app d'escriptori només més endavant si cal.
- Cluber continua per als cobraments al principi; la plataforma importa CSV de Cluber i de l'extracte bancari.
- Cap registre econòmic s'esborra: s'anul·la amb motiu. Numeració de factures correlativa.
- Marge d'activitat = ingressos menys despeses menys cost de material.

> **⚠ Contradicció (rols).** El document de funcionalitats (§2) afegeix dos rols: instructor i Departament d'Història. Vegeu P-04.
>
> Detall tècnic actual de la pila i les integracions: [arquitectura-integracions.md](arquitectura-integracions.md).

## 8. Decisions pendents (no programar sense confirmar)
- Canvi de simpatitzant a ple dret: diferència (55 €), import complet o prorrata.
- Número de soci: reutilitzar els de les baixes?
- Impagats: termini i conseqüències.
- Material llogat: el paga el club o el participant? Cost d'ús del material propi.
- Llicència no vigent: avís o bloqueig.
- Cancel·lacions i devolucions.
- IVA i programa de facturació. Pla real de Cluber.
- Relació amb CRIS-UTH i abast de medicina hiperbàrica.

## 9. Requisits no funcionals
- RGPD: consentiments amb data i versió, exportar i esborrar dades d'un soci, mínim de dades, dades de salut fora d'abast.
- Seguretat: doble factor a administradors, comptes d'emergència, còpies de seguretat provades, secrets fora del repositori.
- Dades de prova (inventades) fins que el tractament estigui resolt.
- Manteniment: responsable a la junta, documentació, repositori amb dos accessos, calendari de manteniment.
- Pressupost: zero en llicències. Cost directe orientatiu 100-120 €/any (servidor, còpies), domini existent.

> **⚠ Contradicció (doble factor).** Aquí: «administradors». Funcionalitats §2: administradors i com a mínim dos comptes d'emergència. Checklist C2 (abans del 27/10/2026): administradors i tresorer. Recomanació del 27/10/2026: administrador, tresorer, secretaria i comptes d'emergència. Vegeu P-05.
>
> **⚠ Contradicció (pressupost).** L'arquitectura del 27/10/2026 estima un cost fix superior als 100-120 €/any quan s'hi afegeixen el correu de pagament, el VPS de proves i el destí de còpies creuades. Vegeu P-06 i [arquitectura-integracions.md §3](arquitectura-integracions.md#3-cost-mensual-estimat).
>
> **⚠ Dada de salut.** Funcionalitats §2 planteja guardar com a molt la data de validesa del certificat mèdic [A validar]. Cal confirmar si aquesta data es considera dada de salut. Vegeu P-07.

## 10. Anàlisi de mercat (resum)
- Alternatives: Cluber (des de 599 €/any), programari genèric per a clubs (Clupik, SportEasy, Playoff) i programari de busseig (Dive Admin, Anolla, Kananas). Les funcions de material per participant, marge per activitat i justificació d'ajuts per departament no consten a les ofertes consultades (a verificar amb demostració).
- Justificació de construir: encaix, una sola font de dades, propietat de dades i codi, cost sostenible, creixement per mòduls. Risc principal: manteniment i dependència de persones.

## 11. Pla de 15 setmanes
- 1-3: entrevistes (tresoreria; cursos, sortides, medi ambient i socis; informàtica) i mapa AS-IS.
- 4-5: rànquing (impacte, esforç, RICE) i tall MoSCoW validats amb la junta.
- 6-8: disseny (rols, model de dades, processos, pantalles).
- 9-12: construcció dels mòduls Must.
- 13: cas pràctic amb una sortida real i comparativa del marge.
- 14-15: business case, pla de manteniment, memòria i presentació.

## 12. Convencions de treball
- Idioma: català per a documents i interfície; codi i noms tècnics en anglès o català coherent (decidir-ho una vegada).
- Cada mòdul és independent, té proves dels càlculs i un issue amb criteris d'acceptació.
- Tot el que no estigui confirmat es marca [A validar].
