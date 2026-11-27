"""SortableJS servit des del VPS, sense CDN (decisions 046 i 106)."""

from django.contrib.staticfiles import finders


def test_sortablejs_es_als_estatics():
    path = finders.find("vendor/sortablejs/Sortable.min.js")
    assert path
    with open(path, encoding="utf-8") as f:
        assert f.readline().startswith("/*! Sortable 1.15.7 - MIT")
