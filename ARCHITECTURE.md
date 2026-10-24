# Architecture

## Vue d'ensemble

```
Insee (Parquet)  ──►  pipeline Python  ──►  DuckDB (travail)  ──►  JSON statiques  ──►  site Vue (navigateur)
 data/raw/            pipeline/*.py         data/work/              site/public/data/      site/src/
```

Internet n'est nécessaire que pour préparer les données. Le site publié est entièrement statique :
aucun serveur, aucune API externe, aucun compte.

## Dossiers

```
prenoms/
├─ PROMPT_PRENOSCOPE.md     cahier des charges
├─ README.md  ARCHITECTURE.md  SOURCES.md  DATA_MODEL.md  ROADMAP.md
├─ requirements.txt         dépendances Python (versions figées)
├─ tout_reconstruire.cmd    reconstruit tout (Windows)
├─ pipeline/                préparation des données (Python)
│  ├─ config.py             URL, chemins, seuils — tout ce qui peut changer
│  ├─ download.py           téléchargement + SHA-256 + date → data/raw/manifest.json
│  ├─ inspect_raw.py        contrôle de structure et relevé des anomalies → data/reports/inspection.json
│  ├─ normalize.py          règles : identifiant, forme normalisée, affichage, lettres, accents, composé
│  ├─ build_db.py           base DuckDB
│  ├─ export_json.py        fichiers publiés
│  ├─ quality_report.py     rapport de qualité → data/reports/qualite.md
│  └─ run_all.py            enchaîne toutes les étapes
├─ tests/                   tests pytest (règles + intégrité des données réelles)
├─ data/
│  ├─ raw/                  (non versionné) fichier Insee + manifeste
│  ├─ work/                 (non versionné) prenoscope.duckdb
│  └─ reports/              rapports générés (versionnés)
└─ site/                    application Vue 3 + Vite (JavaScript)
   ├─ public/data/          JSON générés par le pipeline (versionnés)
   ├─ src/
   │  ├─ main.js            routeur (mode hash) et démarrage
   │  ├─ App.vue            en-tête, pied de page (source et licence)
   │  ├─ style.css          palette et styles communs
   │  ├─ lib/               logique sans interface : normalisation, filtres, chargement des données
   │  ├─ views/             pages : Recherche, Fiche
   │  └─ components/        CourbeNationale (ECharts)
   └─ tests/                tests vitest
```

## Choix techniques

- **DuckDB** : lit directement le Parquet Insee, très rapide (pipeline complet ≈ 15 s), un seul fichier, sans serveur.
- **Python standard + DuckDB uniquement** : pas de pandas ; le code reste court et lisible.
- **Vue 3 + Vite en JavaScript** (sans TypeScript) : plus lisible pour un mainteneur non spécialiste.
- **Routeur en mode « hash »** (`#/prenom/lea`) : fonctionne sur GitHub Pages sans configuration de serveur.
- **ECharts** importé partiellement (courbes seulement) et chargé uniquement à l'ouverture d'une fiche.
- **JSON versionnés dans Git** : la publication n'a pas besoin de relancer le pipeline. Les données brutes et la base, elles, ne sont pas versionnées.
- **Règles en double Python/JS** (normalisation) : un test vérifie que les deux donnent le même résultat sur les 49 163 prénoms.

## Données publiées et performances (mesurées, phase 1)

| Fichier | Rôle | Taille brute | Compressé (gzip) |
|---|---|---|---|
| `index.v1.json` | index de tous les prénoms, chargé au démarrage | ≈ 2,9 Mo | ≈ 675 Ko |
| `prenoms/<lot>.json` (353 lots) | séries nationales, chargées à l'ouverture d'une fiche | 11 Mo au total, ≤ 857 Ko par lot | 3,4 Mo au total |
| `meta.json` | source, licence, règles | < 1 Ko | — |
| Code JS page d'accueil | | 100 Ko | 39 Ko |
| Code JS fiche (avec ECharts) | | 518 Ko | 176 Ko |

Chiffres exacts à jour : `data/reports/qualite.md`. GitHub Pages et Cloudflare Pages servent les fichiers compressés automatiquement.

Un **lot** regroupe les prénoms dont la forme normalisée commence par les mêmes deux lettres (`le.json` contient Léa, Lea, Léo…).
Le nombre de requêtes reste faible et chaque fichier est mis en cache par le navigateur.

Pistes d'allègement si nécessaire (phase 5) : index en format colonne, séries delta-encodées, lots plus fins pour « ma ».

## Évolution prévue

- Phase 2 : nouveaux fichiers d'agrégats (classements, tendances, cartes) ; le régional et le départemental sont déjà en base.
- Phase 3 : tables d'enrichissement (déjà créées, vides) alimentées par des modules séparés dans `pipeline/`.
- Modules ludiques : nouvelles vues dans `site/src/views/`, logique pure dans `site/src/lib/` (testable).
- `VERSION_FORMAT` (config.py) et le suffixe `.v1` permettent de changer le format sans casser les caches.
