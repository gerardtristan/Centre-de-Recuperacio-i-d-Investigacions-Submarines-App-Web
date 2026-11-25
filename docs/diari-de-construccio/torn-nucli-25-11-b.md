# Torn del nucli del 25/11/2026 (b) · Notícies i preguntes freqüents a l'administració, i imatges públiques

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 25/11/2026 02:43 | (vegeu la PR) | 5 noves, 1 fila nova de la matriu i 2 e2e | [A comprovar] |

**En tres línies:** l'administració, el President i la Junta ja poden escriure les preguntes freqüents de l'ajuda i publicar-les o retirar-les sense esborrar-les. Les pantalles de les notícies, fetes al carril A, ja tenen ruta. I l'interruptor de les imatges públiques de la web el pot encendre l'administrador (continua apagat).

## Què s'ha fet
- **Notícies (WP2):** el commit de la branca `tasca/T-M07-08b-noticies-admin` (carril A), sense conflictes; les rutes, a `STANDALONE` de la prova del menú.
- **Preguntes freqüents (WP4):** `apps/website/help_admin_views.py` i `templates/website/admin/help_*.html`, sota `/gestio/web/ajuda/`: llista per tema, tema nou, pregunta nova (sense publicar), editar-la i publicar-la o retirar-la.
- **Imatges públiques:** `settings.edit.website.public_images_enabled` al catàleg i `core/0082`, només l'administrador ([P-663](../decisions/pendents.md)).
- Entrades del menú per a DISSENY: T-DX-149 i T-DX-150. E2e al mapa del hook.

## Decisions i perquè
- **Només l'administrador encén les imatges públiques:** és l'opció més conservadora d'un dubte irreversible (persones que surten a la web); el pilot proposava també el responsable de cursos i sortides, que queda com a opció B.
- **Cap opció d'esborrar una pregunta:** retirar-la la treu de l'ajuda i es pot tornar a publicar.
- **El tema es crea a la mateixa llista:** sense temes no es pot escriure cap pregunta, i no n'hi ha cap d'inicial.

## Com se sap que funciona
- WP4: l'administració, el President i la Junta hi entren; el Secretari, «no trobat» i res desat. Una pregunta nova no surt al cercador fins que es publica; retirada, tampoc, i no s'esborra.
- P-663: una prova per rol de la cel·la nova; el President rep «no trobat» i l'administrador l'encén.

## Comprovació de §15.5
- Només components existents (`targeta`, `taula`, `formulari`, `estat`, Errata); un sol botó primari per formulari; cap `style=`.

## Evidències
- Sortida de proves · executada el 25/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q apps/website apps/core/tests/test_permissions_07_08.py apps/core/tests/test_permission_matrix.py apps/core/tests/test_verificacio_t_m00_07.py apps/accounts/tests/test_navigation_subpages.py
  470 passed
  $ pytest -m e2e apps/core/tests/e2e/test_web_admin_continguts.py
  2 passed
  ```
- Captures a 1280, 390 i 320 px (clar i fosc) a `.e2e-captures/`, mirades: la fitxa i la llista de les notícies, i la pregunta i la llista de l'ajuda.
