"""Enrichissement encyclopédique (phase 3) : correspondances, sources, licences, règle de qualité."""
import json

import pytest

import config
import wikidata

pytestmark = pytest.mark.skipif(not config.BASE.exists(), reason="base absente : lancer pipeline/run_all.py")


@pytest.fixture(scope="module")
def con():
    import duckdb
    c = duckdb.connect(str(config.BASE), read_only=True)
    existe = c.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'fiche_qualite'").fetchone()[0]
    if not existe:
        pytest.skip("enrichissement non lancé")
    yield c
    c.close()


def val(con, sql, *params):
    return con.execute(sql, list(params)).fetchone()[0]


def test_annee_wikidata():
    assert wikidata.annee("1821-12-12T00:00:00Z") == 1821
    assert wikidata.annee("-0063-09-23T00:00:00Z") == -63
    assert wikidata.annee("http://www.wikidata.org/.well-known/genid/abc") is None
    assert wikidata.annee(None) is None


def test_correspondances_par_graphie_exacte(con):
    """Chaque correspondance repose sur une graphie Wikidata identique (casse ignorée, accents compris)."""
    for pid, graphies in con.execute("""SELECT c.prenom_id, w.graphies FROM correspondance_wikidata c
            JOIN wikidata_prenom w ON w.qid = c.qid""").fetchall():
        assert pid in {g.lower() for g in graphies.split("|")}


def test_types_incompatibles_ecartes(con):
    """Les éléments de type incompatible avec l'usage Insee ne fournissent ni personnalité ni variante."""
    assert val(con, """SELECT count(*) FROM correspondance_wikidata c JOIN prenom p ON p.id = c.prenom_id
        JOIN wikidata_prenom w ON w.qid = c.qid
        WHERE c.statut <> 'type_incompatible' AND p.sexe_usage = 'F' AND w.types = 'masculin'""") == 0


def test_accents_distingues(con):
    """Léa et Lea ne partagent pas leurs éléments Wikidata par simple ressemblance."""
    for pid, graphies in con.execute("""SELECT c.prenom_id, w.graphies FROM correspondance_wikidata c
            JOIN wikidata_prenom w ON w.qid = c.qid WHERE c.prenom_id IN ('lea', 'léa')""").fetchall():
        assert pid in {g.lower() for g in graphies.split("|")}


def test_etymologies_sourcees_et_sous_licence(con):
    assert val(con, "SELECT count(*) FROM etymologie") > 0
    assert val(con, """SELECT count(*) FROM etymologie WHERE url_source NOT LIKE 'https://fr.wiktionary.org/wiki/%'
        OR licence <> ? OR texte IS NULL OR texte = ''""", config.LICENCE_WIKTIONNAIRE) == 0


def test_personnalites_selon_la_regle(con):
    assert val(con, "SELECT coalesce(max(n), 0) FROM (SELECT count(*) n FROM personnalite GROUP BY prenom_id)") <= 8
    assert val(con, f"""SELECT count(*) FROM personnalite WHERE nb_liens < {wikidata.PERSONNALITES_MIN_LIENS}
        OR url NOT LIKE 'https://fr.wikipedia.org/wiki/%' OR nom IS NULL""") == 0


def test_regle_de_qualite(con):
    for niveau, n_etym, n_var, n_perso, total in con.execute("""SELECT niveau, n_etym, n_var, n_perso,
            n_etym + n_orig + n_pron + n_var + n_lang + n_perso FROM fiche_qualite""").fetchall():
        if niveau == "complete":
            assert n_etym and n_var and n_perso
        elif niveau == "partielle":
            assert total > 0 and not (n_etym and n_var and n_perso)
        else:
            assert total == 0


def test_cas_connus(con):
    """Léa : étymologie hébraïque dans le Wiktionnaire (texte vérifiable sur la page source)."""
    texte = val(con, "SELECT texte FROM etymologie WHERE prenom_id = 'léa'")
    assert texte and "hébreu" in texte


def test_fichiers_publies_par_licence(con):
    for f in list((config.DOSSIER_PUBLIC / "wiktionnaire").glob("*.json"))[:30]:
        assert "CC BY-SA 4.0" in json.loads(f.read_text(encoding="utf-8"))["licence"]
    for f in list((config.DOSSIER_PUBLIC / "encyclo").glob("*.json"))[:30]:
        contenu = json.loads(f.read_text(encoding="utf-8"))
        assert "CC0" in contenu["licence"]
        assert all("etymologie" not in json.dumps(p) for p in contenu["prenoms"].values())


def test_etymologie_limitee_au_prenom():
    import wiktionnaire as w
    assert w.etymologie_du_prenom(["(Prénom) De jade.\n(Cours d’eau) De l’allemand Jade."]) == "De jade."
    plusieurs = ["(Prénom 1) (Nom de famille) De l’arabe A.", "(Prénom 2) De l’hébreu B."]
    assert w.etymologie_du_prenom(plusieurs, "Prénom 1") == "De l’arabe A."
    assert w.etymologie_du_prenom(plusieurs, "Prénom 2") == "De l’hébreu B."
    assert w.etymologie_du_prenom(["(Nom de famille) Nom allemand."]) is None
    assert w.etymologie_du_prenom(["Du latin leo (« lion »)."]) == "Du latin leo (« lion »)."
