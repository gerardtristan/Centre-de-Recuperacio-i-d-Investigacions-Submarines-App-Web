# Guia del tresorer: despeses, marges, tancaments i factures

**Per a qui és:** el tresorer (i l'administrador, per a la reobertura dels períodes). **Estat:** esborrany de la T-M09-24 [A validar: tresorer]. Està escrita a partir dels serveis que ja funcionen i de les proves de principi a fi; **les pantalles del 09 encara no estan fetes** i aquesta guia es completarà amb els noms dels botons quan hi siguin. Les regles són al [pla, secció M09](../planning.md#M09-5-processos) i les [regles de negoci](../planning.md#M09-7-regles). Per a quotes, cobraments i conciliació, vegeu la [guia de la tresoreria](guia-tresoreria.md); per als ajuts, la [guia d'ajuts](guia-ajuts.md).

## 1. La idea
El **marge d'una activitat** és el que queda dels ingressos després de les despeses i del cost del material: *inscripcions + altres ingressos directes − costos directes − cost de material*. Tot va en cèntims i cap moviment no s'esborra: una correcció és una anul·lació amb motiu i un registre nou.

## 2. Despeses
- **Registrar una despesa:** proveïdor, número i data de la factura, categoria, descripció, import, departament (sempre) i, si cal, centre de cost. L'IVA és opcional.
- **Sense factura:** una despesa sense la factura adjunta queda **«sense factura»**, surt a la seva llista i en rep l'avís qui pot pagar despeses (d'inici, el tresorer i l'administrador). Bloqueja el tancament del període. *Adjuntar el fitxer encara no està fet: espera el xifratge dels documents (T-M09-25).*
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
Per a cada activitat, el responsable de cursos i sortides (les seves) o el tresorer posa els **costos previstos** per categoria (embarcació, aire…). El **marge previst** fa servir els preus de les inscripcions vives (pendents de pagament i confirmades), per a cada categoria els costos reals si n'hi ha i, si no, els previstos, i el cost de material previst. *L'avís de marge baix encara no està fet (T-M09-13, necessita una plantilla de correu del nucli).*

## 6. Tancar una activitat
Quan el 02 marca l'activitat com a feta, el tresorer la pot **tancar econòmicament**. Es rebutja, amb el motiu, si queda res pendent: inscripcions sense pagar o amb una plaça oferta, propostes de devolució sense fer, material pendent (03) o despeses repartides sense factura. En tancar-la, la plataforma calcula el **marge real** i el **congela**:
- inscripcions: el que ha entrat a la tresoreria pels seus cobraments, menys devolucions i retorns;
- costos: els repartiments, les comissions dels cobraments i el lloguer (factura o estimació);
- cost de material: el cost d'ús del material del club.

Un moviment que arriba després (una devolució tardana, una factura que arriba tard) **no canvia** el marge congelat: surt al costat com a **ajust posterior** i compta al període on entra.

## 7. Informes
L'informe d'un departament en un període mostra els marges de les activitats tancades (per activitat, subtipus o projecte), les despeses sense activitat, els ajuts en una línia pròpia i els altres ingressos, i el total. Es pot treure en CSV (en cèntims).

## 8. Períodes
Cada mes (ajust; d'inici, mensual [A validar: tresorer, S-M09-05]) es tanca el període:
1. La **llista de control** mostra el que falta: línies de l'extracte sense conciliar, activitats fetes sense tancar, despeses sense factura, despeses pagades sense conciliar i factures fallides.
2. El tresorer ho resol o, element per element, ho **porta al període següent amb un motiu** [A validar: tresorer, S-M09-15]. Un element portat torna a sortir al mes següent fins que es resol.
3. Un cop tancat, no s'hi pot registrar res del 09 amb data d'aquell mes; els moviments d'origen extern (cobraments, devolucions, comissions del banc) entren al període obert.
4. Només l'**administrador** el pot **reobrir**, amb motiu, i només el darrer període tancat; és per als errors de la feina del propi període. Amb el període reobert, el marge d'una activitat es pot recalcular i substitueix el congelat. *El tancament i la reobertura són a la T-M09-16 (#407), i el correu al tresorer i a la junta en reobrir necessita una plantilla del nucli.*

## 9. Factures
La facturació va amb un servei homologat (Verifactu) que encara no s'ha triat: **està desactivada** i, a les proves, fa servir un servei fictici. Quan s'activi per a un tipus de càrrec, cada cobrament pagat en demana la factura, i cada devolució d'un cobrament facturat en té la rectificativa. Un salt de numeració queda al registre.

## 10. Què encara no fa la plataforma
Les pantalles del 09, adjuntar i xifrar factures i comprovants (T-M09-25), l'avís de marge baix (T-M09-13) i el correu de reobertura d'un període.
