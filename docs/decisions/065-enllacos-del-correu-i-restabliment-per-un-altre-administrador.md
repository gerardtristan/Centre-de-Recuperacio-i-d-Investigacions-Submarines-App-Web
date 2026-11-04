# 065 — Enllaços del correu del compte personal i restabliment per un altre administrador

- **Data:** 03/11/2026
- **Estat:** Acceptada. Validacions del responsable del projecte per completar la T-M01-05. Afegeix una [addenda al M01](../planning.md#M01-addenda-065) (RN-M01-58 a RN-M01-61, CA-M01-48 a CA-M01-55) i dues línies a la [lectura de les tasques substituïdes](../planning.md#ajustos-060-lectura). No edita la spec 00 ni cap regla aprovada. No resol Q-03 ni P-52. Precisada per la [066](066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md) (04/11/2026): el reenviament ja no és d'un sol ús i una petició limitada per destinatari compta per al límit d'origen.

## Context
La T-M01-05 havia de completar la recuperació per correu (C4), el reenviament de la verificació (C5) i el restabliment per un altre administrador (HU-08). La spec 00 deia que la recuperació té limitació de peticions (RN-24), però V-01 no en donava els valors; no deia què passa amb un compte pendent que demana recuperar la contrasenya; ni si qui restableix un altre compte ha de tornar a demostrar que és ell, ni què fer quan el compte afectat no té correu de notificació.

## Decisió
1. **Límits de la recuperació i del reenviament de la verificació** (valors inicials):
   - **per destinatari:** com a màxim 3 correus per hora i 6 cada 24 hores, per a cada adreça normalitzada i cada finalitat (recuperació o verificació), vinguin les peticions d'on vinguin;
   - **per origen:** quan un origen arriba a 10 peticions acceptades en 15 minuts, queda limitat 15 minuts comptats des de la desena. El límit és **conjunt** per a la recuperació i el reenviament;
   - una petició limitada no envia res, **no compta** i no allarga cap finestra;
   - aquests límits no bloquegen l'entrada al compte ni compten com a intents fallits de V-01: el comptador de l'entrada és un altre;
   - la resposta pública és la mateixa tant si la petició s'ha limitat com si no.
   Són valors de seguretat al codi, en un sol lloc (`apps/accounts/limits.py`), com els de V-01: les regles de seguretat no s'editen des de l'app ([059](059-rols-i-permisos-editables.md)). Per ajustar-los cal una decisió nova que canviï RN-M01-58 i, després, el valor en aquest fitxer; les proves el llegeixen d'allà.
2. **Comptes pendents de verificar.** No reben cap enllaç de recuperació fins que confirmen el correu. El reenviament de la verificació només s'ofereix després d'escriure la contrasenya correcta d'un compte pendent, on es manté el missatge «Encara has de confirmar el correu». Aquest estat intermedi es guarda a la sessió com a màxim 10 minuts i un sol reenviament [A validar: responsable del projecte; afegit a la implementació sense aprovació explícita, el codi l'aplica mentrestant]; no és una sessió autenticada i no dona accés a cap dada ni acció del compte. Abans d'enviar, es torna a comprovar que el compte encara és pendent. El destinatari és el correu del compte, decidit al servidor.
3. **Missatges.** La recuperació i el reenviament tenen textos diferents (finalitat i caducitat: una hora i 48 hores). Dins de cada flux, la resposta és la mateixa en tots els casos que no han de revelar si el compte existeix ni en quin estat és.
4. **Enllaços.** Demanar-ne un de nou no anul·la l'anterior dins de la seva caducitat. Quan se'n fa servir un, tots els altres de la mateixa operació deixen de servir.
5. **Restabliment per un altre administrador (HU-08):**
   - qui el fa torna a escriure un **codi TOTP del seu compte a la mateixa petició**, nou: no serveix un codi ja acceptat abans (ni el de l'entrada). També en l'excepció d'emergència de RN-RP-18. Un codi incorrecte no restableix res, compta per al bloqueig de V-01 de qui actua i queda al registre;
   - el **motiu és obligatori** en tots els restabliments (contrasenya i TOTP), no només en el de RN-RP-18, i queda al registre sense cap secret;
   - restablir la contrasenya **no desbloqueja** el compte, **no treu** el TOTP ni els codis de recuperació, tanca les sessions i les entrades a mig fer del compte i anul·la la credencial temporal anterior.
6. **Avís al compte restablert (CA-08.4).** El registre separa el resultat del restabliment i el de l'avís, sense secrets. Un avís posat a la cua no es presenta mai com a lliurat. Si el compte **no té correu de notificació**:
   - el restabliment es pot fer igualment, amb totes les comprovacions (M4, TOTP de qui actua, motiu i registre);
   - abans de confirmar, la pantalla adverteix: «Aquest compte no té correu de notificació. El restabliment es pot fer, però no se li podrà enviar l'avís.»;
   - després, mostra: «Restabliment completat. No s'ha pogut enviar l'avís perquè el compte no té correu de notificació. Avisa la persona afectada per una altra via.»;
   - el registre guarda l'avís com a no enviat, amb el motiu «sense adreça»;
   - no s'hi afegeix cap altre destinatari.
   Aquesta regla no resol Q-03 ni autoritza enviar la credencial temporal per correu (RN-17).

## Conseqüències
- Addenda del M01: RN-M01-58 a RN-M01-61 i CA-M01-48 a CA-M01-55. La feina és de la T-M01-05.
- Els avisos de RN-RP-18 a la junta i als administradors continuen a la T-RP-02 i a la T-M00-03.
- Continuen oberts: Q-03 (canal de la credencial temporal), [P-52](pendents.md) (soci que perd el mòbil, abans de producció del TOTP personal) i la comprovació dels registres del proxy ([arquitectura §7](../arquitectura-integracions.md), abans de dades reals).

## Fonts
- Validacions del responsable del projecte, 03/11/2026, en la revisió de la segona tanda de la T-M01-05
- Spec 00: HU-04, HU-08, RN-16 a RN-18, RN-24, V-01, CA-04.3, CA-08.1 a CA-08.4; [059](059-rols-i-permisos-editables.md); RN-RP-18 del [pla](../planning.md#ajustos-060-rols)
