# 104. Fotos de titulacions d'altres agències, homologació a la FECDAS i tramitació de la primera estrella

- **Data:** 21/11/2026
- **Estat:** Proposada (responsable del projecte, 21/11/2026). S'accepta en fusionar-se la PR `risc:alt` amb el «fusiona la #N» escrit del propietari: toca el xifratge de dades personals (CLAUDE.md, D4; decisió 100).
- **Canvia:** la frase «Cap foto ni escaneig del carnet de titulació» de `DiverCertification` ([M02-6](../planning.md#M02-6-entitats)).
- **Completa:** el mòdul 02 ([addenda de la 104](../planning.md#M02-addenda-104)) i el 06 ([addenda de la 104](../planning.md#M06-addenda-104)), la [matriu de permisos](../planning.md#rols-i-permisos-059-matriu) (AC24 a AC26) i l'[apèndix de valors configurables](../planning.md#valors-configurables) (VC-55 a VC-59).

## Context

Necessitat nova del propietari (21/11/2026):

> «La junta necessita fotos dels carnets d'altres titulacions, si en tenen, perquè de vegades s'ha de passar d'una titulació com PADI a FECDAS (de moment som full FECDAS). I s'han de tramitar de zero les llicències dels bussejadors nous de primera estrella.»

Fins ara:
- El pla prohibia guardar cap foto ni escaneig del carnet de titulació ([M02-6](../planning.md#M02-6-entitats)). Una titulació d'una altra agència només es podia declarar (`source = declared`) i verificar a mà (RN-M02-32).
- La titulació oficial que obté un alumne apte es tramita fora de la plataforma (RN-M02-16), i el pla no deia qui ho fa ni com se'n fa el seguiment.
- La plataforma no s'integra amb la FECDAS ([036](036-fecdas-alia.md)). Les llicències es tramiten amb un llistat exportable i es marquen a mà (P-M06-E).

## Alternatives

- **A.** Mantenir la prohibició: la secretaria mira el carnet en persona i el soci l'envia a la FECDAS pel seu compte. No hi ha cap llista de seguiment.
- **B.** Guardar la foto del carnet com a document privat i xifrat, amb accés per permís i esborrat automàtic. Les homologacions i les titulacions de primera estrella es fan amb llistes de tramitació com les de llicències.
- **C.** Com B, però guardant la foto sense xifrar, només amb el control d'accés.

## Decisió

**Opció B**, amb les regles següents. Per la regla D2, cada dubte que toca dades personals o diners pren l'opció més conservadora.

1. **La foto es permet només per comprovar i homologar.** Una persona pot tenir la foto del carnet (anvers i revers) de les titulacions que té d'una altra agència. No hi ha cap altre ús: no surt a cap llistat general, no es publica i no la rep cap eina d'IA.
2. **Les agències són una dada.** La llista d'agències (FECDAS, PADI, SSI, CMAS, NAUI…) s'edita des dels ajustos del 02. L'agència de destinació de les homologacions és l'ajust VC-55, amb la FECDAS com a valor inicial. Cap nom d'agència va escrit al codi.
3. **Fitxer privat i xifrat, com els documents de la [051](051-abast-de-la-044-i-documents-de-justificacio.md).** Accepta una imatge o un PDF, que es comproven amb `core.validate_upload`. La imatge es desa sense metadades (EXIF) i reduïda. Es xifra a l'aplicació abans de pujar-la a l'emmagatzematge de la UE ([005](005-fitxers.md), [035](035-dades-nomes-dins-ue.md)), amb la clau fora del magatzem i pel mateix camí que la 044 (S-M05a-10). Mai no té cap adreça pública: només s'obre amb una vista que comprova el permís i deixa la visualització al registre d'activitat.
4. **Qui la veu.** Hi ha dos permisos nous de la matriu, que l'administrador pot editar: **AC24** «Fotos de titulacions: veure» i **AC25** «Fotos de titulacions i homologacions: veure i editar».
   - Configuració inicial: la **Secretaria** té AC24 i AC25; la **Junta** només té AC24.
   - L'**instructor** continua veient només el nivell (C3), mai la foto.
   - El **soci** veu, puja i esborra les seves. És una acció pròpia, fora de la matriu.
5. **Homologació.** El soci, o la secretaria per ell, demana «passar la meva titulació a la FECDAS».
   - La sol·licitud entra a la llista **«Homologacions pendents»** (AC26).
   - La secretaria hi comprova la foto i la tramita **fora de la plataforma** (036), amb el llistat exportable.
   - La marca **tramitada** i, després, **feta**: llavors es crea la titulació de l'agència de destinació (agència, nivell, número i data) i la titulació d'origen queda verificada (`verified_by`, `verified_at`).
   - També la pot **rebutjar**, amb un motiu.
6. **Primera estrella.** Quan un alumne queda apte i es crea la seva titulació del club (RN-M02-16 i RN-M02-31), si la fitxa del curs té un **nivell oficial per tramitar**, l'alumne entra sol a la llista **«Titulacions i llicències per tramitar»**.
   - Si no té cap llicència vigent, la llista ho marca, i la secretaria li demana la **primera llicència**: és una sol·licitud nova del 06, sense número anterior.
   - La plataforma no crea la llicència sola: la demana la secretaria, amb el flux normal del 06, i la paga la persona, mentre la junta no digui si el preu del curs ja la inclou (P-426).
   - La titulació i la llicència es tramiten amb els llistats exportables i es marquen tramitades i fetes (o vigents, en el cas de la llicència) quan arriba el número.
7. **Preus.** Els preus de l'homologació i de la tramitació de la titulació són ajustos amb data d'entrada en vigor (VC-58). El valor inicial és 0 i la plataforma no els cobra fins que s'encén l'interruptor VC-59.
8. **Conservació.**
   - La foto s'esborra **3 mesos** (ajust VC-57) després que la titulació quedi verificada o que l'homologació quedi feta o rebutjada. Una foto sense cap d'aquestes coses i sense cap homologació oberta s'esborra el mateix nombre de mesos després de pujar-la.
   - La titulació conserva la verificació sense la foto.
   - En esborrar les dades d'una persona (RGPD), les fotos s'esborren al moment: no són registres econòmics.
   - El termini que valgui de debò és una pregunta per a la gestoria (P-425).
9. **Registre i salut.**
   - Pujar, veure, verificar i esborrar una foto (a mà o per la cua) deixa una fila al registre d'activitat, amb el compte que ho fa o «sistema».
   - La foto entra a l'exportació RGPD de la persona i a cap altra exportació.
   - La pantalla de pujada avisa que no s'hi pugi cap document de salut.
10. **Interruptor.** Tot plegat es construeix darrere de l'ajust **VC-56**, `activities.card_photos_enabled`, que és apagat per defecte. No s'encén a producció fins que s'hagin respost la P-425 i hi hagi el sí escrit del propietari (D2: RGPD i xifratge).

## Conseqüències

- **Pla:**
  - M02-6 marca la frase antiga com a canviada i enllaça l'[addenda del 02](../planning.md#M02-addenda-104): entitats, RN-M02-47 a RN-M02-56, CA-M02-49 a CA-M02-57 i tasques T-M02-41 a T-M02-49.
  - Addenda del 06 ([M06](../planning.md#M06-addenda-104)): RN-M06-28, CA-M06-34 i les tasques T-M06-26 i T-M06-27.
  - Files noves AC24 a AC26 a la matriu i VC-55 a VC-59 a l'apèndix.
- **Estat:** les tasques s'apunten a `docs/estat/M02.md` i `docs/estat/M06.md` (pendents) i entren als carrils de la fase 2. La T-M02-42 (xifratge) és `risc:alt` i espera el sí escrit del propietari, com totes les de la 044 i la 051.
- **Preguntes:** al [tauler](tauler-preguntes.yml) i a [pendents](pendents.md):
  - P-425: el termini de conservació, per a la gestoria.
  - P-426: qui paga la primera llicència de l'alumne.
  - P-427: el departament i l'import de les tramitacions.
- **Document de funcionalitats** (`docs/funcionalitats-processos/`): no es regenera. Mana el pla (047).
- **CLAUDE.md:** no canvia. La regla «Cap dada de salut» continua valent, i la foto d'un carnet de titulació no és una dada de salut.

## Fonts

- Missatge del propietari, 21/11/2026 (necessitat nova per a la fase 2: 02 Activitats i 06 Llicències).
- [M02-6](../planning.md#M02-6-entitats), RN-M02-16, RN-M02-31 i RN-M02-32; [P-M06-E](../planning.md#M06-5-processos); decisions [036](036-fecdas-alia.md), [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md) i [051](051-abast-de-la-044-i-documents-de-justificacio.md).
