# 018 — Perfil únic, comptes i doble factor per entrada

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-16, P-17 i P-18; concreta la [015](015-doble-factor-i-comptes-administrador.md))

## Context
La 015 va fixar dos comptes per a cada administrador, però quedaven oberts tres punts:
- **P-16:** com encaixa amb funcionalitats §2, on diu que «una mateixa persona pot tenir més d'un rol».
- **P-17:** quins rols tenen el doble factor obligatori.
- **P-18:** com s'apliquen les regles C4 i C5 de la checklist als comptes d'administrador.

## Alternatives
- Doble factor segons el rol: cal mantenir una llista de rols «sensibles» i és fàcil equivocar-se.
- Doble factor segons l'entrada: tot compte que entra per l'administració el té obligatori.

## Decisió
1. **Perfil únic:** cada persona té un sol perfil (dades personals, soci o no soci).
2. **Comptes:** una persona amb funcions de gestió té dos comptes lligats al seu perfil:
   - un **compte de soci** (àrea de socis);
   - un **compte d'administrador** (entrada d'administració), que pot tenir **diversos rols** (per exemple, tresorer i responsable de material).
3. **Doble factor:** obligatori per a **qualsevol compte que entri per l'administració**, inclosos instructor i Departament d'Història. Opcional per als comptes de soci.
4. **Recuperació i verificació:**

   | | Compte de soci | Compte d'administrador |
   |---|---|---|
   | Verificació en crear-lo | Per correu (checklist C5) | La crea un administrador; no hi ha verificació per correu |
   | Recuperar la contrasenya | Per correu, amb enllaç d'un sol ús (checklist C4) | La restableix un altre administrador, o s'hi entra amb codis de recuperació guardats fora de línia |

5. El registre d'activitat guarda la persona i el compte que ha fet cada acció (ja ho diu la 015).

## Conseqüències
- La frase de funcionalitats §2 sobre persones amb més d'un rol es manté per al compte d'administrador. El text de substitució per al .docx és a [pendents.md](pendents.md) (P-22).
- Les persones no sòcies (alumnes, assistents, llicència d'un dia) també tenen perfil. Si han de tenir compte d'accés a l'àrea de socis és [A validar] (P-23).
- La checklist C4 i C5 queda adaptada.

## Fonts
- Resolució de P-16, P-17 i P-18 comunicada per l'equip el 27/10/2026
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §2
- `docs/checklist-produccio.md`, C2, C4 i C5
