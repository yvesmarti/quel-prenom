"""Étape 2 : inspecte le fichier Parquet brut avant tout traitement.

Vérifie la structure attendue (et s'arrête si elle a changé), puis relève
les particularités réellement présentes. Résultat : data/reports/inspection.json.

Usage : python pipeline/inspect_raw.py
"""
import json
import sys

import duckdb

import config

COLONNES_ATTENDUES = ["sexe", "prenom", "periode", "niveau_geographique", "geographie", "valeur", "rang"]


def un(con, sql):
    return con.execute(sql).fetchone()


def inspecter():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{config.FICHIER_PARQUET.as_posix()}')")

    colonnes = [ligne[0] for ligne in con.execute("DESCRIBE r").fetchall()]
    erreurs = []
    if colonnes != COLONNES_ATTENDUES:
        erreurs.append(f"Colonnes inattendues : {colonnes}")
    sexes = sorted(v for (v,) in con.execute("SELECT DISTINCT sexe FROM r").fetchall())
    if sexes != ["1", "2"]:
        erreurs.append(f"Valeurs de SEXE inattendues : {sexes}")
    niveaux = sorted(v for (v,) in con.execute("SELECT DISTINCT niveau_geographique FROM r").fetchall())
    if niveaux != ["DEP", "FRANCE", "REG"]:
        erreurs.append(f"Niveaux géographiques inattendus : {niveaux}")
    if erreurs:
        print("\n".join(erreurs))
        sys.exit("Structure du fichier différente de celle attendue : arrêt.")

    resultat = {
        "colonnes": colonnes,
        "nb_lignes": un(con, "SELECT count(*) FROM r")[0],
        "lignes_par_niveau": dict(con.execute(
            "SELECT niveau_geographique, count(*) FROM r GROUP BY 1 ORDER BY 1").fetchall()),
        "zones_par_niveau": dict(con.execute(
            "SELECT niveau_geographique, count(DISTINCT geographie) FROM r GROUP BY 1 ORDER BY 1").fetchall()),
        "codes_regions": [v for (v,) in con.execute(
            "SELECT DISTINCT geographie FROM r WHERE niveau_geographique='REG' ORDER BY 1").fetchall()],
        "codes_departements": [v for (v,) in con.execute(
            "SELECT DISTINCT geographie FROM r WHERE niveau_geographique='DEP' ORDER BY 1").fetchall()],
        "annee_min": un(con, "SELECT min(periode) FROM r")[0],
        "annee_max": un(con, "SELECT max(periode) FROM r")[0],
        "periodes_non_numeriques": [v for (v,) in con.execute(
            "SELECT DISTINCT periode FROM r WHERE NOT regexp_matches(periode, '^[0-9]{4}$')").fetchall()],
        "valeurs_nulles": dict(zip(colonnes, un(con, "SELECT " + ", ".join(
            f"count(*) FILTER (WHERE {c} IS NULL)" for c in colonnes) + " FROM r"))),
        "valeur_min": un(con, "SELECT min(valeur) FROM r")[0],
        "valeur_max": un(con, "SELECT max(valeur) FROM r")[0],
        "valeurs_zero": un(con, "SELECT count(*) FROM r WHERE valeur = 0")[0],
        "valeurs_non_multiples_de_5": un(con, "SELECT count(*) FROM r WHERE valeur % 5 <> 0")[0],
        "doublons_cle": un(con, """SELECT count(*) FROM (SELECT 1 FROM r
            GROUP BY sexe, prenom, periode, niveau_geographique, geographie HAVING count(*) > 1)""")[0],
        "rangs_dupliques": un(con, """SELECT count(*) FROM (SELECT 1 FROM r
            GROUP BY sexe, periode, niveau_geographique, geographie, rang HAVING count(*) > 1)""")[0],
        "groupes_rangs_non_contigus": un(con, """SELECT count(*) FROM (SELECT max(rang) mx, count(*) n FROM r
            GROUP BY sexe, periode, niveau_geographique, geographie) WHERE mx <> n""")[0],
        "inversions_rang_valeur": un(con, """SELECT count(*) FROM (SELECT valeur, lag(valeur) OVER (
            PARTITION BY sexe, periode, niveau_geographique, geographie ORDER BY rang) pv FROM r)
            WHERE valeur > pv""")[0],
        "prenoms_distincts_par_niveau": dict(con.execute(
            "SELECT niveau_geographique, count(DISTINCT prenom) FROM r GROUP BY 1 ORDER BY 1").fetchall()),
        "prenoms_hors_national": un(con, """SELECT count(DISTINCT prenom) FROM r
            WHERE prenom NOT IN (SELECT prenom FROM r WHERE niveau_geographique='FRANCE')""")[0],
        "prenoms_codes_speciaux": [v for (v,) in con.execute(
            "SELECT DISTINCT prenom FROM r WHERE prenom LIKE '\\_%' ESCAPE '\\' OR length(prenom) < 2").fetchall()],
        "caracteres": "".join(sorted({c for (p,) in con.execute(
            "SELECT DISTINCT prenom FROM r").fetchall() for c in p})),
        "prenoms_minuscules": un(con, "SELECT count(DISTINCT prenom) FROM r WHERE prenom <> upper(prenom)")[0],
        "prenoms_avec_espace": [v for (v,) in con.execute(
            "SELECT DISTINCT prenom FROM r WHERE prenom LIKE '% %' ORDER BY 1").fetchall()],
        "nb_prenoms_avec_apostrophe": un(con, "SELECT count(DISTINCT prenom) FROM r WHERE prenom LIKE '%''%'")[0],
        "nb_prenoms_avec_tiret": un(con, "SELECT count(DISTINCT prenom) FROM r WHERE prenom LIKE '%-%'")[0],
        "longueur_min": un(con, "SELECT min(length(prenom)) FROM r")[0],
        "longueur_max": un(con, "SELECT max(length(prenom)) FROM r")[0],
        "mayotte_976_premiere_annee": un(con, "SELECT min(periode) FROM r WHERE geographie='976' AND niveau_geographique='DEP'")[0],
        "lignes_nationales_par_annee_min_max": list(un(con, """SELECT min(n), max(n) FROM (
            SELECT count(*) n FROM r WHERE niveau_geographique='FRANCE' GROUP BY periode)""")),
    }
    config.DOSSIER_RAPPORTS.mkdir(parents=True, exist_ok=True)
    (config.DOSSIER_RAPPORTS / "inspection.json").write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Inspection OK : {resultat['nb_lignes']:,} lignes, {resultat['annee_min']}-{resultat['annee_max']}")
    return resultat


if __name__ == "__main__":
    inspecter()
