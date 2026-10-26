# 004 — Correu transaccional i butlletí amb Brevo

- **Data:** 27/10/2026
- **Estat:** Acceptada (el preu del pla de pagament és [A validar])

## Context
La plataforma envia correus transaccionals (alta aprovada, confirmació d'inscripció, rebuts, recordatoris de quota i llicència, recuperació de contrasenya) i un butlletí a uns 300 subscriptors. Pressupost molt ajustat i dades a la UE.

## Alternatives
- Gmail del club: límits d'enviament baixos i sense estadístiques ni gestió de baixes.
- Altres proveïdors de correu transaccional amb seu fora de la UE: transferència internacional a documentar.
- Brevo (empresa francesa, dades a la UE): pla gratuït amb 300 enviaments diaris comptant tots els tipus.

## Decisió
- Brevo, començant amb el pla gratuït.
- Separar correus transaccionals i butlletí (remitents i categories diferents).
- Comptador diari d'enviaments a la plataforma: es reserva una quota per als transaccionals; el butlletí s'envia en tandes al llarg de diversos dies; avís quan s'arriba al 80 % del límit.
- Pressupostar el pla de pagament (Starter, des d'uns 9 $/mes per a 5.000 correus/mes, sense límit diari; preu consultat en fonts secundàries el 27/10/2026, [A validar] a brevo.com) per a quan s'entri en producció.

## Conseqüències
- Amb el pla gratuït, un butlletí a 300 subscriptors no cap en un sol dia si també hi ha transaccionals.
- Cal configurar SPF, DKIM i DMARC al domini (checklist G1) i enllaç de baixa al butlletí (G2).
- Via de sortida: els correus es generen a la plataforma amb plantilles pròpies i s'envien per SMTP o API; canviar de proveïdor és canviar credencials. La llista de subscriptors i els consentiments viuen a la base de dades del club.

## Fonts
- Encàrrec d'arquitectura del 26/10/2026 i decisió del 27/10/2026
- `docs/checklist-produccio.md`, G1-G2
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §8.2 i §9.14
