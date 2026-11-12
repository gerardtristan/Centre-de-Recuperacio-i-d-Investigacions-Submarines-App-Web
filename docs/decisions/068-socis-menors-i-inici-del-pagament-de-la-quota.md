# 068 — Socis menors i inici del pagament de la quota

- **Data:** 06/11/2026
- **Estat:** Acceptada pel responsable del projecte el 06/11/2026, consultada amb el gestor. Resol en part la [P-33](pendents.md): només els punts d'aquesta decisió.

## Context
Fins ara la plataforma només admetia socis majors d'edat mentre la P-33 fos oberta: RN-M01-54 bloquejava l'alta d'un menor, L-M01-10 demanava confirmar la majoria d'edat i el supòsit de S-M01-13 era «només majors d'edat». La T-M01-13 ho va construir amb una casella obligatòria «Confirmo que soc major d'edat». El full d'inscripció en paper del club (`Inscripcio socis-cat (2025).pdf`) ja preveu la signatura dels pares o tutors per als menors.

## Decisió
1. **Tots els menors poden ser socis** amb l'autorització del pare, la mare o el tutor legal.
2. **Menors de 14 anys:** només poden ser simpatitzants i no tenen quota.
3. **A partir dels 14 anys** es pot triar simpatitzant o ple dret.
4. **Inici del pagament:** la quota es paga a partir de l'**1 de gener següent** al dia en què la persona compleix 14 anys. No es cobra en el moment de l'aniversari ni es prorrateja aquell any. Dit d'una altra manera, el primer any de quota és l'any de naixement més 15.
   - Exemple: qui compleix 14 anys el 10/03/2027 no paga el 2027 i comença a pagar l'01/01/2028.
5. **Dues dates diferents:** l'edat que permet triar el tipus de soci (14 anys complerts el dia de la sol·licitud) no és la data a partir de la qual es paga (l'1 de gener següent). Qui ja ha complert 14 anys durant l'any pot triar ple dret, però aquell any no paga.
6. **Tipus de soci:** no es crea cap tipus nou. El simpatitzant menor de 14 anys té el tipus simpatitzant; que no pagui depèn de la data de naixement, no del tipus.
7. **Autorització del representant:** a l'alta d'un menor es demanen el nom, els cognoms i el document del pare, la mare o el tutor legal, i la seva autorització explícita. L'autorització és del representant, no del menor: es conserva qui autoritza, per a qui, el text i la versió acceptats i el canal. Sense l'autorització i aquestes dades, l'alta d'un menor no es pot enviar.

## Conseqüències
- **Regles del M01** ([pla](../planning.md)): RN-M01-54, L-M01-10 i el supòsit de S-M01-13 queden substituïts per aquesta decisió; RN-M01-49 i les mencions «només majors d'edat» del M01 hi remeten. El text anterior es conserva al pla, marcat com a substituït.
- **T-M01-13** (formulari i alta presencial): demana la data de naixement, calcula l'edat al servidor, demana les dades i l'autorització del representant per als menors, limita el tipus per sota dels 14 anys i explica quan comença el pagament. Desa la sol·licitud; no crea cap soci, número ni quota.
- **T-M01-14** (aprovar l'alta) i **T-M01-18** (generar quotes): no creen cap quota d'un any anterior al primer any de quota. Com passa a actiu un soci que no té quota (RN-M01-07 fa dependre «actiu» de la quota pagada) **no ho decideix aquesta decisió**: és la [P-57](pendents.md).
- **T-M01-33** i **T-M01-35:** el repartiment amb la T-M01-13 és al [pla](../planning.md#M01-addenda-058).
- **Continua obert a la P-33** (no ho resol aquesta decisió):
  - el protocol i la persona de referència per als menors (checklist H5);
  - el mandat SEPA d'un menor, que signa el titular del compte (RN-M05a-13);
  - els menors a les activitats (RN-M02-35, L-M02-08, S-M02-19);
  - qui té el compte personal d'un soci menor i com s'hi entra.
- **Textos legals:** el text de l'autorització del representant és un text legal versionat més (T-M01-08). Els textos de prova de `seed_demo_data` no serveixen per a producció (checklist H1, Q-16).

## Ampliació del 06/11/2026: model i regla uniforme (aprovats pel responsable)
- **`MemberRequest`** guarda la data de naixement i el nom, els cognoms, el tipus i el número de document del representant. Les dades del representant hi són totes o cap (restricció de la base de dades); el servidor les exigeix per a un menor. La data és buida només a les sol·licituds anteriors a la migració `members/0007`; per a les noves, la demanen el formulari i el servei. `Person.birth_date` continua sent de la T-M01-33.
- **`JoinAcceptance`** (nou): cada acceptació d'un text legal en una sol·licitud, amb la versió, qui l'accepta (sol·licitant o representant), el canal, la data i, si és presencial, el compte que la registra. «Per a qui» és el sol·licitant de la mateixa sol·licitud: el model no té cap clau cap a `Person`, perquè una acceptació no s'atribueixi a una persona existent per un document coincident. Només admet files noves (model i disparadors de `members/0008`).
- **Regla uniforme:** en enviar la sol·licitud no es crea cap `core.Consent`, ni per a persones noves ni per a existents. Abans, la T-M01-13 creava els consentiments a la persona; ara queden a la sol·licitud. En aprovar l'alta, la T-M01-14 tracta les acceptacions segons qui les ha fet, sense atribuir al menor les del representant.
- **Esborrat i conservació:** una fila de `JoinAcceptance` no porta dades personals pròpies; les dades són a la sol·licitud i a la persona, que la T-M01-22 exporta i anonimitza (028). Per això la immutabilitat no impedeix l'anonimització. Si algun dia cal **eliminar** sol·licituds senceres (no anonimitzar-les), els disparadors i les claus PROTECT ho impedeixen: caldria una decisió nova. El termini de conservació de les sol·licituds rebutjades o no aprovades no està fixat (Q-14).

## Ampliació del 09/11/2026: document d'identitat del menor (aprovada pel responsable)
- El document d'identitat del sol·licitant és **obligatori per als majors d'edat** (DNI o NIE amb la lletra) i **opcional per als menors**. Si un menor l'indica, es valida igual. El servidor ho decideix amb la data de naixement.
- El document del pare, la mare o el tutor legal continua sent obligatori per a tots els menors i no pot coincidir amb el del menor quan aquest l'ha indicat.
- No cal cap canvi de model: el document del sol·licitant es desa a `Person`, que ja admet el tipus i el número buits (junts) i només n'exigeix la unicitat quan n'hi ha. No s'inventa cap document ni cap valor fals.
- **Duplicats:** sense document no hi ha avís de document repetit ni es busca cap persona pel document; l'avís per correu o per nom i telèfon continua com sempre (V-03). Les sol·licituds de menors sense document **no es poden comparar amb persones existents pel document**: la T-M01-14 ha de decidir com detecta l'administració els duplicats en aprovar-les.

## Fonts
- Decisió del responsable del projecte, 06/11/2026, consultada amb el gestor.
- Full d'inscripció en paper del club, `Inscripcio socis-cat (2025).pdf` (fora del repositori).
- [pendents.md](pendents.md) (P-33); RN-M01-07, RN-M01-49, RN-M01-54, L-M01-10 i S-M01-13 del [pla](../planning.md).
