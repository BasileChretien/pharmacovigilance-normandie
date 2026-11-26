"""Tests for tools/design/make_signal.py (home-page map: towns of Normandy linked to the CRPV)."""

import make_signal as ms

DEPS = [
    {
        "code": "14",
        "crpv": "Caen",
        "contours": [[[-1.0, 49.0], [0.0, 49.0], [0.0, 49.5], [-1.0, 49.0]]],
    },
    {
        "code": "76",
        "crpv": "Rouen",
        "contours": [[[0.0, 49.5], [1.5, 49.5], [1.5, 50.0], [0.0, 49.5]]],
    },
]


def town(nom, dep, pop, lon, lat):
    return {"nom": nom, "departement": dep, "population": pop, "lon": lon, "lat": lat}


TOWNS = [
    town("Rouen", "76", 117000, 1.09, 49.44),
    town("Caen", "14", 109000, -0.37, 49.18),
    town("Le Havre", "76", 166000, 0.13, 49.49),
    town("Sotteville", "76", 29000, 1.091, 49.441),  # on top of Rouen
    town("Lisieux", "14", 19600, 0.24, 49.15),
    town("Bourg", "14", 6000, -0.8, 49.3),
]


def test_projection_fits_the_frame_with_north_up():
    project = ms.make_projection(DEPS, width=560, height=440, margin=20)
    xs, ys = zip(*(project(lon, lat) for lon, lat in [(-1.0, 49.0), (1.5, 50.0)]))
    assert all(20 - 1e-6 <= x <= 540 + 1e-6 for x in xs)
    assert all(20 - 1e-6 <= y <= 420 + 1e-6 for y in ys)
    assert project(0, 50.0)[1] < project(0, 49.0)[1]  # further north is higher up


def test_bigger_towns_get_bigger_dots_with_a_floor():
    assert ms.radius(166000) > ms.radius(29000) > ms.radius(6000)
    assert ms.radius(10) == ms.R_MIN


def test_a_town_hidden_under_a_bigger_one_is_dropped_and_hubs_are_kept():
    project = ms.make_projection(DEPS, width=560, height=440, margin=20)
    names = [t["nom"] for t in ms.select_towns(TOWNS, project)]
    assert "Sotteville" not in names
    assert {"Rouen", "Caen", "Le Havre", "Lisieux", "Bourg"} <= set(names)


def test_each_linked_town_goes_to_the_centre_of_its_department():
    project = ms.make_projection(DEPS, width=560, height=440, margin=20)
    links = ms.links(ms.select_towns(TOWNS, project))
    pairs = {(t["nom"], hub["nom"]) for t, hub in links}
    assert ("Le Havre", "Rouen") in pairs
    assert ("Lisieux", "Caen") in pairs
    assert not any(
        t["nom"] in ("Rouen", "Caen") for t, _ in links
    )  # hubs are not linked to themselves
    assert not any(t["nom"] == "Bourg" for t, _ in links)  # small towns are dots only


def test_svg_is_decorative_deterministic_and_animates_each_link():
    data = {"departements": DEPS, "villes": TOWNS}
    first, second = ms.svg(data), ms.svg(data)
    assert first == second
    assert 'aria-hidden="true"' in first
    project = ms.make_projection(
        DEPS, width=ms.WIDTH, height=ms.HEIGHT, margin=ms.MARGIN
    )
    n_links = len(ms.links(ms.select_towns(TOWNS, project)))
    assert first.count('class="signal-flux"') == n_links
