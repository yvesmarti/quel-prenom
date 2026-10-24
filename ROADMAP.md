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

## Phase 2 — Statistiques ✅ (24/10/2026)

- [x] Dénominateur officiel identifié et intégré : Insee T35 (naissances par sexe), fréquences pour 1 000 depuis 1946
- [x] Couverture du fichier mesurée et documentée (incomplet avant 1946)
- [x] Indicateurs de fiche : dernière année, meilleur rang, record, fréquence record, évolutions 5/10/20 ans
- [x] Tendances chiffrées : émergents, forte progression, déclin, devenus rares, plusieurs vagues, retours
- [x] Comparaison de prénoms sur la courbe (jusqu'à 4)
- [x] Cartes régionales et départementales (indice de spécificité, effectifs, par décennie), outre-mer en encarts
- [x] Classements : par année (officiels) et par décennie (calculés), France / région / département, fin de classement
- [x] Page Méthode (sources, couverture, définitions)
- [x] Tests : pytest 52, vitest 18

Reste à faire ou à décider plus tard :
- Fréquences territoriales officielles : aucune série de naissances par lieu de naissance et par année n'a été trouvée.
- Règle « mixte » par période (aujourd'hui sur 1900–2025).
- Volume des fichiers publiés (≈ 50 Mo au total, chargés à la demande) : à optimiser en phase 5 si besoin.

## Phase 3 — Enrichissement encyclopédique

- Module Wikidata (SPARQL, cache, reprise, journal, contrôle des ambiguïtés).
- Wiktionnaire : **décision de licence à soumettre** avant toute reprise de texte.
- Origines, étymologies, variantes, personnalités — toujours sourcées. Indicateur de qualité de fiche.
- Recensement des sources étrangères réutilisables.

## Phase 4 — Générateur avancé

Filtres d'origine, style, syllabes, popularité ; tirage aléatoire sans répétition ; mode pondéré ; suggestions d'assouplissement ; favoris (localStorage).

## Phase 5 — Finalisation et déploiement

Modules ludiques, accessibilité approfondie, optimisation des tailles, déploiement GitHub Pages via GitHub Actions.
