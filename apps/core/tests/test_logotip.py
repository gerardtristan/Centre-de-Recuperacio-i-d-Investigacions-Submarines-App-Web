"""Logotip (T-DX-51): la base i la pàgina d'error porten les versions ajustades, diferides i amb un
PNG de reserva; cap dels originals de assets/marca (de 344 i 501 KB) no surt a cap pàgina."""

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory


@pytest.mark.django_db
@pytest.mark.parametrize("template", ["base.html", "500.html"])
def test_logo_markup(template):
    request = RequestFactory().get("/")
    html = render_to_string(template, request=request if template == "base.html" else None)
    assert "marca/CRIS_" not in html
    pictures = re.findall(r'<picture class="logo-(clar|fosc)">(.*?)</picture>', html, re.S)
    assert [kind for kind, _ in pictures] == ["clar", "fosc"]
    for kind, body in pictures:
        assert re.findall(r'type="(image/\w+)"', body) == ["image/avif", "image/webp"]
        assert f"img/marca/cris-{kind}-192.png" in body
        assert 'loading="lazy"' in body and 'width="192" height="205"' in body
