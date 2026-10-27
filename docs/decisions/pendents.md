# Pendents de validar per la junta

Contradiccions entre documents i decisions que l'equip no pot resoldre sol. **No s'implementa la part afectada fins que la junta respongui.** Quan es resol un punt, es crea o s'actualitza la decisió numerada corresponent i el punt passa a «Resolts», amb la data i l'origen.

Llegenda: **R** = l'equip ja hi ha fet una recomanació; **—** = només es constata la contradicció.

## Oberts

| ID | Tema | Què diu cada document | Recomanació de l'equip | Afecta | Estat |
|---|---|---|---|---|---|
| P-02 | Facturació | Context v3 §6: «Could; cal confirmar IVA i programa». Funcionalitats §7: facturació via servei homologat Verifactu dins la tresoreria (imprescindible). | — (depèn de la gestoria: IVA i Verifactu) | 04 | Obert |
| P-03 | Numeració dels mòduls | CLAUDE.md i metodologia: 0-8 (2 = cursos i sortides; 4 = tresoreria; 5 = pagaments). Funcionalitats: 0-11 (2 = cursos, 3 = sortides, 5 = tresoreria amb pagaments, 8 = Dept. d'Història, 10 = idees, 11 = botiga). | Fer servir la numeració de CLAUDE.md per a `specs/` i afegir-hi una taula d'equivalències | `specs/` | Obert |
| P-04 | Rols | Context v3 §7: 6 rols. Funcionalitats §2: 8 rols (afegeix instructor i Departament d'Història). | — | 00 (permisos) | Obert |
| P-07 | Data de validesa del certificat mèdic | Funcionalitats §2: «com a molt, es guarda la data fins a la qual és vàlid el certificat mèdic» [A validar]. CLAUDE.md: cap dada de salut. | — (cal criteri del responsable de protecció de dades) | 01, 02 | Obert |
| P-10 | Sistema de disseny | No hi ha `docs/design-system.md` ni cap decisió registrada. | Crear-lo abans d'especificar la web pública i l'àrea de socis | 07; decisió [009](009-sistema-de-disseny.md) | Obert |
| P-11 | Constitució | Metodologia §2-4: fitxer `constitution.md`. CLAUDE.md fa aquesta funció. | Mantenir CLAUDE.md com a constitució i no duplicar | Documentació | Obert |
| P-12 | Registre manual de cobraments | Encàrrec del 26/10/2026: efectiu o presencial, amb motiu i registre d'activitat. Funcionalitats §7 només esmenta «Comptes: banc i caixa». | — (qui el pot fer i quin justificant cal) | 04, 05 | Obert |
| P-13 | Entrevistes | `docs/context/entrevistes.docx` pot contenir dades personals; és fora de Git. | Anonimitzar-lo abans de pujar-lo al repositori | Documentació | Obert |
| P-14 | Versions del document incremental | Es tracta `docs/entregues/document-incremental.pdf` com a versió vigent. | Demanar confirmació abans de moure cap versió a `docs/arxiu/` | Documentació | Obert |
| P-15 | Domini del club | Decisió del 27/10/2026 (015): «cris.es». Context v3 §4, document incremental §1.2 i pantalles de funcionalitats: «cris.barcelona». | — (quin és el domini actiu de la web i del correu, i qui el gestiona) | DNS, correu, 015 | Obert |
| P-16 | Un compte amb diversos rols o dos comptes | Funcionalitats §2: «una mateixa persona pot tenir més d'un rol (per exemple, soci i tresorer)». Decisió 015: cada administrador té un compte de soci i un d'administrador. | — (aclarir si «administrador» inclou tots els rols de gestió: tresorer, secretaria, responsables, instructor, Dept. d'Història) | 00 | Obert |
| P-17 | Quins rols tenen doble factor obligatori | Decisió 015: «tots els rols amb accés a diners o dades de socis». Segons la matriu de funcionalitats §2, l'instructor veu els seus alumnes, el responsable de material veu participants i el Dept. d'Història veu assistents; tots tenen accés a dades de socis. | **R:** doble factor obligatori per a tots els rols excepte «soci» [A validar] | 00 | Obert |
| P-18 | Recuperació i verificació de comptes d'administrador | Checklist C4: restabliment amb enllaç per correu. C5: els comptes nous queden pendents fins a confirmar el correu. Decisió 015: els comptes d'administrador no recuperen la contrasenya per correu i el seu correu no és únic. | Afegir a C4 i C5 que s'apliquen als comptes de soci i definir la regla dels comptes d'administrador | Checklist, 00 | Obert (proposta pendent d'aprovació) |
| P-19 | Canvis al context per P-01, pressupost i calendari | Context v3 (§1, §6, §7, §9, §11) i document incremental (§2.2, §2.3, §4.2-4.6) diuen que Cluber continua per als cobraments, que el cost és de 100-120 €/any i que hi ha un pla de 15 setmanes. Les decisions 014 i 016 i l'encàrrec del 27/10/2026 («treballem per mòduls i passos, sense calendari») hi contradiuen. | Canvis proposats al resum del 27/10/2026; no aplicats | `docs/context-projecte.md`, propera versió del document incremental | Pendent d'aprovació |
| P-20 | Moment de donar de baixa Cluber | Funcionalitats §9.13: campanya de quotes en paral·lel sense cobrar a l'app i baixa de Cluber «quan li venç el contracte». Decisió 014: Cluber es deixa quan la plataforma està activa amb pagaments (mòdul 05 acabat i provat). | — (es manté la campanya en paral·lel? Quan venç el contracte de Cluber?) | 01, 05 | Obert |

## Resolts

| ID | Tema | Resolució | Data i origen | Decisió |
|---|---|---|---|---|
| P-01 | Abast dels cobraments | Migració única de Cluber; Cluber es deixa quan la plataforma estigui activa amb domiciliació, targeta i Bizum; entrada en producció amb el mòdul 05 acabat i provat. Els canvis al context estan pendents (P-19). | 27/10/2026, equip del projecte | [014](014-migracio-cluber-i-entrada-en-produccio.md) |
| P-05 | Abast del doble factor | Obligatori per a tots els rols amb accés a diners o dades de socis i per als comptes d'emergència; dos comptes per a cada administrador; sense recuperació per correu per als comptes d'administrador. Detalls a P-15 a P-18. | 27/10/2026, equip del projecte | [015](015-doble-factor-i-comptes-administrador.md) |
| P-06 | Pressupost | La junta coneix el cost. Es comença amb la producció mínima (≈160 €/any sense IVA més comissions), en comparació amb Cluber (des de 599 €/any). | 27/10/2026, equip del projecte | [016](016-pressupost-produccio-minima.md) |
| P-08 | Comissions de les quotes | Centre de cost «General / Quotes de socis»; tot ingrés i despesa té departament. | 27/10/2026, equip del projecte | [013](013-imputacio-comissions.md) |
| P-09 | Mètodes de pagament de les quotes | Quotes: domiciliació (per defecte), targeta, Bizum i transferència. Inscripcions i llicències: targeta, Bizum i transferència. Domiciliació només per a pagaments recurrents. | 27/10/2026, equip del projecte | [017](017-pagaments-metodes-i-domiciliacions.md) |
