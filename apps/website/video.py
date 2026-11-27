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
from django.utils.translation import gettext as _

from apps.core import business_settings

from . import media

ENABLED = "website.youtube_enabled"
NOTICE = "website.youtube_notice"
THUMBNAIL_URL = "https://i.ytimg.com/vi/{}/hqdefault.jpg"
EMBED_URL = "https://www.youtube-nocookie.com/embed/{}?autoplay=1"
MAX_BYTES = 2 * 1024 * 1024  # límit tècnic: una miniatura no fa més de 2 MB


def _download(youtube_id: str) -> bytes | None:
    """`youtube_id` ja és validat pel catàleg (11 caràcters segurs): l'adreça és sempre aquesta."""
    try:
        with urllib.request.urlopen(THUMBNAIL_URL.format(youtube_id), timeout=5) as response:  # noqa: S310
            return response.read(MAX_BYTES)
    except (OSError, ValueError):
        return None


def with_thumbnail(block: dict, actor) -> dict:
    if block.get("kind") != "video" or block.get("source") != "youtube":
        return block
    if not block.get("youtube_id") or block.get("thumbnail") or not business_settings.get(ENABLED):
        return block
    content = _download(block["youtube_id"])
    if not content:
        return block  # sense miniatura: el bloc es desa igual
    try:
        asset = media.store_image(
            content, actor=actor, alt_text=block.get("title") or _("Miniatura del vídeo"),
            shows_people=True, author=_("YouTube"), licence_note=_("Miniatura del vídeo"),
        )  # fmt: skip
    except ValidationError:
        return block
    return {**block, "thumbnail": str(asset.key)}


def youtube_context(block: dict) -> dict:
    return {"embed_url": EMBED_URL.format(block.get("youtube_id", "")),
            "notice": business_settings.get(NOTICE)}  # fmt: skip
