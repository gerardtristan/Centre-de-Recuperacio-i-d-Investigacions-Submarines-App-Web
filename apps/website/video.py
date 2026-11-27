"""Bloc de vídeo de YouTube (T-M07-23, decisió 106; RN-M07-09 amb l'excepció de la 106; CA-M07-25).

- `with_thumbnail(block, actor)`: amb `website.youtube_enabled` encès i sense miniatura, el
  servidor la baixa en desar el bloc i la desa a la biblioteca de la web (mateixa validació i
  neteja que una pujada). Com que no se sap si s'hi veuen persones, es desa amb «s'hi veuen
  persones» i sense consentiment: no es pot publicar fins que algú amb WP3 ho revisa (P-685).
- `youtube_context(block)`: l'adreça de `youtube-nocookie.com` que obre el clic i el text de
  l'avís (`website.youtube_notice`, P-574). Abans del clic, el navegador no demana res a Google.
"""

import urllib.request

from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import business_settings

from . import blocks as catalog
from . import media

ENABLED = "website.youtube_enabled"
NOTICE = "website.youtube_notice"
THUMBNAIL_URL = "https://i.ytimg.com/vi/{}/hqdefault.jpg"
EMBED_URL = "https://www.youtube-nocookie.com/embed/{}?autoplay=1"
MAX_BYTES = 2 * 1024 * 1024  # límit tècnic: una miniatura no fa més de 2 MB


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Cap redirecció: la baixada només va a l'adreça de la miniatura."""

    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def _download(youtube_id: str) -> bytes | None:
    """Només a `i.ytimg.com`, sense redireccions i com a màxim `MAX_BYTES` (si arriba al límit, es
    descarta: seria una imatge tallada o una altra cosa)."""
    try:
        with _opener.open(THUMBNAIL_URL.format(youtube_id), timeout=5) as response:
            content = response.read(MAX_BYTES + 1)
    except (OSError, ValueError):
        return None
    return content if len(content) <= MAX_BYTES else None


def with_thumbnail(block: dict, actor, previous: dict | None = None) -> dict:
    """`previous`: el bloc tal com era; si és el mateix vídeo i ja tenia miniatura, es conserva
    (el formulari no la porta, perquè encara no es pot publicar)."""
    if block.get("kind") != "video" or block.get("source") != "youtube":
        return block
    youtube_id = block.get("youtube_id") or ""
    previous = previous or {}
    if (
        not block.get("thumbnail")
        and previous.get("thumbnail")
        and (previous.get("youtube_id") == youtube_id)
    ):
        return {**block, "thumbnail": previous["thumbnail"]}
    if not catalog.YOUTUBE_ID.fullmatch(youtube_id) or block.get("thumbnail"):
        return block
    if not business_settings.get(ENABLED):
        return block
    content = _download(youtube_id)
    if not content:
        return block  # sense miniatura: el bloc es desa igual
    try:
        asset = media.store_image(
            content, actor=actor, alt_text=block.get("title") or _("Miniatura del vídeo"),
            shows_people=True, author=_("YouTube"), licence_note=_("Miniatura del vídeo"),
        )  # fmt: skip
    except (ValidationError, Http404):  # sense WP3, el bloc es desa sense miniatura
        return block
    return {**block, "thumbnail": str(asset.key)}


def youtube_context(block: dict) -> dict:
    return {"embed_url": EMBED_URL.format(block.get("youtube_id", "")),
            "notice": business_settings.get(NOTICE)}  # fmt: skip
