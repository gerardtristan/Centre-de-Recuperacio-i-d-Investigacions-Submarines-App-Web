# Guia del tresorer: despeses, marges, tancaments i factures

**Per a qui és:** el tresorer (i l'administrador, per a la reobertura dels períodes). **Estat:** esborrany de la T-M09-24 [A validar: tresorer]. Està escrita a partir dels serveis que ja funcionen, de les proves de principi a fi i de les pantalles que ja hi ha a l'administració: «Despesa nova», «Despeses sense factura» i «Marge de l'activitat». La pantalla dels períodes arriba amb la T-M09-16c i aquí ja se'n descriuen els botons. La resta (repartir, altres ingressos, informes i factures a mà) encara no té pantalla: aquí es descriu què fa la plataforma, i la guia es completarà amb els noms dels botons quan hi siguin. Les regles són al [pla, secció M09](../planning.md#M09-5-processos) i les [regles de negoci](../planning.md#M09-7-regles). Per a quotes, cobraments i conciliació, vegeu la [guia de la tresoreria](guia-tresoreria.md); per als ajuts, la [guia d'ajuts](guia-ajuts.md).

## 1. La idea
El **marge d'una activitat** és el que queda dels ingressos després de les despeses i del cost del material: *inscripcions + altres ingressos directes − costos directes − cost de material*. Tot va en cèntims i cap moviment no s'esborra: una correcció és una anul·lació amb motiu i un registre nou.

## 2. Despeses
- **Registrar una despesa:** al menú de l'administració, **«Despesa nova»** obre «Registra una despesa» (funciona també al mòbil, en una sola columna). S'hi posen el proveïdor, el número i la data de la factura, la categoria, la descripció, l'import, el departament (sempre) i, si cal, el centre de cost. L'IVA és opcional. Es desa amb **«Registra la despesa»**; si falta alguna dada, els errors surten resumits a dalt i al costat de cada camp.
- **Sense factura:** una despesa sense la factura adjunta queda **«sense factura»**, surt a la llista **«Despeses sense factura»** del menú (descripció, proveïdor, data, departament, import i estat) i en rep l'avís per correu qui pot pagar despeses (d'inici, el tresorer i l'administrador; el correu només porta la referència de la despesa). Bloqueja el tancament del període. *Adjuntar el fitxer encara no està fet: espera el xifratge dels documents (T-M09-25). Mentrestant, tota despesa nova queda «sense factura».*
- **Corregir:** mentre està per pagar, cada canvi queda al registre amb el valor anterior. Una despesa **pagada** no es modifica: s'anul·la amb motiu (es crea el contramoviment a la tresoreria) i se'n registra una de nova.
- **Pagar:** es crea exactament un moviment de despesa a la tresoreria amb el mateix import, departament i centre de cost.
- **Categories i proveïdors** són dades que es poden ampliar. La categoria «Lloguer» porta la marca de **lloguer de material**: la factura d'un centre de busseig repartida a una activitat substitueix l'estimació del 03 (mai totes dues).

## 3. Repartir una despesa entre activitats
Una factura (per exemple, l'embarcació de dues sortides) es pot repartir:
- **per participants** (els que van venir; si no s'ha passat llista, les inscripcions confirmades) [A validar: tresorer, S-M09-02],
- **a parts iguals**, o
- **a mà** (per corregir la proposta).

Els cèntims que sobren de l'arrodoniment van, un a un, a les activitats amb més participants (en empat, a la més antiga). La suma no pot passar de l'import; el que no es reparteix queda al departament, sense activitat. Tornar a repartir substitueix el repartiment anterior (el registre guarda tots dos), excepte si una part ja és al marge congelat d'una activitat tancada.

## 4. Altres ingressos
Ajuts, patrocinis, donatius i altres: tipus, pagador (organisme o empresa), import, compte, data de valor i departament. Es crea el moviment a la tresoreria. **Un ajut no porta mai activitat**: compta al departament (vegeu la [guia d'ajuts](guia-ajuts.md)).

## 5. Costos previstos i marge previst
Per a cada activitat, el responsable de cursos i sortides (les seves) o el tresorer posa els **costos previstos** per categoria (embarcació, aire…). El **marge previst** fa servir els preus de les inscripcions vives (pendents de pagament i confirmades), per a cada categoria els costos reals si n'hi ha i, si no, els previstos, i el cost de material previst. A la pantalla **«Marge de l'activitat»** (`/gestio/marges/<activitat>/`; encara no hi ha l'enllaç des de la fitxa de l'activitat) es veuen el marge previst (inscripcions, altres ingressos directes, costos directes, cost de material, marge, percentatge i participants) i la taula de **«Costos previstos»**, on cada import es desa amb **«Desa el cost previst»**. Un cost previst només compta mentre la categoria no té costos reals. **Avís de marge baix:** quan es desa o es treu un cost previst i el marge previst queda per sota del llindar (ajust; d'inici 0 € [A validar: junta, S-M09-04]), el responsable de l'activitat i el tresorer reben un correu amb el nom de l'activitat i els imports. Si la previsió no canvia, no es repeteix.

## 6. Tancar una activitat
Quan el 02 marca l'activitat com a feta, el tresorer la pot **tancar econòmicament** des de l'apartat **«Tancament econòmic»** de la pantalla del marge, amb **«Tanca l'activitat»**. Si encara no es pot, la pantalla diu **«Encara no es pot tancar»** amb els motius: inscripcions sense pagar o amb una plaça oferta, propostes de devolució sense fer, material pendent (03) o despeses repartides sense factura. En tancar-la, la plataforma calcula el **marge real** i el **congela**:
- inscripcions: el que ha entrat a la tresoreria pels seus cobraments, menys devolucions i retorns;
- costos: els repartiments, les comissions dels cobraments i el lloguer (factura o estimació);
- cost de material: el cost d'ús del material del club.

Un moviment que arriba després (una devolució tardana, una factura que arriba tard) **no canvia** el marge congelat: a la pantalla surt a **«Marge congelat»**, a la línia **«Ajustos posteriors»**, i compta al període on entra.

## 7. Informes
L'informe d'un departament en un període mostra els marges de les activitats tancades (per activitat, subtipus o projecte), les despeses sense activitat, els ajuts en una línia pròpia i els altres ingressos, i el total. Es pot treure en CSV (en cèntims).

## 8. Períodes
Cada mes (ajust; d'inici, mensual [A validar: tresorer, S-M09-05]) es tanca el període. Tot es fa a la pantalla **«Tancament de períodes»** (`/gestio/marges/periodes/`), al grup «Quotes i tresoreria» del menú.

**Crear el període:** el primer, amb **«Comença el»** i **«Crea el període següent»**; els següents, amb el mateix botó, comencen l'endemà de l'anterior i duren el que diu l'ajust en aquell moment (si es canvia a trimestral, els que ja hi ha no canvien). No es pot crear un període nou mentre el darrer encara no ha començat.

**Tancar-lo:**
1. La **llista de control** mostra el que falta: línies de l'extracte sense conciliar, activitats fetes sense tancar, despeses sense factura, despeses pagades sense conciliar i factures fallides.
2. El tresorer ho resol o, element per element, ho **porta al període següent amb un motiu** [A validar: tresorer, S-M09-15]: a l'apartat **«Tancar el període del … al …»**, cada element té el seu camp de motiu, i **«Tanca el període»** tanca només si cada element està resolt o té motiu; si no, la pantalla diu **«Encara no es pot tancar»** i quins elements falten. Un element portat torna a sortir al mes següent fins que es resol.
3. Un cop tancat, no s'hi pot registrar res del 09 amb data d'aquell mes; els moviments d'origen extern (cobraments, devolucions, comissions del banc) entren al període obert.
4. Només l'**administrador** el pot **reobrir**, amb motiu, i només el darrer període tancat; és per als errors de la feina del propi període. Amb el període reobert, el marge d'una activitat es pot recalcular i substitueix el congelat. A la pantalla, l'administració hi veu **«Reobrir el període del … al …»**: escriu el **«Motiu de la reobertura»** i prem **«Reobre el període»**. El tresorer i la junta en reben un correu amb el període i el motiu.

## 9. Factures
La facturació va amb un servei homologat (Verifactu) que encara no s'ha triat: **està desactivada** i, a les proves, fa servir un servei fictici. Quan s'activi per a un tipus de càrrec, cada cobrament pagat en demana la factura, i cada devolució d'un cobrament facturat en té la rectificativa. Un salt de numeració queda al registre i el tresorer en rep un correu amb la sèrie, el número esperat i el que ha donat el servei. Cada soci veu les factures emeses a nom seu a **«Les meves factures»**, a la seva àrea personal (la descàrrega en PDF arriba amb la T-M09-25).

## 10. Què encara no fa la plataforma
Les pantalles per repartir despeses, registrar altres ingressos, treure els informes i emetre factures a mà; adjuntar i xifrar factures i comprovants (T-M09-25), i descarregar el PDF de les factures; els avisos dins l'app (ara només surten per correu).
