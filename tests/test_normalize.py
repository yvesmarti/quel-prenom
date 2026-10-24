"""Règles de normalisation et champs dérivés (sans besoin des données)."""
import pytest

import normalize
from build_db import sexe_usage


@pytest.mark.parametrize("insee, attendu", [
    ("LÉA", "lea"), ("LEA", "lea"), ("CHLÖÉ", "chloe"), ("FRANÇOIS", "francois"),
    ("MAËLYS", "maelys"), ("ÆLIS", "aelis"), ("MAŸLIS", "maylis"), ("M'HAMED", "m'hamed"),
])
def test_normaliser(insee, attendu):
    assert normalize.normaliser(insee) == attendu


@pytest.mark.parametrize("insee, attendu", [
    ("LÉA", "Léa"), ("MARIE-CLAIRE", "Marie-Claire"), ("M'HAMED", "M'Hamed"),
    ("O'BRYAN", "O'Bryan"), ("WILLIAM'S", "William's"), ("GWENC'HLAN", "Gwenc'hlan"),
    ("M HAMED", "M Hamed"), ("JEAN-N'GUESSAN", "Jean-N'Guessan"),
])
def test_affichage(insee, attendu):
    assert normalize.affichage(insee) == attendu


def test_identifiant_distingue_les_accents():
    assert normalize.identifiant("LÉA") != normalize.identifiant("LEA")


def test_champs_derives():
    assert normalize.nb_lettres("MARIE-CLAIRE") == 11
    assert normalize.nb_lettres("M'HAMED") == 6
    assert normalize.nb_lettres("ÆLIS") == 4
    assert normalize.a_accent("ÆLIS") and normalize.a_accent("LÉA")
    assert not normalize.a_accent("M'HAMED")
    assert normalize.est_compose("MARIE-CLAIRE") and not normalize.est_compose("M HAMED")
    assert normalize.cle_lot("LÉA") == "le"
    assert normalize.cle_lot("M'RICK") == "mr"


@pytest.mark.parametrize("f, m, attendu", [
    (100, 0, "F"), (0, 50, "M"), (90, 10, "X"), (91, 9, "F"), (5, 95, "M"), (50, 50, "X"),
])
def test_sexe_usage(f, m, attendu):
    assert sexe_usage(f, m) == attendu
