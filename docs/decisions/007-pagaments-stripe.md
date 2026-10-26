# 007 — Pagaments amb Stripe, més transferència i registre manual

- **Data:** 27/10/2026
- **Estat:** Proposada: l'abast dels cobraments contradiu el context v3 i el document incremental (P-01). No es posa res en producció sense autorització escrita.

## Context
El document de funcionalitats preveu que el club deixi Cluber i cobri dins l'app (targeta, Bizum i rebut domiciliat). El context v3 i el document incremental deixen fora d'abast substituir els cobraments de Cluber.

## Alternatives
- Mantenir Cluber per als cobraments i importar-ne els CSV (context v3).
- Passarel·la del banc (TPV virtual): comissions a negociar i domiciliacions per una altra via.
- Stripe: targeta, Apple Pay, Google Pay, Bizum i domiciliació SEPA en un sol proveïdor, amb formularis allotjats i notificacions signades.

## Decisió
- **Stripe** amb tres mètodes:
  1. rebut domiciliat SEPA amb mandat digital, només per a quotes (pagaments recurrents);
  2. targeta (incloent-hi Apple Pay i Google Pay);
  3. Bizum (cal confirmar l'activació al compte del club).
- **Fora de Stripe:** transferència amb referència única (conciliada amb l'extracte) i registre manual (efectiu o presencial, amb motiu i registre d'activitat).
- Targeta, Bizum i transferència per a inscripcions i llicències.
- El pagament només es dona per fet quan arriba un webhook verificat per signatura i processat de manera idempotent.
- No es guarden dades de targeta: es paga en un formulari allotjat per Stripe.
- Stripe sempre en mode de proves fins que la junta autoritzi producció.

## Conseqüències
- Comissions variables (pàgina oficial de Stripe Espanya consultada el 27/10/2026): targeta EEE estàndard i Bizum 1,5 % + 0,25 €; SEPA 0,35 € per cobrament, 3,50 € per cobrament fallit i 15 € per disputa. Apple Pay i Google Pay no hi tenen preu propi [A validar].
- La comissió es registra com a despesa del mateix departament o activitat ([013](013-imputacio-comissions.md)).
- Stripe ingressa al banc en liquidacions agrupades: la conciliació ha de casar la liquidació amb els cobraments que conté.
- Via de sortida: les dades de clients i pagaments es poden exportar; la migració de mandats SEPA a un altre proveïdor s'ha de demanar a Stripe [A validar].
- Si es manté Cluber (P-01), aquesta decisió queda limitada a inscripcions i llicències.

## Fonts
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §1, §2, §7 i §9.5
- `docs/context-projecte.md`, §6 i §7
- `docs/entregues/document-incremental.pdf`, §2.3 i §4.5
- Encàrrec d'arquitectura del 26/10/2026
