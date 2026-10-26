# 006 — Còpies de seguretat creuades i xifrades

- **Data:** 27/10/2026
- **Estat:** Acceptada

## Context
Un sol VPS de producció guarda la base de dades; els fitxers són a Scaleway. Cap proveïdor ha de tenir l'única còpia de res, i les còpies han de ser restaurables (checklist D1-D2).

## Alternatives
- Només les còpies automàtiques de Hetzner: si es perd el compte o el proveïdor, es perd tot.
- Còpies de Coolify a un bucket extern sense xifrar: dades personals en clar fora del servidor.
- Còpies xifrades al servidor abans de sortir, a dos proveïdors diferents.

## Decisió
- **Base de dades:** bolcat diari, xifrat al servidor (per exemple, amb restic) abans de sortir, i enviat a un bucket de còpies de Scaleway (diferent del bucket de fitxers i amb claus pròpies) i a un Storage Box de Hetzner.
- **Fitxers:** còpia periòdica xifrada del bucket de Scaleway cap al Storage Box de Hetzner.
- **Servidor:** còpies automàtiques de Hetzner del VPS sencer (recuperació ràpida).
- **Prova de restauració:** cada mes fins a la posada en producció; després, cada trimestre. Es restaura en un entorn net, es comprova que s'hi pot entrar i que les dades quadren, i es deixa un informe.
- Avís per correu si una còpia falla.

## Conseqüències
- La clau de xifratge és crítica: si es perd, les còpies no serveixen. Es guarda fora de línia en dos llocs (responsable de manteniment i tresorer o presidència) [A validar qui].
- Coolify pot programar els bolcats, però el xifratge s'ha de fer amb una eina a part (restic o equivalent) [A validar en el pla de la base comuna].
- Cost addicional: Storage Box BX11 de 1 TB, 3,20 €/mes sense IVA (pàgina oficial consultada el 27/10/2026), i còpies de Hetzner al voltant del 20 % del preu del VPS.

## Fonts
- Encàrrec d'arquitectura del 26/10/2026 i decisió del 27/10/2026
- `docs/checklist-produccio.md`, D1, D2 i «Continu»
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §2 «Còpies de seguretat»
