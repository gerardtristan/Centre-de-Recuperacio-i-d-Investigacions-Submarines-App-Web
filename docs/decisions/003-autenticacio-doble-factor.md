# 003 — Autenticació i doble factor

- **Data:** 27/10/2026
- **Estat:** Proposada: el mecanisme és acceptat; l'abast dels rols amb doble factor obligatori està pendent de validació de la junta (P-05)

## Context
La plataforma guarda dades de socis i diners. Els documents d'origen no coincideixen en qui ha de fer servir doble factor:
- Context v3, §9: administradors i comptes d'emergència.
- Funcionalitats, §2: administradors i com a mínim dos comptes d'emergència.
- Checklist C2 (abans del 27/10/2026): administradors i tresorer.

## Alternatives
- Proveïdor d'identitat extern (SaaS): més funcions, però un altre proveïdor amb dades de socis i possible cost.
- Autenticació de Django amb TOTP (aplicació d'autenticació al mòbil): sense cost, dades a casa.
- SMS com a segon factor: cost per missatge i menys segur; descartat.

## Decisió
- Autenticació de Django (sessions per a l'administració i l'àrea de socis), amb entrada d'administració separada i discreta.
- TOTP obligatori per a administrador, tresorer i secretaria (qualsevol rol amb accés a diners o dades de socis) i per als comptes d'emergència.
- Com a mínim dos comptes d'emergència; codis de recuperació guardats fora de línia (en paper o en un gestor de contrasenyes del club), mai al repositori.
- Per als socis, el doble factor és opcional.

## Conseqüències
- Si la junta valida només «administradors», s'ha de tornar a tocar CLAUDE.md i la checklist C2. La recomanació es basa en el risc: tresorer i secretaria veuen diners i dades personals.
- Cal un procediment per recuperar l'accés si algú perd el mòbil (comptes d'emergència i codis de recuperació).
- Requereix limitació d'intents d'inici de sessió (checklist C3).

## Fonts
- `docs/context-projecte.md`, §9
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §2 «Funcionalitats comunes»
- `docs/checklist-produccio.md`, C2
- Recomanació de l'equip del 27/10/2026
