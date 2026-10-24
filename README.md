# Prénoscope

Encyclopédie interactive des prénoms donnés en France depuis 1900, construite uniquement à partir de données
ouvertes et sourcées. Site statique (aucun serveur, aucun compte), en français.

**État : phases 1 (fondations) et 2 (statistiques) terminées.** Recherche et filtres sur les 49 163 prénoms du
fichier Insee 2025 ; fiche avec courbes (naissances, fréquence pour 1 000, rang), comparaison, chiffres clés,
tendances et carte régionale/départementale ; pages Classements, Tendances et Méthode.
Voir [ROADMAP.md](ROADMAP.md) pour la suite.

## Documentation

| Fichier | Contenu |
|---|---|
| [PROMPT_PRENOSCOPE.md](PROMPT_PRENOSCOPE.md) | Cahier des charges complet |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Organisation des dossiers, choix techniques, performances |
| [SOURCES.md](SOURCES.md) | Sources, licences, particularités constatées dans les données |
| [DATA_MODEL.md](DATA_MODEL.md) | Tables, fichiers publiés, règles (mixte, composé, accents…) |
| [DEPLOIEMENT.md](DEPLOIEMENT.md) | Mise en ligne sur GitHub Pages, pas à pas |
| [LICENCES.md](LICENCES.md) | Licence de chaque famille de fichiers publiés (Etalab, CC0, CC BY-SA 4.0) |
| [STATISTIQUES.md](STATISTIQUES.md) | Définitions : fréquences, évolutions, tendances, classements, géographie, couverture |
| [ROADMAP.md](ROADMAP.md) | Phases du projet |
| [data/reports/qualite.md](data/reports/qualite.md) | Rapport de qualité généré automatiquement |

## Prérequis

- **Python 3.11 ou plus** — https://www.python.org/downloads/ (cocher « Add Python to PATH »)
- **Node.js 20 ou plus** (fournit `npm`) — https://nodejs.org/
- **Git** — https://git-scm.com/

Vérifier : `python --version`, `node --version`, `git --version`.

## Tout reconstruire en une commande (Windows)

Double-cliquer `tout_reconstruire.cmd`, ou dans un terminal ouvert à la racine du projet :

```
.\tout_reconstruire.cmd
```

Ce script installe les dépendances, télécharge les données Insee, reconstruit la base et les fichiers JSON,
lance les tests et construit le site de production. Durée : 3 à 4 minutes (hors téléchargement d'environ 24 Mo).

## Étape par étape

Toutes les commandes se lancent depuis la racine du projet, sauf indication contraire.

| Étape | Commande | Ce qu'elle fait |
|---|---|---|
| 1. Environnement Python | `python -m venv .venv` | Crée un dossier `.venv` isolé pour les bibliothèques Python |
| 2. Dépendances Python | `.venv\Scripts\python -m pip install -r requirements.txt` | Installe DuckDB et pytest |
| 3. Télécharger les données | `.venv\Scripts\python pipeline\download.py` | Récupère les fichiers sources (prénoms, naissances, contours) et note leur somme de contrôle |
| 4. Inspecter | `.venv\Scripts\python pipeline\inspect_raw.py` | Vérifie la structure et relève les anomalies |
| 5. Construire la base | `.venv\Scripts\python pipeline\build_db.py` | Crée `data/work/prenoscope.duckdb` |
| 6. Statistiques | `.venv\Scripts\python pipeline\stats.py` | Calcule indicateurs, tendances, agrégats géographiques |
| 6b. Wiktionnaire | `.venv\Scripts\python pipeline\wiktionnaire.py` | Extrait les prénoms du Wiktionnaire (≈ 1 min) et les relie aux prénoms Insee |
| 6c. Wikidata | `.venv\Scripts\python pipeline\wikidata.py` | Interroge Wikidata (≈ 1 à 2 h la première fois, puis cache local) |
| 6d. Consolidation | `.venv\Scripts\python pipeline\encyclo.py` | Remplit origines, étymologies, variantes, personnalités, qualité des fiches |
| 7. Générer les fichiers du site | `.venv\Scripts\python pipeline\export_json.py` | Écrit `site/public/data/` |
| 8. Fonds de carte | `.venv\Scripts\python pipeline\geo.py` | Simplifie les contours, place l'outre-mer en encarts |
| 9. Rapport de qualité | `.venv\Scripts\python pipeline\quality_report.py` | Écrit `data/reports/qualite.md` |
| 3 à 9 d'un coup | `.venv\Scripts\python pipeline\run_all.py` | Enchaîne tout le pipeline (`--force` pour retélécharger) |
| Tests des données | `.venv\Scripts\python -m pytest` | Vérifie l'intégrité de la base et des JSON |
| Dépendances du site | `cd site` puis `npm install` | Installe Vue, Vite, ECharts |
| Site en local | `npm run dev` (dans `site/`) | Ouvre le site sur http://localhost:5173 |
| Tests du site | `npm test` (dans `site/`) | Vérifie recherche et filtres |
| Build de production | `npm run build` (dans `site/`) | Produit `site/dist/`, prêt à publier |
| Enrichissements | — | Phase 3 (Wikidata, Wiktionnaire), pas encore disponible |
| Publier | `git push` | Mise en ligne automatique sur GitHub Pages : voir [DEPLOIEMENT.md](DEPLOIEMENT.md) |

Sous macOS/Linux, remplacer `.venv\Scripts\python` par `.venv/bin/python`.

## Ce qui est versionné (ou non)

- **Non versionné** (reconstruit par script) : `data/raw/` (fichier Insee), `data/work/` (base DuckDB), `.venv/`, `site/node_modules/`, `site/dist/`.
- **Versionné** : le code, la documentation, le rapport de qualité et les fichiers JSON publiés (`site/public/data/`),
  pour que le site puisse être publié sans relancer le pipeline.

## Licence des données

Données : Insee, Fichier des prénoms – Édition 2025 ; Insee, statistiques de l'état civil (naissances par sexe, T35) ;
IGN, Admin Express COG 2018 (contours). Toutes sous Licence Ouverte / Open Licence 2.0 (Etalab).
Mention « Source : Insee » avec la date de mise à jour — affichée en pied de page et sur la page Méthode du site.

## Licence du code

EUPL 1.2 (fichier [LICENSE](LICENSE)). Les données publiées ont leurs propres licences : voir [LICENCES.md](LICENCES.md).
