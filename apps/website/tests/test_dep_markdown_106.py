"""La dependència del Markdown restringit hi és (RN-M07-10, decisió 106)."""

from markdown_it import MarkdownIt


def test_markdown_it_converteix_amb_l_html_desactivat():
    md = MarkdownIt("zero").enable(["emphasis"])
    assert md.render("**hola** <b>x</b>") == "<p><strong>hola</strong> &lt;b&gt;x&lt;/b&gt;</p>\n"
