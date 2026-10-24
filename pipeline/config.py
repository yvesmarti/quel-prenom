"""Paramètres centraux du pipeline Prénoscope.

Tout ce qui peut changer (URL, millésime, seuils) est regroupé ici.
"""
import sys
from pathlib import Path

# Affiche correctement les accents dans la console Windows.
sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent

# --- Source INSEE ---------------------------------------------------------
MILLESIME = 2025
PAGE_INSEE = "https://www.insee.fr/fr/statistiques/8595130"
URL_PARQUET = "https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet"
LICENCE_INSEE = "Licence Ouverte / Open Licence 2.0 (Etalab)"
SOURCE_ID = "insee-prenoms-2025"

# --- Chemins --------------------------------------------------------------
DOSSIER_RAW = RACINE / "data" / "raw"
FICHIER_PARQUET = DOSSIER_RAW / "prenoms-2025.parquet"
MANIFESTE = DOSSIER_RAW / "manifest.json"
BASE = RACINE / "data" / "work" / "prenoscope.duckdb"
DOSSIER_RAPPORTS = RACINE / "data" / "reports"
DOSSIER_PUBLIC = RACINE / "site" / "public" / "data"

# --- Règles documentées (voir DATA_MODEL.md) -------------------------------
# Un prénom est « mixte » si le sexe minoritaire représente au moins
# cette part du cumul national des naissances 1900-2025 (effectifs arrondis).
SEUIL_MIXTE = 0.10

# Version du format des fichiers JSON publiés (changer si la structure change).
VERSION_FORMAT = 1
