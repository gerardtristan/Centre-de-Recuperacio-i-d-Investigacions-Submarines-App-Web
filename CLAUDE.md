# CLAUDE.md — Plataforma C.R.I.S.

## Projecte
Plataforma app-web pròpia per al C.R.I.S. (club de busseig de Barcelona): socis, cursos, sortides, material, tresoreria, llicències, web pública i dashboard. Primer web (PWA responsive); app nativa més endavant, no ara. Projecte de l'assignatura Emprenedoria Digital (UAB); el client és real.

## Idioma
Català per a documents, interfície i comentaris de cara a l'usuari. Noms de codi coherents (decidir-ho una vegada i no barrejar).

## On és cada cosa
- `README.md`: estat del projecte i mapa de carpetes.
- `docs/context-projecte.md`: context del club, processos i decisions (v4, 27/10/2026; el v3 original és a `docs/arxiu/context-projecte-v3-2026-10-20.pdf`).
- `docs/funcionalitats-processos/funcionalitats-processos.pdf` (i `.docx` editable): funcionalitats i processos per mòdul.
- `docs/checklist-produccio.md`: portes de qualitat 0 a 3. Consulta-la abans de donar un mòdul per acabat.
- `docs/metodologia-sdd.md`: com es treballa amb especificacions.
- `docs/arquitectura-integracions.md`: components, proveïdors externs, fluxos de pagament, variables d'entorn i riscos.
- `docs/decisions/`: una decisió per fitxer (NNN-nom.md). `docs/decisions/pendents.md`: contradiccions i decisions que ha de validar la junta.
- `docs/context/`: fonts originals (instruccions). `entrevistes.docx` no és al repositori (dades personals) [A validar fins que s'anonimitzi].
- `docs/entregues/`: lliuraments de l'assignatura. `docs/arxiu/`: versions antigues (mai s'esborren).
- `design/`: mapa de la plataforma i arbre de processos (HTML). `assets/marca/`: logotips.
- `docs/planning.md`: **font única** de l'especificació i el pla de cada mòdul, amb 14 seccions i àncores estables (decisió 047). `specs/00-base-comuna/spec.md` és vigent fins que el mòdul 00 tingui secció aprovada. La spec 04 v2 és a l'arxiu (`docs/arxiu/spec-04-tresoreria-v2-2026-10-27.md`) des que es va aprovar la secció M04.
No carreguis tot al començar. Llegeix només el que cal per a la tasca.

## Com es treballa (Spec-Driven Development)
1. No s'escriu codi d'un mòdul sense la seva secció de `docs/planning.md` aprovada (decisió 047).
2. Si una spec té una pregunta oberta ([A validar]) que afecta una regla de negoci, no implementis aquesta part: pregunta.
3. Flux: spec, aclarir, pla, tasques, implementar. Una tasca = un canvi petit amb proves.
4. Si canvia una regla, actualitza primer `docs/planning.md` i després el codi. No dupliquis el contingut del pla en cap altre fitxer: enllaça-hi per l'àncora.
5. Formalitat segons risc: spec completa per a finances, pagaments, autenticació, permisos, RGPD i importacions; spec d'una pàgina per a contingut web, dashboard i conferències; només ticket per a errors petits.

## Mòduls (ordre de construcció, decisions 024 i 060)
Numeració fixa (`docs/planning.md#estat`): 00 Base comuna, 01 Socis i carnet digital, 02 Activitats (cursos i sortides), 03 Material, 04 Tresoreria (part mínima), 05a Alta del mètode de pagament i mandats, 05b Cobraments, 06 Llicències, 07 Web pública, 08 Dashboard, 09 Marge, despeses, ajuts i facturació (abans «resta de la 04»), 10 Missatges i xat per activitat, 11 Departament d'Història i conferències, 12 Idees noves (avatars de fauna marina i bitàcola), 13 Botiga en línia (fora d'abast ara). Cap mòdul no canvia de número; un de nou s'afegeix al final. El número no és l'ordre de construcció.

**Ordre de construcció:**
- **Primer mòdul que es pot començar:** el 01 (Socis i carnet), amb les peces de la 00 que necessita (`docs/planning.md#primer-modul`). Aprovats al pla: 01, 04, 05a, 05b, 02, 03, 06 i 09.
- **Fase 1, abast mínim per deixar Cluber:** 00 Base comuna → 01 Socis i carnet (amb registre mínim de llicència: tipus, data d'alta i de caducitat) → 04 Tresoreria, part mínima → 05a Alta del mètode de pagament i signatura de mandats en mode real → 05b Cobraments, remeses, retornats, devolucions i conciliació.
- **Fase 2** (ordre de la decisió 060): 06 Llicències → 02 Activitats → 03 Material → 09 Marge, despeses, ajuts i facturació → 07 Web pública → 08 Dashboard.
- **Després:** 10, 11 i 12.

Detall de l'abast mínim: `docs/arquitectura-integracions.md` §9.
Estructura de diners (decisió 027): la 00 té l'estructura bàsica de càrrec i pagament (cèntims, estats, mètodes, departament, cap IBAN); la tresoreria (04) hi construeix al damunt (moviments, ingressos, comissions, comptes i conciliació) i va abans de pagaments (05); la integració amb el proveïdor de pagaments, darrere d'un adaptador (decisió 043), és a 05.
Duplicar activitats és un servei comú previst a la 00 que es construeix al mòdul 02 (decisió 026).
Nota: el document de funcionalitats (0–11) i el mapa de la plataforma v8 (M00–M12) fan servir altres numeracions; la correspondència és a `docs/planning.md#numeracio`.

## Regles que sempre s'han de complir
- Diners en cèntims (enter), moviments immutables; les correccions són anul·lacions amb motiu. Marge d'una activitat = ingressos - despeses - cost de material.
- Tot ingrés i tota despesa té departament (centre de cost); les comissions de quotes van a «General / Quotes de socis».
- Persona separada de soci. Un no soci (alumne, assistent, llicència d'un dia) també és una persona: no té compte per defecte, s'inscriu i paga com a convidat amb un enllaç segur, i el compte és opcional (decisió 021).
- Cap dada de salut a la plataforma.
- Mai dades reals de socis fora de producció: només dades inventades.
- Cada endpoint exigeix autenticació i permís per defecte; els públics s'han de declarar de manera explícita.
- Permisos en dos nivells: rol i objecte (el soci només veu el seu; l'instructor només les seves sessions). Els permisos de cada rol són dades: només l'administrador assigna i retira rols i edita els permisos des de l'app, amb TOTP, nota, resum dels afectats i registre, i mai pot quedar cap administrador operatiu. El President no gestiona usuaris, rols ni permisos. Les regles de seguretat i d'integritat són codi i no s'editen (decisió 059; configuració inicial a `docs/planning.md#rols-i-permisos-059-matriu`). Veure el dashboard no dona accés a cap dada personal.
- Cada persona té un únic perfil. Un administrador té dos comptes lligats al perfil: personal (abans «compte de soci», decisió 029; entra amb correu únic, recupera i verifica per correu) i administrador (entra amb nom d'usuari únic per l'entrada separada; pot tenir diversos rols; correu no únic i només per a notificacions; **mai** recupera la contrasenya per correu: la restableix un altre administrador o s'hi entra amb codis de recuperació fora de línia). El registre d'activitat guarda quin compte ha fet cada acció (decisions 015 i 018).
- Doble factor (TOTP) obligatori per a qualsevol compte que entri per l'administració (inclosos instructor i Departament d'Història) i per als comptes d'emergència; opcional per als comptes personals.
- Esborrar les dades d'una persona (RGPD) vol dir desactivar-ne els comptes i anonimitzar-ne les dades personals; els registres econòmics (factures, cobraments, despeses, moviments) no s'eliminen mai: les dades personals que hi surten es bloquegen i, passat el termini legal [A verificar: gestoria, Q-14], s'anonimitzen (decisió 058, punt 7); al registre d'activitat, el que identifica la persona se substitueix per una referència anònima (decisió 028).
- Domini de la plataforma: cris1954.cat. Remitent dels correus a cris1954.cat amb resposta a cris@cris.es (decisió 019).
- Registre d'activitat (qui, quan, què, valor anterior) en dades de socis i diners.
- Secrets fora del repositori. Cap clau ni contrasenya al codi, als registres ni als exemples.
- Notificacions de pagament: verificar la firma i ser idempotents; mai donar un pagament per fet només pel navegador.
- Mètodes (decisions 017 i 058): quotes amb targeta guardada (el mètode recomanat si el proveïdor permet guardar-la; si no, la domiciliació SEPA), domiciliació SEPA, targeta, Bizum o transferència (permesa, sense obligar-hi); inscripcions i llicències amb targeta, Bizum o transferència. La domiciliació només s'aplica a pagaments recurrents. Registre manual amb motiu [A validar, P-12].
- Domiciliacions: avís previ, reintent controlat, alternativa de pagament si falla i estat «retornat» amb conseqüències definides a la spec 05b.
- Proveïdor de pagaments (decisió 043; candidat PaynoPain [A verificar: P-44, P-45]) en mode de proves excepte en els dos nivells de producció, cadascun amb autorització expressa de la junta (decisions 025 i 042):
  - **Nivell 1, producció de mandats** (05a acabat i provat): dades reals **només per recollir el mètode de pagament i els mandats**; **cap cobrament real**. Cal haver passat les portes 0-2 (HTTPS, secrets, còpies i restauració, RGPD i consentiments, registre d'activitat) i, de la porta 3, els punts del flux de mandats marcats «N1» a la checklist (A6, E3, E4, B5, B8, G3).
  - **Nivell 2, producció completa** (05b acabat i provat): cobraments reals. És el criteri per deixar Cluber, que es migra una sola vegada i sense restricció de data (decisions 014 i 020).
- IBAN: la plataforma només el guarda **xifrat al mandat i només per a la domiciliació de quotes** (decisió 044, camí per defecte, revisable si el banc o el proveïdor ofereixen custòdia de mandats); mai en cap altre camp, pantalla, registre ni exportació. Abast (decisió 051): la 044 cobreix els IBAN i mandats dels socis; els documents de justificació d'ajuts (factures, comprovants del banc) es guarden xifrats, només els obren el tresorer i la junta, cap eina d'IA els rep i se'n fa una còpia amb l'IBAN emmascarat. El proveïdor de pagaments ha de complir el requisit de dades dins la UE (decisions 035 i 042). Mandats actuals: escenari base B, campanya de mandats nous al 05a (decisions 022, 024 i 025; arquitectura §4.9).
- Una app no escriu als models d'una altra; ho fa a través de serveis.
- Arquitectura: monòlit modular, una sola base de dades.

## Qualitat
- Cada criteri d'acceptació té una prova. Càlculs econòmics amb cobertura completa.
- No es fusiona res si el pipeline falla.
- Definició de fet: proves passades, pipeline verd, porta de la checklist revisada, documentació actualitzada.

## Pila (acordada; detall a `docs/arquitectura-integracions.md`)
Django amb API REST, PostgreSQL, cua de tasques sobre PostgreSQL (sense Redis), Coolify en un VPS de Hetzner (UE), web pública i PWA a Cloudflare Pages, fitxers a Scaleway Object Storage (París), correu amb Brevo, pagaments amb un proveïdor dins la UE darrere d'un adaptador (decisió 043; candidat PaynoPain [A verificar]).
Comandes: [completar quan existeixi el projecte: instal·lar, executar, proves, lint, migracions].

## Comportament
- Abans de fer canvis grans, proposa el pla i espera confirmació.
- Si falta informació del club, no t'ho inventis: pregunta o marca-ho com a [A validar].
- Si veus un error o una suposició feble en una spec o en una decisió anterior, digues-ho.
- Respon de manera directa i pas a pas.
