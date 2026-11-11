"""Revisió automàtica d'accessibilitat del M01 al navegador (T-M01-28; checklist B8; M01-11).

Dues parts, a les mateixes pantalles:
- **axe** (Q-082, decisió 072; `axe-playwright-python` 0.1.8, que porta axe-core 4.12.1 i no el
  descarrega): regles WCAG 2.0, 2.1 i 2.2 A i AA, en clar i en fosc (el contrast canvia). Fallen
  les violacions d'impacte greu («serious» i «critical»); les altres són avisos, i el que axe no
  pot decidir sol («incomplete») queda per a la revisió manual. Tot va a l'informe.
- **Comprovacions pròpies** d'estructura i de teclat, que axe no fa (recorregut amb el tabulador).

La revisió amb lector de pantalla continua pendent de persona (diari de la T-M01-28).

Per a cada pantalla del M01 (àrea del soci, pàgines públiques i administració):
- estructura: `lang="ca"`, títol, un sol `h1`, la regió `main` i cap salt de nivell de títol;
- noms accessibles: cada camp de formulari visible té etiqueta; cada botó i cada enllaç visible
  té un nom; cada imatge té `alt`; cap `id` repetit;
- teclat: amb el tabulador s'arriba a tots els elements que es poden activar, cadascun visible i
  amb un indicador de focus (contorn o ombra de 2 px o més), sense cap trampa.

L'informe de cada pantalla es desa a `.e2e-captures/accessibilitat/`. Només dades inventades.
"""

import json
from pathlib import Path

import pytest
from axe_playwright_python.sync_playwright import Axe
from django.conf import settings
from django.urls import reverse

from apps.members import cards
from apps.members.models import AnnualFee, MemberCard

from .conftest import login_admin

pytestmark = pytest.mark.e2e

REPORTS = Path(settings.BASE_DIR) / ".e2e-captures" / "accessibilitat"
MAX_TABS = 120
AXE = Axe()
AXE_OPTIONS = {
    "runOnly": {
        "type": "tag",
        "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
    },
    "resultTypes": ["violations", "incomplete"],
}
SERIOUS = {"serious", "critical"}
THEMES = ("light", "dark")

STRUCTURE_JS = r"""
() => {
  const issues = [];
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none";
  };
  // Botons i enllaços: compten si es mostren, encara que no tinguin mida (un enllaç buit no en té,
  // però el lector de pantalla l'anuncia igualment).
  const rendered = (el) => {
    const s = getComputedStyle(el);
    return s.display !== "none" && s.visibility !== "hidden"
      && (el.offsetParent !== null || s.position === "fixed")
      && !el.closest("details:not([open]) > :not(summary)");
  };
  const name = (el) => {
    const label = el.getAttribute("aria-label");
    if (label && label.trim()) return label.trim();
    const by = el.getAttribute("aria-labelledby");
    if (by) {
      const text = by.split(/\s+/).map((id) => document.getElementById(id))
        .filter(Boolean).map((n) => n.textContent).join(" ").trim();
      if (text) return text;
    }
    if (el.labels && el.labels.length) {
      const text = [...el.labels].map((l) => l.textContent).join(" ").trim();
      if (text) return text;
    }
    const alt = [...el.querySelectorAll("img[alt]")].map((i) => i.alt).join(" ").trim();
    const text = (el.textContent || "").trim() || alt || (el.getAttribute("title") || "").trim();
    if (["INPUT"].includes(el.tagName) && ["submit", "button", "reset"].includes(el.type)) {
      return (el.value || "").trim() || text;
    }
    return text;
  };
  const html = document.documentElement;
  const lang = html.getAttribute("lang");
  if (lang !== "ca") issues.push(`lang de <html>: «${lang}»`);
  if (!document.title.trim()) issues.push("sense <title>");
  const h1 = [...document.querySelectorAll("h1")].filter(visible);
  if (h1.length !== 1) issues.push(`${h1.length} títols h1 visibles`);
  if (!document.querySelector("main")) issues.push("sense regió <main>");
  let previous = 0;
  for (const h of document.querySelectorAll("h1, h2, h3, h4, h5, h6")) {
    if (!visible(h)) continue;
    const level = Number(h.tagName[1]);
    if (previous && level > previous + 1) {
      const text = h.textContent.trim().slice(0, 60);
      issues.push(`salt de títol h${previous} → h${level}: «${text}»`);
    }
    previous = level;
  }
  const fields = document.querySelectorAll("input:not([type=hidden]), select, textarea");
  for (const f of fields) {
    if (!visible(f) && !(f.type === "checkbox" || f.type === "radio")) continue;
    if (["submit", "button", "reset"].includes(f.type)) continue;
    if (!name(f)) issues.push(`camp sense etiqueta: <${f.tagName.toLowerCase()} name="${f.name}">`);
  }
  const buttons = "button, [role=button], input[type=submit], input[type=button]";
  for (const b of document.querySelectorAll(buttons)) {
    if (rendered(b) && !name(b)) issues.push(`botó sense nom: ${b.outerHTML.slice(0, 120)}`);
  }
  for (const a of document.querySelectorAll("a[href]")) {
    if (rendered(a) && !name(a)) issues.push(`enllaç sense nom: ${a.outerHTML.slice(0, 120)}`);
  }
  for (const img of document.querySelectorAll("img")) {
    if (!img.hasAttribute("alt")) issues.push(`imatge sense alt: ${img.outerHTML.slice(0, 120)}`);
  }
  const seen = new Map();
  for (const el of document.querySelectorAll("[id]")) seen.set(el.id, (seen.get(el.id) || 0) + 1);
  for (const [id, n] of seen) if (n > 1) issues.push(`id repetit ${n} vegades: «${id}»`);
  return issues;
}
"""

FOCUS_JS = r"""
() => {
  const el = document.activeElement;
  if (!el || el === document.body || el === document.documentElement) return null;
  el.scrollIntoView({block: "center", inline: "nearest"});
  el.setAttribute("data-a11y-focus", "1");
  const r = el.getBoundingClientRect();
  const s = getComputedStyle(el);
  const outline = s.outlineStyle !== "none" && parseFloat(s.outlineWidth) >= 2;
  const shadow = s.boxShadow && s.boxShadow !== "none";
  const describe = (el.tagName.toLowerCase() + (el.id ? "#" + el.id : "")
    + (el.getAttribute("name") ? `[name=${el.getAttribute("name")}]` : "")
    + " «" + ((el.getAttribute("aria-label") || el.textContent || el.value || "")
      .trim().slice(0, 40)) + "»");
  return {
    key: describe + "@" + Math.round(r.left) + "," + Math.round(r.top + window.scrollY),
    // Chromium mou el tabulador pels subcamps (dia, mes, any) dins del mateix <input>.
    subfields: ["date", "time", "datetime-local", "month", "week"].includes(el.type),
    describe,
    visible: r.width > 0 && r.height > 0 && s.visibility !== "hidden",
    indicator: outline || shadow,
  };
}
"""

COUNT_FOCUSABLE_JS = r"""
() => {
  const groups = new Set();
  window.__a11yFocusable = [...document.querySelectorAll(
    "a[href], button:not([disabled]), input:not([type=hidden]):not([disabled]), "
    + "select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])"
  )].filter((el) => {
    const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    const shown = r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none";
    if (!shown) return false;
    // El contingut d'un <details> tancat no rep el focus fins que s'obre amb el seu <summary>.
    const closed = el.closest("details:not([open])");
    if (closed && el.tagName !== "SUMMARY") return false;
    // Un grup de botons d'opció és una sola parada del tabulador (les fletxes canvien l'opció).
    if (el.type === "radio" && el.name) {
      if (groups.has(el.name)) return false;
      groups.add(el.name);
    }
    return true;
  });
  return window.__a11yFocusable.length;
}
"""

UNREACHED_JS = r"""
() => window.__a11yFocusable.filter((el) => !el.hasAttribute("data-a11y-focus")
  && !(el.type === "radio" && el.name
    && document.querySelector(`input[name="${el.name}"][data-a11y-focus]`)))
  .map((el) => el.outerHTML.slice(0, 160))
"""


def keyboard_walk(page) -> tuple[list[str], int, list[str], str]:
    """Recorre la pàgina amb el tabulador. Torna els problemes, quants elements ha visitat,
    l'ordre en què hi ha arribat i per què s'ha aturat."""
    issues, seen, order, repeats, last, stop = [], [], [], 0, None, "límit de tabulacions"
    page.locator("body").evaluate("b => { b.setAttribute('tabindex', '-1'); b.focus(); }")
    for _ in range(MAX_TABS):
        page.keyboard.press("Tab")
        info = page.evaluate(FOCUS_JS)
        if info is None:
            stop = "el focus surt del document"
            break
        if seen and info["key"] == seen[0]:
            stop = "torna al primer element (recorregut complet)"
            break
        if info["key"] == last:
            repeats += 1
            if repeats >= (6 if info["subfields"] else 3):
                issues.append(f"trampa de teclat a {info['describe']}")
                stop = "trampa"
                break
            continue
        repeats, last = 0, info["key"]
        if info["key"] in seen:
            stop = f"torna a un element ja visitat: {info['describe']}"
            break
        seen.append(info["key"])
        order.append(info["describe"])
        if not info["visible"]:
            issues.append(f"focus en un element invisible: {info['describe']}")
        elif not info["indicator"]:
            issues.append(f"sense indicador de focus visible: {info['describe']}")
    page.locator("body").evaluate("b => b.removeAttribute('tabindex')")
    return issues, len(seen), order, stop


def _rule(rule: dict) -> dict:
    return {
        "regla": rule["id"],
        "impacte": rule.get("impact"),
        "ajuda": rule.get("help"),
        "url": rule.get("helpUrl"),
        "elements": [
            {
                "selector": node.get("target"),
                "html": (node.get("html") or "")[:200],
                "detall": (node.get("failureSummary") or "")[:400],
            }
            for node in rule.get("nodes", [])
        ],
    }


def axe_audit(page) -> dict:
    """axe en clar i en fosc: violacions greus, avisos i el que necessita revisió manual."""
    out = {}
    for theme in THEMES:
        page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
        page.wait_for_timeout(500)  # transicions de color del tema
        response = AXE.run(page, options=AXE_OPTIONS).response
        violations = response["violations"]
        out[theme] = {
            "violacions": [_rule(r) for r in violations if r.get("impact") in SERIOUS],
            "avisos": [_rule(r) for r in violations if r.get("impact") not in SERIOUS],
            "revisio_manual": [_rule(r) for r in response.get("incomplete", [])],
        }
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    return out


def audit(page, name: str, results: dict) -> None:
    page.wait_for_load_state("networkidle")
    axe = axe_audit(page)
    structure = page.evaluate(STRUCTURE_JS)
    focusable = page.evaluate(COUNT_FOCUSABLE_JS)
    keyboard, reached, order, stop = keyboard_walk(page)
    if reached < focusable:
        missing = page.evaluate(UNREACHED_JS)
        keyboard.append(
            f"amb el tabulador s'arriba a {reached} de {focusable} elements que es poden activar;"
            f" no s'hi arriba: {missing}"
        )
    results[name] = {
        "url": page.url,
        "structure": structure,
        "keyboard": keyboard,
        "reached": reached,
        "focusable": focusable,
        "order": order,
        "stop": stop,
        "axe": axe,
    }


def save(results: dict, label: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{label}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def problems(results: dict) -> list[str]:
    own = [
        f"{name}: {issue}"
        for name, result in results.items()
        for issue in result["structure"] + result["keyboard"]
    ]
    axe = [
        f"{name} ({theme}): axe {rule['regla']} ({rule['impacte']}) a {len(rule['elements'])}"
        f" element(s): {rule['ajuda']}"
        for name, result in results.items()
        for theme, found in result["axe"].items()
        for rule in found["violacions"]
    ]
    return own + axe


def test_personal_and_public_screens(page, live_server, builder, member, page_checks):
    results = {}
    page_checks.expect(404, "/aquesta-adreca-no-existeix/")
    card = MemberCard.objects.filter(member=member, revoked_at__isnull=True).first()
    token = cards.qr_token(card) if card else None
    public = [
        ("public-fer-se-soci", reverse("members:join")),
        ("public-entrar", reverse("accounts:login")),
        ("public-contrasenya-oblidada", reverse("accounts:password_reset_request")),
        ("public-ajuda-iphone", reverse("core:install_help_iphone")),
        ("public-convidat-enllac-nou", reverse("core:guest_link_request")),
        ("public-404", "/aquesta-adreca-no-existeix/"),
    ]
    if token:
        public.append(("public-verificacio-carnet", reverse("members:card_verify", args=[token])))
    for name, path in public:
        page.goto(f"{live_server.url}{path}")
        audit(page, name, results)

    account = builder.personal(member.person)
    page.goto(f"{live_server.url}{reverse('accounts:login')}")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(builder.password)
    page.get_by_role("button", name="Entrar").click()
    fee = AnnualFee.objects.filter(member=member).order_by("-pk").first()
    personal = [
        ("soci-inici", reverse("core:home")),
        ("soci-perfil", reverse("members:profile")),
        ("soci-quotes", reverse("members:fees")),
        ("soci-carnet", reverse("members:card")),
        ("soci-canvi-tipus", reverse("members:change_type")),
        ("soci-baixa", reverse("members:leave")),
        ("soci-esborrar", reverse("members:erase")),
        ("soci-seguretat", reverse("accounts:security")),
    ]
    if fee:
        personal.append(("soci-quota", reverse("members:fee_detail", args=[fee.pk])))
    for name, path in personal:
        page.goto(f"{live_server.url}{path}")
        audit(page, name, results)
    save(results, "soci-i-public")
    assert not problems(results), "\n".join(problems(results))


def test_admin_screens(page, live_server, texts, member):
    results = {}
    login_admin(page, live_server.url, texts.login)
    admin = [
        ("admin-inici", reverse("administration:home")),
        ("admin-socis", reverse("administration:members_list")),
        ("admin-fitxa", reverse("administration:member_detail", args=[member.pk])),
        ("admin-edita", reverse("administration:member_edit", args=[member.pk])),
        ("admin-altes", reverse("administration:join_requests")),
        ("admin-alta-presencial", reverse("administration:join_in_person")),
        ("admin-sollicituds", reverse("administration:member_requests")),
        ("admin-quotes", reverse("administration:fees")),
        ("admin-llicencies", reverse("administration:licence_bulk_confirm")),
        ("admin-cluber", reverse("administration:cluber_preview")),
        ("admin-registre", reverse("administration:audit_log")),
        ("admin-comptes", reverse("administration:accounts")),
        ("admin-rgpd", reverse("administration:gdpr_requests")),
        ("admin-enllacos-convidat", reverse("administration:guest_links")),
        ("admin-dades-bloquejades", reverse("administration:locked_data")),
    ]
    for name, path in admin:
        page.goto(f"{live_server.url}{path}")
        audit(page, name, results)
    save(results, "administracio")
    assert not problems(results), "\n".join(problems(results))


def test_the_checks_detect_known_defects(page):
    """Control de les comprovacions: una pàgina inventada amb defectes coneguts els ha de mostrar
    tots. Si aquesta prova passa sense detectar-los, les altres no demostren res."""
    page.set_content(
        """<!doctype html><html lang="en"><head><title></title>
        <style>.sense-focus:focus { outline: none; box-shadow: none; }</style></head><body>
        <h1>U</h1><h1>Dos</h1><h3>Salt</h3>
        <input name="sense_etiqueta">
        <button class="sense-focus"></button>
        <a href="#x" class="sense-focus"></a>
        <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
        <p id="doble"></p><p id="doble"></p>
        </body></html>"""
    )
    structure = page.evaluate(STRUCTURE_JS)
    text = "\n".join(structure)
    for expected in (
        "lang de <html>",
        "sense <title>",
        "2 títols h1",
        "sense regió <main>",
        "salt de títol h1 → h3",
        "camp sense etiqueta",
        "botó sense nom",
        "enllaç sense nom",
        "imatge sense alt",
        "id repetit",
    ):
        assert expected in text, (expected, structure)
    keyboard, _reached, _order, _stop = keyboard_walk(page)
    assert any("sense indicador de focus visible" in issue for issue in keyboard), keyboard
    # axe també ha de veure els defectes greus de la mateixa pàgina.
    found = {r["regla"] for r in axe_audit(page)["light"]["violacions"]}
    for rule in ("image-alt", "button-name", "link-name", "label", "document-title"):
        assert rule in found, (rule, found)
