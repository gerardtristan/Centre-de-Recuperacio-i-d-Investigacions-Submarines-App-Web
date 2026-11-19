# 098. Una PR `risc:alt` només es fusiona amb un sí escrit del propietari que n'esmenti el número

- **Data:** 18/11/2026
- **Estat:** Modificada temporalment per la [100](100-risc-alt-es-fusionen-soles-fins-al-final-de-la-prova.md) fins al 27/11/2026: les `risc:alt` es fusionen soles amb condicions, i el sí escrit amb el número només el necessiten les excepcions de la 100 (punt 2). Acceptada (propietari, 18/11/2026; instrucció escrita). El text del propietari: «Una PR risc:alt només es fusiona amb un sí escrit meu que esmenti el número de la PR. Una resposta a una pregunta o una especificació que jo dicto no compta com a sí per fusionar: obre la PR i espera. La #229 l'accepto tal com està.» I, el mateix dia: «Accepto la #226 tal com està. Sí: apunta la regla com a decisió 098 i afegeix-la a la D4 del CLAUDE.md».
- **Canvia:** el punt 1 de la [094](094-fusio-de-les-risc-alt-i-tres-carrils.md) (Claude fusiona les `risc:alt` sense esperar el propietari) i l'extensió d'aquell punt a la sessió de DISSENY. La resta de la 094 continua vigent: les fusions `risc:baix` i `risc:mitja`, les tres preguntes prèvies (punt 2), els tres carrils (punt 3) i el resum diari (punt 4).

## Context

La 094 (16/11/2026) deixava que Claude fusionés una `risc:alt` amb el CI verd, la revisió automàtica neta i les normes complertes. Amb diverses PR de diners, pagaments i permisos fusionades en poc temps, el propietari vol tornar a decidir cada fusió d'aquest tipus.

## Decisió

1. **Una PR `risc:alt` només es fusiona amb un sí escrit del propietari que esmenti el número de la PR** (per exemple, «fusiona la #241»). Abans, ha de tenir el CI verd, la branca al dia amb `master` i la revisió automàtica sense res pendent, com diu la 094.
2. **No compten com a sí per fusionar:** la resposta a una pregunta (també les del tauler i les de [`pendents.md`](pendents.md)), una especificació o una regla que dicti el propietari, ni l'aprovació d'un commit del pla dins la PR. En aquests casos, Claude obre la PR i espera.
3. **Val per a les dues sessions**, PILOT i DISSENY.
4. **Les PR `risc:baix` i `risc:mitja` es continuen fusionant sense esperar el propietari**, amb les condicions de la 094.
5. **Cap guió de fusió automàtica per a una `risc:alt`** no es posa en marxa abans del sí escrit que n'esmenta el número. Un guió que fusiona diverses PR en cadena només hi inclou les `risc:alt` que ja tenen el seu sí.

## Conseqüències

- **PR fusionades abans d'aquesta norma**, acceptades pel propietari tal com estan: la [#229](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/229) i la [#226](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/226) (totes dues, 18/11/2026).
- Una `risc:alt` llesta queda oberta fins al sí; Claude la presenta al propietari amb el CI, la revisió i els límits coneguts.
- Al resum diari, la línia de cada `risc:alt` fusionada diu quin sí del propietari l'ha autoritzat.
- En revocar-la, torna el punt 1 de la 094.
