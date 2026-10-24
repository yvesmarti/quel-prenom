# Prénoscope

Encyclopédie interactive des prénoms donnés en France depuis 1900, construite uniquement à partir de données
ouvertes et sourcées. Site statique (aucun serveur, aucun compte), en français.

**État : phase 1 (fondations) terminée.** Recherche et filtres sur les 49 163 prénoms du fichier Insee 2025,
fiche simple avec la courbe nationale (naissances et rang). Voir [ROADMAP.md](ROADMAP.md) pour la suite.

## Documentation

| Fichier | Contenu |
|---|---|
| [PROMPT_PRENOSCOPE.md](PROMPT_PRENOSCOPE.md) | Cahier des charges complet |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Organisation des dossiers, choix techniques, performances |
| [SOURCES.md](SOURCES.md) | Sources, licences, particularités constatées dans les données |
| [DATA_MODEL.md](DATA_MODEL.md) | Tables, fichiers publiés, règles (mixte, composé, accents…) |
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
lance les tests et construit le site de production. Durée : 1 à 2 minutes (hors téléchargement de 18 Mo).

## Étape par étape

Toutes les commandes se lancent depuis la racine du projet, sauf indication contraire.

| Étape | Commande | Ce qu'elle fait |
|---|---|---|
| 1. Environnement Python | `python -m venv .venv` | Crée un dossier `.venv` isolé pour les bibliothèques Python |
| 2. Dépendances Python | `.venv\Scripts\python -m pip install -r requirements.txt` | Installe DuckDB et pytest |
| 3. Télécharger les données | `.venv\Scripts\python pipeline\download.py` | Récupère le fichier Insee et note sa somme de contrôle |
| 4. Inspecter | `.venv\Scripts\python pipeline\inspect_raw.py` | Vérifie la structure et relève les anomalies |
| 5. Construire la base | `.venv\Scripts\python pipeline\build_db.py` | Crée `data/work/prenoscope.duckdb` |
| 6. Générer les fichiers du site | `.venv\Scripts\python pipeline\export_json.py` | Écrit `site/public/data/` |
| 7. Rapport de qualité | `.venv\Scripts\python pipeline\quality_report.py` | Écrit `data/reports/qualite.md` |
| 3 à 7 d'un coup | `.venv\Scripts\python pipeline\run_all.py` | Enchaîne tout le pipeline (`--force` pour retélécharger) |
| Tests des données | `.venv\Scripts\python -m pytest` | Vérifie l'intégrité de la base et des JSON |
| Dépendances du site | `cd site` puis `npm install` | Installe Vue, Vite, ECharts |
| Site en local | `npm run dev` (dans `site/`) | Ouvre le site sur http://localhost:5173 |
| Tests du site | `npm test` (dans `site/`) | Vérifie recherche et filtres |
| Build de production | `npm run build` (dans `site/`) | Produit `site/dist/`, prêt à publier |
| Enrichissements | — | Phase 3 (Wikidata, Wiktionnaire), pas encore disponible |
| Publier | — | Phase 5 (GitHub Pages via GitHub Actions), pas encore configuré |

Sous macOS/Linux, remplacer `.venv\Scripts\python` par `.venv/bin/python`.

## Ce qui est versionné (ou non)

- **Non versionné** (reconstruit par script) : `data/raw/` (fichier Insee), `data/work/` (base DuckDB), `.venv/`, `site/node_modules/`, `site/dist/`.
- **Versionné** : le code, la documentation, le rapport de qualité et les fichiers JSON publiés (`site/public/data/`),
  pour que le site puisse être publié sans relancer le pipeline.

## Licence des données

Données : Insee, Fichier des prénoms – Édition 2025, Licence Ouverte / Open Licence 2.0 (Etalab).
Mention obligatoire « Source : Insee » avec la date de mise à jour — affichée en pied de page du site.
