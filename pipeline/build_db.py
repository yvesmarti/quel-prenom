"""Étape 3 : construit la base de travail DuckDB (data/work/prenoscope.duckdb).

- raw_prenoms : copie fidèle du Parquet INSEE (niveaux FRANCE, REG, DEP) ;
- prenom      : une ligne par graphie INSEE, avec les champs dérivés ;
- statistique : effectifs arrondis et rangs officiels, reliés à prenom ;
- source      : description des sources ;
- tables vides des phases suivantes (origine, etymologie, variante, personnalite, anecdote).

Usage : python pipeline/build_db.py
"""
import csv
import json

import duckdb

import config
import normalize
import xlsx

SCHEMA_FUTUR = """
CREATE TABLE origine (id INTEGER PRIMARY KEY, prenom_id VARCHAR, langue VARCHAR, culture VARCHAR,
    region_pays VARCHAR, justification VARCHAR, source_id VARCHAR, confiance VARCHAR);
CREATE TABLE etymologie (id INTEGER PRIMARY KEY, prenom_id VARCHAR, signification VARCHAR,
    evolution VARCHAR, alternatives VARCHAR, source_id VARCHAR, statut_verification VARCHAR);
CREATE TABLE variante (prenom_id VARCHAR, prenom_associe_id VARCHAR, type VARCHAR, source_id VARCHAR);
CREATE TABLE personnalite (id INTEGER PRIMARY KEY, nom VARCHAR, prenom_id VARCHAR, wikidata_id VARCHAR,
    domaine VARCHAR, periode VARCHAR, presentation VARCHAR, url VARCHAR, score_pertinence DOUBLE);
CREATE TABLE anecdote (id INTEGER PRIMARY KEY, prenom_id VARCHAR, titre VARCHAR, texte VARCHAR,
    categorie VARCHAR, source_id VARCHAR, statut_editorial VARCHAR);
"""


def lire_t35():
    """Lignes (annee, sexe, champ, naissances) du tableau T35 de l'Insee.

    Feuille FM = France métropolitaine (depuis 1901), FR = France entière (depuis 1994).
    Les cellules « nd » (non disponible) sont ignorées.
    """
    lignes = []
    for feuille, champ in (("FM", "metropole"), ("FR", "france")):
        for r in xlsx.lire(config.FICHIER_T35)[feuille]:
            if len(r) < 4 or not (isinstance(r[0], str) and r[0].isdigit()):
                continue
            garcons, filles = r[2], r[3]
            if isinstance(garcons, float) and isinstance(filles, float):
                lignes += [(int(r[0]), "M", champ, int(garcons)), (int(r[0]), "F", champ, int(filles))]
    if not lignes:
        raise SystemExit("T35 : aucune ligne lue, le format du fichier a peut-être changé")
    return lignes


def sexe_usage(total_f, total_m):
    """F, M ou X (mixte) selon la règle documentée SEUIL_MIXTE (cumul national 1900-2025)."""
    total = total_f + total_m
    if total_f and total_m and min(total_f, total_m) / total >= config.SEUIL_MIXTE:
        return "X"
    return "F" if total_f >= total_m else "M"


def construire():
    manifeste = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))["fichiers"]
    config.BASE.parent.mkdir(parents=True, exist_ok=True)
    config.BASE.unlink(missing_ok=True)
    con = duckdb.connect(str(config.BASE))

    print("Import du Parquet…")
    con.execute(f"""CREATE TABLE raw_prenoms AS
        SELECT * FROM read_parquet('{config.FICHIER_PARQUET.as_posix()}')""")

    con.execute("""CREATE TABLE source (id VARCHAR PRIMARY KEY, organisme VARCHAR, titre VARCHAR,
        url VARCHAR, fichier_url VARCHAR, licence VARCHAR, publication VARCHAR,
        date_recuperation VARCHAR, sha256 VARCHAR)""")
    for s in config.SOURCES:
        m = manifeste[s["id"]]
        con.execute("INSERT INTO source VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
            s["id"], s["organisme"], s["titre"], s["page"], s["url"], s["licence"],
            s["publication"], m["recupere_le"], m["sha256"]])

    print("Naissances officielles (T35)…")
    con.execute("""CREATE TABLE naissances_officielles (annee INTEGER, sexe VARCHAR, champ VARCHAR,
        naissances INTEGER, source_id VARCHAR)""")
    con.executemany("INSERT INTO naissances_officielles VALUES (?, ?, ?, ?, 'insee-naissances-t35-2025')",
                    lire_t35())

    print("Table prenom…")
    lignes = con.execute("""
        SELECT prenom,
               coalesce(sum(valeur) FILTER (WHERE sexe = '2'), 0) AS total_f,
               coalesce(sum(valeur) FILTER (WHERE sexe = '1'), 0) AS total_m,
               min(periode)::INTEGER, max(periode)::INTEGER
        FROM raw_prenoms WHERE niveau_geographique = 'FRANCE'
        GROUP BY prenom""").fetchall()
    prenoms = []
    for p, tf, tm, a1, a2 in lignes:
        prenoms.append((
            normalize.identifiant(p), p, normalize.affichage(p), normalize.normaliser(p),
            normalize.nb_lettres(p), normalize.normaliser(p)[0], normalize.est_compose(p),
            normalize.a_accent(p), sexe_usage(tf, tm), int(tf), int(tm), a1, a2,
            normalize.cle_lot(p), "statistique_seule"))
    con.execute("""CREATE TABLE prenom (id VARCHAR PRIMARY KEY, graphie_insee VARCHAR UNIQUE,
        graphie_affichage VARCHAR, norm VARCHAR, nb_lettres INTEGER, initiale VARCHAR,
        compose BOOLEAN, a_accent BOOLEAN, sexe_usage VARCHAR, total_f_arrondi BIGINT,
        total_m_arrondi BIGINT, premiere_annee INTEGER, derniere_annee INTEGER, lot VARCHAR,
        statut_validation VARCHAR)""")
    # Passage par un CSV temporaire : bien plus rapide qu'une insertion ligne à ligne.
    temporaire = config.BASE.parent / "prenom_tmp.csv"
    with open(temporaire, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(prenoms)
    con.execute(f"""INSERT INTO prenom SELECT * FROM read_csv('{temporaire.as_posix()}',
        header = false, quote = '"', columns = {{
        'a': 'VARCHAR', 'b': 'VARCHAR', 'c': 'VARCHAR', 'd': 'VARCHAR', 'e': 'INTEGER', 'f': 'VARCHAR',
        'g': 'BOOLEAN', 'h': 'BOOLEAN', 'i': 'VARCHAR', 'j': 'BIGINT', 'k': 'BIGINT', 'l': 'INTEGER',
        'm': 'INTEGER', 'n': 'VARCHAR', 'o': 'VARCHAR'}})""")
    temporaire.unlink()

    print("Table statistique…")
    con.execute(f"""CREATE TABLE statistique AS
        SELECT p.id AS prenom_id,
               CASE r.sexe WHEN '2' THEN 'F' ELSE 'M' END AS sexe,
               r.periode::INTEGER AS annee,
               r.niveau_geographique AS niveau,
               r.geographie AS territoire,
               r.valeur AS valeur_arrondie,
               r.rang AS rang_officiel,
               '{config.SOURCE_ID}' AS source_id,
               {config.MILLESIME} AS millesime
        FROM raw_prenoms r JOIN prenom p ON p.graphie_insee = r.prenom""")
    con.execute("CREATE INDEX idx_stat_prenom ON statistique (prenom_id)")

    print("Cas ambigus (graphies distinctes, même forme normalisée)…")
    con.execute("""CREATE TABLE ambiguite_normalisation AS
        SELECT norm, list(graphie_insee ORDER BY graphie_insee) AS graphies, count(*) AS nb
        FROM prenom GROUP BY norm HAVING count(*) > 1""")

    con.execute(SCHEMA_FUTUR)

    n_stat = con.execute("SELECT count(*) FROM statistique").fetchone()[0]
    n_raw = con.execute("SELECT count(*) FROM raw_prenoms").fetchone()[0]
    if n_stat != n_raw:
        raise SystemExit(f"Erreur : {n_raw - n_stat} lignes brutes sans prénom associé")
    print(f"Base OK : {len(prenoms):,} prénoms, {n_stat:,} statistiques")
    con.close()


if __name__ == "__main__":
    construire()
