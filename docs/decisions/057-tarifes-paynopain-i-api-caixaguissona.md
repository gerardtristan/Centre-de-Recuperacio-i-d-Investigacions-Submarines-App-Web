# 057 — Tarifes públiques de PaynoPain i API de CaixaGuissona per a la conciliació

- **Data:** 28/10/2026
- **Estat:** Acceptada el 28/10/2026 pel responsable del projecte com a **ampliació** de la [043](043-proveidor-de-pagaments-dins-la-ue.md), la [016](016-pressupost-produccio-minima.md) i la [037](037-pressupost-amb-web-installable.md), que no s'editen. No toca la spec 04 ni el mòdul 04 aprovat. Tot el que depèn del banc o de PaynoPain és **[A verificar]** fins que hi hagi una oferta o una resposta per escrit. (El número 056 queda reservat per a la retirada eventual de la llicència d'un dia, VC-40.)

## Context
- La 043 recomana en primer lloc el TPV virtual de CaixaGuissona via PaynoPain (plataforma Paylands), però deixa la columna de costos com a [A verificar].
- PaynoPain publica les seves comissions a la seva web. CaixaGuissona té un portal d'API per a desenvolupadors (API Market).
- Consulta de les pàgines públiques: 28/10/2026. La documentació tècnica (swagger) de l'API de CaixaGuissona no s'ha pogut llegir; només les pàgines de productes i de funcionament.

## Decisió

### 1. Tarifes públiques de PaynoPain [A verificar a l'oferta contractual]
| Concepte | Tarifa pública |
|---|---|
| Targeta de consum de l'EEE (tarifa Start) | 0,60 % + 0,15 € per operació |
| Bizum | 1,20 + 0,15 € per operació (no consta si l'1,20 és percentatge) |
| Open Banking (pagament des del banc del pagador) | 1,20 + 0,15 € per operació |
| Quota fixa (tarifa Start) | Cap |
| Liquidació (tarifa Start) | A D+4, per l'**import net** (la comissió es descompta de la liquidació) |
| Permanència | Cap |

- No publicades: domiciliació SEPA, devolucions, contracàrrecs, quota d'alta, IVA de les comissions, i on es tracten les dades.
- Exemple (tarifa Start): quota de 35 € → 0,36 € amb targeta i 0,57 € amb Bizum; quota de 90 € → 0,69 € i 1,23 €.
- Amb el volum previsible del club, la tarifa Start surt més barata que la tarifa plana (20 €/mes amb 2.000 € processats inclosos) [A verificar el significat de «Start s'activa a partir de 2.000 €»].
- La part variable del pressupost de la 016 i la 037 es pot estimar amb aquestes tarifes; les xifres d'aquelles decisions no es modifiquen fins que hi hagi oferta.

### 2. Llicència de PaynoPain [A verificar]
PaynoPain diu tenir llicència d'**entitat de pagament** supervisada pel Banc d'Espanya (anunci del 10/11/2022), que inclou adquirència, transferències i **domiciliacions**. El número de registre, la seu i el compliment de la [035](035-dades-nomes-dins-ue.md) (servidors, subencarregats i contracte d'encarregat) estan pendents de verificar.

**Si PaynoPain confirma per escrit que gestiona domiciliacions SEPA amb custòdia dels mandats** i compleix la 035, s'aplicaria l'**alternativa 2** de la [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md) i la 044 quedaria substituïda (la plataforma tornaria a no guardar l'IBAN, RN-70). Caldria una decisió nova per fer-ho efectiu.

### 3. L'API de CaixaGuissona complementa PaynoPain; no el substitueix
- Productes publicats: **comptes** (ACCOUNTS), **saldos** (BALANCES), **moviments** (TRANSACTIONS) i **pagaments** (PAYMENTS: iniciar, confirmar, consultar i cancel·lar pagaments des d'un compte de l'entitat). Pel catàleg i pel certificat eIDAS QSealC que demana, és l'API d'accés al compte de la directiva europea de serveis de pagament.
- No hi ha cap API de domiciliacions, remeses (pain.008), mandats, rebuts retornats, TPV ni Bizum. La targeta i el Bizum continuen anant pel proveïdor de la 043; la domiciliació, per remesa al banc (044) o pel proveïdor (punt 2).
- PAYMENTS només inicia pagaments des de comptes de CaixaGuissona: no serveix per cobrar socis d'altres bancs, i el pla no preveu que l'app mogui diners del club sola.
- Accés: entorn de proves obert; producció a petició, amb certificat QSealC o per una via «sense certificat» amb aprovació de l'entitat. Si un client sense certificat hi pot accedir en producció, la durada del consentiment i el cost: **[A verificar amb el banc]**.

### 4. Lectura de moviments per API: millora opcional de la conciliació
- La **base** i el **camí de reserva** de la conciliació són la importació de l'extracte en fitxer (Norma 43 o equivalent), tal com està al pla.
- La lectura automàtica de moviments per l'API (TRANSACTIONS) és una **millora opcional**, que s'afegiria a través de l'adaptador bancari sense canviar les regles de la 04. Només es planifica si el banc confirma l'accés de producció per al club.
- Dades dins la UE: el banc ja té les dades del compte, així que la lectura no afegeix cap proveïdor nou; on s'executa la plataforma de l'API és [A verificar].

## Conseqüències
- Bloc de seguiment de preguntes al banc i a PaynoPain a [`preguntes-externes.md`](../preguntes-externes.md#seguiment-057).
- Si les respostes confirmen el punt 2 o el punt 4, cal una decisió nova; aquesta no canvia cap mòdul.
- Recerca completa (28/10/2026): fitxer «paynopain-i-api-caixaguissona.md» de la carpeta del projecte, fora del repositori.

## Fonts
- PaynoPain, comissions: https://paynopain.com/comisiones-pasarela-pago/
- PaynoPain, llicència d'entitat de pagament (10/11/2022): https://paynopain.com/en/?p=7524
- CaixaGuissona API Market, productes: https://apimarket.caixaguissona.com/productos
- CaixaGuissona API Market, funcionament: https://apimarket.caixaguissona.com/funcionamiento
