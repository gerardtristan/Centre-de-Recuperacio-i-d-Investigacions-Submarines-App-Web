"""La dependència de les pujades hi és (RN-M07-19, decisió 106)."""

import io

from PIL import Image


def test_pillow_torna_a_codificar_sense_exif():
    exif = Image.Exif()
    exif[0x010F] = "Fabricant inventat"
    src = io.BytesIO()
    Image.new("RGB", (4, 4)).save(src, "JPEG", exif=exif)
    assert Image.open(io.BytesIO(src.getvalue())).getexif()
    out = io.BytesIO()
    Image.open(io.BytesIO(src.getvalue())).save(out, "JPEG")
    assert not Image.open(io.BytesIO(out.getvalue())).getexif()
