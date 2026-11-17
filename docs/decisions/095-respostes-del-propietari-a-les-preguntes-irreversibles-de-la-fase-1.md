# 095. Respostes del propietari a les preguntes irreversibles de la fase 1

- **Data:** 17/11/2026
- **Estat:** Acceptada (propietari, 17/11/2026; instrucció escrita). Les respostes dels blocs A i B són **definitives**. Les del bloc C són **provisionals**: esperen la confirmació per escrit del banc, de PaynoPain, de Cluber o de la gestoria, no activen res a producció i el **nivell 2 continua bloquejat** fins que arribi.
- **Origen:** les preguntes obertes de la fase 1 a [`pendents.md`](pendents.md) i al [tauler](tauler-preguntes.yml), i el document «Preguntes irreversibles de la fase 1».
- **Canvia:** cap interruptor de producció. Les regles congelades del 01, el 04, el 05a i el 05b ([089](089-prova-d-acceleracio-interruptors-d1-a-d6.md), D1) només es toquen on una resposta canvia una regla escrita, amb una sola edició al lloc de la regla en una PR `risc:alt` a part. La regla nova de Verifactu s'afegeix a la secció del [09](../planning.md#M09-7-regles), que no és de la fase 1, també en una PR `risc:alt`.

## Norma recordada pel propietari (17/11/2026)

Tots els permisos es donen i es treuen des de l'app, per rol, amb «veure» o «veure i editar», sense tocar codi ([059](059-rols-i-permisos-editables.md)). Les respostes sobre permisos d'aquesta decisió només fixen la **matriu inicial**.

## Bloc A — propietari (definitives)

| ID | Resposta | Tipus | Què canvia al codi |
|---|---|---|---|
| P-281 | Les devolucions no passen per la salvaguarda del nivell 1, ni tampoc les notificacions, la xarxa de seguretat, les liquidacions i la conciliació (A, com està) | definitiva | Res |
| P-213 | Una remesa no inclou mai una persona amb les dades esborrades ni un mandat bloquejat (C, com està) | definitiva | Res |
| P-247 | El nom del pagador només es mostra a qui té també P4 (A, com està) | definitiva | Res |
| P-126 | Una contrasenya buida perquè la sessió ha caducat no compta com a intent fallit (A, com està) | definitiva | Res |
| P-127 | Revocar el mandat funciona sempre, també amb la signatura apagada; el menú mostra «Mandat de domiciliació» a qui en té un d'actiu (B) | definitiva | **Sí:** la revocació no depèn de `MANDATE_SIGNING_ENABLED` i l'entrada de menú surt a qui té un mandat actiu (tasca P-127, M05a) |
| P-246 | El rebut de la transferència continua amb el senyal, a la mateixa transacció que el pagament (A, com està) | definitiva | Res |
| P-243 | T11 i P10 són el mateix permís; no hi ha cap codi nou (A, com està) | definitiva | Res |
| P-244 | La Secretaria comença sense B7; l'administrador l'hi pot donar sencer. Un permís no es pot limitar a «només quotes» (A, com està) | definitiva | Res al codi. Canvia la cel·la B7 de la Secretaria al pla (PR `risc:alt` del pla) |
| P-190 | Excloure una línia (T8) i veure la llista «a revisar» (T10) tenen cadascun el seu permís al catàleg. Matriu inicial: T8, el Tresorer; T10, el Tresorer i l'Administrador (A) | definitiva | **Sí:** dos codis de permís nous i les vistes que els comproven (tasca P-190, M04) |
| P-131 | La configuració del proveïdor (targeta, Bizum, targeta guardada) s'edita des de l'app, amb un permís propi «veure i editar», doble factor, nota obligatòria, registre i avís al tresorer. Les claus i els secrets continuen a les variables d'entorn (B) | definitiva | **Sí:** pantalla d'edició i permís nou (tasca P-131, M05a) |
| P-119 | S'afegeix un identificador de devolució al moviment; si arriba repetit, es torna la devolució que ja existeix (B) | definitiva | **Sí:** camp i migració (`risc:alt`), `record_refund` idempotent per identificador (tasca P-119, M04) |
| P-80 | En desplegar hi haurà dos usuaris de base de dades: un per a les migracions i un per a l'aplicació, sense UPDATE, DELETE ni TRUNCATE a les taules on només s'afegeixen files (A) | definitiva | Es fa en desplegar (tasca P-80, M00) |

## Bloc B — tresoreria i junta (definitives)

El propietari les aprova i les comunicarà al tresorer i a la junta.

| ID | Resposta | Tipus | Què canvia al codi |
|---|---|---|---|
| P-125 | Quan el soci signa el mandat, la preferència passa a «domiciliació» amb aquest mandat (B) | definitiva | **Sí:** signar desa la preferència (tasca P-125, M05a) |
| P-134 | Quan el soci passa a «pagar cada vegada» amb un mandat actiu, se li pregunta si el vol revocar. Si no respon, el mandat queda actiu però no entra a cap remesa (C) | definitiva | **Sí:** pregunta en canviar la preferència i la remesa només agafa qui té la preferència «domiciliació» (tasca P-134, M05a). Canvia el pas 3 de [P-M05a-A](../planning.md#M05a-5-processos) (PR `risc:alt` del pla) |
| P-240 | Com està: el pagament retornat s'anul·la amb el motiu del banc i només el registra el tresorer (A) | definitiva | Res |
| P-290 | Com està: l'intent domiciliat passa a «cancel·lat», el rebut s'anul·la amb una nota i el rebut domiciliat queda «retornat» (A) | definitiva | Res |
| P-230 | Com està: entren les quotes pendents que vencen com a molt el dia del cobrament; el període només és una etiqueta (A) | definitiva | Res |
| P-231 | Com està: entra el soci amb la domiciliació triada i un mandat actiu, i el rebut porta el mandat vigent (A) | definitiva | Res |
| P-232 | Com està: sense adreça per a l'avís previ, el rebut queda sense avís i la remesa es queda en esborrany (A) | definitiva | Res |
| P-235 | Com està: les remeses van al compte de les transferències (A). El banc ho ha de confirmar (bloc C, punt 11 de la P-45) | definitiva | Res |
| P-236 | Com està: no es genera el fitxer i es diu quins mandats són (A) | definitiva | Res |
| P-111 | L'ingrés d'una transferència conciliada porta la data de valor de la línia de l'extracte (A). La gestoria ho ha de confirmar | definitiva | **Sí:** `record_payment` del nucli accepta una data i la conciliació hi passa la de la línia (tasca P-111, M04) |
| P-114 | Com està: una pota de traspàs no s'anul·la; un traspàs equivocat es corregeix amb un traspàs de sentit contrari (A) | definitiva | Res |
| P-115 | Com està: un contramoviment no s'anul·la; l'error es corregeix amb un moviment nou amb motiu (A) | definitiva | Res |
| P-118 | Com està: les devolucions i el retorn sumen junts fins a l'import cobrat (A) | definitiva | Res |
| P-222 | Com està: un traspàs a mà només es pot fer entre comptes bancaris i de caixa (A) | definitiva | Res |
| P-224 | Com està: es rebutja una data futura (A) | definitiva | Res |
| P-220 | Com està: una liquidació «a revisar» no apunta res i no es pot confirmar (A) | definitiva | Res |
| P-221 | Com està: la comissió porta la data de l'ingrés (A). La gestoria ho ha de confirmar | definitiva | Res |
| P-227 | Com la A (no s'apunta res) i, a més, s'envia un correu a qui té el permís de tresoreria (B) | definitiva | **Sí:** correu en rebutjar una liquidació que no quadra (tasca P-227, M05b) |
| P-228 | Com està: la devolució es registra amb el motiu, l'import i qui la fa, sense fitxer (A) | definitiva | Res |
| P-250 | Qui té el permís pot descartar amb motiu una devolució pendent (B) | definitiva | **Sí:** tasca nova (P-250, M05b) |
| P-110 | (junta) La plataforma no toca el soci sola: avisa per correu qui pot editar les quotes, i aquesta persona decideix a mà (A) | definitiva | Res |
| P-112 | (junta) A la matriu inicial, només el Tresorer pot conciliar (A) | definitiva | Res al codi. La cel·la T4 de l'Administrador al pla passa de «[A validar]» a «—» (PR `risc:alt` del pla) |
| P-193 | (junta) La Secretaria té «Cons.» a A4: només veu «té mètode: sí/no» (B) | definitiva | **Sí:** una cel·la de la matriu inicial (tasca P-193, M05a). Al pla es treu el «[A validar]» de la cel·la |

## Bloc C — provisionals (falta la confirmació per escrit; el nivell 2 continua bloquejat)

| ID | Resposta provisional | Tipus | Qui ha de confirmar | Què canvia al codi |
|---|---|---|---|---|
| P-233 | pain.008.001.02, sempre RCUR, sense BIC (NOTPROVIDED) i el nom del club tal com el té el banc, configurable a «Ajustos» (A) | provisional | Banc | Res nou (és l'opció per defecte); el nom ha de ser un ajust si encara no ho és |
| P-237 | Un sol abonament per remesa; la comissió va a part o descomptada, i s'admeten les dues formes (A) | provisional | Banc | Res |
| P-291 | Els codis ISO estàndard. La llista de codis i l'acció de cada un passen a ser dades editables a «Ajustos», amb els valors per defecte actuals (norma «llistes = dades») | provisional | Banc | **Sí:** la llista de `returns.py` passa a ajust (tasca P-291, M05b) |
| P-123 | Els països admesos són una llista editable a «Ajustos», que de bon principi és tota la zona SEPA (C). La signatura continua apagada a producció fins que el banc respongui | provisional | Banc | **Sí:** ajust nou i validació del país (tasca P-123, M05a) |
| P-24 | L'identificador de creditor és el del club: ES + dígits de control + sufix «000» + NIF. Stripe està descartat | provisional | Banc | Res |
| P-21 | Es manté l'escenari B (campanya de mandats nous) fins que se sàpiga si Cluber cedeix els mandats | provisional | Cluber i banc | Res |
| P-44, P-45 (part del banc) | Extracte en Norma 43; antelació de la remesa configurable, per defecte 3 dies hàbils; pagaments sortints amb pain.001 al mòdul 09. La part de PaynoPain continua oberta, i el requisit de dades només a la UE (punt 4 de la consulta a PaynoPain; [035](035-dades-nomes-dins-ue.md)) és eliminatori | provisional | Banc i PaynoPain | Res ara |
| Q-14 | Es mantenen 6 anys ([085](085-respostes-del-responsable-a-les-preguntes-pendents-de-t-m00-i-t-m01.md), G1), configurable per tipus de document, a l'espera de saber si els ajuts públics demanen més temps | provisional | Gestoria | Res ara |
| P-47, P-02 (IVA) | Cursos, sortides i material amb IVA general; quotes i llicències exemptes. Els tipus d'IVA i el text d'exempció queden provisionals | provisional | Gestoria | Res ara (mòdul 09) |

## Decisió nova del propietari: integració amb Verifactu (definitiva)

Part Verifactu de la P-02 i la P-47.

1. El club farà servir **Verifactu**. La plataforma tindrà una integració amb un **servei homologat** de Verifactu perquè totes les factures quedin controlades: emissió, registre, enviament a l'Agència Tributària i consulta de l'estat de cada factura.
2. Es fa **darrere d'un adaptador**, com el de pagaments ([043](043-proveidor-de-pagaments-dins-la-ue.md)), al **mòdul 09**. No es programa Verifactu a casa.
3. El proveïdor ha de complir les normes del projecte: dades només dins la UE ([035](035-dades-nomes-dins-ue.md)), contracte d'encarregat del tractament (RGPD, art. 28), i tots els valors configurables (sèries, textos d'exempció, tipus d'IVA) a «Ajustos».
4. Quin servei homologat es tria és una pregunta nova, la **P-293** ([pendents](pendents.md), [tauler](tauler-preguntes.yml)), que respon el propietari amb la gestoria.
5. El 09 no és de la fase 1 i no és congelat: la regla s'afegeix a [M09-7](../planning.md#M09-7-regles) en una PR `risc:alt`. **Ara no es construeix cap codi de Verifactu.**

## Conseqüències

- Les preguntes dels blocs A i B passen a «Resolts» a `pendents.md` i surten del tauler. Les del bloc C es queden obertes, amb la resposta provisional a la columna «Estat».
- Les respostes amb canvi al codi són tasques a `docs/estat/` (una línia per tasca), cada una en una PR petita, per ordre del camí crític: P-125, P-134, P-127, P-111, P-227, P-250 i P-119. P-190, P-131 i P-193 són canvis de permisos; P-291 i P-123 són ajusts; P-80 es fa en desplegar.
- Cap interruptor de producció no s'encén. `MANDATE_SIGNING_ENABLED` i `PAYMENTS_LIVE_CHARGES_ALLOWED` continuen apagats a producció, i el nivell 2 continua bloquejat pel bloc C.
