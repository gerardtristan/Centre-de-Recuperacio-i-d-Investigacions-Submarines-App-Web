---
name: webapp-testing
description: Comprovar al navegador (Playwright per a Python) pantalles de la plataforma C.R.I.S. o dels wireframes: fluxos, captures a 1280 i 390 px, errors de consola i peticions fallides. Fes-la servir abans de donar per acabada qualsevol tasca que toqui plantilles, CSS o vistes.
license: Apache 2.0, a LICENSE.txt. Adaptada de github.com/anthropics/skills (skills/webapp-testing, commit 2c5958e); canvis del projecte C.R.I.S. el 10/11/2026 (text en català i adaptat a Django; sense scripts/ ni examples/).
---

# Comprovar al navegador

## 1. La suite de prova ràpida (primer de tot)

```
pytest -m e2e
```

- Són a `apps/*/tests/e2e/`. Fan servir `live_server` de pytest-django i dades inventades (CLAUDE.md: mai dades reals).
- Cada prova falla si hi ha errors a la consola o respostes 4xx/5xx que no s'esperaven (fixture `page_checks` de `conftest.py`).
- Les captures queden a `.e2e-captures/` (fora del repositori; el CI les puja si falla).
- **Mira les captures** de les pantalles que has tocat, a 1280 i a 390 px, abans de dir que la tasca està acabada.

Si la pantalla nova no hi és, afegeix-hi una prova abans de comprovar-la a mà.

## 2. Una comprovació puntual

Per a una pantalla que encara no té prova:

1. `python manage.py seed_demo_data` (només en local i amb una base de dades buida) i `python manage.py runserver`.
2. Un script de Playwright síncron fora del repositori (al directori temporal):

```python
from playwright.sync_api import sync_playwright

errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width in (1280, 390):
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.on("response", lambda r: r.status >= 400 and errors.append(f"{r.status} {r.url}"))
        page.goto("http://127.0.0.1:8000/")
        page.wait_for_load_state("networkidle")  # abans d'inspeccionar el DOM
        page.screenshot(path=f"captura-{width}.png", full_page=True)
    browser.close()
print(errors or "sense errors")
```

3. Selectors per rol o text visible (`get_by_role`, `get_by_label`), no per classes de CSS.

## 3. Wireframes (HTML estàtic)

`design/wireframes/*.html` s'obren amb `Path("design/wireframes/socis.html").resolve().as_uri()` (funciona a Windows). Llegeix l'HTML per trobar els selectors abans d'escriure el script.

## Regles

- Navegador sempre en mode sense finestra (`headless=True`) i tancat en acabar.
- Cap credencial real: la contrasenya de proves és `contrasenya-de-proves-1954`.
- Amagar un element a la pantalla no és un control: els permisos es proven al servidor (proves unitàries), no aquí.
