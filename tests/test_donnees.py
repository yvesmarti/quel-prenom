"""Intégrité de la base et des fichiers publiés.

Nécessite d'avoir lancé le pipeline (python pipeline/run_all.py) ; sinon ces tests sont ignorés.
"""
import json
from collections import defaultdict

import pytest

import config
import normalize
from build_db import sexe_usage

pytestmark = pytest.mark.skipif(not config.BASE.exists(), reason="base absente : lancer pipeline/run_all.py")


@pytest.fixture(scope="module")
def con():
    import duckdb
    c = duckdb.connect(str(config.BASE), read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def index():
    data = json.loads((config.DOSSIER_PUBLIC / "index.v1.json").read_text(encoding="utf-8"))
    return [dict(zip(data["colonnes"], ligne)) for ligne in data["lignes"]]


def val(con, sql):
    return con.execute(sql).fetchone()[0]


def test_toutes_les_lignes_brutes_sont_reliees(con):
    assert val(con, "SELECT count(*) FROM statistique") == val(con, "SELECT count(*) FROM raw_prenoms")
    assert val(con, "SELECT count(*) FROM statistique s LEFT JOIN prenom p ON p.id = s.prenom_id WHERE p.id IS NULL") == 0


def test_identifiants_uniques(con):
    assert val(con, "SELECT count(*) - count(DISTINCT id) FROM prenom") == 0
    assert val(con, "SELECT count(*) - count(DISTINCT graphie_insee) FROM prenom") == 0


def test_graphies_accentuees_non_fusionnees(con):
    ids = {i for (i,) in con.execute("SELECT id FROM prenom WHERE norm = 'lea'").fetchall()}
    assert {"léa", "lea"} <= ids


def test_rangs_officiels_conserves(con):
    """Les rangs publiés sont exactement ceux du fichier Insee (aucun recalcul)."""
    assert val(con, """SELECT count(*) FROM statistique s
        JOIN prenom p ON p.id = s.prenom_id
        JOIN raw_prenoms r ON r.prenom = p.graphie_insee AND r.periode::INTEGER = s.annee
         AND r.niveau_geographique = s.niveau AND r.geographie = s.territoire
         AND (CASE r.sexe WHEN '2' THEN 'F' ELSE 'M' END) = s.sexe
        WHERE r.rang <> s.rang_officiel OR r.valeur <> s.valeur_arrondie""") == 0


def test_effectifs_multiples_de_5(con):
    assert val(con, "SELECT count(*) FROM statistique WHERE valeur_arrondie % 5 <> 0 OR valeur_arrondie <= 0") == 0


def test_trois_niveaux_geographiques_importes(con):
    niveaux = {n for (n,) in con.execute("SELECT DISTINCT niveau FROM statistique").fetchall()}
    assert niveaux == {"FRANCE", "REG", "DEP"}


def test_index_complet_et_coherent(con, index):
    assert len(index) == val(con, "SELECT count(*) FROM prenom")
    for p in index:
        assert p["norm"] == normalize.normaliser(p["id"])
        assert p["sexe"] == sexe_usage(p["total_f"], p["total_m"])
        assert p["premiere_annee"] <= p["derniere_annee"]


def test_index_trie_par_popularite(index):
    totaux = [p["total_f"] + p["total_m"] for p in index]
    assert totaux == sorted(totaux, reverse=True)


def test_lots_de_details(index):
    """Chaque prénom de l'index a sa série dans son lot, et les totaux concordent."""
    par_lot = defaultdict(list)
    for p in index:
        par_lot[p["lot"]].append(p)
    for lot, prenoms in par_lot.items():
        contenu = json.loads((config.DOSSIER_PUBLIC / "prenoms" / f"{lot}.json").read_text(encoding="utf-8"))
        assert len(contenu["prenoms"]) == len(prenoms)
        for p in prenoms:
            series = contenu["prenoms"][p["id"]]
            assert sum(v for _, v, _ in series.get("F", [])) == p["total_f"]
            assert sum(v for _, v, _ in series.get("M", [])) == p["total_m"]
            for points in (series.get("F", []), series.get("M", [])):
                annees = [a for a, _, _ in points]
                assert annees == sorted(set(annees))


def test_meta(con):
    meta = json.loads((config.DOSSIER_PUBLIC / "meta.json").read_text(encoding="utf-8"))
    assert meta["annee_min"] == 1900 and meta["annee_max"] == config.MILLESIME
    assert meta["source"]["licence"] == config.LICENCE_INSEE


def test_profils_de_suggestion(index):
    """Les profils sont cohérents avec l'index et assez variés pour suggérer."""
    data = json.loads((config.DOSSIER_PUBLIC / "profils.v1.json").read_text(encoding="utf-8"))
    profils = [dict(zip(data["colonnes"], ligne)) for ligne in data["lignes"]]
    ids = {p["id"]: p for p in index}
    assert 5000 < len(profils) < 20000
    assert len({p["id"] for p in profils}) == len(profils)
    for p in profils:
        base = ids[p["id"]]
        assert p["sexe"] == base["sexe"] and p["lettres"] == base["lettres"]
        assert p["syllabes"] >= 1 and p["rec_f"] >= 0 and p["rec_m"] >= 0
    # Chaque sexe et chaque famille d'origine doivent être représentés.
    assert {"F", "M"} <= {p["sexe"] for p in profils}
    familles = {f for p in profils for f in p["orig"].split("|") if f}
    assert set(config.GROUPES_ORIGINE) <= familles
