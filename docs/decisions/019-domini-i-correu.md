# 019 — Domini de la plataforma i adreces de correu

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-15). El control del DNS i la redirecció de cris.barcelona estan [A validar].

## Context
Als documents apareixien tres dominis: cris.barcelona (web actual; context v3, document incremental, pantalles de funcionalitats), cris.es (decisió 015) i cap domini fixat per a la plataforma.

## Alternatives
- Fer servir cris.barcelona per a la plataforma: és el domini de la web WordPress actual.
- Fer servir cris1954.cat, ja pagat pel club, per a la plataforma i la web nova.

## Decisió
| Ús | Domini o adreça |
|---|---|
| Plataforma i web nova | **cris1954.cat** (ja pagat pel club; cap cost addicional al pressupost) |
| Adreça de contacte del club | **cris@cris.es** |
| Remitent dels correus de la plataforma | Una adreça de cris1954.cat (per exemple, `no-respon@cris1954.cat` [A validar el nom]) amb **resposta a** cris@cris.es |
| Web actual | cris.barcelona: redirecció cap a la web nova [A validar] |

- [A validar] Que el club controla el DNS de cris1954.cat, i si també controla el de cris.es.
- Opció futura per als àlies dels comptes d'administrador ([015](015-doble-factor-i-comptes-administrador.md), punt 5): Cloudflare Email Routing sobre cris1954.cat. Aquesta decisió substitueix la menció a cris.es d'aquell punt.

## Conseqüències
- SPF, DKIM i DMARC es configuren a cris1954.cat per a Brevo (checklist G1). Els registres de cris.es no es toquen.
- Si el DNS de cris1954.cat passa a Cloudflare, abans cal fer inventari dels registres actuals.
- Els comptes dels proveïdors s'obren amb una adreça que controli el club [A validar quina].

## Fonts
- Resolució de P-15 comunicada per l'equip el 27/10/2026
- `docs/arxiu/context-projecte-v3-2026-10-20.pdf`, §4 (web cris.barcelona)
- `docs/arquitectura-integracions.md`, §2 i §7
