# Guia del tresorer: quotes i socis a la plataforma del C.R.I.S.

**Per a qui és:** la persona que fa la tresoreria del club. **Estat:** esborrany, pendent de revisió (T-M01-29). Els cobraments reals encara no estan connectats: arribaran amb la part de pagaments (05b). Els textos i alguns valors són provisionals; quan ho són, ho diu cada apartat.

## 1. Entrar a l'administració
- L'administració té una adreça pròpia, diferent de la dels socis. Te la dona l'administrador de la plataforma.
- Entres amb el teu **nom d'usuari** (no amb el correu), la contrasenya i el **codi de sis xifres** de l'aplicació d'autenticació del mòbil. Sense codi no s'hi entra.
- Si perds el mòbil o oblides la contrasenya, **no hi ha cap enllaç de recuperació per correu**. Fes servir un dels codis de recuperació que vas guardar en donar d'alta el codi del mòbil, o demana a un altre administrador que et restableixi l'accés.
- A l'esquerra (o darrere del botó «Menú», al mòbil) hi ha només les seccions que pots fer servir. A sota hi ha el teu usuari i «Surt».

## 2. Quotes i impagats
**Quotes i impagats** mostra l'estat de la quota de cada soci.
- **«Vàlid fins al»:** és la data fins a la qual el soci està al corrent. Es calcula sempre de la mateixa manera per al llistat, la fitxa, el carnet i la generació de quotes: 12 mesos després del pagament confirmat, l'exempció d'un menor o la data importada de Cluber.
- **Pendent** vol dir que el venciment ja ha passat sense pagar, o que el rebut ha estat retornat. Una renovació emesa que encara no ha vençut **no** surt com a pendent: el soci continua vàlid.
- **Impagat** és una marca que poses tu, a mà, amb un motiu. La plataforma no la posa mai sola (decisió 040). Amb **Marca impagat…** escrius el motiu i la data efectiva; amb **Desmarca impagat…** la treus, també amb motiu. Tot queda a l'historial del soci i al registre d'activitat.

## 3. Pagaments per revisar
- A **Quotes i impagats**, l'apartat **Pagaments per revisar** recull els pagaments que necessiten una persona. Per exemple, la quota pagada per algú que ja estava de baixa: la plataforma no el torna a donar d'alta sola.
- Revisa cada cas i prem **Marca com a revisat…** amb una nota. La nota queda al registre.
- Quan arriba un pagament d'aquest tipus, o un rebut retornat, la plataforma avisa per correu els comptes que poden gestionar les quotes.

### Eximir o anul·lar una quota
A la fitxa d'un soci, la secció **Quotes** mostra totes les seves quotes. Al costat d'una de pendent hi tens dues accions:
- **Eximeix…:** la quota no es cobra i el període compta com a resolt. El soci queda actiu (un de pendent passa a actiu) i el carnet és vàlid fins al mateix dia de l'any següent. Fes-ho servir quan la junta acorda que algú no pagui un període.
- **Anul·la…:** la quota deixa de constar com a deute, però no dona cap dret. Fes-ho servir per a una quota generada per error o un deute que es perdona.

A totes dues has d'escriure **el motiu** i tornar a posar la contrasenya i el codi de l'aplicació. Queda al registre amb el teu compte. No pots eximir ni anul·lar una quota teva.

Límits: una quota pagada no es pot eximir (seria una devolució); una de retornada es resoldrà quan hi hagi el mòdul de cobraments; un soci marcat com a impagat continua impagat fins que el desmarquis.

## 4. Llistat de socis (dades mínimes)
El teu llistat mostra només el que cal per cobrar: número, nom, tipus, estat i quota. No hi veus el document, l'adreça ni la data de naixement; en lloc de la data, la fitxa et mostra la franja d'edat.

## 5. Sol·licituds de socis
Pots consultar i resoldre les altes i els canvis de tipus, igual que la secretaria (vegeu la guia de la secretaria, apartats 2 i 5). Ningú no pot resoldre una sol·licitud seva.

**Pas a simpatitzant: atenció.** Mentre no estigui feta la part que aplica el canvi en renovar (T-M01-43), la renovació d'un soci amb el pas acceptat es generaria a preu de ple dret. Per això aquesta funció no entrarà en producció sense la T-M01-43.

## 6. Dades bloquejades
Quan una persona demana l'esborrat de les seves dades, les quotes i els pagaments no s'esborren. El nom i el document que hi surten queden **bloquejats i xifrats** durant 6 anys des del final de l'any de l'últim cobrament; després es destrueixen (decisió 085).
- **Dades bloquejades** mostra només la referència («A-0001») i la data del bloqueig.
- Per veure la identitat i els registres econòmics, has d'escriure **el motiu** (per exemple, una inspecció o un requeriment de la gestoria). Cada consulta queda al registre amb el teu compte i el motiu.
- Fes servir aquestes dades només per a l'obligació legal que has escrit; no les copiïs fora de la plataforma.

## 7. Què encara no fa la plataforma
- **Cobrar:** el pagament en línia, les domiciliacions, les remeses i la conciliació són de les parts 05a i 05b.
- **Pagament en tres terminis:** tasca T-M01-49, pendent dels punts oberts de la P-61.

**Renovacions i recordatoris: no cal fer res.** Cada dia, a primera hora, la plataforma genera la quota de renovació dels socis que vencen aviat (el dia del primer recordatori) i envia els recordatoris que toquen, un sol cop per quota i dia. Els recordatoris després del venciment només s'envien si la quota no s'ha pagat. Els dies dels recordatoris estan confirmats (decisió 085). Falta decidir des de quina data compten els 12 mesos d'un soci importat de Cluber.

## 8. Si alguna cosa no funciona
- Si una pàgina diu **«No s'ha trobat la pàgina»**, pot ser que l'adreça sigui incorrecta o que no tinguis permís per a aquella secció: les dues coses es veuen igual, a propòsit.
- Si diu **«La sessió ha caducat»**, torna a entrar. La sessió de l'administració dura com a màxim 8 hores.
