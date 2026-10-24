"""Tout reconstruire : téléchargement → inspection → base → JSON → rapport.

Usage : python pipeline/run_all.py [--force]   (--force retélécharge le fichier INSEE)
"""
import sys

import build_db
import download
import export_json
import inspect_raw
import quality_report

if __name__ == "__main__":
    print("1/5 Téléchargement");   download.telecharger(force="--force" in sys.argv)
    print("2/5 Inspection");       inspect_raw.inspecter()
    print("3/5 Base DuckDB");      build_db.construire()
    print("4/5 Fichiers JSON");    export_json.exporter()
    print("5/5 Rapport qualité");  quality_report.rapport()
    print("Terminé.")
