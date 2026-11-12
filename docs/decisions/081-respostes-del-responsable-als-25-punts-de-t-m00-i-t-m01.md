# 081. Respostes del responsable als 25 punts de la depuració de T-M00 i T-M01

- **Data:** 11/11/2026
- **Estat:** Acceptada (responsable del projecte, 11/11/2026)
- **Origen:** llista de 25 punts de la depuració dels pendents de T-M00 i T-M01 (11/11/2026).

## Abast

Aquesta decisió recull les respostes del responsable als **punts 1 i 15 a 25**. Els **punts 2 a 14**
eren concrecions ja implementades: el missatge del responsable **no les converteix en aprovacions**.
Per a aquests punts només s'aplica el següent:

- es respecten les decisions ja aprovades i implementades;
- es corregeixen els falsos bloquejos segons la [079](079-respostes-del-responsable-al-grup-a-de-t-m00-i-t-m01.md), que diu de les seves concrecions «No bloquegen cap tasca»: la nota de la [080](080-revisio-visual-al-final-de-la-fase-1.md) les havia presentades com a motiu per no tancar la T-M01-15b, la T-M01-26 i, en part, la T-M01-14, la T-M00-02 i la T-M00-06;
- cap concreció de la 079 no es torna a tractar com a bloqueig, i no s'hi introdueix cap alternativa nova.

## Decisions

| Punt | Tema | Decisió | Regla i tasca |
|---|---|---|---|
| 1 | Hook de fi de torn | **Opció B, tres capes.** (1) Hook de fi de torn amb un límit de 90 s: ruff, conjunt mínim d'e2e i les e2e del mapa quan hi caben. (2) Verificació completa explícita abans del commit quan el hook la deixa pendent (fitxers compartits, desconeguts o una selecció massa llarga). (3) CI sense reduir-ne la cobertura. Un temps esgotat és «no conclusiu», mai verd; cap bucle de bloqueig sense amagar errors; resultats lligats al contingut exacte verificat; una sola execució alhora, matant només els processos propis; cap procés en segon pla. **No s'instal·la ara** el `pre-commit` opcional | CA-M00-07f (nou text), T-M00-07 |
| 15 | Còpia del carnet sense connexió | **30 dies.** La còpia no allarga la vigència real del carnet (mai després del «vàlid fins al»), mostra que és sense connexió i quan es va comprovar, s'actualitza en recuperar la connexió i no es presenta com una comprovació en temps real. La prova en un mòbil real **continua pendent** | RN-M01-101, T-M01-21 |
| 16 | Data de naixement declarada que comporta l'exempció | **Opció A:** s'accepta la data declarada. No hi ha confirmació prèvia de la secretaria com a condició de l'exempció. La secretaria revisa les dades i, en el cas d'un menor exempt, comprova l'edat demanant el DNI del menor al seu representant legal. Es distingeix la declaració de la comprovació posterior. **No autoritza** guardar una còpia o fotografia del DNI ni cap sistema de pujada de documents | RN-M01-99, T-M01-35 i T-M01-18; excepció: P-73 |
| 17 | Pas a simpatitzant acceptat quan es valida una baixa | **Opció A:** es cancel·la en validar la baixa, amb el motiu «baixa», conservant-ne l'historial, i el procés posterior no el torna a aplicar | RN-M01-98, T-M01-42 i T-M01-43 |
| 18 | TOTP i codis de recuperació en l'esborrat RGPD | **S'esborren** el secret TOTP i els codis de recuperació; es comprova que cap mecanisme d'accés del compte no continua vigent. No substitueix les consultes de la gestoria i l'assessor | RN-M01-100, T-M01-22 |
| 19 | Files de Cluber sense document | **Opció A:** no s'importen automàticament; queden pendents perquè la secretaria revisi el cas i faci l'alta a mà. No es descarten en silenci ni s'inventen documents. Es respecten les excepcions dels menors | T-M01-25 |
| 20 | President i baixes sense accedir a les fitxes | **No.** Es mantenen P7 amb edició i P4; cap pantalla de cerca mínima ni cap circuit nou | T-M01-17 |
| 21 | Destinatari de l'avís del 80 % del límit de correu | **Només l'administrador**, a l'adreça configurada expressament (`EMAIL_ALERT_TO`). Informàtica no és destinatària automàtica. Cap adreça inventada. Sense adreça, el pendent de configuració és visible i l'avís no es dona per operatiu | Q-26, T-M00-06 |
| 22 | Pantalla «La sessió ha caducat» | **Sí**, per caducitat per inactivitat. El responsable delega el temps (vegeu més avall) | RN-M01-102, T-M01-45 |
| 23 | Formats de la importació de Cluber | **CSV i XLSX**, amb les mateixes regles, una dependència declarada i reproduïble, cap fórmula ni contingut actiu, control de format, mida i errors, missatges clars i un criteri documentat per triar el full | P-63, RN-M01-103, T-M01-50 (nova) |
| 24 | Pèrdua del mòbil amb doble factor | **Restabliment presencial per la secretaria** amb comprovació d'identitat. No s'afegeixen codis de recuperació als comptes personals ni es treuen els d'altres comptes. Permís corresponent, comprovació presencial, registre de qui i quan, invalidació del factor anterior, possibilitat de configurar-ne un de nou, avís al titular i cap drecera per correu. Condició de producció fins que estigui fet i provat | P-52, RN-M01-104, T-M01-51 (nova) |
| 25 | Terminis, punts 1 a 4 de la P-61 | **Ajornats** fins a l'inici de la T-M01-49. No s'aprova cap comportament concret; el recàrrec continua pendent de la junta. No bloquegen altres tasques, i els terminis no s'activen sense resoldre'ls | P-61, T-M01-49 |

## Criteris de l'equip on el responsable els delegava o la decisió no els fixava

- **Temps d'inactivitat (punt 22).** Es reutilitzen els de V-01, que ja s'aplicaven al servidor: **30 minuts a l'administració, amb un màxim de 8 hores**, i **14 dies a l'àrea de socis**. Justificació: l'administració dona accés a les dades de tots els socis i als diners, i un temps curt hi és proporcionat; l'àrea de socis només mostra les dades pròpies i el carnet (que s'ha de poder ensenyar a la porta), i les operacions sensibles ja demanen tornar a identificar-se. Reutilitzar-los evita dos temporitzadors contradictoris. No hi ha cap estàndard universal: són valors proporcionats al tipus d'aplicació. **Activitat** és qualsevol petició a una pàgina protegida que fa la persona; no ho són les precàrregues del navegador ni les peticions marcades com a automàtiques (`X-CRIS-Automatica`). La galeta auxiliar `cris_sessio_previa` només indica el motiu de la pantalla (valor fix, sense dades personals ni capacitat d'autenticació).
- **Permís del restabliment presencial (punt 24).** M2 (`core.people.manage`), que a la matriu de la 059 ja és «crear i editar perfils d'altres persones i els seus comptes personals» (secretaria i administrador). No s'ha creat cap permís nou ni s'ha canviat la matriu.
- **Full de l'XLSX (punt 23).** Es llegeix el full que té totes les columnes obligatòries de Cluber a la primera fila; si no n'hi ha cap, falta una columna; si n'hi ha més d'un, el fitxer es rebutja. Les fórmules no s'executen i fan rebutjar el fitxer; macros, enllaços externs i ActiveX també.
- **Concurrència de la verificació (punt 1).** Si ja hi ha una verificació en marxa, la nova no comença i ho diu; no s'atura mai el procés d'un altre (la proposta deia «s'atura l'anterior»; s'ha triat l'opció més segura per no afectar altres sessions).

## Contradicció identificada

- **Punt 16 i RN-M01-70.** La comprovació de l'edat d'un menor exempt es fa «demanant el DNI del menor», però el document és opcional per als menors (RN-M01-70) i molts menors de 14 anys no en tenen. Només aquesta excepció queda pendent: **P-73** a [pendents.md](pendents.md). Per a aquests menors la data declarada s'aplica igual i la fitxa ho diu.

## Conseqüències

- Implementació a la branca `night/2026-11-11` (vegeu el pla, files de cada tasca, i el [diari](../diari-de-construccio/README.md)).
- Pendents moguts o actualitzats a [pendents.md](pendents.md): P-50, P-52, P-63 i Q-26 a «Resolts»; P-66 a P-70 i P-72 surten d'«Oberts» (ja eren a «Resolts»); estat exacte al principi de P-29, P-54, P-61, P-62, P-65 i P-71; P-73 nova.
- No canvia res de les concrecions de la 079 (punts 2 a 14), que segueixen sense cap confirmació nova.
