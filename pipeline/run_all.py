"""Tout reconstruire : téléchargement → inspection → base → statistiques → enrichissement
→ JSON → cartes → rapport.

L'enrichissement Wikidata réutilise son cache (data/raw/wikidata/cache/) : seule la première
exécution interroge réellement Wikidata (≈ 1 à 2 heures). Supprimer ce dossier pour actualiser.

Usage : python pipeline/run_all.py [--force]   (--force retélécharge les fichiers sources)
"""
import sys

import duckdb

import build_db
import config
import download
import encyclo
import export_json
import geo
import inspect_raw
import quality_report
import stats
import wikidata
import wiktionnaire

if __name__ == "__main__":
    print("1/9 Téléchargement");      download.telecharger(force="--force" in sys.argv)
    print("2/9 Inspection");          inspect_raw.inspecter()
    print("3/9 Base DuckDB");         build_db.construire()
    print("4/9 Statistiques");        stats.calculer()
    print("5/9 Wiktionnaire")
    if "--force" in sys.argv or not wiktionnaire.EXTRAIT.exists():
        wiktionnaire.extraire()
    con = duckdb.connect(str(config.BASE)); wiktionnaire.importer(con); con.close()
    print("6/9 Wikidata");            wikidata.enrichir()
    print("7/9 Consolidation");       encyclo.consolider()
    print("8/9 Fichiers JSON");       export_json.exporter(); geo.generer()
    print("9/9 Rapport qualité");     quality_report.rapport()
    print("Terminé.")
