# 108. Respostes del propietari del 27/11/2026: preguntes del tauler, contingut de la web, butlletí i fer-se soci, i compte ràpid

- **Data:** 27/11/2026
- **Estat:** Acceptada (sí escrit del propietari del 27/11/2026, «RESPOSTES DEL PROPIETARI DEL 27/11/2026», parts A a D). Les respostes que ha de confirmar algú altre són **provisionals** i es queden a «Oberts» de [`pendents.md`](pendents.md) amb qui les confirma (part A). Res no s'encén a producció amb aquesta decisió.
- **Canvia:** regles congelades del 01 (D1, [089](089-prova-d-acceleracio-interruptors-d1-a-d6.md)) i del 07, la definició del compte personal de la [spec 00](../../specs/00-base-comuna/spec.md) i, amb un matís, la [051](051-abast-de-la-044-i-documents-de-justificacio.md). Cada regla té una sola edició al seu lloc, que enllaça aquí.

## Context

El tauler tenia obertes les preguntes que van sortir construint el 06, el 07 i el 09 (23 a 25/11/2026). A més, el propietari vol que la web nova tingui tot el contingut de la web actual, que el butlletí arribi a tantes persones com es pugui dins de la llei, i que crear un compte sigui tan ràpid com a qualsevol web.

## Decisió

### A. Preguntes del tauler

| Pregunta | Resposta | Estat |
|---|---|---|
| P-43 | B, precisada: una sola persona manté la web, el rol de Resp. comunicació; si no n'hi ha, la Secretaria. Després es reparteix des dels permisos | Provisional: confirma la junta |
| P-500 | A | Resolta |
| P-501 | A | Provisional: confirma la secretaria |
| P-502 | A | Provisional: confirma la secretaria |
| P-550 | La còpia amb el número de compte emmascarat només cal quan el document porta dades bancàries d'un soci o d'una altra persona física. El compte del club i el d'una empresa proveïdora no s'emmascaren, i el paquet de justificació porta l'original. Quan cal, la còpia la fa el tresorer a mà. Matisa la [051](051-abast-de-la-044-i-documents-de-justificacio.md) (vegeu més avall) | Provisional: confirma el tresorer |
| P-551 | A; quan entri Pillow amb la [106](106-editor-visual-de-la-web-publica.md), la foto també es redueix | Resolta |
| P-552 | A | Provisional: confirma la gestoria |
| P-590 | Les pàgines inicials són les de la web actual (part B), no la llista de vuit | Resolta |
| P-591 | A | Resolta |
| P-592 | C: la factura a una empresa és del club (fitxer sense persona propietària a la 00, obert només amb MG9) | Provisional: confirma el tresorer |
| P-593 | A | Provisional: confirma el tresorer |
| P-620 | A | Provisional: confirma la gestoria |
| P-621 | A (doble confirmació amb un botó al formulari públic); la resta, substituïda per la part C | Resolta |
| P-622 | B: baixa amb un botó i d'un clic des del programa de correu (`List-Unsubscribe-Post`, RFC 8058) | Resolta |
| P-623 | A | Provisional: confirma la gestoria |
| P-624 | A | Provisional: confirma la junta |
| P-630 | A | Resolta |
| P-631, P-632 | Substituïdes per la part C | Resoltes |
| P-633 | A: només JPEG i PNG, nets de metadades (també a la web: RN-M07-19 accepta només JPEG i PNG) | Resolta |

**Matís de la 051 (P-550).** La 051 deia que la plataforma fa una còpia amb l'IBAN emmascarat de cada document de justificació. Ara: la còpia només cal quan el document porta dades bancàries d'un soci o d'una altra persona física; el compte del club i el d'una empresa proveïdora no s'emmascaren i, en aquest cas, el paquet de justificació porta l'original. Quan cal, el tresorer puja la còpia a mà (sense detecció automàtica). La resta de la 051 (xifrat a la UE, només tresorer i junta, cap eina d'IA, descàrrega al registre) no canvia. Regla: RN-M09-23.

### B. Contingut de la web pública (07)

1. La web nova té **tot el contingut** de https://cris1954.cat/ (el contingut, no el format).
2. Es fa un **inventari exhaustiu** des de l'ordinador del responsable (el núvol no hi arriba) a `docs/web/contingut-cris1954/`: una fitxa per pàgina i subpàgina amb l'adreça, el títol, tots els textos, les dades de contacte i horaris, els enllaços, els documents descarregables i les imatges. Les imatges i els documents van a la carpeta local de fotos o a `static/img/web/`, segons la [107](107-fotos-reals-del-club-per-a-plantilles-mostres-i-captures.md).
3. Aquest contingut són les **pàgines inicials** de l'editor (dades inicials, editables), amb la **mateixa estructura de menú** que la web actual (tanca la P-590).
4. El que la web actual tingui i el pla no prevegi va a `pendents.md` com a dubte **reversible** amb l'opció per defecte «es manté».
5. DISSENY en revisa la presentació.

### C. Butlletí i fer-se soci (dins de l'RGPD i la LSSI)

Objectiu: tenir el màxim de persones al butlletí del C.R.I.S. (què fa el club, sortides, cursos i activitats) i animar a fer-se soci.

1. **Darrere de la sessió.** Per veure el preu de la quota, per fer-se soci i per apuntar-se com a no soci cal iniciar sessió o crear un compte. La web pública ho anuncia, però el preu i el formulari són darrere de la sessió. Les inscripcions de convidat a una activitat amb l'enllaç segur ([021](021-persones-no-socies-com-a-convidades.md)) no canvien.
2. **Casella en crear el compte.** Una casella ben visible i atractiva: «Vull rebre les sortides, els cursos i les novetats del C.R.I.S.». No ve marcada ni és obligatòria per crear el compte, i és el pas més destacat. Com que el correu del compte és verificat, marcar-la subscriu al moment, sense doble confirmació (substitueix la P-631). La casella de «Fer-se soci» també subscriu de debò (substitueix la P-632).
3. **Excepció de client (art. 21.2 LSSI).** Socis i persones que ja han pagat una activitat, un curs o una llicència reben per defecte la informació d'activitats del club, amb una casella per dir que no en el moment de donar les dades i la baixa a cada correu. **Irreversible:** ho ha de confirmar la gestoria ([P-710](pendents.md)); fins llavors, darrere d'un interruptor apagat.
4. **Benvinguda i seguiment.** Qui crea un compte i no és soci rep un correu de benvinguda amb què guanya si es fa soci i l'enllaç per fer-se'n. Correus de seguiment per fer-se soci, només si s'ha subscrit al butlletí.
5. **Baixa d'un clic.** Sempre d'un clic a cada correu (obligatori; és el que demanen Gmail i Yahoo): `List-Unsubscribe` i `List-Unsubscribe-Post` (P-622 B). Abans de confirmar la baixa, la pàgina pot oferir alternatives («només sortides», «menys correus»), però la baixa total queda a un sol clic. No es pot fer difícil.
6. **Àrea del soci.** Un avís discret per subscriure's a qui no ho està, que es pot tancar.
7. **Formulari públic.** El formulari del butlletí sense compte continua, amb la doble confirmació amb un botó (P-621 A).

Tot va darrere dels interruptors del butlletí, apagats a producció fins que la gestoria confirmi el punt 3.

**Lectura del punt 1 (de l'equip, reversible):** «apuntar-se com a no soci» és el formulari públic d'inscripció a una activitat; l'enllaç segur que el convidat rep per pagar i gestionar la inscripció (021) continua igual. Si el propietari volia dir una altra cosa, es corregeix a l'estat del 02 (T-M02-54).

### D. Crear compte ràpid

1. **Dades mínimes** del compte personal: nom, correu i contrasenya, més la casella del butlletí i l'acceptació de la política de privacitat. Res més. El document, la data de naixement, el telèfon o l'adreça es demanen quan calen (fer-se soci, apuntar-se a una activitat), no en crear el compte.
2. **Entrar i crear compte amb Google** («Continua amb Google»), al costat del correu i la contrasenya, amb OpenID Connect:
   - només per als comptes personals; **mai** per a l'entrada d'administració, que continua amb nom d'usuari i TOTP;
   - només es rep el nom i el correu verificat; si el correu ja té compte, s'hi enllaça després que la persona ho confirmi;
   - **excepció acotada a la regla de dades només a la UE** ([035](035-dades-nomes-dins-ue.md); el propietari la va citar com a «decisió 0002»): Google és una empresa de fora de la UE i veu que la persona entra a la plataforma. És una opció voluntària de la persona, la plataforma només en rep el nom i el correu, i les dades continuen desades a la UE. Al [registre de proveïdors](../proveidors-i-dades-ue.md);
   - la dependència (biblioteca d'OpenID Connect) va en una PR `risc:alt` pròpia; la clau del client de Google, a variables d'entorn, mai al repositori ([arquitectura](../arquitectura-integracions.md), §5 i §7);
   - darrere d'un interruptor apagat fins que hi hagi la clau; proves amb un proveïdor fals;
   - Apple no: el botó d'Apple no es fa ara (cal un compte de pagament); a l'iPhone, la clau d'accés ja dona l'entrada amb Face ID.
3. **Clau d'accés** (passkey: Face ID, empremta o el PIN del mòbil, WebAuthn) i **codi o enllaç pel correu**, sense contrasenya. No passen per cap empresa de fora. La dependència de WebAuthn va en una PR `risc:alt` pròpia.
4. **Mínim de passos:** el compte es crea en una pantalla i la persona torna directament on volia anar (el preu de la quota, fer-se soci o l'activitat).

## Conseqüències

- Regles (una edició a cada lloc): [P-M01-A](../planning.md#M01-5-processos) pas 1 i la fila P1 de [M01-4](../planning.md#M01-4-rols) (C.1); definició del compte personal a la [spec 00](../../specs/00-base-comuna/spec.md), «Glossari» (D); [RN-M07-06](../planning.md#M07-7-regles) (C); RN-M07-19 a l'[addenda de la 106](../planning.md#M07-addenda-106) (P-633); [RN-M09-23](../planning.md#M09-7-regles) (P-550).
- Tasques noves a l'estat (D1): [01](../estat/M01.md) T-M01-53 a T-M01-56; [07](../estat/M07.md) T-M07-32 a T-M07-38; [02](../estat/M02.md) T-M02-54 i T-M02-55; [09](../estat/M09.md) T-M09-32 i T-M09-33. El codi va en PR a part, per l'ordre de les tasques.
- El resum de regles del `CLAUDE.md` (la còpia emmascarada de la 051 i les dades a la UE) no es toca en aquesta PR: és una excepció de la decisió 100 i el propietari l'ha de fer o autoritzar.

## Font

Missatge escrit del propietari del 27/11/2026, «RESPOSTES DEL PROPIETARI DEL 27/11/2026 (sí escrits meus)», parts A, B, C i D, i «COM REGISTRAR-HO».
