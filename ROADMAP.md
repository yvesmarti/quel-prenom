# Feuille de route

## Phase 1 — Fondations ✅ (24/10/2026)

- [x] Prérequis vérifiés (Python 3.13, Node 24, npm 11, Git 2.55)
- [x] Dépôt Git, structure, documentation initiale
- [x] Pipeline Insee : téléchargement avec SHA-256, inspection réelle, base DuckDB (national, régional, départemental)
- [x] Modèle de données (tables d'enrichissement créées vides)
- [x] Index complet des 49 163 prénoms + 353 lots de séries nationales
- [x] Rapport de qualité automatique
- [x] Site : recherche insensible aux accents, filtres sexe / lettres / initiale / terminaison / accents / composé, tri
- [x] Fiche simple : courbe nationale effectif + rang, autres graphies, mention de source
- [x] Tests : pytest (34) et vitest (9)

## Phase 2 — Statistiques

- Identifier la série officielle des naissances (dénominateur) pour les fréquences pour 1 000.
- Évolutions 5/10/20 ans, année record, comparaison de prénoms.
- Tendances (émergents, déclin, retours, vagues) avec définitions mathématiques, seuils et lissage documentés.
- Cartes régionales et départementales (GeoJSON), Outre-mer traité correctement.
- Classements top 10/50/100/500 par année, décennie, sexe, territoire.
- Affiner la règle « mixte » (par période).

## Phase 3 — Enrichissement encyclopédique

- Module Wikidata (SPARQL, cache, reprise, journal, contrôle des ambiguïtés).
- Wiktionnaire : **décision de licence à soumettre** avant toute reprise de texte.
- Origines, étymologies, variantes, personnalités — toujours sourcées. Indicateur de qualité de fiche.
- Recensement des sources étrangères réutilisables.

## Phase 4 — Générateur avancé

Filtres d'origine, style, syllabes, popularité ; tirage aléatoire sans répétition ; mode pondéré ; suggestions d'assouplissement ; favoris (localStorage).

## Phase 5 — Finalisation et déploiement

Modules ludiques, accessibilité approfondie, optimisation des tailles, déploiement GitHub Pages via GitHub Actions.
