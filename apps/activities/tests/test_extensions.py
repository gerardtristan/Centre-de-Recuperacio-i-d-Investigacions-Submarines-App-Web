"""Punts d'extensió i senyals del 02, provats amb un mòdul fals (T-M02-09; M02-8).

El mòdul fals fa el que farà el 03: afegeix preguntes a la inscripció, un motiu que impedeix
tancar i un bloc a la fitxa, i escolta quan una activitat es marca com a feta. El 02 no l'importa
mai. Qui envia `activity_done` (els estats) arriba amb la T-M02-03b. Només dades inventades.
"""

import ast
from pathlib import Path

import pytest
from django import forms
from django.core.exceptions import ImproperlyConfigured

from apps.activities import catalogue, extensions
from apps.activities.models import Activity
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import outing_data

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_registries(monkeypatch):
    """Cada prova comença sense res registrat i no deixa res per a la següent."""
    monkeypatch.setattr(extensions, "_enrolment_sections", {})
    monkeypatch.setattr(extensions, "_detail_sections", {})
    monkeypatch.setattr(extensions, "_closing_checks", [])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def an_outing(manager, **fields):
    place = catalogue.create_place(by=manager, name=f"Lloc {Activity.objects.count()}")
    return Activity.objects.create(**outing_data(place, **fields))


class FakeEquipmentModule:
    """Un mòdul inventat que s'enganxa al 02 com ho farà el de material."""

    def __init__(self):
        self.saved = []
        self.done = []
        self.pending = {}  # activitat → motius que impedeixen tancar
        self.fail_on_done = False

    def ready(self):
        extensions.register_enrolment_section(
            extensions.EnrolmentSection(
                key="equipment",
                label="Material",
                fields=lambda activity, person: {
                    "needs_regulator": forms.BooleanField(required=False)
                },
                save=lambda enrolment, data: self.saved.append((enrolment, dict(data))),
            )
        )
        extensions.register_closing_check(self.closing_check)
        extensions.register_detail_section(
            extensions.DetailSection(
                key="equipment",
                label="Material assignat",
                template_name="equipment/_assigned.html",
                context=self.detail_context,
            )
        )
        extensions.activity_done.connect(self.on_done, dispatch_uid="fake-equipment")

    def closing_check(self, activity):
        return self.pending.get(activity.pk, [])

    def detail_context(self, activity, *, place, viewer, person):
        if place == extensions.PLACE_PERSONAL and person is None:
            return None  # sense participant no hi ha res a ensenyar
        return {"activity": activity.pk, "place": place}

    def on_done(self, sender, activity, by, **kwargs):
        if self.fail_on_done:
            raise RuntimeError("El mòdul fals falla")
        self.done.append((activity.pk, activity.status, by))


@pytest.fixture
def fake():
    module = FakeEquipmentModule()
    module.ready()
    yield module
    extensions.activity_done.disconnect(dispatch_uid="fake-equipment")


# --- Formulari d'inscripció -----------------------------------------------------------------------


def test_a_module_adds_questions_to_the_enrolment_form(fake, manager):
    (section,) = extensions.enrolment_sections()
    assert (section.key, section.label) == ("equipment", "Material")
    fields = section.fields(an_outing(manager), None)
    assert isinstance(fields["needs_regulator"], forms.BooleanField)
    section.save("inscripció inventada", {"needs_regulator": True})
    assert fake.saved == [("inscripció inventada", {"needs_regulator": True})]


def test_sections_keep_the_order_and_have_unique_keys(fake):
    other = extensions.EnrolmentSection(
        key="transport", label="Transport", fields=lambda a, p: {}, save=lambda e, d: None
    )
    extensions.register_enrolment_section(other)
    assert [s.key for s in extensions.enrolment_sections()] == ["equipment", "transport"]
    with pytest.raises(ImproperlyConfigured):
        extensions.register_enrolment_section(other)


@pytest.mark.parametrize(
    "broken",
    [
        {"key": ""},
        {"label": ""},
        {"fields": None},
        {"save": "no és una funció"},
    ],
    ids=["sense clau", "sense títol", "sense camps", "sense desar"],
)
def test_a_broken_enrolment_section_is_a_programming_error(broken):
    data = {"key": "x", "label": "X", "fields": lambda a, p: {}, "save": lambda e, d: None}
    with pytest.raises(ImproperlyConfigured):
        extensions.register_enrolment_section(extensions.EnrolmentSection(**{**data, **broken}))
    with pytest.raises(ImproperlyConfigured):
        extensions.register_enrolment_section({"key": "x"})
    assert extensions.enrolment_sections() == []


# --- Comprovacions de tancament -------------------------------------------------------------------


def test_a_module_adds_reasons_that_block_closing(fake, manager):
    outing, other = an_outing(manager), an_outing(manager, title="Una altra sortida")
    assert extensions.closing_reasons(outing) == []
    fake.pending[outing.pk] = ["Material pendent de tornar: 2 reguladors"]
    extensions.register_closing_check(lambda activity: ["Un altre motiu inventat"])
    assert extensions.closing_reasons(outing) == [
        "Material pendent de tornar: 2 reguladors",
        "Un altre motiu inventat",
    ]
    assert extensions.closing_reasons(other) == ["Un altre motiu inventat"]


def test_registering_the_same_check_twice_counts_once(fake, manager):
    outing = an_outing(manager)
    fake.pending[outing.pk] = ["Material pendent"]
    extensions.register_closing_check(fake.closing_check)
    assert extensions.closing_reasons(outing) == ["Material pendent"]
    with pytest.raises(ImproperlyConfigured):
        extensions.register_closing_check("no és una funció")


def test_a_closing_check_that_fails_is_never_silenced(manager):
    def broken(activity):
        raise RuntimeError("No s'ha pogut mirar el material")

    extensions.register_closing_check(broken)
    with pytest.raises(RuntimeError):
        extensions.closing_reasons(an_outing(manager))


# --- Blocs de pantalla ----------------------------------------------------------------------------


def test_a_module_adds_a_block_to_the_detail_screens(fake, manager):
    outing = an_outing(manager)
    ((section, context),) = extensions.detail_sections(
        outing, place=extensions.PLACE_ADMIN, viewer=manager
    )
    assert (section.key, section.template_name) == ("equipment", "equipment/_assigned.html")
    assert context == {"activity": outing.pk, "place": "admin"}
    # La secció decideix si té res a mostrar: sense participant, a l'àrea personal no surt.
    assert extensions.detail_sections(outing, place=extensions.PLACE_PERSONAL) == []
    person = outing.responsible
    assert len(extensions.detail_sections(outing, place="personal", person=person)) == 1
    with pytest.raises(ImproperlyConfigured):
        extensions.detail_sections(outing, place="public")


def test_a_broken_detail_section_is_a_programming_error(fake):
    good = {"key": "y", "label": "Y", "template_name": "y.html", "context": lambda a, **k: {}}
    for broken in ({"template_name": ""}, {"context": None}, {"key": "equipment"}):
        with pytest.raises(ImproperlyConfigured):
            extensions.register_detail_section(extensions.DetailSection(**{**good, **broken}))


# --- Senyals --------------------------------------------------------------------------------------


def test_a_module_hears_that_an_activity_is_done(fake, manager):
    outing = an_outing(manager)
    extensions.activity_done.send(sender=Activity, activity=outing, by=manager)
    assert fake.done == [(outing.pk, Activity.Status.DRAFT, manager)]


def test_a_failing_subscriber_is_never_silenced(fake, manager):
    """`send`, no `send_robust`: l'error puja i el canvi que l'envia es desfà (T-M02-03b)."""
    fake.fail_on_done = True
    with pytest.raises(RuntimeError):
        extensions.activity_done.send(sender=Activity, activity=an_outing(manager), by=manager)


def test_the_other_signals_are_declared_for_the_tasks_that_will_send_them():
    # `activity_done` l'enviarà la T-M02-03b; `activity_duplicated`, la T-M02-07, i
    # `enrolment_confirmed`, la T-M02-10. Les cancel·lacions són esdeveniments de la 049
    # (RN-M02-36, T-M02-35), no senyals.
    assert extensions.activity_duplicated is not extensions.enrolment_confirmed
    assert not hasattr(extensions, "activity_cancelled")
    assert not hasattr(extensions, "enrolment_cancelled")


# --- El 02 no importa els mòduls que s'hi enganxen ------------------------------------------------


def test_the_module_only_imports_the_common_base_accounts_and_members():
    """«Sense que el 02 els importi» (M02-8): cap fitxer del 02, fora de les proves, importa
    cap altra app que les que consumeix per contracte."""
    allowed = {"core", "accounts", "members", "activities"}
    root = Path(extensions.__file__).parent
    for path in root.rglob("*.py"):
        if "tests" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            for name in names:
                parts = name.split(".")
                if parts[0] == "apps" and len(parts) > 1:
                    assert parts[1] in allowed, (path.name, name)
