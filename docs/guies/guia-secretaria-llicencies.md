# Guia de la secretaria: llicències federatives

**Per a qui és:** la persona que fa la secretaria del club (i qui tingui el permís de tramitar llicències). **Estat:** esborrany, pendent de revisió (T-M06-18). El mòdul de llicències encara no és a producció; els textos de les pantalles, el format del fitxer per a la federació i alguns valors són provisionals, i cada apartat ho diu. Les regles són a [`planning.md#M06-5-processos`](../planning.md#M06-5-processos) i [`#M06-7-regles`](../planning.md#M06-7-regles).

## 1. On és
A l'administració, **Llicències** (`/gestio/llicencies/`). L'entrada del menú només surt a qui pot veure el llistat. Sense permís, la pàgina respon «no trobat».

## 2. El llistat
Una fila per llicència, per cognoms, amb l'estat que té **avui**:

| Estat | Què vol dir |
|---|---|
| Sol·licitada | La persona l'ha demanat; el càrrec encara no està pagat. |
| Pagada | Pagada i pendent de tramitar a la federació. |
| Tramitada | L'has enviada a la federació; encara no l'ha confirmada. No és vigent. |
| Vigent | Confirmada per la federació i dins de les dates. |
| Per renovar | Vigent, però caduca d'aquí a pocs dies (ajust «per renovar»). |
| Vigent més endavant | Confirmada, però encara no ha començat (per exemple, la de l'any vinent) [A validar: P-440]. |
| Pendent de confirmar | Ve dels registres antics de la fitxa del soci sense data de caducitat. A la columna «Caduca» hi diu «Per confirmar» (vegeu el punt 6). |
| Caducada | Ha passat la data de caducitat. |
| Cancel·lada | Cancel·lada amb motiu. |
| No tramitada a temps | Una llicència d'un dia que no es va tramitar abans del dia. |

**Filtres:** tipus i estat; amb el permís de veure'n els detalls, també categoria i «Caduca d'aquí a» (60, 30 o 7 dies o menys). La categoria, la data de caducitat i el número federatiu només surten amb aquest permís. La data de naixement i el document no surten mai al llistat.

## 3. Tramitar a la federació
1. Filtra per **Pagada** (o mira el recompte del botó de descàrrega).
2. Prem **Descarrega el fitxer per a la federació (N pagades)**. És un CSV amb cognoms, nom, data de naixement (només si tens permís per veure-la), tipus, categoria i data d'inici. **El format és provisional** fins que la FECDAS digui quines columnes vol [A validar: P-444]. La plataforma no desa el fitxer; el registre d'activitat n'apunta qui l'ha baixat, quan i l'empremta. Conté dades personals: envia'l només a la federació i esborra'l després.
3. Tramita-les a la web de la federació (fora de la plataforma).
4. Prem **Marca tramitada** a cada una. Una llicència anual comença el dia que la tramites; la de l'any vinent continua començant l'1/1 i la d'un dia, el dia triat.
5. Quan la federació la confirmi, prem **Vigent…**, escriu el **número federatiu** i prem **Sí, deixa-la vigent**. El número és obligatori a les del club [A validar: secretaria]. Si no cal esperar, des de «Pagada» pots anar directament a «Vigent…».

Quan una llicència queda vigent, la fitxa del soci la mostra (en té una còpia de lectura). La comprovació diària corregeix la còpia si mai no coincideix.

## 4. Venciments i avisos
- Cada dia, la plataforma avisa el titular als **60, 30 i 7 dies** del venciment (ajust «dies d'avís»), una sola vegada per tram. Si ja ha demanat la renovació, no rep més avisos. Les d'un dia no s'avisen.
- **Tu no reps un correu per llicència:** reps un sol resum per dia i tram, agrupat per data de venciment i categoria, i ordenat per data i nom. Com que gairebé totes les d'any natural caduquen el 31/12, al novembre i al desembre és normal que el resum sigui llarg.
- Per veure-les al llistat, filtra **Caduca d'aquí a** i tria el tram.
- L'endemà del venciment, la llicència passa a «Caducada» sola. No cal fer res.
- La llicència d'any natural de l'any vinent es pot demanar a partir de la data d'obertura (ajust, inicialment l'1/12). Es tramita quan la federació obre el període.

L'enviament dels correus d'avís i del resum està pendent de la plantilla de correu (T-M06-11): fins llavors, fes servir el filtre del llistat.

## 5. Cancel·lar
Una llicència sol·licitada, pagada o tramitada es pot cancel·lar amb un motiu. Una de vigent no es cancel·la: es deixa caducar.
- Si encara no era pagada, el càrrec s'anul·la.
- Si ja era pagada, el tresorer rep una **proposta de devolució** i decideix si la fa. La plataforma no torna mai diners sola.

La pantalla per cancel·lar encara no és feta: ara mateix, demana-ho a l'administrador.

## 6. Llicències «pendents de confirmar»
Quan el mòdul entri en producció, l'administrador passarà al 06 els registres de llicència que ara hi ha a les fitxes dels socis (els de Cluber i els que vas afegir a mà). Els que no tenen data de caducitat hi entren com a **Pendent de confirmar**:
- no reben cap avís ni caduquen;
- a la fitxa del soci, la caducitat continua «desconeguda»;
- el responsable d'una activitat la veu «pendent de confirmar» i l'instructor, «no»; per inscriure's a una activitat que demana llicència, **no compta com a vigent** [A validar: P-446].

Posar-hi la data la converteix en una llicència normal: comença a rebre avisos i la fitxa del soci en té la data l'endemà com a molt tard. Ho pot fer qui té el permís de tramitar [A validar: P-447], des de **Llicències**, l'enllaç **N per confirmar**:
- **En bloc:** marca les d'any natural sense data, tria l'any (l'actual o el següent) i prem **Confirma les seleccionades**. Caducaran el 31/12 d'aquell any. Si alguna no es pot confirmar (per exemple, comença després del 31/12), no se'n confirma cap.
- **Una a una:** **Confirma…** al costat de cada una. Si el titular ja ha escrit la data a «La meva llicència», la columna «Declarada pel titular» la mostra i el camp ja la porta: comprova-la amb la federació i confirma-la.

Mentre el titular l'ha declarada però tu no l'has confirmada, continua pendent: cap avís ni cap altre mòdul no la veu. Les pendents de confirmar que ja són al mòdul de llicències no surten a la pantalla antiga de la fitxa del soci («Llicències de la fitxa per confirmar» del menú de socis). **Abans d'obrir les inscripcions del mòdul d'activitats, confirma-les totes** (RN-M02-34).

## 7. «Ja en tinc una»
Si una persona ja té la llicència d'una altra banda, es desa amb el número, el tipus i la data de caducitat, sense càrrec ni tramitació. Si no se sap la data d'inici, es pren el dia que es declara [A validar: P-443].

## 8. La pàgina pública per a no socis
Mentre la junta no activi l'opció de llicències per a no socis, la pàgina pública `/llicencies/` no existeix. Quan l'activi, hi surten els preus de no soci i de soci de cada tipus, la diferència i la quota anual de soci, i el botó **Demana-la**. Una persona de fora hi escriu el nom, els cognoms, el correu i la data de naixement, accepta la política de privacitat i rep al correu l'enllaç per pagar-la al preu de no soci. Quan l'ha pagada, et surt com a **Pagada** al llistat, com les dels socis. De moment, només majors d'edat [A validar: P-449].

## 9. Què no fa la plataforma
- No envia res a la federació: el fitxer el puges tu.
- No desa el fitxer de la federació ni cap dada de salut.
- No canvia el preu d'una llicència ja demanada si després canvia el preu del tipus.
