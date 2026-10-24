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

## Phase 3 — Enrichissement encyclopédique (en cours ; partie publiée dans le MVP)

- [x] Décision de licence (24/10/2026) : textes du Wiktionnaire repris sous CC BY-SA 4.0, fichiers séparés (`LICENCES.md`)
- [x] Wiktionnaire (extraction kaikki.org) : étymologies (3 545 prénoms), langues d'origine, prononciations, variantes
- [x] Wikidata : 18 086 prénoms Insee reliés (graphie exacte, type compatible, ambiguïtés signalées), variantes, langues d'usage
- [x] Qualité des fiches (complète / partielle / minimale) et filtre dans la recherche
- [x] Sources étrangères identifiées (États-Unis, Angleterre et pays de Galles, Belgique, Québec, Suisse) — non intégrées
- [ ] **Personnalités** : la première méthode était trop lente (≈ 11 h, limitation de débit) ; nouvelle méthode en deux
      requêtes (candidats légers, puis détails des 8 retenus) à terminer, puis `WIKIDATA_PERSONNALITES = True`
- [ ] Anecdotes : aucune source ouverte et fiable identifiée

## MVP en ligne (24/10/2026)

- [x] Licence du code : EUPL 1.2
- [x] Publication automatique sur GitHub Pages (`.github/workflows/deploy.yml`, guide `DEPLOIEMENT.md`)
- [ ] Création du dépôt et premier envoi (par le porteur du projet)

## Phase 4 — Générateur avancé

Filtres d'origine, style, syllabes, popularité ; tirage aléatoire sans répétition ; mode pondéré ; suggestions d'assouplissement ; favoris (localStorage).

## Phase 5 — Finalisation et déploiement

Modules ludiques, accessibilité approfondie, optimisation des tailles, déploiement GitHub Pages via GitHub Actions.
