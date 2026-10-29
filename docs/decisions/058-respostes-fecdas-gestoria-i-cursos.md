# 058 — Respostes de la FECDAS, la gestoria, cursos i sortides i el tresorer (29/10/2026)

- **Data:** 29/10/2026
- **Estat:** Acceptada pel responsable del projecte. S'aplica amb **addendes** als mòduls aprovats (00 i 01, 02, 05a, 05b, 06 i 09), sense editar-ne cap regla ni cap decisió existent, com la [052](052-llicencia-font-unica-al-06.md) i la [055](055-ajustos-configurables-i-addendes.md). Substitueix **només en els punts que s'indiquen** la V-04 de la [spec 00](../../specs/00-base-comuna/spec.md), la [017](017-pagaments-metodes-i-domiciliacions.md) (mètode recomanat per a la quota), la [028](028-esborrat-rgpd-i-registre-d-activitat.md) (què es fa amb els registres econòmics passat el termini legal) i el supòsit S-M09-03. Tot el que encara falta porta [A verificar] (dada externa) o [A validar] (decisió del club), amb propietari. El número 056, reservat per retirar la llicència d'un dia, no es fa servir: la llicència d'un dia existeix.

## Context
- El 28/10/2026 es van preparar les preguntes externes que bloquegen entrar en producció ([preguntes-externes.md](../preguntes-externes.md)).
- El 29/10/2026 el responsable del projecte ha portat les respostes de la FECDAS, la gestoria, el responsable de cursos i sortides i el tresorer, i ha pres decisions sobre nivells, titulacions i pagament de quotes.
- Els mòduls 01, 02, 03, 04, 05a, 05b, 06 i 09 estan aprovats i no s'editen.

## Alternatives
- Editar les regles dels mòduls aprovats: trenca la norma de no editar el que està aprovat i en perd la traçabilitat.
- Esperar que totes les preguntes tinguin resposta: bloqueja el que ja se sap.
- **Una decisió nova amb addendes per mòdul**, que deixa oberts amb propietari els punts que falten.

## Decisió

### Part 1 · Respostes
1. **Data de naixement.** Es recull a la persona (00). Finalitat: tramitar llicències i comprovar l'edat mínima dels cursos. Només la veuen la secretaria i l'administrador; la resta de rols que veuen la persona veuen només «major d'edat» o «menor d'edat». S'inclou a l'exportació RGPD i s'anonimitza amb la resta de dades. P-33 (socis i participants menors) continua obert. Substitueix la V-04 de la spec 00 **només en aquest punt**, sense editar la spec.
2. **Llicències** (06):
   - Tipus: **Aficionat** i **Tècnic**. Durades: **un dia**, **any natural** i **365 dies**. Se suposa que els dos tipus tenen les tres durades [A verificar: FECDAS].
   - Any natural: des del dia que es tramita fins al 31 de desembre. No canvia res del 06.
   - 365 dies: caduca el **mateix dia de l'any següent menys un dia** (del 15/03 al 14/03). Els anys de traspàs no compten.
   - La llicència d'un dia **existeix i s'activa**.
   - Recàrrec de no soci: valor inicial **20 €** (2000 cèntims). El preu de soci continua sent el de la federació.
   - Obertura de la renovació de l'any natural: valor configurable, inicial l'**1 de desembre**. Els avisos als 60, 30 i 7 dies continuen.
   - Camp de format del carnet (físic o digital) [A validar: secretaria].
   - El llistat per a la FECDAS es fa en el format que triï el club.
   - No hi ha cap cànon de club.
   - Si la FECDAS varia el preu segons el mes de compra, cal un preu per tram [A verificar: FECDAS]. Mentre no se sàpiga, hi ha un preu per tipus i durada.
3. **Instructors** (02): per assignar un instructor a una sessió cal que sigui **soci actiu** i que tingui **llicència tècnica vigent** (`licences.current`). Que «adherit al C.R.I.S.» vol dir soci actiu: [A validar: junta]. Mode per defecte: **bloqueig**, configurable [A validar: junta].
4. **Facturació** (09): es factura **tot cobrament**. Porten IVA els cursos, les sortides i el material; la botiga en línia continua fora d'abast. Les quotes i les llicències no porten IVA (text d'exempció [A verificar: gestoria]). El tipus d'IVA és configurable per tipus de càrrec, amb valor inicial [A verificar: gestoria]. El servei homologat i Verifactu (P-02, P-47) continuen oberts.
5. **Llicències a la comptabilitat:** sempre ingrés del soci i despesa a la federació. Marge 0 per als socis i +20 € (el recàrrec) per als no socis.
6. **Moviments tardans:** es confirma que entren al període obert amb la data original, com ja diu la [053](053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md) (addenda de la [050](050-addenda-tresoreria-despeses-ingressos-i-periodes.md)). No canvia res.
7. **Conservació:** els registres econòmics **no s'eliminen mai**. Les dades personals que hi surten s'anonimitzen passat el termini legal [A verificar: gestoria, Q-14]. Substitueix la 028 només en el que es fa amb els registres econòmics passat el termini (anonimitzar en lloc de destruir).
8. **Donatius de persones:** es fan, amb nom i NIF del donant, certificat de donatiu i model 182. Substitueix el supòsit S-M09-03. Que el club pugui emetre certificats deduïbles: [A verificar: gestoria].
9. **Ajuts:** camp opcional de termini d'esmena per convocatòria. Sense prioritat ara.
10. **Llicències de Cluber sense caducitat:** Cluber no guarda la data de caducitat. El registre mínim del 01 admet la caducitat desconeguda, i el pas únic del 06 importa aquestes llicències com a «pendents de confirmar», sense avisos fins que se'n sàpiga la data.
11. **Rebut retornat:** al segon intent, el soci paga un import extra que cobreix el cost del retorn de CaixaGuissona [A validar: junta i banc; cal cobertura als estatuts]. Mentre no es validi, s'aplica el valor actual (el paga el club).
12. **Informàtica:** es mantenen els supòsits del pla tal com són. No s'afluixa el requisit de dades dins la UE ([035](035-dades-nomes-dins-ue.md)).

### Part 2 · Nivells, titulacions i pagament de quotes
13. **Nivells i especialitats** (02):
   - Llista de nivells **ordenada** i editable pel responsable de cursos i sortides (per exemple, B1 < B2; nivells d'1 i 2 estrelles de la FECDAS).
   - Requisit de **nivell mínim** per activitat. Un «B1/B2» vol dir «mínim B1»; si els grups fan coses diferents, es fan dues activitats (duplicar).
   - Requisit d'**especialitats** del catàleg, amb «totes» o «alguna».
   - Mode avís o bloqueig per activitat, modificable, amb un valor per defecte per tipus d'activitat.
   - En mode bloqueig només compten les titulacions **verificades** o d'un **curs del club**; les declarades només donen avís [A validar: junta].
14. **Titulacions** (02):
   - En emetre el certificat d'un curs del club, es crea la titulació lligada al curs: qui l'expedeix (el C.R.I.S.), data, instructor, nivell o especialitat i número de certificat.
   - Les titulacions inicials es carreguen a mà (origen «declarada» o «importada»), amb opció de verificar-les. S'importen de Cluber si el fitxer en porta [A verificar: tresorer, mostra Q-23].
15. **Pagament de quotes** (05a i 05b):
   - Als socis nous se'ls recomana per defecte la **targeta guardada**, si PaynoPain ho permet [A verificar: PaynoPain]. La domiciliació continua disponible. La transferència es permet, sense obligar-hi. Substitueix la 017 només en quin mètode es recomana per defecte; si el proveïdor no permet guardar la targeta, es continua recomanant la domiciliació.
   - Avís abans que caduqui la targeta guardada, i reintent si el cobrament falla.
   - La quota de soci es renova cada any; la baixa s'ha de demanar abans d'una data límit, i el soci rep un avís previ del cobrament. Data i termini: [A validar: junta i gestoria].
   - Opció per convidar els qui paguen per transferència a passar a un pagament automàtic.

## Conseqüències
- Addendes noves al pla: [M01](../planning.md#M01-addenda-058) (amb la part de la 00), [M02](../planning.md#M02-addenda-058), [M05a](../planning.md#M05a-addenda-058), [M05b](../planning.md#M05b-addenda-058), [M06](../planning.md#M06-addenda-058) i [M09](../planning.md#M09-addenda-058). Cap regla aprovada no s'edita.
- Preguntes que es tanquen o canvien d'estat: a [preguntes-externes.md](../preguntes-externes.md).
- Continuen obertes: el banc, PaynoPain, la mostra de l'exportació de Cluber (Q-23), els preus de la FECDAS i els trams, la devolució d'una llicència tramitada, Verifactu i el servei homologat, els tipus i el text d'exempció de l'IVA, el termini legal de conservació i P-33.
- CLAUDE.md encara diu «domiciliació SEPA (per defecte)» per a les quotes i que els registres que la llei obliga a conservar «es destrueixen». Els punts 7 i 15 d'aquesta decisió hi discrepen: cal decidir si s'actualitza CLAUDE.md.

## Fonts
- Respostes de la FECDAS, la gestoria, el responsable de cursos i sortides i el tresorer, portades pel responsable del projecte el 29/10/2026.
- Decisions preses amb el responsable del projecte a la conversa del 29/10/2026.
