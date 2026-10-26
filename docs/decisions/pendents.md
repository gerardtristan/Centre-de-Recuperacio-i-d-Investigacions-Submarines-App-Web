# Pendents de validar per la junta

Contradiccions entre documents i decisions que l'equip no pot resoldre sol. **No s'implementa la part afectada fins que la junta respongui.** Quan es resolgui un punt, es crea o s'actualitza la decisió numerada corresponent i aquí es marca com a resolt, amb data i qui ho ha decidit.

Llegenda: **R** = l'equip ja hi ha fet una recomanació; **—** = només es constata la contradicció.

| ID | Tema | Què diu cada document | Recomanació de l'equip | Afecta | Estat |
|---|---|---|---|---|---|
| P-01 | Abast dels cobraments | Context v3 §6-7 i document incremental §2.3, §4.5: Cluber continua per als cobraments; substituir-los és fora d'abast. Funcionalitats §1, §2, §7: «Cluber es deixa de fer servir», cobraments dins l'app. Encàrrec del 26/10/2026: Stripe amb SEPA, targeta i Bizum. | — | 01, 04, 05; decisió [007](007-pagaments-stripe.md) | Obert |
| P-02 | Facturació | Context v3 §6: «Could; cal confirmar IVA i programa». Funcionalitats §7: facturació via servei homologat Verifactu dins la tresoreria (imprescindible). | — (depèn de la gestoria: IVA i Verifactu) | 04 | Obert |
| P-03 | Numeració dels mòduls | CLAUDE.md i metodologia: 0-8 (2 = cursos i sortides; 4 = tresoreria; 5 = pagaments). Funcionalitats: 0-11 (2 = cursos, 3 = sortides, 5 = tresoreria amb pagaments, 8 = Dept. d'Història, 10 = idees, 11 = botiga). | Fer servir la numeració de CLAUDE.md per a `specs/` i afegir-hi una taula d'equivalències | `specs/` | Obert |
| P-04 | Rols | Context v3 §7: 6 rols. Funcionalitats §2: 8 rols (afegeix instructor i Departament d'Història). | — | 00 (permisos) | Obert |
| P-05 | Abast del doble factor | Context v3 §9: administradors. Funcionalitats §2: administradors i dos comptes d'emergència. Checklist C2 (anterior): administradors i tresorer. | **R:** obligatori per a administrador, tresorer i secretaria (qualsevol rol amb accés a diners o dades de socis) i comptes d'emergència; codis de recuperació fora de línia. Ja aplicat a CLAUDE.md i C2, pendent de confirmació. | 00; decisió [003](003-autenticacio-doble-factor.md) | Pendent de validació |
| P-06 | Pressupost | Context v3 §9, incremental §4.2 i funcionalitats §2: 100-120 €/any de servidor i còpies. L'arquitectura del 27/10/2026 estima més quan s'hi sumen el correu de pagament, el VPS de proves i el Storage Box. | Aprovar l'escenari recomanat o el mínim de [l'arquitectura, §3](../arquitectura-integracions.md#3-cost-mensual-estimat) | Totes les integracions | Obert |
| P-07 | Data de validesa del certificat mèdic | Funcionalitats §2: «com a molt, es guarda la data fins a la qual és vàlid el certificat mèdic» [A validar]. CLAUDE.md: cap dada de salut. | — (cal criteri del responsable de protecció de dades) | 01, 02 | Obert |
| P-08 | Comissions de les quotes | Funcionalitats §7: la comissió és despesa «de la mateixa activitat». Funcionalitats §3: les quotes no entren al marge de cap activitat. | **R:** imputar-les al departament «General / Quotes de socis»; tota partida té departament. | 04, 05; decisió [013](013-imputacio-comissions.md) | Pendent de validació |
| P-09 | Mètodes de pagament de les quotes | Encàrrec del 26/10/2026: «Domiciliació només per a quotes; targeta, Bizum i transferència per a inscripcions i llicències». Funcionalitats §3 i §9.5: les quotes també es poden pagar amb targeta o Bizum («qui no té domiciliació rep un enllaç»). | — (cal aclarir si una quota es pot pagar també amb targeta, Bizum o transferència) | 01, 05 | Obert |
| P-10 | Sistema de disseny | No hi ha `docs/design-system.md` ni cap decisió registrada. | Crear-lo abans d'especificar la web pública i l'àrea de socis | 07; decisió [009](009-sistema-de-disseny.md) | Obert |
| P-11 | Constitució | Metodologia §2-4: fitxer `constitution.md`. CLAUDE.md fa aquesta funció. | Mantenir CLAUDE.md com a constitució i no duplicar | Documentació | Obert |
| P-12 | Registre manual de cobraments | Encàrrec del 26/10/2026: efectiu o presencial amb motiu i registre d'activitat. Funcionalitats §7 només esmenta «Comptes: banc i caixa». | — (qui pot registrar-lo, i si cal rebut o justificant) | 04, 05 | Obert |
| P-13 | Entrevistes | `docs/context/entrevistes.docx` pot contenir dades personals; fora de Git. | Anonimitzar-lo abans de pujar-lo al repositori | Documentació | Obert |
| P-14 | Versions del document incremental | Es tracta `docs/entregues/document-incremental.pdf` com a versió vigent. | Demanar confirmació abans de moure cap versió a `docs/arxiu/` | Documentació | Obert |

## Resolts
(Cap encara.)
