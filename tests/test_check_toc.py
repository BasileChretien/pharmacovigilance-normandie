"""Tests for tools/checks/check_toc.py (every section heading is listed in "Sur cette page")."""

import check_toc as ct

PAGE = """
<nav id="TOC" role="doc-toc"><h2 id="toc-title">Sur cette page</h2>
<ul><li><a href="#pour-les-patients">Pour les patients</a>
<ul><li><a href="#que-faire">Que faire ?</a></li></ul></li></ul></nav>
<main class="content" id="quarto-document-content">
<section id="pour-les-patients" class="level2"><h2>Pour les patients</h2>
<section id="que-faire" class="level3"><h3>Que faire ?</h3></section>
<section id="quels-risques" class="level3"><h3>Quels risques ?</h3></section>
</section>
<div class="carte membre"><section id="prenom-nom" class="level2"><h2>Prénom Nom</h2></section></div>
</main>
"""


def test_listed_headings_pass_and_missing_ones_are_reported():
    assert ct.missing_from_toc(PAGE) == ["quels-risques"]


def test_headings_in_member_cards_are_not_sections():
    assert "prenom-nom" not in ct.missing_from_toc(PAGE)


def test_page_without_toc_is_not_checked():
    assert (
        ct.missing_from_toc("<main><section id='a'><h2>A</h2></section></main>") == []
    )


def test_heading_id_on_the_heading_itself_is_found():
    html = (
        '<nav id="TOC"><ul><li><a href="#b">B</a></li></ul></nav>'
        '<main><h2 id="a">A</h2><h2 id="b">B</h2></main>'
    )
    assert ct.missing_from_toc(html) == ["a"]
