# Guia d'ajuts per al tresorer i la junta

**Per a qui és:** el tresorer i la junta (i qui sigui responsable d'una sol·licitud). **Estat:** esborrany de la T-M09A-14 [A validar: tresorer i junta]. Està escrita a partir dels serveis que ja funcionen i de la prova de principi a fi dels ajuts; **les pantalles encara no estan fetes**. Les regles són al [pla, apartat d'ajuts](../planning.md#M09-ajuts-5-processos). Per a despeses i marges, vegeu la [guia de despeses i marges](guia-despeses-i-marges.md).

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

*Els avisos del calendari (tancament de la convocatòria, resposta, justificació, requeriments) encara no surten: necessiten plantilles i tasques del nucli.*

## 4. Resolució
- **Concedida:** import concedit, data i resolució adjunta. Si és més del que s'havia demanat, surt un avís.
- **Denegada:** motiu, data, resolució i què caldria millorar. Es pot **copiar** a una convocatòria nova (o copiar la convocatòria a l'edició següent): la sol·licitud nova mostra les observacions de la denegació.

## 5. Cobrar l'ajut
Quan arriba l'ingrés (una o més vegades: bestreta i saldo), el tresorer el registra des de la sol·licitud: va a la tresoreria com a «altres ingressos», al departament de la sol·licitud, amb la resolució com a document. **Un ajut no s'imputa mai a cap activitat**: a l'informe del departament surt en una línia pròpia.

## 6. Justificar
1. El tresorer lliga a l'ajut les **despeses** del departament dins el període subvencionable, amb l'import imputat de cadascuna. Una despesa no es pot imputar per més del seu import, ni una d'un altre departament o fora del període.
2. Quan l'organisme fa un **requeriment d'esmena**, es registra amb la data límit (si la convocatòria té termini d'esmena, es proposa sola), qui l'ha de respondre i, després, la resposta. Una pròrroga de la justificació porta el motiu.
3. Amb una sol·licitud ja justificada, les despeses lligades només es poden canviar si hi ha un requeriment obert.

*El paquet de justificació (resum, llistat de factures i ZIP) espera el xifratge dels documents (T-M09-25).*

## 7. Qui ho pot fer
Els permisos AJ1 a AJ13 són dades que l'administrador assigna: d'inici, el tresorer i l'administrador gestionen els ajuts, i la junta hi té consulta i les accions de les sol·licituds de què és responsable. Cap eina d'IA rep els documents de justificació.

## 8. Què encara no fa la plataforma
Les pantalles, els avisos del calendari, el paquet de justificació i adjuntar documents xifrats.
