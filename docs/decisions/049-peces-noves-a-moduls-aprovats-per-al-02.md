# 049 — Dues peces noves a mòduls aprovats per al mòdul 02: lectura de la llicència i esdeveniment «càrrec pagat»

- **Data:** 27/10/2026
- **Estat:** Acceptada. Amplia els contractes del [M01](../planning.md#M01-8-serveis) i del [M05b](../planning.md#M05b-8-serveis) de `planning.md`, que ja estaven aprovats, **sense canviar-ne cap regla**. La spec 00 no s'edita.

## Context
- El mòdul 02 (activitats) necessita saber si la llicència d'un participant és vigent, però el 01 guarda el registre mínim de llicència sense oferir cap servei per llegir-lo.
- El 02 també necessita saber quan es paga el càrrec d'una inscripció. El 05b només avisa el 01 (`members.on_fee_paid`) amb una crida directa.
- Afegir una crida directa per a cada mòdul nou (02, 03, 06, 09) faria que el 05b depengués de tots ells.

## Alternatives
- Que el 02 llegeixi directament els models del 01 i consulti l'estat dels càrrecs periòdicament: trenca la regla «una app no escriu ni llegeix els models d'una altra, ho fa a través de serveis» i afegeix retard.
- Crides directes del 05b a cada mòdul: acobla el 05b als mòduls que vénen després.
- **Un servei de lectura al 01 i un esdeveniment general «càrrec pagat» al qual es subscriuen els mòduls.**

## Decisió
1. **01 — lectura de la llicència, només lectura.** El 01 ofereix `members.licence_record(person)` (tipus, data d'alta i data de caducitat del registre mínim, o res) i `members.licence_records()` (la mateixa dada per a tots els socis, per al 06). No escriuen res i no canvien cap regla del 01.
2. **05b — esdeveniment «càrrec pagat» com a mecanisme general**, no com a crida directa al 02:
   - Quan un càrrec passa a «pagat», s'emet l'esdeveniment `charge.paid` amb l'identificador del càrrec, el tipus, el mòdul d'origen, l'activitat (si en té) i l'import.
   - S'emet **dins la mateixa transacció** que el canvi d'estat (taula d'esdeveniments pendents a PostgreSQL), sigui quin sigui el camí que el posa en «pagat»: notificació verificada del proveïdor, conciliació d'una transferència o d'una remesa.
   - Els mòduls **s'hi subscriuen** (`events.subscribe("charge.paid", handler)`); el 05b no coneix els subscriptors.
   - **Lliurament a la cua de tasques** (sobre PostgreSQL, [012](012-cua-de-tasques.md)), com a mínim una vegada i amb reintents.
   - **Idempotent:** cada lliurament es desa amb la parella (esdeveniment, subscriptor) única; si arriba dues vegades, el segon no fa res.
   - **Registre:** cada emissió i cada lliurament (correcte, fallit o repetit) queden al registre d'activitat.
3. La crida directa actual del 05b a `members.on_fee_paid` **es manté tal com és**. Passar el 01 a l'esdeveniment és opcional i requeriria una decisió nova.
4. Les seccions M01 i M05b de `planning.md` s'actualitzen només per afegir aquestes peces (serveis, una tasca per mòdul) i continuen aprovades.

## Conseqüències
- Tasques noves: T-M01-30 (servei de lectura de la llicència) i T-M05b-21 (esdeveniment `charge.paid`, taula d'esdeveniments pendents i lliuraments idempotents).
- El 02 (i més endavant el 03, el 06 i el 09) s'hi subscriuen sense que el 05b canviï.
- Altres esdeveniments («càrrec retornat», «devolució feta») poden fer servir el mateix mecanisme, però cadascun s'ha d'aprovar abans.

## Fonts
- Aprovació del responsable del projecte, 27/10/2026, punt 3 de les aprovacions ([`planning.md`](../planning.md#M02-14-aprovar))
