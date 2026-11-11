"""Recorreguts dels wireframes (T-M01-48; decisió 079, A-31): la comprovació de
`design/recorreguts/comprova.py` passa amb les dades del repositori, i falla quan una àncora no
existeix al wireframe o una tasca no existeix al pla. Sense base de dades.
"""

import copy
import importlib.util
import json
from pathlib import Path

from django.conf import settings

FOLDER = Path(settings.BASE_DIR) / "design" / "recorreguts"
spec = importlib.util.spec_from_file_location("comprova_recorreguts", FOLDER / "comprova.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def data():
    return json.loads(check.DATA.read_text(encoding="utf-8"))


def problems(changed):
    return check.problems(
        changed, plan_text=check.PLAN.read_text(encoding="utf-8"), wireframes_dir=check.WIREFRAMES
    )


def step(changed, journey, number):
    steps = next(j for j in changed["recorreguts"] if j["id"] == journey)["passos"]
    return next(s for s in steps if s["pas"] == number)


def test_the_check_passes_with_the_repository_data(capsys):
    assert check.main([]) == 0
    assert "Recorreguts correctes" in capsys.readouterr().out


def test_every_process_of_the_module_has_its_journey_with_actor_and_task():
    journeys = data()["recorreguts"]
    assert [j["id"] for j in journeys] == [f"P-M01-{letter}" for letter in "ABCDEFG"]
    for journey in journeys:
        for item in journey["passos"]:
            assert item["actor"] and item["que"] and item["tasca"].startswith("T-"), item
            # Un pas amb pantalla i sense wireframe ho diu amb el distintiu.
            if item["pantalla"] and not item["wireframes"]:
                assert item.get("distintiu") == check.NO_WIREFRAME, item


def test_the_browser_copy_is_the_json_data():
    # `index.html` s'obre amb file:// i no pot llegir el JSON: llegeix `dades.js`.
    assert check.SCRIPT.read_text(encoding="utf-8") == check.script_text(data())


def test_the_index_shows_the_prototype_notice_and_links_no_external_resource():
    html = (FOLDER / "index.html").read_text(encoding="utf-8")
    assert "Prototip de disseny, no és l'aplicació real" in html
    assert data()["avis"] in html
    assert "http://" not in html and "https://" not in html and "style=" not in html
    script = (FOLDER / "index.js").read_text(encoding="utf-8")
    assert "fetch(" not in script and "innerHTML" not in script


def test_a_missing_anchor_fails():
    changed = copy.deepcopy(data())
    step(changed, "P-M01-B", "1")["wireframes"][0]["ancora"] = "no-existeix"
    assert problems(changed) == [
        "P-M01-B, pas 1: l'àncora socis.html#no-existeix no existeix al wireframe"
    ]


def test_a_missing_wireframe_file_or_role_fails():
    changed = copy.deepcopy(data())
    step(changed, "P-M01-C", "1")["wireframes"][0]["fitxer"] = "../../README.md"
    step(changed, "P-M01-G", "1")["wireframes"][0]["rol"] = "ningu"
    assert problems(changed) == [
        "P-M01-C, pas 1: el wireframe ../../README.md no existeix",
        "P-M01-G, pas 1: el rol «ningu» no és a admin.html",
    ]


def test_a_task_or_a_permission_that_is_not_in_the_plan_fails():
    changed = copy.deepcopy(data())
    step(changed, "P-M01-A", "8")["tasca"] = "T-M01-999"
    step(changed, "P-M01-A", "8")["permisos"] = ["P99"]
    assert problems(changed) == [
        "P-M01-A, pas 8: la tasca T-M01-999 no existeix al pla",
        "P-M01-A, pas 8: el permís P99 no existeix a la matriu del pla",
    ]


def test_an_unknown_badge_or_a_process_without_journey_fails():
    changed = copy.deepcopy(data())
    step(changed, "P-M01-F", "4")["distintiu"] = "inventat"
    changed["recorreguts"] = [j for j in changed["recorreguts"] if j["id"] != "P-M01-E"]
    found = problems(changed)
    assert "P-M01-E: el procés del pla no té recorregut" in found
    assert "P-M01-F, pas 4: el distintiu «inventat» no està declarat" in found
