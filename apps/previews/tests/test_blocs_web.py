"""T-M07-19: les plantilles dels blocs de la web segueixen el contracte amb el renderitzador del 07
(design-system §6.27): reben `block`, escapen el text cru i les variants són classes tancades."""

from django.template.loader import render_to_string


def _render(block):
    return render_to_string(f"website/blocs/{block['kind']}.html", {"block": block, "page": None})


def test_raw_text_is_escaped_in_every_text_block():
    raw = "<script>alert(1)</script>"
    for block in (
        {"kind": "heading", "text": raw, "level": 2},
        {"kind": "text", "title": raw, "body": raw},
        {"kind": "quote", "text": raw, "attribution": raw},
        {"kind": "list", "title": raw, "items": [raw]},
        {"kind": "disclosure", "question": raw, "answer": raw},
        {"kind": "callout", "title": raw, "body": raw},
    ):
        html = _render(block)
        assert "<script>" not in html, block["kind"]
        assert "&lt;script&gt;" in html, block["kind"]


def test_variants_become_closed_classes():
    assert "<h3" in _render({"kind": "heading", "text": "T", "level": 3})
    assert "<h2" in _render({"kind": "heading", "text": "T", "level": 2})
    assert "<ol" in _render({"kind": "list", "items": ["a"], "style": "numbers"})
    assert "es-comprovacio" in _render({"kind": "list", "items": ["a"], "style": "checks"})
    assert "bloc-fons-marine" in _render({"kind": "quote", "text": "T", "background": "marine"})
    assert "bloc-fons-none" in _render({"kind": "quote", "text": "T"})
    assert "avis-avis" in _render({"kind": "callout", "body": "T", "tone": "warning"})
    assert "avis-info" in _render({"kind": "callout", "body": "T"})
    assert "bloc-amplada-normal" in _render({"kind": "text", "body": "T"})


def test_a_section_paints_each_inner_block_with_its_template():
    html = _render(
        {
            "kind": "section",
            "columns": [
                [{"kind": "heading", "text": "<b>Un</b>", "level": 3}],
                [{"kind": "divider"}],
            ],
        }
    )
    assert "bloc-columnes-2" in html
    assert '<h3 class="bloc bloc-heading">&lt;b&gt;Un&lt;/b&gt;</h3>' in html
    assert "bloc-divider" in html


def test_action_blocks_escape_the_label_and_mark_one_primary():
    button = {"kind": "button", "label": "<i>x</i>", "target": "/activitats/", "style": "primary"}
    html = _render(button)
    assert "&lt;i&gt;x&lt;/i&gt;" in html and "boto-principal" in html
    assert "boto-principal" not in _render({"kind": "button", "label": "x", "target": "/"})
    assert "/fer-se-soci/" in _render({"kind": "join_cta", "title": "T", "body": "B"})
