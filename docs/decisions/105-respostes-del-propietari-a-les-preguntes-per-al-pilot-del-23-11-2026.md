# 105. Respostes del propietari a les preguntes per al pilot del 23/11/2026

- **Data:** 23/11/2026
- **Estat:** Acceptada (propietari, instrucció escrita del 23/11/2026). Les respostes marcades «provisional» es construeixen així, però no s'encén res a producció fins que arribi la confirmació per escrit que s'hi indica.
- **Completa:** [`pendents.md`](pendents.md) (les definitives passen a «Resolts»; les provisionals continuen a «Oberts» amb la resposta), el [tauler](tauler-preguntes.yml), l'estat de les tasques ([`M00`](../estat/M00.md), [`M02`](../estat/M02.md), [`M04`](../estat/M04.md), [`M05a`](../estat/M05a.md), [`M06`](../estat/M06.md)) i la [checklist de producció](../checklist-produccio.md).

## Context

El 23/11/2026 el propietari va respondre per escrit les preguntes obertes de la fase 2 que hi havia a `pendents.md` i al tauler de `master`, i a les PR obertes #403, #448 i #455. Cap resposta no encén res a producció ni toca diners o dades reals.

- **D1:** les regles congelades (01, 04, 05a i 05b) no s'editen quan la resposta coincideix amb el que ja està construït. L'única regla nova d'aquests mòduls, la P-411, va amb una sola edició a la fila VC-08 de l'[apèndix de valors configurables](../planning.md#valors-configurables), que no és cap secció congelada.
- **Mòduls no congelats:** primer el pla, després el codi. Les respostes del 06 que canvien una regla o un exemple s'escriuen a la secció M06. Les del 07 i el 08 (P-485 a P-492) s'escriuen a la PR #448, al lloc de cada pregunta, abans de fusionar-la.
- **P-425, P-426 i P-427** ja tenen la resposta provisional del propietari a la PR #403. Aquesta PR no crea cap decisió nova: completa la [104](104-fotos-de-titulacions-homologacio-a-fecdas-i-primera-estrella.md), que ja és a `master`, i per això no s'ha renumerat.
- **P-459:** el propietari va escriure «AC27», però la #403 ja fa servir l'AC27 i l'AC28 («Inclou la primera llicència»). El permís nou de la P-459 és l'**AC29**, amb el mateix nom, rols i abast.
- **P-500** és la mateixa pregunta del lot #463 (CA-M06-19), no una col·lisió de números.

## Decisió

| ID | Resposta | Definitiva o provisional | Canvi al codi |
|---|---|---|---|
| P-401 | A, com s'ha construït: la sessió de qui desa no es tanca, perquè ja ha escrit el codi TOTP a la mateixa petició | Definitiva | No |
| P-402 | B: esborrar la targeta guardada també demana al proveïdor que n'esborri la referència. Ara es queda com està (A); l'operació s'afegeix a l'adaptador quan hi hagi el proveïdor real (P-45, punt 6). Requisit del nivell 1 a la checklist (fila G4) | Definitiva | Sí, més endavant: T-M05a-27 (bloquejada pel proveïdor real) |
| P-407 | A, com s'ha construït. La VC-18 i la CA-M05b-27 continuen congelades amb la T-M05b-23 | Definitiva | No |
| P-410 | A: una tasca nova de la fase 1 al 04, la pantalla per crear, reanomenar i desactivar departaments, centres de cost i comptes de tresoreria (T3, M7), sobre els serveis de la 00, amb registre (qui, quan, valor anterior). Cap llista no queda al codi | Definitiva | Sí: T-M04-22 (toca el nucli) |
| P-411 | A: «General», «Quotes de socis» i «General / Ajustos de caixa» són entrades del sistema: no es reanomenen ni es desactiven, i la pantalla de la P-410 ho mostra i ho impedeix al servidor | Definitiva | Sí: dins la T-M04-22 |
| P-412 | A: el termini de bloqueig és un termini legal al codi (6 anys, variable d'entorn `LOCKED_DATA_RETENTION_YEARS`) que només canvia amb una decisió. Es corregeix el docstring d'`apps/core/privacy.py` perquè digui el mateix que la G-1 | Provisional: falta la confirmació per escrit de la gestoria (Q-14) | Sí: T-M00-13 (docstring, torn del nucli) |
| P-413 | A, com s'ha construït (P23, d'inici només la Secretaria, amb motiu, contrasenya i codi) | Definitiva | No |
| P-414 | A, com s'ha construït (la suma no canvia, cap termini amb pagament o cobrament en curs, cap de 0 €, sense límit de dates) | Definitiva | No |
| P-415 | A, com s'ha construït (P23, només la quota d'una alta presencial, amb les condicions de la P-396) | Definitiva | No |
| P-416 | A, com s'ha construït. `GDPR_ADMIN_NOTES_EXPORT_ENABLED` continua apagat a producció | Provisional: falta la confirmació per escrit de l'assessor de protecció de dades, i el propietari ho ha de dir per escrit | No |
| P-417 | A, com s'ha construït (M11b, d'inici la Secretaria, només l'esborrat d'un menor de 14 anys, amb la identitat del representant comprovada; l'atén M11) | Definitiva | No |
| P-418 | C: l'exportació d'un menor de 14 anys es lliura fora de la plataforma; la plataforma només registra la petició. No es construeix cap canal nou | Provisional: falta la confirmació per escrit de l'assessor de protecció de dades | No |
| P-419 | A: només la frase. El comptador visible no es fa ara | Definitiva | No |
| P-420 | A: les referències del proveïdor i de la transferència es queden en clar; només el nom i el document es bloquegen. Apuntat a la revisió RGPD del nivell 2 (H1) | Provisional: falta la confirmació per escrit de l'assessor de protecció de dades, abans del nivell 2 | No |
| P-423 | A: sense IP a les entrades que escriu la tasca (minimització) | Definitiva | No |
| P-424 | A: «Textos legals» no deixa publicar un text que porti «[A validar» o «[A verificar», amb un missatge que diu quina marca cal treure | Definitiva | Sí: T-M00-10 (al mateix lloc que la comprovació de l'HTML; torn del nucli) |
| P-425 | Resposta provisional a la PR #403 (decisió 104) | Provisional: falta la confirmació per escrit de la gestoria | Segons la 104 |
| P-426 | Resposta provisional a la PR #403 (decisió 104) | Provisional: falta la confirmació per escrit de la junta i el tresorer | Segons la 104 (T-M02-50, T-M02-51) |
| P-427 | Resposta provisional a la PR #403 (decisió 104) | Provisional: falta la confirmació per escrit del tresorer | Segons la 104 |
| P-440 | A: un estat derivat més, «Vigent més endavant», que no compta com a vigent fins al dia d'inici | Definitiva | No (ja construït, T-M06-03); s'escriu a la taula d'estats de M06-5 |
| P-441 | A: val el codi (60 dies de calendari: V−60 és l'1/11). Es corregeix l'exemple de M06-7 | Definitiva | No |
| P-442 | B: renova la vigent de qualsevol tipus que caduca més tard; passar d'aficionat a tècnic també atura els avisos de l'anterior | Definitiva | Sí: T-M06-28 |
| P-443 | A: la data d'inici és opcional; si no se'n dona cap, el dia que es declara, i mai després del venciment | Definitiva | No (ja construït, T-M06-08); s'escriu a RN-M06-14 |
| P-444 | C quan la secretaria porti el model de la FECDAS; mentrestant, A (el CSV provisional, sense document ni contacte) | Provisional: falta la confirmació per escrit de la secretaria, amb el model de la FECDAS | No ara |
| P-445 | B: `imports.mark_undone(batch, by)` al nucli, fet servir des del 01 i el 06, traient els `shortcut:`. Mentrestant, A | Definitiva | Sí: T-M00-11 (torn del nucli) |
| P-446 | A: una llicència «pendent de confirmar» no compleix el requisit; en mode d'avís s'inscriu marcada i en mode de bloqueig, no | Provisional: falta la confirmació per escrit de la secretaria | No (ja construït) |
| P-447 | A: qui tramita (LC5) posa la caducitat; cap permís nou | Definitiva | No (ja construït) |
| P-448 | A: tots els tipus de soci actius amb la seva quota vigent, de més barat a més car. La pàgina continua apagada | Provisional: falta la confirmació per escrit de la junta | No (ja construït) |
| P-449 | A: només majors d'edat al formulari públic; un menor rep un missatge perquè escrigui a la secretaria | Definitiva | No (ja construït) |
| P-450 | B: una finalitat pròpia «llicència de convidat» al limitador. Mentrestant, A (comparteix el límit de «Fer-se soci») | Definitiva | Sí: T-M00-12 (torn del nucli) |
| P-455 | A: la sessió copiada conserva el lloc desactivat i l'activitat no es pot publicar fins que totes les sessions tenen un lloc actiu | Definitiva | No (ja construït) |
| P-456 | A, com RN-M02-30: compleix sense marca; el responsable en veu l'origen al detall del requisit | Definitiva | No |
| P-457 | A: l'accepta per ell qui té AC5, i en acceptar-la el convidat rep l'enllaç de convidat per pagar | Definitiva | No (ja construït) |
| P-458 | A, la proposta, com el propietari ja va dir el 21/11/2026: text legal editable amb aquesta proposta per defecte, publicada només a local i a proves; a producció, cap versió fins que la junta la validi | Provisional: falta la confirmació per escrit de la junta | No (ja construït) |
| P-459 | A: un permís nou, **AC29 «Titulacions: carregar i verificar»**, d'inici per a la Secretaria, el responsable de cursos i sortides i l'administrador; la junta, només consulta. L'administrador el pot donar o treure des de l'editor de permisos. Desbloqueja la càrrega a mà i la verificació de la T-M02-31 (la importació continua esperant la mostra Q-23) | Definitiva | Sí: T-M02-52 (catàleg de permisos, torn del nucli, `risc:alt`) |
| P-470 | A, com s'ha construït (la meitat lluny del zero) | Definitiva | No |
| P-471 | A, com s'ha construït (per reobrir un període anterior, primer es reobren els posteriors, i queda al registre) | Definitiva | No |
| P-472 | A, com s'ha construït (la despesa guarda la data real de la factura; el bloqueig és al moviment) | Definitiva | No |
| P-473 | A, com s'ha construït (qui té MG2) | Definitiva | No |
| P-474 | A: abans de migrar `equipment/0009` a producció, qui administra la base de dades executa `CREATE EXTENSION btree_gist;`. L'usuari de l'aplicació no té permisos d'administrador. Pas afegit a la checklist (fila A8) | Provisional: falta la confirmació per escrit d'informàtica, en desplegar | No |
| P-485 | A: el butlletí surt per la cua de correu de la plataforma, amb prioritat baixa i dins del comptador diari; la llista només és a la plataforma. Darrere de `website.newsletter_enabled`, apagat | Definitiva | S'escriu a la spec del 07 (PR #448) |
| P-486 | A: tots els motius a la Secretaria; els tancats s'esborren 6 mesos després. Tots dos són ajustos (el termini i la llista de motius amb el seu destinatari). Darrere de `website.contact_enabled`, apagat | Provisional: falta la confirmació per escrit de la junta, i de la gestoria per al termini | S'escriu a la spec del 07 (PR #448) |
| P-487 | A: per sota de 3 es mostra «menys de 3», amb la cel·la següent amagada si només n'hi ha una d'amagada. El 3 és un ajust | Definitiva | S'escriu a la spec del 08 (PR #448) |
| P-488 | B (diferent de la recomanació): la definició exacta de cada indicador viu al codi amb el càlcul i sempre es mostra; a més, cada indicador té un text d'ajuda editable (permisos «veure» i «veure i editar») per a explicacions del club. Motiu: els textos d'ajuda són dades, i la definició fixa evita que el text digui una cosa i el càlcul una altra | Definitiva | S'escriu a la spec del 08 (PR #448) |
| P-489 | A: una vista pública declarada que només serveix les imatges actives de la web, comprovant-ho a cada petició; cap carpeta pública | Definitiva | S'escriu a la spec del 07 (PR #448) |
| P-490 | A: panells fixos primer; ordenar i amagar blocs per compte com a última tasca del 08 | Definitiva | S'escriu a la spec del 08 (PR #448) |
| P-491 | A: cap analítica de visites | Definitiva | S'escriu a la spec del 07 (PR #448) |
| P-492 | A: fila pròpia del 07 (correu, versió del text legal, esdeveniments només afegits); si se subscriu un soci des de la seva àrea, també el consentiment de la 00 | Definitiva | S'escriu a la spec del 07 (PR #448) |
| P-500 | A: el criteri vol dir «la llicència canvia dues vegades després de la versió 1»; el text de CA-M06-19 es corregeix quan es desfaci la congelació, sense canviar el codi | Definitiva | No |

## Conseqüències

- Tasques noves de codi, en l'ordre del camí crític (D4); les del nucli (`apps/core`, `apps/accounts`) van una a una, en el torn del nucli: T-M00-10 (P-424), T-M00-13 (P-412), T-M00-11 (P-445), T-M00-12 (P-450), T-M02-52 (P-459), T-M06-28 (P-442), T-M04-22 (P-410 i P-411) i, quan hi hagi el proveïdor real, T-M05a-27 (P-402).
- Tot valor o llista nova va a «Ajustos», amb els permisos «veure» i «veure i editar» (055, 059).
- Res no s'encén a producció per aquesta decisió. Les provisionals continuen a «Oberts» de `pendents.md` fins que arribi la confirmació per escrit.
