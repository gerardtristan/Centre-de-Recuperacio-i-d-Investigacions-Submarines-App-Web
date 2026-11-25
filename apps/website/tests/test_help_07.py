"""Preguntes freqüents amb cercador (T-M07-09; RN-M07-12; CA-M07-16). Només dades
inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import help as faq
from apps.website.models import FaqEntry, FaqTopic

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def editor(make_admin):  # noqa: F811
    """WP4 és de l'administrador, el President i la Junta a la matriu inicial (T-M07-02)."""
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def topic(editor):
    return faq.save_topic(None, actor=editor, name="Quotes")


def _entry(editor, topic, question, answer="Resposta inventada.", published=True):
    return faq.save_entry(None, actor=editor, topic=topic, question=question, answer=answer,
                          published=published)  # fmt: skip


def test_ca_m07_16_the_search_finds_only_published_entries(editor, topic):
    first = _entry(editor, topic, "Quan es paga la quota?")
    second = _entry(editor, topic, "Com canvio el compte?", "La Quota es domicilia al banc.")
    _entry(editor, topic, "Quota d'una persona de fora?", published=False)
    _entry(editor, topic, "On és el local?")
    assert faq.search("quota") == [first, second]
    assert faq.search("QUÒTA") == [first, second]  # sense majúscules ni accents


def test_ca_m07_16_without_results_the_list_is_empty(editor, topic):
    _entry(editor, topic, "Quan es paga la quota?")
    assert faq.search("immersió nocturna") == []
    assert faq.search("   ") == []


def test_published_entries_follow_the_order_and_unpublishing_hides_them(editor, topic):
    other = faq.save_topic(None, actor=editor, name="Cursos", order=1)
    late = _entry(editor, other, "Com m'inscric a un curs?")
    early = faq.save_entry(None, actor=editor, topic=topic, question="Quant val la quota?",
                           answer="Inventat.", order=0, published=True)  # fmt: skip
    assert list(faq.published_entries()) == [early, late]
    assert list(faq.published_entries(other)) == [late]
    faq.save_entry(late, actor=editor, published=False)
    assert list(faq.published_entries()) == [early]


def test_a_new_entry_is_not_published_by_default(editor, topic):
    entry = faq.save_entry(None, actor=editor, topic=topic, question="P?", answer="R.")
    assert not entry.published and faq.search("P") == []


def test_a_rejected_change_is_not_kept(editor, topic):
    entry = _entry(editor, topic, "Quan es paga la quota?")
    with pytest.raises(ValidationError):
        faq.save_entry(entry, actor=editor, question="")
    entry = faq.save_entry(entry, actor=editor, answer="Una altra.")
    assert entry.question == "Quan es paga la quota?"
    with pytest.raises(ValidationError):
        faq.save_topic(None, actor=editor, name="Quotes")  # el nom és únic


def test_the_board_can_edit_the_help_and_a_role_without_wp4_cannot(editor, topic, make_admin):  # noqa: F811
    _entry(make_admin(R.BOARD), topic, "Pregunta de la junta?")
    secretary = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        faq.save_topic(None, actor=secretary, name="Llicències")
    with pytest.raises(Http404):
        _entry(secretary, topic, "No hauria de quedar?")
    assert FaqEntry.objects.count() == 1 and FaqTopic.objects.count() == 1


def test_ca_m07_16_the_public_help_searches_and_links_the_contact(client, editor, topic):
    from apps.core.models import Setting

    _entry(editor, topic, "Quan es paga la quota?")
    _entry(editor, topic, "Esborrany de quota?", published=False)
    page = client.get("/ajuda/").content.decode()
    assert "Quan es paga la quota?" in page and "Esborrany" not in page
    found = client.get("/ajuda/", {"q": "quota"}).content.decode()
    assert "Quan es paga la quota?" in found and "Esborrany" not in found
    empty = client.get("/ajuda/", {"q": "immersió nocturna"}).content.decode()
    assert "No hem trobat cap resposta" in empty and 'href="/contacte/"' not in empty
    Setting.objects.filter(key="website.contact_enabled").update(initial_value=True)
    empty = client.get("/ajuda/", {"q": "immersió nocturna"}).content.decode()
    assert 'href="/contacte/"' in empty


def test_rn_m07_10_the_answer_is_escaped(client, editor, topic):
    _entry(editor, topic, "Una <b>pregunta</b>?", "<script>alert(1)</script>")
    page = client.get("/ajuda/").content.decode()
    assert "<script>alert(1)" not in page and "&lt;script&gt;" in page
