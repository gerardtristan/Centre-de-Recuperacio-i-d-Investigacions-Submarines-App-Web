# 085. Respostes del responsable a les preguntes pendents de T-M00 i T-M01

- **Data:** 12/11/2026
- **Estat:** Acceptada (responsable del projecte, 12/11/2026)
- **Origen:** document de preguntes agrupades per destinatari de l'11/11/2026 (codis J, T, S, G, A i I).

## Qui respon

Totes les respostes són del **responsable del projecte**. On la pregunta era d'un tercer (junta, tresorer, secretaria, gestoria, assessor o informàtica), el responsable l'ha respost ell. A les de **gestoria i assessor** ha delegat la recerca i la redacció en l'equip, sense demanar-ne validació: el que se n'ha fet (G-1, G-4, A-3 i J-10) surt de la normativa consultada i **no és un dictamen professional**.

## Respostes

### Junta
| Codi | Resposta | Què se'n fa |
|---|---|---|
| J-1 | No cal decidir-ho ara: qui veu i qui edita cada bloc ho decidirà l'administrador des de la configuració | Es manté RN-M01-84 com a comportament inicial. Depèn de l'editor de permisos (T-RP-03) |
| J-2 | Eximeix una quota qui tingui el rol de Tresoreria actiu, amb edició i visualització | Assignació inicial del permís «Eximir una quota»: Tresorer. **Desbloqueja la T-M01-40** |
| J-3 | No hi ha llicenciats fora de Cluber | P-62, punt 3, resolt |
| J-4 | A: 30 dies | Un soci és candidat a impagat 30 dies després del venciment sense pagar, o amb un rebut retornat; el tresorer ho confirma amb motiu. **Per implementar a la T-M01-18** |
| J-5 | A | Amb un rebut retornat, el carnet continua vàlid fins que el tresorer marca l'impagat. Regla per al 05b (Q-146 resolta) |
| J-6 | El NIF és V08591042 | Surt al darrere del carnet |
| J-7 | Tot això ha de ser editable sempre | El permís dels enllaços de convidat (M5) comença a l'administrador i es canvia des de l'editor de permisos (T-RP-03). Principi general: cap assignació de permisos queda fixada al codi |
| J-8 | L'administrador custodia els comptes d'emergència | Vegeu «Advertiments» |
| J-9 | Només hi ha pagament a terminis per a la quota de soci de ple dret, en tres mesos | Tres terminis mensuals, i cap altre pagament a terminis a la plataforma. **Falta l'import total** (vegeu «Queda obert») |
| J-10 | Que l'equip redacti el protocol de menors segons la normativa de Catalunya, Espanya i la Unió Europea | Esborrany a `docs/protocols/proteccio-de-menors.md`. L'ha d'aprovar la junta perquè sigui vigent |
| J-11 | Els simpatitzants són socis que ajuden el club amb la quota; tenen veu (dir, proposar i escoltar) però no vot | S-M01-11 resolt. Al mòdul de socis no canvia res; el vot no és a la plataforma |

### Tresorer
| Codi | Resposta | Què se'n fa |
|---|---|---|
| T-1 | A: 7 dies | Confirmat el termini del suplement |
| T-2 | A | Confirmats els dies i el text dels recordatoris |
| T-3 | De Cluber s'importen la data de naixement i la data d'inscripció, que pot ser buida; es poden omplir a mà, pel soci o per l'administració (configurable). La resta no interessa | Vegeu «Queda obert»: falta dir des de quan compten els 12 mesos d'un soci importat |
| T-4 | No la troba i no importa | La columna «Renovació» continua sense llegir-se. P-62, punt 2, resolt |
| T-5 | A | Si el pas a simpatitzant s'accepta amb la quota de renovació ja generada i sense pagar ni enviar al banc, s'anul·la i se'n genera una a preu de simpatitzant. **Desbloqueja la T-M01-43** (punt 1 de la 073) |
| T-6 | A | Avís el mateix dia del mes anterior, per correu i als avisos, configurable (punt 5 de la 073) |
| T-7 | Aprovada | Guia del tresorer |

### Secretaria
| Codi | Resposta | Què se'n fa |
|---|---|---|
| S-1, S-3 | Aprovats. A més, tots els textos (impagats, termes i condicions, avisos de renovació, correus) s'han de poder configurar i editar sense tocar el codi: és una missió de tot el projecte | Textos aprovats. **Tasca nova T-M00-08** per als textos editables |
| S-2 | Aprovat | Correu del restabliment del doble factor |
| S-4 | B | Només l'any actual o el següent. Implementat |
| S-5 | B: no es pot inscriure, se li diu per què, i pot demanar que l'administració l'apunti igualment (per exemple, si espera la FECDAS) | Regla per al mòdul 02 (RN-M01-50 i RN-M02-10): bloqueig amb explicació i inscripció feta per l'administració com a excepció |
| S-6 | A | Format del passaport confirmat |
| S-7 | Ara no hi ha menors; si n'hi ha, es gestionarà a mà | T-M01-44 sense feina pendent ara |
| S-8 | Aprovada | Guia de la secretaria |

### Gestoria (recerca delegada en l'equip)
| Codi | Resposta | Què se'n fa |
|---|---|---|
| G-1 | Nom, cognoms i document xifrats, amb el termini legal que trobi l'equip | **6 anys** des del 31/12 de l'any de l'últim registre econòmic; després es destrueixen. Implementat (vegeu «Recerca») |
| G-2 | A; a més, qui tingui el permís pot esborrar el deute | No s'esborra amb deutes pendents; anul·lar una quota amb motiu ja existeix com a servei i tindrà pantalla a la T-M01-40 |
| G-3 | No | No es guarda cap còpia de l'exportació final de Cluber. P-64 tancada |
| G-4 | Que l'equip els redacti respectant la llei | Textos definitius del butlletí i de les imatges. Implementats (vegeu «Recerca») |

### Assessor de protecció de dades (resposta del responsable)
| Codi | Resposta | Què se'n fa |
|---|---|---|
| A-1 | C | Les notes de l'administració van a l'exportació després que les revisi qui atén la sol·licitud. **Per implementar a la T-M01-22** |
| A-2 | A | Els drets d'un menor de 14 anys es demanen en persona i la secretaria ho registra. **Per implementar a la T-M01-22** (ara no hi ha menors) |
| A-3 | B | El correu de rebuig d'un esborrat diu el motiu i com reclamar. Implementat |
| A-4 | Sí | N'hi ha prou amb conservar el registre dels consentiments lligat a la referència. Les imatges ja publicades es retiren dels canals del club si la persona ho demana (text de G-4) |
| A-5 | A | De 14 a 17 anys, els consentiments opcionals els dona el mateix menor |
| A-6 | Confirmat | Preval el català i no cal tornar a consentir en canviar de llengua |

### Informàtica
| Codi | Resposta | Què se'n fa |
|---|---|---|
| I-1 | C | El proxy no ha de desar les adreces dels enllaços d'un sol ús i els registres han de tenir conservació curta i accés restringit. Condició de producció |
| I-2 | Els correus els envia cris@cris.es | **Substitueix el remitent de la [019](019-domini-i-correu.md)** (`no-respon@cris1954.cat`). Implementat. Vegeu «Advertiments» |
| I-3 | L'accés al domini el té la junta; ara el gestiona una empresa i es pot demanar. No ha d'afectar el projecte | Sense canvis. Condició de producció |

## Recerca feta per l'equip (G-1, G-4, A-3 i J-10)

Fonts: textos consolidats del BOE consultats el 12/11/2026. **No és un dictamen professional.**

- **Termini de les dades bloquejades (G-1): 6 anys.**
  - El Codi de comerç (article 30) obliga a conservar llibres i justificants 6 anys des de l'últim assentament. És per a empresaris; s'aplica a l'associació per analogia.
  - El llibre tercer del Codi civil de Catalunya (articles 313-1 a 313-3) obliga les associacions a portar comptabilitat i llibres, però no hi hem trobat cap termini.
  - La Llei general tributària (article 66) fixa 4 anys de prescripció: queden coberts.
  - La LOPDGDD (article 32) diu que les dades bloquejades només es conserven pel termini de prescripció de les responsabilitats i després s'han de destruir. Per això es destrueixen, i no es conserven indefinidament.
  - **Límit conegut:** la Llei 10/2010 (articles 25 i 39) obliga les associacions a conservar 10 anys la identificació de qui aporta fons a títol gratuït, a partir de 100 €. No s'ha aplicat a les quotes ni a les inscripcions, que no són donatius. Si el club registra donatius de 100 € o més, caldran 10 anys per a aquells registres. El termini és configurable.
- **Textos del butlletí i de les imatges (G-4):** consentiment exprés i separat per a cada cosa (RGPD, articles 6 i 7; LSSI, article 21, per al correu; Llei orgànica 1/1982 per a la imatge), opcional, amb la manera de retirar-lo i sense condicionar ser soci. A partir dels 14 anys consent el menor (LOPDGDD, article 7).
- **Rebuig d'un esborrat (A-3):** l'article 12.4 del RGPD demana dir-ne els motius i informar del dret a reclamar. L'autoritat que s'hi cita és l'Agència Espanyola de Protecció de Dades, perquè el club és una entitat privada.
- **Menors (J-10):** la Llei orgànica 8/2021 (articles 47, 48 i 57 a 59) obliga les entitats que fan activitats esportives amb menors de manera habitual a aplicar protocols, tenir un delegat de protecció, formar el personal i exigir el certificat negatiu del Registre Central de Delinqüents Sexuals.

## Advertiments de l'equip

1. **I-2, remitent cris@cris.es.** Perquè els correus no acabin a la carpeta de brossa, el proveïdor de correu ha de tenir el domini **cris.es** autenticat (SPF i DKIM), i això demana accés al DNS de cris.es, que ara no es té (I-3). Mentre no es faci, la plataforma no pot enviar correus reals. És una condició de producció nova.
2. **J-8, custòdia per l'administrador.** Els comptes d'emergència serveixen per quan l'administrador perd l'accés o no hi és. Si els custodia només ell, en aquest cas ningú no els pot fer servir. Es registra la decisió tal com és; es recomana que una segona persona de la junta en tingui una còpia tancada.
3. **G-1, G-4, A-3 i J-10** són feina de l'equip sense revisió d'una gestoria ni d'un assessor.

## Queda obert

- **J-9:** l'import total de la quota de ple dret a terminis (el full en paper deia 3 × 32 €, 96 €; d'un sol cop són 90 €). Amb els punts 1 a 4 de la P-61, per a la T-M01-49.
- **T-3:** des de quina data compten els 12 mesos de quota i de carnet d'un soci importat de Cluber, si «Data alta/renovació» no es fa servir. Afecta la T-M01-25, que ja està bloquejada fins al 05a.

## Conseqüències

- **Implementat (branca `night/2026-11-11`, sense push):** S-4, J-6, I-2, A-3, G-4 i G-1.
- **Tasques desbloquejades, per implementar:** T-M01-40 (J-2 i G-2), T-M01-43 (T-5 i T-6; depèn de la T-M01-32), llista de candidats a impagat a la T-M01-18 (J-4), exportació amb notes revisades i canal presencial per a menors a la T-M01-22 (A-1 i A-2), i la regla S-5 al mòdul 02.
- **Tasca nova T-M00-08:** textos editables sense tocar el codi (S-1 i S-3).
- **T-M01-29:** guies aprovades; passa a «Feta».
- **Document nou:** `docs/protocols/proteccio-de-menors.md` (esborrany per a la junta).
- **Pendents:** vegeu `pendents.md`.
