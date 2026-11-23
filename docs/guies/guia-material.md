# Guia del responsable de material

**Per a qui és:** el responsable de material (i qui l'ajuda: responsable de cursos i sortides, instructors). **Estat:** esborrany de la T-M03-21 [A validar: responsable de material]. Està escrita a partir dels serveis que ja funcionen. De les pantalles del material, ja hi ha els informes i el cost d'ús (secció 8 i 10); la resta (inventari, assignació, lliurament i retorn) encara no hi és, i la guia es completarà quan hi siguin. Els noms del menú són provisionals. Les regles són al [pla, secció M03](../planning.md#M03-5-processos) i les [regles de negoci](../planning.md#M03-7-regles).

## 1. Què fa la plataforma amb el material
- Porta l'**inventari** de les peces del club (codi `MAT-NNNN`, tipus, talla o litres, propera revisió) i el seu historial.
- Guarda els **centres de busseig** i les seves **tarifes** amb versions: canviar un preu crea una versió nova i el que ja s'ha assignat conserva el preu antic.
- Pregunta als participants, en inscriure's, **què porten i què necessiten**.
- Ajuda a **assignar** a cada participant una peça del club, un lloguer a un centre o el seu propi material, a **lliurar-lo** i a **recollir-lo**.
- Calcula el **cost del material** de cada activitat per al marge que fa el tresorer.

Cap pantalla del material mostra dades de contacte dels participants. Dels participants, el responsable de material veu nom, talles i necessitats; el tresorer veu costos i no talles; l'instructor veu el material dels alumnes de les seves sessions, sense costos.

## 2. Tipus, inventari i stock
- **Tipus de material:** n'hi ha 14 d'inicials (aletes, màscara, tub, neoprè, escarpins, ploms, jaquet, regulador, ordinador, brúixola, boia, llanterna, ganivet de seguretat i ampolla). L'ampolla va en litres (un número amb un decimal com a màxim, per exemple 12 o 11,5); aletes, neoprè, escarpins i jaquet, amb talla; la resta, sense mida. L'ampolla i el regulador porten data de revisió.
- **Donar d'alta una peça:** la plataforma proposa el codi següent. La talla, els litres o la revisió són obligatoris segons el tipus.
- **Estats d'una peça:** disponible, en revisió o donada de baixa (amb motiu: perduda, trencada, revisió fallida). Una peça donada de baixa no torna. «Assignada» i «en ús» no són estats de la peça: surten de les assignacions.
- **Stock en una data:** per tipus i talla, quantes peces hi ha disponibles, assignades, en ús i en revisió. Cada peça compta una sola vegada i les de baixa no hi surten.

## 3. Centres i tarifes
Per a cada centre, cada equip o servei té un **preu de cost** (el que paga el club) i un **preu per al soci** (i, si cal, per al no soci; si no n'hi ha, el no soci paga el de soci [A validar: junta, S-M03-01]). Una tarifa nova porta data d'entrada en vigor (no anterior a avui) i una nota, i avisa el tresorer i la junta. Un centre desactivat no surt en una assignació nova.

Cada lloc de sortida pot tenir un **centre habitual**: és el que la plataforma proposa.

## 4. Material típic
Cada fitxa de curs o tipus de sortida té el seu **material típic** (per exemple, una immersió: jaquet, regulador, ampolla, ploms i neoprè, un de cada per participant). En crear una activitat se'n copia, i en duplicar-la es copia el de l'original. És el que el formulari d'inscripció pregunta i el que serveix per calcular el **cost de material estàndard** de l'activitat.

## 5. Abans de l'activitat: necessitats i assignació
1. **Necessitats.** En inscriure's, cada participant diu, per a cada peça del material típic, «porto el meu» o «necessito», i la talla (o els litres). Si la necessita, la talla és obligatòria. També ho diu qui va a la llista d'espera.
2. **Assignar.** Només a inscripcions **confirmades** (pagades). Per a cada necessitat:
   - **Del club:** la plataforma només ofereix peces **disponibles** de la talla aquells dies i amb la revisió vigent fins a l'últim dia. Una peça no pot estar a dues activitats amb dies que es toquin: ho impedeix la base de dades encara que dues persones assignin alhora.
   - **Llogat:** tria el centre; es copien el preu de cost i el preu per al participant de la tarifa vigent el primer dia de l'activitat.
   - **Propi:** queda constància que el porta.
3. **Llista de lloguer.** Per a cada centre, la plataforma genera la llista agrupada per material i talla, amb una **referència** per participant (número d'inscripció i inicials, mai el nom ni el contacte [A validar: junta, S-M03-04]). La llista no es desa: queda constància de qui l'ha generada i quan. L'envies pel canal del club i la marques **enviada**.

**Encara no està fet:** el càrrec del lloguer al participant (espera que la junta decideixi si el participant el paga a part, RN-M03-11).

## 6. El dia de l'activitat i després
1. **Lliurar:** marca cada peça com a lliurada.
2. **Recollir:** marca-la com a retornada i tria si torna a estar **disponible** o va **a revisió** (llavors no es pot assignar).
3. **Quantitats reals:** el que no s'ha fet servir (per exemple, d'un participant que no ha vingut) es marca **no s'ha fet servir**: no compta al cost ni al registre de la persona.
4. **Cost:** la plataforma calcula el cost d'ús del material del club, el cost i el preu dels lloguers (i el marge que en queda) i el cost per participant. El tresorer el veu al marge de l'activitat; quan registra la factura del centre, la factura substitueix l'estimació (mai totes dues).

**Material pendent.** Mentre hi hagi peces previstes o lliurades sense tancar, necessitats sense assignar o una llista de lloguer sense enviar, l'activitat **no es pot tancar** econòmicament: el tresorer veu el motiu (sense noms).

**Cancel·lacions.** Si una inscripció es cancel·la o caduca, o l'activitat es cancel·la, les peces que s'hi havien previst queden lliures soles. Les que ja s'havien lliurat s'han de recollir.

## 7. Revisions
Les ampolles i els reguladors porten la data de la propera revisió (la posa el responsable segons la normativa o el fabricant). La plataforma llista les peces amb la revisió dins dels dies de l'ajust (d'entrada, 30 [A validar: junta, S-M03-06]) o ja vençuda. En enviar una peça a revisió passa a «en revisió»; en tornar, es registra el resultat: correcta (torna disponible amb la data nova) o fallida (de baixa amb el motiu).

**Avís diari:** cada matí, si hi ha peces amb la revisió a prop o vençuda, rebràs un correu amb el codi, el tipus i la data de cada una (cal que el teu compte tingui un correu de notificació). **Encara no està fet:** l'avís a l'app.

## 8. Informes
Al menú de l'administració, **Activitats › Material: informes**. Cada bloc surt només si el teu rol el pot veure:
- **Material més usat:** tria les dates a «Des del» i «Fins al» i prem **Mostra**. Hi surt, per tipus i origen (del club, llogat o propi), quantes vegades s'ha fet servir. **Descarrega el CSV** baixa la mateixa taula.
- **Revisions properes:** les peces amb la revisió dins dels dies de l'ajust o vençuda (marcades «Vençuda»).
- **Cost de material per activitat:** les activitats amb material que pots veure; en triar-ne una, el cost d'ús del material del club, el cost i el preu dels lloguers, el marge dels lloguers i el cost per número d'inscripció (sense noms), amb el seu CSV.

**Imprimeix** obre la impressió del navegador (també es pot desar com a PDF); els formularis i els botons no surten al paper.

## 9. Càrrega inicial de l'inventari
**Encara no està fet** (T-M03-17): es farà amb la importació de la plataforma (pujar un CSV, validar sense escriure res, confirmar i, si cal, desfer). Fins aleshores, les peces es donen d'alta una a una. En proves, només amb dades inventades.

## 10. Cost d'ús del material del club
Al menú, **Ajustos › Material: cost d'ús**. Per a cada tipus, quant costa al club cada dia que es fa servir una peça seva (d'entrada, 0) i el proper canvi, si n'hi ha. El veu qui veu l'apartat «Material» dels ajustos; el canvia el tresorer: tria el tipus, escriu el cost per dia en euros, la data **Vigent des del** (no anterior a avui) i una **Nota**, i prem **Desa el cost**. El canvi queda al registre, avisa el tresorer i la junta i no toca les assignacions ja fetes.
