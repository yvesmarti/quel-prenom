"""Étape 4 : génère les fichiers JSON publiés par le site (site/public/data/).

- meta.json            : source, licence, millésime, règles, chiffres clés ;
- index.v1.json        : index léger de tous les prénoms (chargé au démarrage) ;
- prenoms/<lot>.json   : séries nationales par prénom, chargées à la demande
                          (un lot = les prénoms dont la forme normalisée commence par les mêmes 2 lettres).

Le régional et le départemental restent dans la base (exploités en phase 2).

Usage : python pipeline/export_json.py
"""
import json
import shutil
from collections import defaultdict

import duckdb

import config

COLONNES_INDEX = ["id", "affichage", "norm", "sexe", "total_f", "total_m",
                  "premiere_annee", "derniere_annee", "lettres", "accent", "compose", "lot"]


def ecrire(chemin, donnees):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def exporter():
    con = duckdb.connect(str(config.BASE), read_only=True)
    sortie = config.DOSSIER_PUBLIC
    if sortie.exists():
        shutil.rmtree(sortie)  # dossier entièrement généré : on repart de zéro

    lignes = con.execute("""
        SELECT id, graphie_affichage, norm, sexe_usage, total_f_arrondi, total_m_arrondi,
               premiere_annee, derniere_annee, nb_lettres, a_accent::INTEGER, compose::INTEGER, lot
        FROM prenom ORDER BY total_f_arrondi + total_m_arrondi DESC, id""").fetchall()
    ecrire(sortie / f"index.v{config.VERSION_FORMAT}.json",
           {"version": config.VERSION_FORMAT, "colonnes": COLONNES_INDEX, "lignes": [list(l) for l in lignes]})

    lots = defaultdict(dict)
    series = con.execute("""
        SELECT p.lot, s.prenom_id, s.sexe, list([s.annee, s.valeur_arrondie, s.rang_officiel] ORDER BY s.annee)
        FROM statistique s JOIN prenom p ON p.id = s.prenom_id
        WHERE s.niveau = 'FRANCE'
        GROUP BY ALL""").fetchall()
    for lot, prenom_id, sexe, serie in series:
        lots[lot].setdefault(prenom_id, {})[sexe] = serie
    for lot, contenu in lots.items():
        ecrire(sortie / "prenoms" / f"{lot}.json",
               {"version": config.VERSION_FORMAT, "format_serie": ["annee", "valeur_arrondie", "rang_officiel"],
                "prenoms": contenu})

    source = con.execute("SELECT * FROM source").fetchone()
    colonnes_source = [d[0] for d in con.description]
    annees = con.execute("SELECT min(annee), max(annee) FROM statistique").fetchone()
    ecrire(sortie / "meta.json", {
        "version": config.VERSION_FORMAT,
        "source": dict(zip(colonnes_source, source)),
        "annee_min": annees[0], "annee_max": annees[1],
        "nb_prenoms": len(lignes),
        "nb_lots": len(lots),
        "regles": {
            "seuil_mixte": config.SEUIL_MIXTE,
            "arrondi": "Effectifs arrondis par l'Insee au multiple de 5 le plus proche.",
            "rang": "Rang officiel Insee, calculé sur les effectifs non arrondis (par sexe, année et zone).",
        },
    })
    print(f"Export OK : index de {len(lignes):,} prénoms, {len(lots)} lots de détails")
    con.close()


if __name__ == "__main__":
    exporter()
