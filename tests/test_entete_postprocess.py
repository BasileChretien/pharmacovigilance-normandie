"""Tests for tools/build/entete_postprocess.py (notice after the fixed header, skip link first)."""

import entete_postprocess as ep
import pytest

# The top of a page as Quarto 1.10 writes it (_site/index.html, 29/11/2026).
PAGE = """<body class="nav-fixed quarto-light">
<div id="quarto-search-results"></div>
  <header id="quarto-header" class="headroom fixed-top">
    <nav class="navbar navbar-expand-xl " data-bs-theme="dark">
      <div class="navbar-container container-fluid">
      <a class="nav-link" href="./declarer.html">Déclarer</a>
      </div> <!-- /container-fluid -->
    </nav>
  <div id="quarto-announcement" data-announcement-id="310808e0" class="alert alert-warning hidden"><div class="quarto-announcement-content">
<p><strong>Prototype non officiel</strong> : brouillons. <a href="mailto:x@example.org" class="signaler-correction">Signaler une correction</a></p>
</div></div>
</header>
<!-- content -->
<div id="quarto-content" class="quarto-container page-columns page-rows-contents page-layout-article page-navbar">
<a class="lien-evitement" href="#quarto-document-content">Aller au contenu</a>

<header id="title-block-header" class="quarto-title-block default page-columns page-full">
</header>
<main class="content" id="quarto-document-content">
</main>
</div>
</body>"""


def fixed_header(html: str) -> str:
    start = html.index('<header id="quarto-header"')
    return html[start : html.index("</header>", start)]


def test_the_notice_leaves_the_fixed_header():
    out = ep.patch(PAGE)
    assert "quarto-announcement" not in fixed_header(out)
    assert "</nav>" in fixed_header(out)


def test_the_notice_comes_right_after_the_header_before_the_content():
    out = ep.patch(PAGE)
    after = out[out.index("</header>") :]
    assert after.index('id="quarto-announcement"') < after.index("<!-- content -->")
    assert out.index('id="quarto-announcement"') < out.index('id="title-block-header"')


def test_the_notice_keeps_its_text_link_and_classes():
    out = ep.patch(PAGE)
    assert 'class="alert alert-warning"' in out
    assert 'data-announcement-id="310808e0"' in out
    assert 'class="signaler-correction">Signaler une correction</a>' in out
    assert out.count("<div") == PAGE.count("<div")
    assert out.count("</div>") == PAGE.count("</div>")


def test_the_notice_shows_without_waiting_for_quartos_script():
    out = ep.patch(PAGE)
    notice = out[out.index('<div id="quarto-announcement"') :]
    assert "hidden" not in notice[: notice.index(">")]


def test_the_notice_is_a_named_region():
    out = ep.patch(PAGE)
    assert '<div id="quarto-announcement" role="region" aria-label="Avertissement" data-announcement-id' in out


def test_the_skip_link_comes_before_the_navigation():
    out = ep.patch(PAGE)
    link = out.index('class="lien-evitement"')
    assert link < out.index('<header id="quarto-header"') < out.index("Déclarer")
    assert out.count('class="lien-evitement"') == 1
    assert '<div id="quarto-content" class="quarto-container page-columns page-rows-contents page-layout-article page-navbar">\n\n<header id="title-block-header"' in out


def test_the_skip_link_sits_on_its_own_line_before_the_header():
    out = ep.patch(PAGE)
    assert '\n<a class="lien-evitement" href="#quarto-document-content">Aller au contenu</a>\n  <header id="quarto-header"' in out


def test_patching_twice_changes_nothing():
    once = ep.patch(PAGE)
    assert ep.patch(once) == once


def test_a_page_without_notice_or_skip_link_is_unchanged():
    page = PAGE.replace("quarto-announcement", "autre-chose").replace("lien-evitement", "autre")
    assert ep.patch(page) == page


def test_a_notice_that_is_not_last_in_the_header_stops_the_build():
    page = PAGE.replace("</div></div>\n</header>", "</div></div>\n<span>en plus</span>\n</header>")
    with pytest.raises(ValueError, match="dernier élément"):
        ep.patch(page)


def test_a_page_with_a_notice_but_no_fixed_header_stops_the_build():
    page = PAGE.replace('id="quarto-header"', 'id="autre"')
    with pytest.raises(ValueError, match="introuvable"):
        ep.patch(page)


def test_two_skip_links_stop_the_build():
    page = PAGE.replace("<main", '<a class="lien-evitement" href="#x">Aller</a>\n<main')
    with pytest.raises(ValueError, match="2 liens"):
        ep.patch(page)


def test_main_patches_the_files_and_reports(tmp_path, capsys):
    page = tmp_path / "index.html"
    page.write_text(PAGE, encoding="utf-8")
    assert ep.main([str(page)]) == 0
    assert "quarto-announcement" not in fixed_header(page.read_text(encoding="utf-8"))
    assert "1 page(s)" in capsys.readouterr().out


def test_main_fails_on_unexpected_markup(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(PAGE.replace('id="quarto-header"', 'id="autre"'), encoding="utf-8")
    assert ep.main([str(page)]) == 1
