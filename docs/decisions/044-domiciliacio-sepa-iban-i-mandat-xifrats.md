# 044 — Domiciliació SEPA pròpia: IBAN i mandat xifrats, només per a aquest ús

- **Data:** 27/10/2026
- **Estat:** Acceptada el 27/10/2026 pel responsable del projecte com a **camí per defecte, revisable si el banc o el proveïdor ofereixen custòdia de mandats** (alternatives 1 i 2), amb l'ampliació de més avall. És una **excepció** a la RN-70 de la spec 00 («cap camp guarda un IBAN») i a la condició sobre l'IBAN de la [025](025-dos-nivells-de-produccio.md); la spec 00 no s'edita. Pendent de verificar amb el banc (identificador de creditor i remeses, P-45) i amb la gestoria i el responsable de protecció de dades (conservació).

## Context
- Amb Stripe descartat ([042](042-proveidors-substituits-pel-requisit-ue.md)), ningú no custodia l'IBAN i el mandat en nom del club.
- Si les quotes es cobren per domiciliació amb una remesa del banc (fitxer pain.008), la plataforma ha de generar el fitxer amb l'IBAN de cada deutor i la referència i la data del mandat.
- L'escenari B de la [022](022-mandats-sepa-escenari-base-b.md) (mandats nous signats a la plataforma) es manté.

## Alternatives
1. Que el banc custodiï els mandats i la plataforma només enviï imports [A verificar si CaixaGuissona ho ofereix].
2. Que el proveïdor de pagaments ofereixi domiciliació amb custòdia pròpia (per exemple, Mollie) [A verificar compliment de la 035].
3. **La plataforma guarda l'IBAN i el mandat xifrats, només per a la domiciliació.**

## Decisió
Si el banc no ofereix l'alternativa 1 i no es tria l'alternativa 2:
- La plataforma guarda **l'IBAN i el mandat** (referència única, data de signatura, tipus recurrent, identificador de creditor, text acceptat i versió) **només per a la domiciliació de quotes**.
- **Xifrat a nivell de camp** amb una clau fora de la base de dades i fora del repositori; mai als registres, a les exportacions ni a les còpies sense xifrar.
- **Accés:** només el procés que genera la remesa. A la pantalla, sempre emmascarat (per exemple, `ES•• •••• •••• •••• •••• 1234`). El tresorer no veu l'IBAN complet.
- **Signatura del mandat dins l'app:** text SEPA estàndard, acceptació explícita, correu de confirmació amb la referència del mandat (CK G3). Menors: el signa el titular del compte (P-33).
- **RGPD:** base legal, execució del contracte de soci; finalitat única, cobrament de quotes; informació al soci al text del mandat.
- **Conservació:** mentre el mandat sigui vigent; quan es revoca o el soci es dona de baixa, es conserva el que obliga la llei (prova del mandat durant el termini de reclamació d'un rebut no autoritzat, 13 mesos, més el termini legal que digui la gestoria) i després es destrueix [A validar amb la gestoria: Q-14].
- **Esborrat RGPD ([028](028-esborrat-rgpd-i-registre-d-activitat.md)):** el mandat i l'IBAN es bloquegen, no s'anonimitzen, fins al final del termini; després es destrueixen.

## Ampliació abans d'acceptar-la (27/10/2026)
Afegida perquè la revisió prèvia a l'acceptació va trobar que faltava una norma i que dues més eren només a les conseqüències. No canvia res del que hi havia.
- **Clau de xifratge:** fora de la base de dades i del repositori, amb versió; **rotació** provada (es torna a xifrar cada IBAN amb la clau nova i es retira la vella) i **prova de restauració** d'una còpia amb la clau, abans del nivell 1 de producció i després de cada rotació. Hi ha una còpia de la clau guardada fora del servidor per les persones que fixi la junta.
- **Ningú no veu l'IBAN complet a cap pantalla**, cap correu, cap registre ni cap exportació. L'única sortida en clar és el fitxer de la remesa, que necessita el banc.
- **Fitxer de la remesa (pain.008):** la plataforma el genera a demanda, no el desa i en registra l'empremta i qui l'ha descarregat. **Norma per al tresorer:** el descarrega només en un dispositiu del club o personal amb bloqueig de pantalla i disc xifrat; no l'envia per correu ni el desa en cap carpeta sincronitzada ni compartida; el puja al banc i **l'esborra del dispositiu el mateix dia** (també de la paperera i de les baixades). Si l'ha de tornar a pujar, el torna a generar. La plataforma recorda la norma en cada descàrrega i demana confirmar que s'ha esborrat en marcar la remesa com a enviada [A validar: tresorer].
- **Millora opcional (afegida en acceptar-la):** l'enllaç de descàrrega del fitxer de la remesa és **d'un sol ús** i **caduca** al cap d'un temps curt [A validar: tresorer, quant]; per tornar-lo a baixar, se'n genera un de nou, que també queda al registre.
- **Conservació:** continua [A validar: gestoria, Q-14] fins que respongui la gestoria.

## Conseqüències
- Una prova automàtica comprova que l'IBAN només és en el camp xifrat del mandat (substitueix CA-15.6 per a aquest camp).
- CK C9 s'ha d'actualitzar: «la plataforma no guarda l'IBAN, excepte xifrat al mandat (044)».
- Requisit de seguretat nou: rotació de la clau de xifratge i prova de restauració de còpies amb la clau.
- Si s'aplica l'alternativa 1 o 2, aquesta decisió queda substituïda i es torna a la RN-70.

## Fonts
- Requisit comunicat per l'equip el 27/10/2026
- Spec 00, RN-70 i decisió [028](028-esborrat-rgpd-i-registre-d-activitat.md); arquitectura §4.3
