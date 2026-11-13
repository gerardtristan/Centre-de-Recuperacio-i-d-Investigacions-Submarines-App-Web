# 092. Carril extern amb un proveïdor i un banc ficticis mentre no responguin PaynoPain i el banc

- **Data:** 13/11/2026
- **Estat:** Proposta (instrucció escrita del propietari del 13/11/2026; PR `risc:alt`, pendent del seu sí)
- **Origen:** el carril extern del [pla d'acceleració](../plans/pla-acceleracio.md#llesques-3-a-7--completar-la-fase-1) esperava l'entorn de proves del proveïdor, i [P-44 i P-45](pendents.md) no tenen resposta.

## Decisió

1. **El carril extern ja no queda bloquejat per P-44 i P-45.** Mentre PaynoPain i el banc no responguin, les seves tasques es fan contra un proveïdor i un banc **ficticis** que es comporten de manera semblant als reals.
2. **Proveïdor fictici «tipus PaynoPain».** S'amplia el `FakeProvider` de la T-M05a-03 darrere del mateix adaptador ([043](043-proveidor-de-pagaments-dins-la-ue.md)), seguint el que ja se sap de Paylands ([integracio-paylands.md](../integracio-paylands.md)): pagament amb targeta i Bizum, targeta guardada, notificacions signades, reintents, devolucions i liquidacions. Allà on no se sap el format real, el tria l'equip i el marca **[A verificar: P-44/P-45]**. Com que el fals declara que admet guardar la targeta, les tasques «condicionals» (targeta guardada) es construeixen; si el real no ho admet, ho diu la seva capacitat i el codi ja ho ha de suportar.
3. **Banc fictici.** Fitxer de remesa SEPA amb l'esquema estàndard (pain.008), retornats amb pain.002 i codis R, i extracte en **Norma 43**. Els fitxers d'exemple són inventats i viuen amb les proves. Si el banc respon amb un altre format d'extracte, s'hi afegeix un lector, sense tocar la conciliació.
4. **Tot és fictici:** cap credencial real, cap dada real i cap connexió de xarxa sortint. Les claus de signatura fan servir el valor de proves del projecte.
5. **A producció queda apagat, i l'aplicació no arrenca si s'hi activa.** No n'hi ha prou amb l'error que dona avui el `FakeProvider` en crear-lo: cal una comprovació en arrencar que falli si, amb la configuració de producció o amb l'entorn real del proveïdor, el proveïdor o el banc configurat és el fictici. És la primera tasca del carril, amb la seva prova.
6. **Quan arribin les respostes reals, només canvia l'adaptador concret.** Ni els models, ni els serveis, ni les vistes depenen del fictici; les proves de contracte es tornen a passar contra el real.
7. **Continuen bloquejades** les tasques que no tenen sentit sense el proveïdor o el banc reals: la implementació del proveïdor real en mode de proves (T-M05a-05), activar el mode real, la certificació amb el proveïdor si se'n demana, i les portes del nivell 1 i del nivell 2 ([025](025-dos-nivells-de-produccio.md), [042](042-proveidors-substituits-pel-requisit-ue.md)).

## Conseqüències

- Les tasques T-M05a-12, T-M05a-23, T-M05a-26, T-M05b-15, T-M05b-24 i T-M05b-26 es poden començar quan les seves dependències internes estiguin fetes.
- Les llesques 3, 5 i 6 ja no esperen el format del banc ni el de la liquidació: es fan contra el fictici, amb els formats marcats [A verificar].
- P-44 i P-45 continuen obertes a [pendents.md](pendents.md); quan es responguin, cada format [A verificar] es revisa contra la resposta.
- Risc: el real es comporta diferent del fictici. Es mitiga amb el punt 6 i amb els formats marcats.

## Fonts

- Instrucció escrita del propietari del 13/11/2026.
