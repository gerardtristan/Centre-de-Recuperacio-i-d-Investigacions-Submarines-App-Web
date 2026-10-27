# 043 — Proveïdor de pagaments dins la UE i pagament sense sortir de l'app

- **Data:** 27/10/2026
- **Estat:** Acceptada la recomanació d'ordre. El proveïdor concret queda **pendent de verificar** amb el banc (P-44, P-45). Substitueix el proveïdor de la [017](017-pagaments-metodes-i-domiciliacions.md) (Stripe, descartat a la [042](042-proveidors-substituits-pel-requisit-ue.md)); els mètodes per tipus de cobrament de la 017 es mantenen. Substitueix la pregunta QT-02 de la spec 04.

## Context
- Requisit: el soci ha de poder pagar la quota i les inscripcions **sense sortir de l'app**, amb **targeta** o **Bizum**, amb informació clara i sense errors. Entra a la fase 1 després de la 04 (mòduls 05a i 05b, [024](024-abast-minim-i-ordre-per-deixar-cluber.md)).
- La targeta s'escriu sempre en un camp o una pàgina segura del proveïdor, **mai en un formulari propi**: l'app no veu ni guarda mai el número.
- Banc del club: **CaixaGuissona** [A verificar].
- Informació no confirmada: CaixaGuissona oferiria TPV virtual i datàfons mitjançant **PaynoPain** (plataforma Paylands). PaynoPain anuncia l'acord amb CaixaGuissona (TPV físic, Tap to Pay, passarel·la en línia Paylands amb Bizum, i pagament per enllaç) en una nota de premsa del 16/12/2024. Que PaynoPain sigui entitat de pagament autoritzada pel Banc d'Espanya, i que el club ho pugui contractar com a associació, és [A verificar].
- Camí de reserva sempre disponible: **transferència amb referència única** per càrrec i conciliació amb l'extracte (spec 04).
- Stripe queda descartat per la [035](035-dades-nomes-dins-ue.md).

## Alternatives

Costos per cobrament amb targeta de consum de l'EEE, sense IVA. Totes les xifres són **[A verificar]** a l'oferta contractual; les fonts són les pàgines públiques consultades el 27/10/2026.

| | (a) TPV virtual de CaixaGuissona via PaynoPain (Paylands) | (b) PAYCOMET | (c) MONEI | (d) Mollie | (e) Domiciliació SEPA pròpia (remesa pain.008 pel banc) |
|---|---|---|---|---|---|
| Seu | Espanya [A verificar ciutat i entitat] | Espanya [A verificar grup: les fonts secundàries es contradiuen] | Màlaga (Espanya). Entitat de pagament, registre del Banc d'Espanya núm. 6911 (segons la seva web) | Amsterdam (Països Baixos) [A verificar llicència] | El banc del club |
| Servidors i subencarregats | [A verificar] | [A verificar] | La web diu «Powered by … AWS»: AWS és una empresa dels EUA → **probable CONFLICTE** amb la 035 [A verificar regió i contracte] | [A verificar llista de subencarregats] | Banc (Espanya) [A verificar] |
| Targeta: camp incrustat o redirecció | Totes dues: la pàgina de pagament es pot obrir per redirecció o dins un `iframe`; SDK de tokenització en `iframe` del domini de Paylands | [A verificar] | [A verificar] | [A verificar] | No aplica |
| Bizum | Sí, via Redsys; s'ha d'activar per terminal (documentació de Paylands) | Sí (fonts secundàries) [A verificar] | Sí; tarifa pròpia no publicada | Sí: «Acquirer Fees + 0,10 % + 0,10 €» | No |
| Cost, quota de 35 € | [A verificar] | ≈0,27 € (0,50 % + 0,09 €, font secundària) + ≈19 €/mes | ≈0,67-0,71 € (0,90 % + 0,25 € + interchange 0,2-0,3 % + 0,10 % d'adquirència) + quotes de marca | 0,88 € (1,80 % + 0,25 €) | [A verificar] comissió del banc per rebut |
| Cost, quota de 90 € | [A verificar] | ≈0,54 € + ≈19 €/mes | ≈1,33-1,42 € + quotes de marca | 1,87 € | [A verificar] |
| Quota mensual | [A verificar] | ≈19 €/mes fins a cert volum (font secundària) | 0 €; algun mètode alternatiu, 0,15 €/dia | 0 € (pagaments en línia) | [A verificar] |
| Pagaments recurrents | Tokenització amb autenticació inicial (3DS) i cobraments posteriors sense intervenció (`/payment/direct`) | [A verificar] | [A verificar] | SEPA Direct Debit: 0,35 € | Sí, és el mètode natural per a quotes |
| Dependència del banc | Alta: el contracte va amb el banc del club [A verificar qui contracta] | Baixa | Baixa | Baixa | Total |
| Liquidació | No consta a la documentació pública [A verificar] | [A verificar] | Interchange descomptat a la liquidació (segons la seva web) | [A verificar] | Abonament de la remesa al compte |

**Iniciació de transferència per PSD2** (el soci autoritza una transferència des del seu banc dins el flux): possible tercera via de l'opció (a). La documentació pública de Paylands consultada no en parla [A verificar amb PaynoPain].

## Decisió
1. **Ordre de recomanació:**
   1. **(a) TPV virtual de CaixaGuissona via PaynoPain**, si el banc confirma per escrit que el club el pot contractar i que compleix la 035 (seu, servidors, subencarregats i contracte d'encarregat).
   2. Si no hi ha TPV o no compleix: **la millor alternativa verificada** entre (b), (c) i (d), triada amb les respostes de P-45. Ara mateix (c) té un probable conflicte per AWS.
   3. **Quotes recurrents:** domiciliació SEPA (e), amb mandat signat a l'app ([044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md)). Si el proveïdor triat ofereix tokenització amb autenticació inicial, la targeta guardada és una alternativa per a qui no vulgui domiciliar.
   4. **Sempre:** transferència amb referència única com a camí de reserva.
2. **Integració:** a través d'un adaptador de proveïdor al mòdul 05, perquè canviar de proveïdor no afecti la 04 ni la resta de l'aplicació. La 04 rep els cobraments, les comissions i les liquidacions a través dels seus serveis.
3. **Targeta:** camp incrustat (`iframe` del proveïdor) o pàgina del proveïdor. L'app no rep mai el número.
4. **Experiència de pagament:** requisits de la spec 04, annex D, per a la spec 05b.

## Conseqüències
- La spec 04 fa servir «proveïdor de cobrament» i «compte de trànsit» genèrics; la tasca T13 (liquidacions) passa a ser obligatòria.
- Resum tècnic de Paylands: [`docs/integracio-paylands.md`](../integracio-paylands.md).
- Preguntes per al banc i per a PaynoPain: [pendents.md](pendents.md), P-45.
- La [016](016-pressupost-produccio-minima.md) i la [037](037-pressupost-amb-web-installable.md) recalculen la part variable quan hi hagi tarifes contractuals.

## Fonts
- Decisió i requisits comunicats per l'equip el 27/10/2026
- PaynoPain, nota de premsa «PaynoPain will manage payments for CaixaGuissona» (16/12/2024): https://paynopain.com/en/?p=9093
- Documentació de Paylands: https://docs.paylands.com/en/docs/integration/simple-integration/, https://docs.paylands.com/en/docs/apm/apm-bizum/, https://docs.paylands.com/en/docs/guides/guide-cards/
- MONEI, preus: https://monei.com/pricing/
- Mollie, preus: https://www.mollie.com/pricing
- PAYCOMET, font secundària (Bankkers, 13/10/2026): https://bankkers.com/tpv-paycomet/
