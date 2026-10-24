"""Statistiques de la phase 2 : outils de calcul, définitions des tendances, fichiers publiés."""
import json

import pytest

import config
import normalize
import stats

T = config.TENDANCES


# --- Outils de calcul (sans données) ---------------------------------------

def test_moyenne_compte_les_annees_absentes_comme_zero():
    assert stats.moyenne({2020: 10, 2022: 20}, 2020, 2023) == 7.5


def test_moyenne_mobile_centree_et_tronquee_aux_bords():
    assert stats.moyenne_mobile([0, 3, 6, 9], 3) == [1.5, 3, 6, 7.5]


def test_sommets_deux_vagues():
    y = [5, 4, 2, 0, 1, 3, 5, 4]
    assert stats.sommets(y, 2) == [0, 6]


def test_sommets_ignore_les_petites_bosses():
    assert stats.sommets([5, 4, 4.5, 3, 1], 2) == [0]


def test_sommet_en_bord_mesure_cote_interieur():
    # Vague toujours en cours à la fin : le côté droit (ouvert) est ignoré.
    assert stats.sommets([3, 1, 0, 2, 4, 3.9], 2) == [0, 4]


def serie(valeurs, debut=1946):
    """Série artificielle pour tester les règles : [(annee, valeur, rang)] avec rang = 1."""
    return [(debut + i, v, 1) for i, v in enumerate(valeurs) if v]


def test_indicateurs_progression_et_evolution():
    annees = list(range(1946, 2026))
    valeurs = [100 if a >= 2021 else 30 if 2011 <= a <= 2015 else 20 for a in annees]
    denom = {a: 1000 for a in annees}
    ind = stats.indicateurs(serie(valeurs), {a: 100 for a in annees}, denom, 1946, 2025)
    assert "progression" in ind["tendances"]
    assert "declin" not in ind["tendances"]
    # [2023..2025] = 100/an contre [2018..2020] = 20/an, à naissances constantes : fréquence × 5.
    assert ind["evolutions"]["5"]["variation"] == pytest.approx(4.0)
    assert ind["record_effectif"] == [2021, 100]


def test_indicateurs_emergent():
    annees = list(range(1946, 2026))
    valeurs = [40 if a >= 2015 else 0 for a in annees]
    ind = stats.indicateurs(serie(valeurs), {a: 100 for a in annees}, {a: 1000 for a in annees}, 1946, 2025)
    assert "emergent" in ind["tendances"]
    assert ind["premiere_annee"] == 2015


def test_pas_d_evolution_sous_le_seuil():
    annees = list(range(1946, 2026))
    valeurs = [5] * len(annees)
    ind = stats.indicateurs(serie(valeurs), {a: 100 for a in annees}, {a: 1000 for a in annees}, 1946, 2025)
    assert "variation" not in ind["evolutions"]["5"]


# --- Données réelles ---------------------------------------------------------

donnees = pytest.mark.skipif(not config.BASE.exists(), reason="base absente : lancer pipeline/run_all.py")


@pytest.fixture(scope="module")
def con():
    import duckdb
    c = duckdb.connect(str(config.BASE), read_only=True)
    yield c
    c.close()


def lire(chemin):
    return json.loads((config.DOSSIER_PUBLIC / chemin).read_text(encoding="utf-8"))


@donnees
def test_denominateurs(con):
    lignes = con.execute("SELECT annee, champ FROM denominateur").fetchall()
    assert min(a for a, _ in lignes) == config.ANNEE_DEBUT_FREQUENCES
    assert all((c == "france") == (a >= config.ANNEE_DEBUT_FRANCE_ENTIERE) for a, c in lignes)
    assert con.execute("SELECT count(DISTINCT annee) FROM denominateur").fetchone()[0] == 2025 - 1946 + 1


@donnees
def test_couverture_avant_1946_incomplete(con):
    """Constat documenté : le fichier ne recense qu'une partie des naissances avant 1946."""
    assert con.execute("SELECT max(ratio) FROM couverture WHERE annee < 1946").fetchone()[0] < 0.96
    assert con.execute("SELECT min(ratio) FROM couverture WHERE annee < 1946").fetchone()[0] < 0.5
    assert con.execute("SELECT min(ratio) FROM couverture WHERE annee >= 1994").fetchone()[0] > 0.85


@donnees
def test_tendances_respectent_leurs_definitions(con):
    Y = config.MILLESIME
    for cat, pid, sexe, details in con.execute("SELECT categorie, prenom_id, sexe, details FROM tendance").fetchall():
        d = json.loads(details)
        if cat == "progression":
            assert d["effectif_recent"] >= T["progression_min"] and d["ratio_frequence"] >= T["progression_facteur"]
        elif cat == "declin":
            assert d["effectif_ancien"] >= T["declin_min_avant"] and d.get("ratio_frequence", 0) <= T["declin_facteur"]
        elif cat == "emergent":
            premiere = con.execute(f"""SELECT min(annee) FROM statistique WHERE niveau='FRANCE'
                AND prenom_id = ? AND sexe = ?""", [pid, sexe]).fetchone()[0]
            assert premiere > Y - T["emergent_depuis"] and d["effectif_recent"] >= T["emergent_min"]
        elif cat == "retour":
            assert d["sommet_ancien"][0] < T["retour_avant"] and d["sommet_recent"][0] > Y - T["retour_recent"]


@donnees
def test_cas_connus(con):
    """Quelques prénoms dont l'histoire est bien connue (vérifiable dans les données brutes)."""
    cats = lambda p, s: {c for (c,) in con.execute(
        "SELECT categorie FROM tendance WHERE prenom_id = ? AND sexe = ?", [p, s]).fetchall()}
    assert "retour" in cats("louise", "F")
    assert "devenu_rare" in cats("sylvie", "F")


@donnees
def test_classement_national_conforme_aux_rangs_officiels(con):
    for annee in (1900, 1960, 2025):
        fichier = lire(f"classements/france/{annee}.json")
        for sexe in ("F", "M"):
            officiel = con.execute("""SELECT prenom_id, valeur_arrondie FROM statistique WHERE niveau='FRANCE'
                AND annee = ? AND sexe = ? AND rang_officiel <= ? ORDER BY rang_officiel""",
                                   [annee, sexe, config.CLASSEMENT_NATIONAL_TOP]).fetchall()
            assert [tuple(x) for x in fichier[sexe]["top"]] == officiel
            assert len(fichier[sexe]["fin"]) == config.CLASSEMENT_NATIONAL_FIN
            assert fichier[sexe]["fin"][-1][2] == fichier[sexe]["nb_publies"]


@donnees
def test_classement_territorial_conforme(con):
    zone = lire("classements/zones/DEP-2A.json")
    officiel = con.execute("""SELECT prenom_id, valeur_arrondie FROM statistique WHERE niveau='DEP'
        AND territoire='2A' AND annee=2000 AND sexe='M' ORDER BY rang_officiel LIMIT ?""",
                           [config.CLASSEMENT_TERRITORIAL_TOP["DEP"]]).fetchall()
    assert [tuple(x) for x in zone["annees"]["2000"]["M"]] == officiel


@donnees
def test_geo_coherent_avec_la_base(con):
    lot = lire(f"geo/prenoms/g_{normalize.cle_lot('LÉA', 3)}.json")["prenoms"]["léa"]
    total = sum(v for _, _, v in lot["F"]["DEP"])
    assert total == con.execute("""SELECT sum(valeur_arrondie) FROM statistique
        WHERE niveau='DEP' AND prenom_id='léa' AND sexe='F'""").fetchone()[0]


@donnees
def test_cartes_couvrent_toutes_les_zones(con):
    zones = lire("geo/zones.json")
    for niveau, fichier in (("REG", "regions"), ("DEP", "departements")):
        codes = {c for (c,) in con.execute(
            "SELECT DISTINCT territoire FROM statistique WHERE niveau = ?", [niveau]).fetchall()}
        carte = {f["properties"]["code"] for f in lire(f"geo/{fichier}.json")["features"]}
        assert codes == carte == set(zones[niveau])


@donnees
def test_meta_naissances(con):
    meta = lire("meta.json")
    assert str(config.ANNEE_DEBUT_FREQUENCES) in meta["naissances"]
    assert "1945" not in meta["naissances"]
    assert {s["id"] for s in meta["sources"]} == {s["id"] for s in config.SOURCES}


@donnees
def test_tous_les_lots_geographiques_existent(con):
    """Chaque prénom présent en région ou département figure dans son fichier g_<lot>.json."""
    attendus = {}
    for pid, graphie in con.execute("""SELECT DISTINCT g.prenom_id, p.graphie_insee FROM geo_decennie g
            JOIN prenom p ON p.id = g.prenom_id""").fetchall():
        attendus.setdefault(normalize.cle_lot(graphie, 3), set()).add(pid)
    for lot, ids in attendus.items():
        assert set(lire(f"geo/prenoms/g_{lot}.json")["prenoms"]) == ids
