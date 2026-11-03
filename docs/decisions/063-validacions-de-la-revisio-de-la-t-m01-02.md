# 063 — Validacions de la revisió de la T-M01-02: preus de les quotes, text de conservació, contrasenya abans d'esborrar el compte i preus fora de la portada

- **Data:** 03/11/2026
- **Estat:** Acceptada. Validacions del responsable del projecte en la revisió dels wireframes de la T-M01-02. Afegeix una [addenda al M01](../planning.md#M01-addenda-063) (RN-M01-57, CA-M01-46) i una [peça de la 00](../planning.md#ajustos-060-peces-00) (T-M00-05). No tanca Q-14.

## Context
La revisió de les pantalles de la T-M01-02 va trobar quatre punts:
- els preus de les quotes sortien com a «A validar» tot i que el pla ja els tenia com a valors inicials (VC-01);
- el text de conservació d'«Esborra el meu compte» duia l'etiqueta de Q-14;
- el pla no deia si calia tornar a demanar la contrasenya abans d'enviar la sol·licitud d'esborrat;
- el responsable del projecte volia que els preus estiguessin menys exposats a la web pública.

## Decisió
1. **Preus de les quotes.** Simpatitzant, 3500 cèntims (35 €), i ple dret, 9000 cèntims (90 €), són valors validats. Continuen sent editables pel tresorer o l'administrador, amb motiu i data d'entrada en vigor (VC-01, CA-M01-35). Continuen pendents què inclou cada tipus (S-M01-11) i la quota sencera a mig any (RN-M01-16).
2. **Text de conservació.** «Les quotes, els rebuts i els pagaments no s'esborren mai. Les teves dades que hi surten quedaran bloquejades i s'anonimitzaran passat el termini legal» queda validat com a principi (desenvolupa la [058](058-respostes-fecdas-gestoria-i-cursos.md), punt 7, i RN-M01-51). **No fixa cap termini**: depèn de la gestoria (Q-14, S-M01-15), i la pantalla no en mostra cap.
3. **Contrasenya abans d'esborrar el compte.** Per enviar la sol·licitud d'esborrat, el soci torna a escriure **sempre** la contrasenya, i el codi TOTP si el compte en té (RN-M01-57). Es fa servir el servei de reautenticació de la 00 (T-M00-05), sense la finestra de 15 minuts del 05a.
4. **Preus només al formulari d'alta.** La portada pública no mostra els preus de les quotes: surten al pas «Tipus de soci» del formulari d'alta. Per començar l'alta continua sense caldre compte (P-M01-A). És una tria de presentació, no un control de seguretat: els preus són informació pública.

## Conseqüències
- Q-14 continua oberta a S-M01-15, a RN-M01-51 i a `preguntes-externes.md`.
- Addenda del M01: RN-M01-57, CA-M01-46 i pas 3 de P-M01-F. La prova és a la T-M01-22, que depèn de la T-M00-05.
- Una contrasenya incorrecta compta per al bloqueig per intents de V-01.
- La T-M00-05 també serveix el 05a (RN-M05a-12, T-M05a-09), i el 01 no depèn de cap mòdul posterior.

## Fonts
- Revisió de la T-M01-02 pel responsable del projecte, 03/11/2026
- [058](058-respostes-fecdas-gestoria-i-cursos.md) (punt 7); RN-M01-51, VC-01, P-M01-A i RN-M05a-12 del [pla](../planning.md)
