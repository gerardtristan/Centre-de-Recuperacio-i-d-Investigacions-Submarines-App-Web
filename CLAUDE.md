# CLAUDE.md — Plataforma C.R.I.S.

## Projecte
Plataforma app-web pròpia per al C.R.I.S. (club de busseig de Barcelona): socis, cursos, sortides, material, tresoreria, llicències, web pública i dashboard. Primer web (PWA responsive); app nativa més endavant, no ara. Projecte de l'assignatura Emprenedoria Digital (UAB); el client és real.

## Idioma
Català per a documents, interfície i comentaris de cara a l'usuari. Noms de codi coherents (decidir-ho una vegada i no barrejar).

## On és cada cosa
- `README.md`: estat del projecte i mapa de carpetes.
- `docs/context-projecte.md`: context del club, processos i decisions (versió Markdown del context v3; original a `docs/context/context-projecte.pdf`).
- `docs/funcionalitats-processos/funcionalitats-processos.pdf` (i `.docx` editable): funcionalitats i processos per mòdul.
- `docs/checklist-produccio.md`: portes de qualitat 0 a 3. Consulta-la abans de donar un mòdul per acabat.
- `docs/metodologia-sdd.md`: com es treballa amb especificacions.
- `docs/arquitectura-integracions.md`: components, proveïdors externs, fluxos de pagament, variables d'entorn i riscos.
- `docs/decisions/`: una decisió per fitxer (NNN-nom.md). `docs/decisions/pendents.md`: contradiccions i decisions que ha de validar la junta.
- `docs/context/`: fonts originals (context, instruccions). `entrevistes.docx` no és al repositori (dades personals) [A validar fins que s'anonimitzi].
- `docs/entregues/`: lliuraments de l'assignatura. `docs/arxiu/`: versions antigues (mai s'esborren).
- `design/`: mapa de la plataforma i arbre de processos (HTML). `assets/marca/`: logotips.
- `specs/NN-modul/`: spec.md, plan.md, data-model.md, tasks.md de cada mòdul.
No carreguis tot al començar. Llegeix només el que cal per a la tasca.

## Com es treballa (Spec-Driven Development)
1. No s'escriu codi d'un mòdul sense `spec.md` revisada.
2. Si una spec té una pregunta oberta ([A validar]) que afecta una regla de negoci, no implementis aquesta part: pregunta.
3. Flux: spec, aclarir, pla, tasques, implementar. Una tasca = un canvi petit amb proves.
4. Si canvia una regla, actualitza primer la spec i després el codi.
5. Formalitat segons risc: spec completa per a finances, pagaments, autenticació, permisos, RGPD i importacions; spec d'una pàgina per a contingut web, dashboard i conferències; només ticket per a errors petits.

## Mòduls (ordre de construcció)
0 Base comuna, 1 Socis i carnet, 2 Activitats (cursos i sortides), 3 Material, 4 Tresoreria i marge, 5 Pagaments, 6 Llicències, 7 Web pública, 8 Dashboard. Botiga en línia: fora d'abast ara.
Tresoreria (04) va abans de pagaments (05): el model de càrrec, pagament i ingrés viu a 04; la integració amb la passarel·la (Stripe) és a 05.
Nota: el document de funcionalitats fa servir una altra numeració (12 mòduls); vegeu `docs/decisions/pendents.md`.

## Regles que sempre s'han de complir
- Diners en cèntims (enter), moviments immutables; les correccions són anul·lacions amb motiu. Marge d'una activitat = ingressos - despeses - cost de material.
- Tot ingrés i tota despesa té departament (centre de cost); les comissions de quotes van a «General / Quotes de socis».
- Persona separada de soci. Un no soci (alumne, assistent, llicència d'un dia) també és una persona.
- Cap dada de salut a la plataforma.
- Mai dades reals de socis fora de producció: només dades inventades.
- Cada endpoint exigeix autenticació i permís per defecte; els públics s'han de declarar de manera explícita.
- Permisos en dos nivells: rol i objecte (el soci només veu el seu; l'instructor només les seves sessions).
- Doble factor (TOTP) obligatori per a administrador, tresorer, secretaria (qualsevol rol amb accés a diners o dades de socis) i per als comptes d'emergència; codis de recuperació guardats fora de línia [pendent de validació de la junta].
- Registre d'activitat (qui, quan, què, valor anterior) en dades de socis i diners.
- Secrets fora del repositori. Cap clau ni contrasenya al codi, als registres ni als exemples.
- Notificacions de pagament: verificar la firma i ser idempotents; mai donar un pagament per fet només pel navegador.
- Stripe sempre en mode de proves fins que la junta autoritzi producció per escrit.
- Una app no escriu als models d'una altra; ho fa a través de serveis.
- Arquitectura: monòlit modular, una sola base de dades.

## Qualitat
- Cada criteri d'acceptació té una prova. Càlculs econòmics amb cobertura completa.
- No es fusiona res si el pipeline falla.
- Definició de fet: proves passades, pipeline verd, porta de la checklist revisada, documentació actualitzada.

## Pila (acordada; detall a `docs/arquitectura-integracions.md`)
Django amb API REST, PostgreSQL, cua de tasques sobre PostgreSQL (sense Redis), Coolify en un VPS de Hetzner (UE), web pública i PWA a Cloudflare Pages, fitxers a Scaleway Object Storage (París), correu amb Brevo, pagaments amb Stripe.
Comandes: [completar quan existeixi el projecte: instal·lar, executar, proves, lint, migracions].

## Comportament
- Abans de fer canvis grans, proposa el pla i espera confirmació.
- Si falta informació del club, no t'ho inventis: pregunta o marca-ho com a [A validar].
- Si veus un error o una suposició feble en una spec o en una decisió anterior, digues-ho.
- Respon de manera directa i pas a pas.
