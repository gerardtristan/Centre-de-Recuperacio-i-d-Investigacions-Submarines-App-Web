# 051 — Abast de la 044 i documents de justificació amb IBAN

- **Data:** 27/10/2026
- **Estat:** Acceptada. **Aclareix l'abast** de la [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md), que no es modifica.

## Context
- La 044 diu que la plataforma només guarda l'IBAN xifrat al mandat i només per domiciliar quotes.
- Per justificar un ajut, l'organisme demana els comprovants de pagament del banc (F 9.10), i aquests documents solen portar l'IBAN del club i del proveïdor. Les factures de despesa també poden portar-ne.
- Calia aclarir si la regla de la 044 s'aplica també a aquests documents ([M09-13](../planning.md#M09-13-riscos), dubte 4).

## Decisió
1. **La 044 cobreix els IBAN i els mandats dels socis.** No s'hi afegeix ni s'hi treu res.
2. **Els documents de justificació** es regeixen per les regles del magatzem de documents d'aquesta decisió, no per la 044. Ho són els comprovants de pagament del banc, les factures de despesa i els paquets de justificació d'ajuts.
   - **Només el tresorer i la junta** els poden obrir. Cap altre rol, tampoc l'administrador, en veu el contingut, encara que gestioni la despesa o la sol·licitud.
   - Es guarden **xifrats** a l'emmagatzematge de fitxers dins la UE ([005](005-fitxers.md), [035](035-dades-nomes-dins-ue.md)), amb xifratge fet per l'aplicació abans de pujar-los i clau fora del magatzem.
   - **Cap eina d'IA** no els rep, ni per llegir-los ni per resumir-los.
   - El sistema pot generar una **còpia amb l'IBAN emmascarat** (només els quatre últims dígits) i **conserva l'original**. La còpia es fa dins la plataforma, sense cap servei extern: en un PDF amb text, es detecta l'IBAN amb el patró i el dígit de control. Si no es pot detectar (per exemple, una foto), el document es marca «no emmascarat» i el tresorer en puja una còpia emmascarada a mà.
   - **[A verificar: tresorer, per a cada convocatòria]** si l'organisme accepta la còpia emmascarada. Mentre no se sàpiga, el paquet porta la còpia emmascarada i l'original es dona a part si l'organisme el demana.
3. Cap camp, pantalla, registre ni exportació de la plataforma mostra l'IBAN com a text. El fitxer original només surt sencer quan el tresorer o la junta el descarreguen, i la descàrrega queda al registre d'activitat.

## Conseqüències
- El 09 i el seu apartat d'ajuts apliquen aquestes regles ([M09-12](../planning.md#M09-12-seguretat), [M09-ajuts-12](../planning.md#M09-ajuts-12-seguretat)). La convocatòria té un camp nou: si accepta la còpia emmascarada.
- CLAUDE.md enllaça aquesta decisió a la regla de l'IBAN, sense canviar-la.
- La biblioteca de xifratge i la custòdia de la clau segueixen el mateix camí que la 044 (S-M05a-10 [A verificar: informàtica]).

## Fonts
- Aprovació del responsable del projecte, 27/10/2026 (punt 3 de les aprovacions)
- [`planning.md`, M09-13](../planning.md#M09-13-riscos), dubte 4
