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
│  ├─ build_db.py           base DuckDB (dont naissances officielles T35)
│  ├─ xlsx.py               lecture des classeurs .xlsx de l'Insee (bibliothèque standard)
│  ├─ stats.py              indicateurs, tendances, agrégats géographiques, couverture
│  ├─ outils.py             insertion rapide dans DuckDB
│  ├─ wiktionnaire.py       extraction des prénoms du Wiktionnaire (fichier kaikki.org) et import
│  ├─ wikidata.py           requêtes SPARQL en lots (cache, reprise, journal), correspondances, personnalités
│  ├─ encyclo.py            consolidation : origine, étymologie, variantes, personnalités, qualité des fiches
│  ├─ export_json.py        fichiers publiés
│  ├─ geo.py                fonds de carte simplifiés, outre-mer en encarts
│  ├─ quality_report.py     rapport de qualité → data/reports/qualite.md
│  └─ run_all.py            enchaîne toutes les étapes
├─ tests/                   tests pytest (règles + intégrité des données réelles)
├─ data/
│  ├─ raw/                  (non versionné) fichiers sources + manifeste ; wikidata/cache/ (réponses SPARQL)
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

- **DuckDB** : lit directement le Parquet Insee, rapide (pipeline complet ≈ 1 min 30, dont l’essentiel pour écrire et mesurer les milliers de fichiers publiés), un seul fichier, sans serveur.
- **Python standard + DuckDB uniquement** : pas de pandas ; le code reste court et lisible.
- **Vue 3 + Vite en JavaScript** (sans TypeScript) : plus lisible pour un mainteneur non spécialiste.
- **Routeur en mode « hash »** (`#/prenom/lea`) : fonctionne sur GitHub Pages sans configuration de serveur.
- **ECharts** importé partiellement (courbes et cartes) et chargé uniquement à l'ouverture d'une page qui l'utilise.
  Les cartes sont dessinées par ECharts à partir des GeoJSON : aucune bibliothèque cartographique supplémentaire.
- **Indicateurs calculés par le site** à partir des séries (plutôt que publiés) : publier les indicateurs de 52 340
  séries aurait fait passer les fichiers de détails de 11 à 40 Mo. Un test garantit l'égalité avec le calcul Python.
- **JSON versionnés dans Git** : la publication n'a pas besoin de relancer le pipeline. Les données brutes et la base, elles, ne sont pas versionnées.
- **Règles en double Python/JS** (normalisation) : un test vérifie que les deux donnent le même résultat sur les 49 163 prénoms.

## Données publiées et performances (mesurées, phase 2)

| Fichier | Chargé… | Taille brute | Compressé (gzip) |
|---|---|---|---|
| `index.v1.json` | au démarrage | ≈ 2,9 Mo | ≈ 675 Ko |
| `meta.json` | au démarrage | 10 Ko | 3 Ko |
| `prenoms/<lot>.json` (353 lots) | à l'ouverture d'une fiche | 11 Mo au total, ≤ 868 Ko par lot | 3,4 Mo au total |
| `geo/prenoms/g_<lot3>.json` (2 638 lots) | section carte d'une fiche | 18,7 Mo au total, ≤ 862 Ko par lot | 4,0 Mo au total |
| `geo/regions.json`, `departements.json`, `totaux.json`, `zones.json` | section carte | 353 Ko | 103 Ko |
| `classements/france/<annee>.json` (126) | page Classements | 2,1 Mo au total, ≤ 17 Ko | 741 Ko |
| `classements/zones/*.json` (119) | page Classements, territoire choisi | 11,9 Mo au total, ≤ 219 Ko | 2,2 Mo |
| `classements/france-decennies.json` | page Classements | 44 Ko | 14 Ko |
| `tendances.json` | page Tendances | 188 Ko | 28 Ko |
| `couverture.json` | page Méthode | 12 Ko | 4 Ko |
| Code JS commun / fiche / ECharts | | 102 / 109 / 516 Ko | 40 / 37 / 174 Ko |

Chiffres exacts à jour : `data/reports/qualite.md`. GitHub Pages et Cloudflare Pages servent les fichiers compressés automatiquement.

Un **lot** regroupe les prénoms dont la forme normalisée commence par les mêmes lettres (2 pour les séries, 3 pour
la géographie, plus lourde). Chaque fichier n'est téléchargé qu'une fois par visite.

Pistes d'allègement si nécessaire (phase 5) : index en format colonne, séries delta-encodées, lots plus fins pour « ma »
et « mar », codes de zones numérotés.

## Évolution prévue

- Phase 2 : réalisée (voir STATISTIQUES.md).
- Phase 3 : réalisée. Les données d'enrichissement sont publiées dans deux dossiers séparés par licence
  (`encyclo/` en CC0, `wiktionnaire/` en CC BY-SA 4.0, voir LICENCES.md), chargés à l'ouverture d'une fiche.
  Wikidata est interrogé une seule fois (≈ 1 à 2 h) puis relu depuis le cache local à chaque reconstruction.
- Phase 3 : tables d'enrichissement (déjà créées, vides) alimentées par des modules séparés dans `pipeline/`.
- Modules ludiques : nouvelles vues dans `site/src/views/`, logique pure dans `site/src/lib/` (testable).
- `VERSION_FORMAT` (config.py) et le suffixe `.v1` permettent de changer le format sans casser les caches.
