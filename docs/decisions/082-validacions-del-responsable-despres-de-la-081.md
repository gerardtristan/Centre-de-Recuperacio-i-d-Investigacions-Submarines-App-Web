# 082. Validacions del responsable després de la 081

- **Data:** 11/11/2026
- **Estat:** Acceptada (responsable del projecte, 11/11/2026)
- **Origen:** informe de l'aplicació de la [081](081-respostes-del-responsable-als-25-punts-de-t-m00-i-t-m01.md).

## Decisions

1. **P-73, menor sense document a la fitxa.** La secretaria pot marcar com a «comprovada» la data de naixement d'un menor després de veure'n el DNI a través del tutor (representant legal), **sense desar cap còpia ni cap document**. Només es registra **qui** ho ha comprovat i **quan**. **RN-M01-70 no canvia:** el document continua opcional per als menors i, si no n'hi ha, la fitxa continua sense.
2. **P-61, punt 5.** Els menors renoven **als 12 mesos de cada pagament**, com tothom ([070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md)). És la interpretació que ja estava implementada.
3. **Concrecions de la [079](079-respostes-del-responsable-al-grup-a-de-t-m00-i-t-m01.md), punts 2 a 14 de la llista de la 081: confirmades**, amb una excepció de redacció: la referència «A-NNNN» es descriu com a **«referència»**, no com a «referència anònima». Es confirmen, per tant:
   - A-11: invitació de 48 hores, només l'empremta, reenviament amb M2;
   - A-08: P5 amb C2 per buidar el document d'un menor;
   - A-17: «Pagaments per revisar» dins de «Quotes i impagats», amb P10;
   - A-09 i A-03: només es retira el pas a simpatitzant pendent;
   - A-02: sense etiqueta «Renovació emesa»;
   - els límits de la petició d'un enllaç de convidat (RN-M01-58) i que només es renoven els enllaços que ja existien;
   - l'avís per correu de l'entrada amb un compte d'emergència (CA-10.2);
   - la prioritat de cada plantilla de correu (V-07);
   - la referència «A-NNNN» a partir de l'identificador intern;
   - el pas a simpatitzant amb una quota pendent (es pot demanar; no s'accepta si el soci no és actiu) i la data de renovació només amb P10;
   - el recordatori de la data de naixement només com a avís en entrar;
   - P-28 tancada: les llicències es tramiten segons la Q-078 de la [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md).
4. **Recordatori de la data de naixement (RN-M01-55).** El correu queda per a quan hi hagi una **campanya de dades**; mentrestant, només l'avís en entrar.
5. **Abans del push:** si els commits posteriors a `09fc2f4` han tocat codi, es repeteix la verificació completa sobre el HEAD.
6. **Push** de `night/2026-11-11` a `feature/night-2026-11-11`, sense force, per passar el CI, amb l'escaneig de secrets de tots els commits nous ([078](078-escaneig-de-secrets-de-tota-la-pr-limit-de-30-commits.md)). No es fusiona la PR #7.

## Per què «referència» i no «anònima»

La referència surt de l'identificador intern: qui té accés a la base de dades la pot relacionar amb altres files del mateix registre. No fa la persona anònima; només en treu les dades personals. Dir-ne «anònima» seria inexacte.

## Conseqüències

- **Codi:** la comprovació de la data ja no exigeix document a la fitxa, i el registre de la comprovació no porta cap detall més que qui i quan. Els textos de les pantalles, la guia del tresorer, els comentaris del codi i l'etiqueta del camp diuen «referència». La migració `core/0026` només canvia l'etiqueta del camp: la columna i les dades no canvien. Els noms del codi (`anonymous_ref`) i les migracions anteriors no es toquen.
- **Text aprovat:** on el pla, la spec o una decisió anterior diuen «referència anònima», val «referència» (precisió d'aquesta decisió; no s'edita el text antic).
- **Pendents:** P-73, P-28 i les preguntes de les concrecions passen a «Resolts»; P-61 només queda oberta pels punts 1 a 4 i el recàrrec (T-M01-49).
