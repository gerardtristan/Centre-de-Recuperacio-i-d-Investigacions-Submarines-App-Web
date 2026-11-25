# Torn del nucli del 25/11/2026 · Llocs als ajustos, avís del lloguer i dades inventades del 07

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 25/11/2026 01:20 | (vegeu la PR) | 7 noves i 1 fila nova de la matriu | [A comprovar] |

**En tres línies:** la pantalla d'ajustos ja enllaça «Llocs» per a qui els pot veure. Si algun dia el club cobra el material llogat, el participant rebrà l'avís del càrrec, i l'interruptor el podran encendre l'administrador i el tresorer (continua apagat). I la llavor de proves ja porta missatges de contacte, subscripcions i un butlletí.

## Què s'ha fet
- **T-M02-39:** `apps/core/views/business_settings.py` i `templates/core/settings_index.html`: l'enllaç «Llocs» amb AC21, com «Textos legals» amb M12.
- **T-M03-11:** plantilla `avis-carrec-lloguer` a `core.mail`; `apps/equipment/rental_charges.notify`, a la cua dins de la mateixa transacció del càrrec (un convidat rep l'enllaç de convidat del càrrec). `settings.edit.equipment.rental_charges_enabled` al catàleg i `core/0081` (administrador i tresorer, [P-662](../decisions/pendents.md)).
- **T-M07-17:** `apps/website/demo_data.py`, cridat per `seed_demo_data`: missatges nou, respost i tancat; subscripcions confirmada, pendent i de baixa; un butlletí en esborrany.

## Decisions i perquè
- **Qui encén el cobrament del lloguer:** el pla no ho diu; d'inici, l'administrador i el tresorer, i l'interruptor continua apagat (D2, irreversible: diners que veu un soci).
- **L'avís porta només l'activitat, el tipus de material, l'import i l'enllaç**, que demana sessió.
- **L'esborrany del butlletí de la llavor es desa sense el servei:** el butlletí és apagat (P-42) i `save_draft` el rebutjaria.

## Com se sap que funciona
- T-M02-39: el RCS veu l'enllaç; el Secretari, no; el responsable de material, amb AC21 i cap apartat, també obre la pantalla.
- T-M03-11: un soci rep l'avís amb l'import i l'enllaç al càrrec; un convidat, l'enllaç de convidat; apagat, ningú res. Una cel·la per rol del permís nou; el tresorer l'encén amb registre i el responsable de material rep «no trobat».
- T-M07-17: la llavor deixa cada estat, i cap adreça que no sigui inventada.

## Evidències
- Sortida de proves · executada el 25/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q apps/website/tests/test_demo_data_07.py apps/equipment/tests/test_rental_charges.py apps/core/tests/test_permissions_03.py apps/core/tests/test_business_settings_views.py apps/core/tests/test_mail_limit.py apps/core/tests/test_seed_demo_data.py
  244 passed
  ```
