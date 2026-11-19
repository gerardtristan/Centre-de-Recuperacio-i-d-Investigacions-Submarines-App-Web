# 099. Servidor de proves al portàtil del propietari

- **Data:** 19/11/2026
- **Estat:** Acceptada (propietari, instrucció escrita del 19/11/2026: «lo millor serà per proves, fer un server local amb el portàtil […] obre una tasca»). L'aplicació a `master` espera el seu sí a la PR (`risc:alt`, [098](098-risc-alt-nomes-amb-el-si-escrit-del-propietari.md)).
- **Relació:** completa el punt 1 de la [090](090-respostes-del-propietari-del-13-11-entorn-de-proves-i-branques-de-nit.md) (servidor CX23 de Hetzner). La 090 continua aprovada, però no es crea res a Hetzner mentre el portàtil faci la feina.

## Context

La fase 1 està a punt d'acabar-se sense pagaments reals. Per provar la interfície, els moviments i els canvis de dades, el propietari i la junta necessiten la plataforma en marxa i accessible des de fora. El servidor de Hetzner no s'ha creat (falta el compte), i el propietari té un portàtil disponible.

## Decisió

1. **El servidor de proves corre en un portàtil amb Windows** del propietari, amb Docker Desktop: PostgreSQL, l'aplicació (gunicorn), la cua de tasques, una bústia de proves (Mailpit) i un Caddy amb una contrasenya al davant. Guia: [`docs/guies/servidor-de-proves-al-portatil.md`](../guies/servidor-de-proves-al-portatil.md).
2. **Només dades inventades** (`seed_demo_data`), pagaments i banc ficticis (092) i cap correu cap a fora. La configuració és `config/settings/staging.py`, la mateixa que es preveia per al servidor de Hetzner.
3. **Accés des de fora: Cloudflare Tunnel ràpid per defecte** (adreça `https://….trycloudflare.com`, sense compte, nova a cada arrencada). Cloudflare és dels EUA: s'accepta com a excepció només de proves i amb dades inventades (propietari, 17/11/2026). Alternatives: un túnel fix amb compte de Cloudflare, o Tailscale (privat).
4. **Els secrets es generen al portàtil** la primera vegada (`deploy/proves/local/`, fora del repositori i de la imatge). El secret del doble factor dels comptes inventats és propi del portàtil; el de prova continua refusat sense `DEBUG` (RN-M01-84).
5. **Actualitzar** és `actualitza.cmd`: baixa `master`, reconstrueix la imatge i aplica les migracions en arrencar, conservant les dades.

## Conseqüències

- Dependència nova només per a la imatge: `gunicorn` (extra `deploy` de `pyproject.toml`), no a la instal·lació de desenvolupament.
- El servidor només funciona amb el portàtil encès i connectat; l'adreça del túnel ràpid canvia a cada arrencada.
- La prova en dispositius reals del flux de mandat (P-284, 097) es pot fer en aquest servidor.
- Fer servir un subdomini de `cris1954.cat` per a l'adreça fixa voldria dir moure'n els DNS a Cloudflare: no està decidit [A validar].
