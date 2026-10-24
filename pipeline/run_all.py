"""Tout reconstruire : téléchargement → inspection → base → statistiques → JSON → cartes → rapport.

Usage : python pipeline/run_all.py [--force]   (--force retélécharge les fichiers sources)
"""
import sys

import build_db
import download
import export_json
import geo
import inspect_raw
import quality_report
import stats

if __name__ == "__main__":
    print("1/7 Téléchargement");    download.telecharger(force="--force" in sys.argv)
    print("2/7 Inspection");        inspect_raw.inspecter()
    print("3/7 Base DuckDB");       build_db.construire()
    print("4/7 Statistiques");      stats.calculer()
    print("5/7 Fichiers JSON");     export_json.exporter()
    print("6/7 Fonds de carte");    geo.generer()
    print("7/7 Rapport qualité");   quality_report.rapport()
    print("Terminé.")
