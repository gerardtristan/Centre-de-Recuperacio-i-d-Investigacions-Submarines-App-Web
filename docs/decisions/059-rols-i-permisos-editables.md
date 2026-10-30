# 059 — Rols i permisos editables des de l'app i configuració inicial de la matriu

- **Data:** 30/10/2026
- **Estat:** Acceptada pel responsable del projecte, que dona la matriu per validada (resol P-04 i Q-01). S'aplica amb una **peça comuna de la 00** ([apèndix del pla](../planning.md#rols-i-permisos-059)) i **addendes** als mòduls aprovats (01, 02, 03, 04, 05a, 05b, 06 i 09, amb l'apartat d'ajuts), sense editar-ne cap regla. Amplia la [018](018-perfil-comptes-i-rols.md) i la [055](055-ajustos-configurables-i-addendes.md) sense editar-les. Substitueix **només en els punts que s'indiquen** la matriu de la [spec 00](../../specs/00-base-comuna/spec.md) (§2.2 a §2.4 i RN-45) i les cel·les de les taules «Rols i permisos» dels mòduls que canvien. No toca cap regla de seguretat ni d'integritat.

## Context
- La spec 00 tenia una matriu provisional de 8 rols (P-04, Q-01) i els mòduls del pla, una de 13 rols amb moltes cel·les [A validar: junta].
- El 30/10/2026 el responsable del projecte ha facilitat la taula «Què pot fer cada rol» (document de funcionalitats, §2), amb un rol nou, **President**, i ha decidit que **l'administrador ha de poder, des de l'app i sense tocar codi**:
  1. assignar i retirar un o diversos rols als comptes de gestió;
  2. modificar els permisos de cada rol, amb efecte sobre tots els comptes que el tenen.
- La taula és la **configuració inicial**. Només l'administrador gestiona usuaris, rols i permisos; el President no.
- La revisió de la taula respecte del pla, amb els dubtes D-01 a D-19, és a `/mnt/project-files/plans/rols-i-permisos/revisio-matriu-rols-i-permisos.md` (fora del repositori). El responsable del projecte en va respondre quatre i va acceptar la proposta per defecte de la resta.

## Alternatives
- **Matriu al codi**, com deia la spec 00: cada canvi de permís demana una versió nova de l'aplicació. No compleix la decisió del responsable.
- **Tot editable**, també les regles de seguretat: un error a l'editor podria donar accés a l'IBAN, als documents de justificació o deixar el club sense administrador.
- **Permisos editables amb regles protegides al codi** (la que s'escull).

## Decisió

### 1. Tres capes
| Capa | Què és | Editable des de l'app |
|---|---|---|
| **Permís per rol** | Una acció concreta d'un mòdul (per exemple, registrar una despesa, pagar-la o fer una devolució són tres permisos) | **Sí**, només pel rol administrador |
| **Abast per objecte** | Sobre quins objectes s'aplica el permís, d'una llista tancada que fixa el codi per a cada permís («tots», «les seves activitats», «les seves sessions»…) | En part: l'administrador tria entre els abasts que el codi permet. Els abasts base no s'amplien mai |
| **Camps sensibles** | Quins camps veu qui té el permís de lectura (data de naixement, document, número federatiu, imports, marge, beneficis dels lloguers…) | Només els no protegits |

Autoritzar una acció no autoritza cap altra: cada permís s'atorga sol. L'editor rebutja les combinacions incoherents (per exemple, aprovar sense poder consultar) i no afegeix mai cap permís per deducció.

### 2. Rols
- **Rols de gestió** (s'assignen a comptes d'administrador i es poden editar): Instructor, Secretaria, Responsable de cursos i sortides, Responsable de material, Tresorer, Departament d'Història, Administrador, **President** (nou), Junta, Responsable de comunicació i Responsable de botiga.
- **Junta, Responsable de comunicació i Responsable de botiga** es mantenen: la Junta amb els permisos que el pla ja li donava (ajuts, documents de justificació de la [051](051-abast-de-la-044-i-documents-de-justificacio.md) i consultes); els altres dos sense cap permís fins que s'escriguin el 07, el 10 i el 13.
- **No són rols editables:** Soci (el té el compte personal d'un soci; només accions pròpies), Visitant (sense sessió; endpoints públics declarats al codi) i Participant no soci (el convidat de la [021](021-persones-no-socies-com-a-convidades.md)).
- **President:** només el que diu la taula. El que la taula no li dona, no ho pot fer. Si un compte de President també té un altre rol (per exemple, Junta), té la unió dels dos.
- La llista de rols és fixa: l'administrador no en crea ni en reanomena des de l'app. Un rol nou demana una decisió.

### 3. Configuració inicial
- És la taula del responsable del projecte, separada en permisos concrets a l'[apèndix del pla](../planning.md#rols-i-permisos-059-matriu). Respostes del responsable:
  - El preu que l'instructor escriu en un **lloguer puntual** a un centre és el **cost del centre**; el preu que paga l'alumne és el de la tarifa, que manté el responsable de material.
  - El **dashboard** inclou les xifres econòmiques per a tots els rols que el veuen; la secretaria, el responsable de material i el Departament d'Història el veuen sencer i sense poder modificar res.
- Propostes per defecte acceptades (D-03 a D-19 de la revisió):
  - El tresorer aprova altes, baixes i canvis de tipus, sense veure la data de naixement ni el document, i sense crear altes ni editar dades del soci.
  - El tresorer i el President gestionen activitats completes, sense passar llista ni avaluar.
  - El responsable de material conserva la consulta d'activitats i participants que necessita per assignar material.
  - Avaluar i posar apte només ho fa qui fa classe a la sessió. El responsable de cursos i sortides, l'administrador i el President confirmen reforços i emeten certificats.
  - El responsable de cursos i sortides registra despeses amb factura de les seves activitats i en veu el marge. Pagar despeses, emetre factures i fer devolucions es queden al tresorer (i a l'administrador on el pla ja ho deia), i ni l'administrador ni el President obren documents de justificació.
  - Preus per catàleg:
    - cursos i especialitats: responsable de cursos i sortides, tresorer, administrador i President;
    - llicències: tresorer, administrador i President;
    - centres i tarifes: responsable de material, tresorer, administrador i President.
  - Llicències:
    - el responsable de cursos i sortides i el tresorer veuen el llistat i els venciments i registren «ja en tinc una»;
    - exportar a la federació i cancel·lar ho fan la secretaria, l'administrador i el President;
    - la data de naixement es queda com a la [058](058-respostes-fecdas-gestoria-i-cursos.md).
- **Cel·les [A validar] que la taula no cobreix:** prenen el supòsit per defecte del mòdul (punt 8 de l'ordre del dia de la junta). Si no n'hi ha, «—». Si amb «—» l'acció es quedaria sense ningú, la té l'administrador. Es poden canviar des de l'editor.

### 4. Regles protegides (codi, no editables)
L'editor les mostra com a només lectura, amb la decisió que les fixa:
1. Autenticació i permís per defecte a cada endpoint; els públics es declaren al codi (RN-40).
2. TOTP obligatori a l'administració, entrades separades, el compte personal no hereta cap rol i el compte d'administrador mai recupera per correu ([015](015-doble-factor-i-comptes-administrador.md), [018](018-perfil-comptes-i-rols.md), [029](029-compte-personal.md)).
3. Abasts base: el soci només el seu, el convidat només l'objecte de l'enllaç, l'instructor només les seves sessions.
4. IBAN complet: ningú. Fitxer de la remesa: només el tresorer ([044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md)).
5. Documents de justificació: només el tresorer i la junta; l'administrador mai ([051](051-abast-de-la-044-i-documents-de-justificacio.md)).
6. Data de naixement: només la secretaria i l'administrador ([058](058-respostes-fecdas-gestoria-i-cursos.md)).
7. Dades bloquejades i persones anonimitzades ([028](028-esborrat-rgpd-i-registre-d-activitat.md)).
8. Registre d'activitat immutable, també per a l'administrador.
9. Moviments immutables, període tancat (només l'administrador el reobre) i preu de soci de la llicència igual al de la federació.
10. Conflicte d'interès: ningú aprova la seva alta, canvia el seu estat, es marca impagat, es posa apte ni revoca el seu mandat des de l'administració.
11. Un sol tresorer i cap doble aprovació (P-48). Assignar el rol tresorer a un segon compte mostra un avís, però no es bloqueja.
12. Nivell 2 de producció només amb l'autorització escrita de la junta; claus i secrets per variables d'entorn ([025](025-dos-nivells-de-produccio.md)).
13. **Gestionar usuaris, rols i permisos és exclusiu del rol administrador**, que no el pot perdre. No es pot donar a cap altre rol, tampoc al President.
14. Mai sense administrador operatiu (punt 6).
15. El dashboard no dona accés a cap dada per si mateix: hi surten xifres econòmiques, però cap dada personal que el rol no pugui veure per un altre permís, i no obre cap pantalla de detall ni cap acció.

### 5. Diversos rols, retirada i canvis
- El permís d'un compte d'administrador és la **unió** dels seus rols (es manté RN-27). Si un mateix permís té abasts diferents, guanya el més ampli. Les regles protegides s'apliquen sempre, tingui els rols que tingui.
- Els permisos es calculen **a cada petició**, no es guarden a la sessió: retirar un rol o modificar un permís té efecte a la **petició següent**. En desar, un formulari obert es torna a comprovar al servidor.
- Si un compte es queda sense cap rol, se'n tanquen les sessions; el compte continua actiu sense accés. Desactivar-lo és una acció a part.
- Si un canvi **amplia** l'accés a dades personals o a diners, es tanquen les sessions d'administració dels comptes afectats, perquè tornin a entrar amb TOTP.
- Els objectes on el compte constava com a responsable (activitat, sessió, sol·licitud d'ajut) no es reassignen sols: surten a una llista «sense responsable».
- Les accions fetes abans d'un canvi continuen sent vàlides. El registre d'activitat guarda també amb quins rols s'ha fet cada acció.

### 6. Garanties de l'editor
1. Només el rol administrador, amb el **TOTP demanat de nou** en desar i una **nota obligatòria**.
2. **Resum abans de desar:** què canvia, quins comptes queden afectats i un avís si el canvi toca diners, dades personals o un camp sensible.
3. **Registre:** cada canvi al registre d'activitat (qui, quan, compte, rol, permís, abast, valor anterior, valor nou i nota) i una **versió nova de la matriu**. Les versions no s'editen ni s'esborren. Tornar a la configuració inicial és un canvi més.
4. **Avís per correu** a tots els comptes amb el rol administrador, als comptes afectats i al President.
5. **Administrador operatiu:** actiu, amb TOTP, no bloquejat i que no és d'emergència. Es rebutja qualsevol canvi que en deixi menys d'un; per sota de dos, avís permanent a l'administració (R10b de l'arquitectura).

## Conseqüències
- La matriu de la spec 00 i les taules «Rols i permisos» dels mòduls aprovats passen a ser la **configuració inicial**. Les cel·les que canvien s'indiquen a les addendes; les taules no s'editen.
- La peça d'ajustos de la 055 deixa de tenir els rols escrits al camp `editor_roles`: cada valor demana un permís del catàleg (`settings.edit_<mòdul>`). Les columnes «Qui el canvia» de l'[apèndix de valors configurables](../planning.md#valors-configurables) en són la configuració inicial.
- Les proves de permisos (checklist B4) passen a cobrir la configuració inicial, el motor, cada regla protegida i cada garantia de l'editor.
- Queden resolts P-04, Q-01, S-M01-14 (el permís; qui és el responsable de protecció de dades continua a Q-15), S-M01-22, S-M01-23, S-M02-16 a 18, S-M03-10, S-M04-09, S-M05a-13, S-M05b-13, S-M06-05 i S-M09-01 (aquest, amb la diferència que el responsable de material no registra despeses), i el punt 8 de l'ordre del dia de la junta.
- Continuen oberts: Q-10 (instructor o Departament d'Història que no és soci), Q-15 (responsable de protecció de dades), P-12 (cobrament manual) i P-43 (qui manté la web).
- **Punt feble que cal tenir present:** l'instructor no veu el marge, però si escriu el cost del centre i veu el preu de l'alumne, el pot calcular. És una conseqüència de la configuració inicial i es pot canviar des de l'editor.

## Fonts
- Taula «Què pot fer cada rol» del responsable del projecte (30/10/2026), document de funcionalitats §2.
- Respostes del responsable del projecte del 30/10/2026 als dubtes D-01, D-02, D-07 i D-14, i acceptació de la resta de propostes.
- [Spec 00](../../specs/00-base-comuna/spec.md), §2 i §5.2 a §5.5; [planning.md](../planning.md), seccions «Rols i permisos» de cada mòdul.
- Decisions [015](015-doble-factor-i-comptes-administrador.md), [018](018-perfil-comptes-i-rols.md), [021](021-persones-no-socies-com-a-convidades.md), [028](028-esborrat-rgpd-i-registre-d-activitat.md), [029](029-compte-personal.md), [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md), [051](051-abast-de-la-044-i-documents-de-justificacio.md), [055](055-ajustos-configurables-i-addendes.md) i [058](058-respostes-fecdas-gestoria-i-cursos.md).
- `docs/arquitectura-integracions.md`, R10b; `docs/checklist-produccio.md`, B4, C1 i C2.
