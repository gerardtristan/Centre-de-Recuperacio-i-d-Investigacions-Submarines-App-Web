# Guia d'ajuts per al tresorer i la junta

**Per a qui és:** el tresorer i la junta (i qui sigui responsable d'una sol·licitud). **Estat:** esborrany de la T-M09A-14 [A validar: tresorer i junta]. Està escrita a partir dels serveis que ja funcionen, de la prova de principi a fi dels ajuts i de les pantalles **«Calendari d'ajuts»** (T-M09A-05) i **«Justificació de l'ajut»** (T-M09A-10c), posada al dia el 25/11/2026; les pantalles de convocatòries i de sol·licituds encara no estan fetes. Les regles són al [pla, apartat d'ajuts](../planning.md#M09-ajuts-5-processos). Per a despeses i marges, vegeu la [guia de despeses i marges](guia-despeses-i-marges.md).

## 1. Els estats d'una sol·licitud
| Estat | Què vol dir |
|---|---|
| **Detectada** | El club ha vist la convocatòria i la vigila |
| **En preparació** | S'ha decidit presentar-s'hi i es preparen els documents |
| **Presentada** | S'ha presentat a l'organisme (fora de la plataforma) |
| **Concedida** / **Denegada** | L'organisme ha resolt |
| **Justificada** | S'ha enviat la justificació |
| **Tancada** | No hi ha res més a fer |

Cada canvi d'estat queda al registre. L'administrador pot desfer l'últim canvi, amb motiu.

## 2. Convocatòria i elegibilitat
1. Es dona d'alta la **convocatòria**: organisme, nom, dates, import màxim, documents requerits, termini de resolució (si l'organisme el publica), període de despeses subvencionables i, si n'hi ha, el termini d'esmena.
2. Es crea la **sol·licitud** (detectada) amb el responsable, el departament i l'import previst.
3. Una persona llegeix les bases i marca la convocatòria **elegible** o **no elegible**, amb notes. La plataforma no ho decideix mai sola. Si no és elegible, les sol·licituds obertes es tanquen amb el motiu.

## 3. Preparar i presentar
Amb l'elegibilitat revisada, la sol·licitud passa a **en preparació** i surt la llista de documents requerits per marcar-los a punt. Quan es presenta, s'hi posa la data, el número de registre d'entrada i l'import demanat, i passa a **presentada**. Si l'organisme publica el termini de resolució, es calcula la data prevista de resposta.

## 3b. Calendari i avisos
- **«Calendari d'ajuts»** (menú de l'administració, `/gestio/ajuts/calendari/`; el veuen el tresorer, la junta i l'administració): les dates d'un mes, amb **«Mes anterior»** i **«Mes següent»**, i a sota totes les **«Properes dates»** a partir d'avui. Hi surten els tancaments de les convocatòries, les respostes previstes de les presentades, les dates de justificació de les concedides (la pròrroga, si n'hi ha) i les dates límit dels requeriments sense resposta. No hi surt cap nom de persona ni la descripció dels requeriments.
- **Avisos per correu** (cada dia, una tasca de la plataforma; cada avís surt una sola vegada encara que la tasca es repeteixi). Els reben el responsable de la sol·licitud (o del requeriment) i qui configura els dies dels avisos (AJ10; d'inici el tresorer i l'administrador) [A validar: tresorer i junta, P-503]:
  - **tancament:** 30, 14 i 7 dies abans del tancament de la convocatòria, si la sol·licitud encara és detectada o en preparació; si la data de tancament canvia, es calculen sobre la nova;
  - **resposta:** el dia de la resposta prevista, si encara és presentada;
  - **justificació:** 30, 14 i 7 dies abans de la data de justificació (o de la pròrroga) de les concedides [A validar: junta, S-M09A-04];
  - **requeriment d'esmena:** un en registrar-lo i, mentre no es respon, 7 i 2 dies abans de la data límit [A validar: junta, S-M09A-09]. Si la data límit canvia, els que falten es calculen sobre la nova i els ja enviats no es repeteixen.
- Els dies són ajustos (d'inici, 30, 14 i 7 per als tancaments i la justificació, i 7 i 2 per als requeriments). Els correus només porten l'organisme, la convocatòria, les dates i la referència de la sol·licitud. L'avís dins l'app arribarà més endavant.

## 4. Resolució
- **Concedida:** import concedit, data i resolució adjunta. Si és més del que s'havia demanat, surt un avís.
- **Denegada:** motiu, data, resolució i què caldria millorar. Es pot **copiar** a una convocatòria nova (o copiar la convocatòria a l'edició següent): la sol·licitud nova mostra les observacions de la denegació.

## 5. Cobrar l'ajut
Quan arriba l'ingrés (una o més vegades: bestreta i saldo), el tresorer el registra des de la sol·licitud: va a la tresoreria com a «altres ingressos», al departament de la sol·licitud, amb la resolució com a document. **Un ajut no s'imputa mai a cap activitat**: a l'informe del departament surt en una línia pròpia.

## 6. Justificar
1. El tresorer lliga a l'ajut les **despeses** del departament dins el període subvencionable, amb l'import imputat de cadascuna. Una despesa no es pot imputar per més del seu import, ni una d'un altre departament o fora del període.
2. Quan l'organisme fa un **requeriment d'esmena**, es registra amb la data límit (si la convocatòria té termini d'esmena, es proposa sola), qui l'ha de respondre i, després, la resposta. Una pròrroga de la justificació porta el motiu.
3. Amb una sol·licitud ja justificada, les despeses lligades només es poden canviar si hi ha un requeriment obert.

4. **El paquet de justificació** es fa a la pantalla **«Justificació de l'ajut»**: s'hi arriba des del «Calendari d'ajuts», amb l'enllaç de la sol·licitud (només les concedides i les justificades). Hi surten les **«Despeses incloses»** amb l'import imputat i les **«Despeses excloses»**, pel número i el motiu (cap nom de persona).
   - **«Genera el paquet»** fa una versió nova amb el resum, el llistat de factures, els comprovants i les **«Còpies amb l'IBAN tapat»** (o els **«Originals»**, si la convocatòria no accepta còpies). Es descarrega amb **«Descarrega el ZIP»**: queda xifrat i al registre, i només el baixa qui té el permís.
   - **«Envia'l i marca l'ajut com a justificat»** apunta la **«Data d'enviament a l'organisme»**. Un cop enviada, una versió nova només es pot enviar lligada a un requeriment obert (**«Requeriment que respon»** → **«Envia aquesta versió»**).
   - Si es marca il·legible una factura d'una versió ja enviada, el tresorer en rep un avís.

## 7. Qui ho pot fer
Els permisos AJ1 a AJ13 són dades que l'administrador assigna: d'inici, el tresorer i l'administrador gestionen els ajuts, i la junta hi té consulta i les accions de les sol·licituds de què és responsable. Cap eina d'IA rep els documents de justificació.

## 8. Què encara no fa la plataforma
Les pantalles de convocatòries i de sol·licituds (alta, elegibilitat, documents a punt, presentació, resolució i cobrament: avui només els serveis), lligar les despeses a l'ajut des d'una pantalla i registrar els requeriments; els avisos dins l'app (ara només per correu). [A validar: tresorer i junta, com es fa mentrestant.]
