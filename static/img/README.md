# Icones allotjades al servidor

Decisions 035 i 046: res no es carrega de fora. Joc d'icones de la plataforma (T-DX-58; sistema de disseny §6.20), descarregat el 18/11/2026.

| Joc | Versió | Font oficial | Llicència |
|---|---|---|---|
| Lucide (`lucide-static`) | 1.67.0 (publicada el 03/11/2026) | `https://registry.npmjs.org/lucide-static/-/lucide-static-1.67.0.tgz`, carpeta `package/icons/` | [LICENSE-lucide.txt](LICENSE-lucide.txt) · ISC · Copyright 2026 Lucide Icons and Contributors |

L'sprite `icones.svg` només porta les icones de `apps/core/icones.py`. Els traçats són els oficials, sense modificar. Només es treuen els atributs de color i de traç de l'arrel de cada SVG, perquè els posa el CSS de `.icona`. Es genera amb:

```
python -I tools/icones/genera.py <carpeta package/icons del paquet> <arrel del repositori>
```

## Empremtes del paquet descarregat

```
sha512-Lu/Ntwfw1GOQiNgTC2iHd/PC4QbqzwktLVFHTB84tldlfUjFgQ+EBWiZc/UPrlNdX97O/KXWRn792hIdQh6nhA==   (integritat que publica npm; comprovada)
7dde5a356b87f250cabba45a6343917711f59345f800036c0474418e3c27b840   (SHA-256 de lucide-static-1.67.0.tgz)
```

Per afegir una icona: s'afegeix el nom a `apps/core/icones.py` i es torna a generar l'sprite amb el mateix paquet (mateixa versió i empremta). Per canviar de versió: es descarrega de la mateixa font oficial, es comprova la integritat i s'actualitza aquesta taula.

Els PNG de `icones/` són les icones de la web instal·lable (T-M01-21), no d'aquest joc.
