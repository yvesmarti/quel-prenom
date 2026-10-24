"""Paramètres centraux du pipeline Prénoscope.

Tout ce qui peut changer (URL, millésime, seuils) est regroupé ici.
"""
import sys
from pathlib import Path

# Affiche correctement les accents dans la console Windows.
sys.stdout.reconfigure(encoding="utf-8")

RACINE = Path(__file__).resolve().parent.parent

# --- Chemins --------------------------------------------------------------
DOSSIER_RAW = RACINE / "data" / "raw"
MANIFESTE = DOSSIER_RAW / "manifest.json"
BASE = RACINE / "data" / "work" / "prenoscope.duckdb"
DOSSIER_RAPPORTS = RACINE / "data" / "reports"
DOSSIER_PUBLIC = RACINE / "site" / "public" / "data"

# --- Sources --------------------------------------------------------------
MILLESIME = 2025
LICENCE_ETALAB = "Licence Ouverte / Open Licence 2.0 (Etalab)"
LICENCE_INSEE = LICENCE_ETALAB
SOURCE_ID = "insee-prenoms-2025"

# Chaque source : identifiant, fichier local, URL de téléchargement et description.
SOURCES = [
    {
        "id": SOURCE_ID,
        "fichier": "prenoms-2025.parquet",
        "url": "https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet",
        "page": "https://www.insee.fr/fr/statistiques/8595130",
        "organisme": "Insee",
        "titre": "Fichier des prénoms – Édition 2025",
        "licence": LICENCE_ETALAB,
        "publication": "2026-07-16",
    },
    {
        "id": "insee-naissances-t35-2025",
        "fichier": "naissances/t35.xlsx",
        "url": "https://www.insee.fr/fr/statistiques/fichier/9000187/t35.xlsx",
        "page": "https://www.insee.fr/fr/statistiques/9000187?sommaire=9000195",
        "organisme": "Insee",
        "titre": "Les naissances en 2025 et en séries longues – T35 : naissances vivantes selon le sexe",
        "licence": LICENCE_ETALAB,
        "publication": "2026-07-06",
    },
    {
        "id": "ign-contours-departements-2018",
        "fichier": "geo/departements-avec-outre-mer.geojson",
        "url": "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson",
        "page": "https://github.com/gregoiredavid/france-geojson",
        "organisme": "IGN (Admin Express COG 2018) et Insee (COG 2018), mis en forme par G. David",
        "titre": "Contours des départements, avec outre-mer",
        "licence": LICENCE_ETALAB,
        "publication": "2018",
    },
    {
        "id": "ign-contours-regions-2018",
        "fichier": "geo/regions-avec-outre-mer.geojson",
        "url": "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-avec-outre-mer.geojson",
        "page": "https://github.com/gregoiredavid/france-geojson",
        "organisme": "IGN (Admin Express COG 2018) et Insee (COG 2018), mis en forme par G. David",
        "titre": "Contours des régions, avec outre-mer",
        "licence": LICENCE_ETALAB,
        "publication": "2018",
    },
    {
        "id": "wiktionnaire-kaikki",
        "fichier": "wiktionnaire/raw-wiktextract-data.jsonl.gz",
        "url": "https://kaikki.org/frwiktionary/raw-wiktextract-data.jsonl.gz",
        "page": "https://kaikki.org/frwiktionary/rawdata.html",
        "organisme": "Wiktionnaire (contributeurs), extraction structurée wiktextract / kaikki.org (T. Ylonen)",
        "titre": "Wiktionnaire en français – extraction structurée (dump du 1er octobre 2026)",
        "licence": "CC BY-SA 4.0 (textes du Wiktionnaire)",
        "publication": "2026-10-01",
        "lourd": True,  # ≈ 700 Mo : téléchargé une fois, puis réutilisé
    },
]
SOURCES_PAR_ID = {s["id"]: s for s in SOURCES}

# Wikidata est interrogé par requêtes SPARQL (pas de fichier unique) : voir pipeline/wikidata.py.
SOURCE_WIKIDATA = {
    "id": "wikidata",
    "organisme": "Wikidata (contributeurs)",
    "titre": "Wikidata – éléments « prénom » (variantes, langues d'usage)",
    "page": "https://www.wikidata.org/",
    "url": "https://query.wikidata.org/sparql",
    "licence": "CC0 1.0 (domaine public)",
}
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_USER_AGENT = "Prenoscope/0.3 (projet personnel non commercial ; https://github.com/) python-urllib"
DOSSIER_CACHE_WIKIDATA = DOSSIER_RAW / "wikidata"
LICENCE_WIKTIONNAIRE = "CC BY-SA 4.0"
# Personnalités : désactivé pour la première version en ligne (requêtes trop longues, méthode à revoir).
WIKIDATA_PERSONNALITES = False


def chemin_source(source_id):
    return DOSSIER_RAW / SOURCES_PAR_ID[source_id]["fichier"]


FICHIER_PARQUET = chemin_source(SOURCE_ID)
FICHIER_T35 = chemin_source("insee-naissances-t35-2025")

# --- Règles documentées (voir DATA_MODEL.md et STATISTIQUES.md) ------------
# Un prénom est « mixte » si le sexe minoritaire représente au moins
# cette part du cumul national des naissances 1900-2025 (effectifs arrondis).
SEUIL_MIXTE = 0.10

# Dénominateur officiel (T35) : utilisé seulement à partir de cette année,
# car avant 1946 le fichier des prénoms ne recense qu'une partie des naissances.
ANNEE_DEBUT_FREQUENCES = 1946
# Première année où la série officielle couvre la France entière (sinon : métropole seule).
ANNEE_DEBUT_FRANCE_ENTIERE = 1994

# Tendances (voir STATISTIQUES.md). Y = dernière année du millésime.
TENDANCES = {
    "fenetre": 5,               # largeur des fenêtres comparées (années)
    "decalage_progression": 10,  # on compare [Y-4..Y] à [Y-14..Y-10]
    "emergent_depuis": 20,      # première apparition dans les 20 dernières années
    "emergent_min": 20,         # ≥ 20 naissances/an en moyenne sur [Y-4..Y]
    "progression_facteur": 2.0,  # fréquence au moins doublée
    "progression_min": 50,      # ≥ 50 naissances/an sur [Y-4..Y]
    "progression_min_avant": 10,  # ≥ 10 naissances/an avant (sinon c'est un émergent)
    "declin_facteur": 0.5,      # fréquence au moins divisée par deux
    "declin_min_avant": 50,     # ≥ 50 naissances/an sur [Y-14..Y-10]
    "rare_pic_min": 500,        # pic historique ≥ 500 naissances/an (moyenne sur 5 ans)
    "rare_recent_max": 20,      # ≤ 20 naissances/an sur [Y-4..Y]
    "vague_rang_max": 300,      # sommet de vague : rang lissé ≤ 300
    "vague_prominence": 0.6,    # creux entre deux vagues : rang au moins 4 fois moins bon (log10 4 ≈ 0,6)
    "lissage_rang": 5,          # moyenne mobile centrée sur 5 ans (log10 du rang)
    "retour_avant": 1960,       # retour : un sommet de vague avant 1960…
    "retour_recent": 15,        # … et un autre dans les 15 dernières années,
    "retour_rang_max": 100,     # tous deux au rang lissé ≤ 100
}
# Évolutions affichées sur la fiche : moyenne sur 3 ans autour de chaque date.
EVOLUTIONS = [5, 10, 20]
EVOLUTION_MIN = 10  # pas d'évolution calculée sous 10 naissances/an en moyenne

# Géographie : en dessous de ce nombre de naissances, l'indice de spécificité n'est pas calculé.
GEO_MIN_INDICE = 20

# Classements publiés
CLASSEMENT_NATIONAL_TOP = 500
CLASSEMENT_NATIONAL_FIN = 50
CLASSEMENT_TERRITORIAL_TOP = {"REG": 50, "DEP": 20}  # par an ; limité pour la taille des fichiers
CLASSEMENT_DECENNIE_TOP = 100

# Version du format des fichiers JSON publiés (changer si la structure change).
VERSION_FORMAT = 1
