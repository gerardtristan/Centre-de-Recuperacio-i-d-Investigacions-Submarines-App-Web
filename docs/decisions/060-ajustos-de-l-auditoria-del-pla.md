# 060 — Ajustos de l'auditoria del pla: ordre de la fase 2, peces de la 00 sense tasca i casos límit

- **Data:** 31/10/2026
- **Estat:** Acceptada pel responsable del projecte el 31/10/2026, després de l'auditoria del pla de la mateixa data. S'aplica amb un **apèndix** del pla ([ajustos de la 060](../planning.md#ajustos-060)) i **addendes** als mòduls aprovats (01, 04, 05a, 05b, 06, 02, 03 i 09), sense editar-ne cap regla. Substitueix **només en l'ordre de la fase 2** la [024](024-abast-minim-i-ordre-per-deixar-cluber.md). Precisa la [059](059-rols-i-permisos-editables.md) en tres punts (ordre de les tasques, restabliment del TOTP per un compte d'emergència i nom del permís d'ajustos) sense editar-la. No toca cap regla de diners, de seguretat ni d'integritat aprovada.

## Context
- L'auditoria del 31/10/2026 va revisar les decisions 001 a 059 i el pla de tots els mòduls aprovats. Va trobar:
  - quatre peces de la 00 sense cap tasca, de les quals ja depenen tasques de la fase 1;
  - tres tasques que depenen de mòduls que es construeixen després;
  - tasques que es construeixen i després es reescriuen;
  - quatre casos límit sense regla: targeta caducada, segon retorn d'un rebut, cancel·lació d'una activitat amb material llogat o amb un pagament en curs, i l'últim administrador sense TOTP.
- El 06 només depèn del 01 i del 05b ([M06-2](../planning.md#M06-2-dependencies)), però es construïa després del 02, que el necessita.

## Alternatives
- Editar les regles i les taules aprovades: trenca la norma de no editar el que està aprovat i en perd la traçabilitat.
- Deixar-ho per a la implementació: cada buit es resoldria sense especificació.
- **Una decisió nova amb addendes per mòdul i un apèndix de lectura** (la que s'escull).

## Decisió

### 1. Ordre de la fase 2
- **06 Llicències → 02 Activitats → 03 Material → 09 Marge, despeses, ajuts i facturació → 07 → 08.** La fase 1 no canvia.
- Desapareixen les dependències cap endavant: la T-M01-31 i la T-M02-30 ja troben el 06 construït i el mode provisional de RN-M02-26 (llicència només com a avís) no s'aplica mai.
- **Conseqüència trobada en aplicar-ho:** el pagament a la federació és una despesa del 09 (RN-M09-20). El 06 es pot construir primer, però **no entra en producció fins que el nucli de despeses del 09 (T-M09-02 a T-M09-05) existeixi**. Aquestes tasques no depenen ni del 02 ni del 03 i es construeixen just després del 06.

### 2. Peces de la 00 amb tasca pròpia
Les quatre peces que el pla esmentava sense tasca reben un identificador ([apèndix](../planning.md#ajustos-060-peces-00)):
- T-M00-01: importació de l'extracte bancari (HU-21);
- T-M00-02: enllaços de convidat (HU-02);
- T-M00-03: comptes d'emergència i codis de recuperació (HU-09, HU-10);
- T-M00-04: consulta de dades bloquejades (M13, [028](028-esborrat-rgpd-i-registre-d-activitat.md)).

Les dependències que no apuntaven a cap tasca hi apunten ara.

### 3. Rols i permisos (precisa la 059)
- La T-RP-01 i la T-RP-04 es fan **just després de la T-M01-06 i abans de cap vista**. La T-AJ-01 hi depèn i fa servir directament el catàleg.
- La **T-RP-05 queda retirada**: no hi ha `editor_roles` a reescriure.
- Cada vista declara i comprova el seu permís quan es fa. Les tasques «declarar els permisos» de cada mòdul queden com a revisió final de la cobertura per cel·la.
- **L'editor de permisos (T-RP-03) surt del camí crític.** No és condició del nivell 1 ni del 2: es construeix en acabar el 05b. Fins llavors, la matriu només canvia amb una migració de dades revisada, que deixa registre.
- **Restabliment del TOTP de l'últim administrador:** un compte d'emergència sí que el pot restablir. Queda una entrada immutable al registre d'activitat i s'avisa la junta i tots els administradors. És l'única excepció a RN-RP-13.
- El nom del permís d'ajustos és **`settings.edit.<clau>`**, com diu RN-RP-17. On la 059 diu `settings.edit_<mòdul>`, val `settings.edit.<clau>`.

### 4. Casos límit
1. **Targeta guardada:**
   - una denegació definitiva (caducada, perduda o robada, compte tancat, targeta no vàlida; codis [A verificar: PaynoPain]) no es reintenta mai, i el soci rep directament l'alternativa;
   - si la caducitat coneguda és anterior a la data del cobrament, no es fa l'intent;
   - valor inicial de `payments.card_expiry_notice_days` (VC-48): **30 dies** [A validar: tresorer].
2. **Segon retorn d'un rebut:**
   - quan torna l'últim intent permès (`max_direct_debit_attempts`), la quota no entra en cap remesa més i s'ofereix l'alternativa de pagament;
   - la **T-M05b-23** (import extra del retorn) queda **congelada** fins que la junta validi el punt 11 de la 058. En validar-lo, cal definir el tipus del càrrec extra, l'IVA i què passa si el soci paga per l'alternativa.
3. **Cancel·lacions:**
   - la cancel·lació d'una inscripció i la d'una activitat es propaguen amb els **esdeveniments idempotents de la 049** (`enrolment.cancelled` i `activity.cancelled`), en lloc de senyals;
   - un càrrec amb un intent en curs es marca «anul·lar quan acabi»; si l'intent acaba pagat, es crea una proposta de devolució;
   - el que el centre de busseig cobra per una cancel·lació és una **despesa de l'activitat al 09**, de categoria «lloguer», i mai es cobra als participants.
4. **Llicències pendents en obrir el 02:** la confirmació en bloc de les llicències d'any natural pendents és **requisit previ per obrir les inscripcions del 02** a producció. Abans del pas únic al 06 es fa amb la T-M01-36; amb el 06 actiu, amb la T-M06-24.
5. **Convidats menors:**
   - mentre P-33 sigui oberta, tota inscripció d'un convidat que no demana la data de naixement porta una casella obligatòria **«Soc major d'edat»**;
   - no es guarda cap data: queda la declaració, amb la data i la versió del text.

### 5. Lectura de les tasques substituïdes
L'apèndix té una taula d'una línia per tasca afectada: què val i on. Es fa per no escriure proves d'una regla que ja no s'aplica. No edita cap fila aprovada.

## Conseqüències
- Apèndix nou del pla ([ajustos de la 060](../planning.md#ajustos-060)) i una addenda a cada mòdul afectat. Les taules aprovades no s'editen.
- Canvien l'ordre de la fase 2 a `CLAUDE.md`, a la secció 1 del pla i al [mapa de mòduls](../mapa-de-moduls.md).
- `CLAUDE.md` deixa de dir Stripe: el proveïdor és el de la [043](043-proveidor-de-pagaments-dins-la-ue.md), darrere d'un adaptador.
- Continuen obertes: P-33 (menors), el punt 11 de la 058 (import extra del retorn), els codis de denegació de PaynoPain i els codis de retorn del banc.

## Fonts
- Auditoria del pla del 31/10/2026 i aprovació del responsable del projecte de la mateixa data.
- [planning.md](../planning.md): M01-2, M02-2, M03-2, M05b-7, M06-2, RN-M09-20 i l'apèndix de rols i permisos.
- [Spec 00](../../specs/00-base-comuna/spec.md): HU-02, HU-09, HU-10, HU-21 i la matriu (M13).
