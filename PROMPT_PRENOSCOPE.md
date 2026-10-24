# PROJET PRÉNOSCOPE — Générateur et encyclopédie interactive des prénoms

> Ce fichier est le cahier des charges du projet. Garde-le à la racine du dépôt et relis-le au début de chaque session.

## 0. À lire en premier : façon de travailler

- Je ne suis pas développeur. Quand tu me demandes de lancer une commande, dis en une phrase ce qu'elle fait. Explications courtes, pas de longs paragraphes.
- Avant d'écrire du code, vérifie les prérequis installés sur ma machine (Python, Node.js/npm, Git) et dis-moi précisément ce qui manque et comment l'installer.
- Initialise un dépôt Git. Fais un commit à chaque étape cohérente avec un message clair en français.
- **Cette session couvre uniquement la phase 1** (section 13). Une fois la phase 1 terminée et testée : commit, bilan (section 14), puis arrête-toi et attends mes instructions. Ne commence pas les phases 2 à 5.
- Si une décision est réellement bloquante, pose-moi la question. Sinon, documente ton choix et avance.

## 1. Mission générale

Développer une application web francophone, **Prénoscope** : une encyclopédie interactive des prénoms, pas un simple générateur.

Elle associe :
- une base très importante (plusieurs dizaines de milliers de prénoms) ;
- un moteur de découverte multicritère ;
- des fiches encyclopédiques ;
- des statistiques historiques et géographiques ;
- des informations étymologiques et culturelles sourcées ;
- des personnalités associées ;
- des fonctions ludiques de sélection et de comparaison ;
- une architecture permettant d'enrichir et d'actualiser les données.

Public principal : futurs parents. Expérience agréable, intuitive, riche, parfois surprenante.

**Exigence fondamentale : aucune donnée inventée.** Statistiques issues de sources officielles ; informations historiques, culturelles et étymologiques documentées.

## 2. Contraintes techniques

- Hébergement gratuit : GitHub Pages ou Cloudflare Pages (déploiement via GitHub Actions si GitHub Pages).
- Frontend : Vue 3 + Vite (TypeScript facultatif ; privilégie la lisibilité).
- Préparation des données : Python.
- Base de travail : DuckDB (lit le Parquet INSEE directement) ; SQLite acceptable si justifié.
- Données publiées : fichiers JSON optimisés, découpés, compressibles.
- Graphiques : Apache ECharts ou Chart.js.
- Cartographie : GeoJSON + bibliothèque légère.
- Favoris : localStorage.
- Aucun backend, aucun compte, aucun service payant ni clé API pour le site publié.
- Projet compréhensible et maintenable par une personne aux connaissances limitées en programmation : README en français, scripts simples, structure explicite.
- Les données brutes téléchargées (`data/raw/`) et la base de travail ne sont pas versionnées dans Git (`.gitignore`) ; elles se reconstruisent par script.

## 3. Constitution de la base de données (priorité absolue)

### 3.1 Source principale : INSEE — Fichier des prénoms, millésime 2025 (paru le 16/07/2026)

Page : https://www.insee.fr/fr/statistiques/8595130

Fichiers disponibles (vérifiés) :
- Parquet unique national + régional + départemental, 1900-2025 (~18 Mo) :
  https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet
  → **source à privilégier** pour le pipeline.
- CSV national (~725 000 lignes) : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025-nat_csv.zip
- CSV régional (~2 M lignes) : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025-reg_csv.zip
- CSV départemental (~4 M lignes) : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025-dpt_csv.zip
- Liste des prénoms par sexe attribués au moins 3 fois depuis 1900, **sans effectifs** : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025-liste_csv.zip

Variables : SEXE (1 masculin, 2 féminin), PRENOM (premier prénom), PERIODE (année), VALEUR, RANG ; dans le Parquet : NIVEAU_GEOGRAPHIQUE (FRANCE / REG / DEP) et GEOGRAPHIE (F, code région ou code département).

**Particularités méthodologiques à respecter et documenter dans SOURCES.md :**
1. **VALEUR est arrondie au multiple de 5 le plus proche.** Toujours afficher « environ » ou équivalent ; ne jamais présenter ces chiffres comme exacts. Les très petits effectifs sont donc peu fiables.
2. **RANG est calculé par l'INSEE sur les effectifs non arrondis** (par sexe, année, zone), avec tri aléatoire en cas d'égalité. Utiliser ce rang officiel ; ne pas le recalculer à partir des valeurs arrondies.
3. Les sommes départementales peuvent différer des valeurs régionales ou nationales (arrondis). Ne pas « corriger » les écarts.
4. **Géographie du dernier millésime** : un département affiché peut ne pas exister à l'année de naissance (ex. né en 1949 à Issy-les-Moulineaux → codé 92). Corse découpée en 2A/2B. Saint-Barthélemy et Saint-Martin ne sont plus inclus dans la Guadeloupe.
5. Avant 2012, les données ne concernent que la France hors Mayotte.
6. **Inspecte réellement les données** avant de conclure : présence éventuelle de codes spéciaux (agrégats de prénoms rares, prénom inconnu, année manquante…), valeurs 0 après arrondi, doublons, graphies avec tirets/apostrophes. Documente ce que tu trouves au lieu de supposer.
7. Absence d'une ligne ≠ zéro naissance. Effectifs de naissances ≠ personnes vivantes.
8. Vérifier et documenter la licence de réutilisation des données INSEE (normalement Licence Ouverte Etalab — à confirmer sur le site).

Script Python attendu :
- télécharger (avec somme de contrôle et date de récupération enregistrées) ;
- vérifier le fichier (colonnes, années, nombre de lignes) ;
- importer dans DuckDB ;
- normaliser pour la recherche (sans accents, minuscules) **en conservant la graphie originale** ;
- détecter les doublons et cas ambigus ;
- calculer les statistiques dérivées ;
- générer les JSON du frontend ;
- produire un rapport de qualité.

**Dénominateur pour les taux :** le fichier ne fournit pas le total des naissances, et la somme des effectifs par prénom ne le reconstitue pas (arrondis). Les taux pour 1 000 naissances nécessitent une série officielle séparée des naissances (INSEE, état civil) par année, sexe et territoire. À identifier et documenter en phase 2 ; en phase 1, se limiter aux effectifs et rangs.

### 3.2 Wikidata (phase 3)

https://www.wikidata.org/ — https://query.wikidata.org/ — licence CC0.

À exploiter : prénoms internationaux, identifiants, origines documentées, variantes, formes alternatives, personnalités, liens Wikipédia.
Module d'enrichissement par API ou SPARQL avec pagination, cache local, respect des limites (User-Agent identifié), reprise après interruption, journal d'erreurs, contrôle des correspondances ambiguës.
Une personne portant un prénom n'est pas automatiquement une référence pertinente : sélection éditoriale ou score de pertinence explicable.

### 3.3 Wiktionnaire (phase 3)

https://fr.wiktionary.org/ — licence CC BY-SA (et GFDL) : la réutilisation impose l'attribution et le partage dans les mêmes conditions des contenus repris.
**Décision à me soumettre en phase 3** : licence des données publiées du projet compatible avec ce partage, ou non-reprise des textes du Wiktionnaire.
Privilégier les dumps officiels (dumps.wikimedia.org) ou des extractions structurées existantes ; pas d'extraction massive du site.

### 3.4 Sources supplémentaires

Identifier d'autres jeux ouverts fiables (statistiques de prénoms d'autres pays légalement réutilisables).
Pour chaque source dans SOURCES.md : URL, producteur, licence, périmètre, date de publication, date de récupération, champs exploitables, limites.
Ne pas intégrer une source à la licence incompatible.

## 4. Modèle de données

Entités minimales :

- **Prenom** : identifiant stable, graphie principale, graphie normalisée, sexe statistique ou usage documenté, nombre de lettres, syllabes si vérifiable, initiale, terminaison, composé ou non, catégories stylistiques, statut de validation.
- **Origine** : langue, culture, région/pays, justification, source, niveau de confiance.
- **Etymologie** : signification, évolution, alternatives, source, statut de vérification.
- **Variante** : prénom source, prénom associé, type (orthographique, traduction, diminutif, forme historique…).
- **Statistique** : prénom, sexe, année, territoire, effectif publié (arrondi), rang officiel, source et millésime.
- **Personnalite** : nom, prénom associé, identifiant Wikidata, domaine, période, présentation courte, URL, score de pertinence.
- **Anecdote** : prénom, titre, texte, catégorie, source, statut éditorial.
- **Source** : identifiant, organisme, URL, licence, date de consultation.

Relations plusieurs-à-plusieurs nécessaires. Ne pas fusionner des prénoms parce que leurs graphies normalisées se ressemblent (Léa ≠ Lea dans les données). Un prénom peut avoir plusieurs origines, significations et usages.

Le sexe : un même prénom peut apparaître pour les deux sexes ; la notion de « mixte » doit reposer sur une règle chiffrée documentée.

## 5. Moteur de recherche et de génération (phase 4, sauf recherche/filtres de base en phase 1)

Filtres : sexe (féminin, masculin, mixte, tous), origine, nombre de lettres, initiale, terminaison, syllabes si disponible, accents, composé, popularité, style (classique, ancien, rétro, moderne, rare, international), France ou base internationale.
Les catégories subjectives reposent sur des règles documentées ou une classification éditoriale, jamais arbitraire.

Fonctionnement : calcul des éligibles, nombre de résultats, tirage aléatoire relançable sans répétition dans la session, ouverture de la fiche, ajout aux favoris. Mode pondéré facultatif. Ne pas favoriser systématiquement les prénoms populaires. Proposer des assouplissements si aucun résultat.

## 6. Fiches encyclopédiques

Graphie, genre/usage, origine, étymologie, signification, prononciation, variantes, diminutifs, personnalités, anecdotes, popularité, statistiques territoriales, prénoms similaires, sources.
Champs non documentés : omis ou signalés comme tels. Jamais d'étymologie ou d'anecdote générée sans source.
Indicateur de qualité de fiche : complète, partielle, minimale.

## 7. Module statistique (phase 2)

- Popularité historique : courbe depuis 1900, effectif, rang, année record, évolution 5/10/20 ans, comparaison, position parmi les prénoms du même sexe. Distinguer effectifs absolus et fréquences relatives.
- Tendances : émergents, forte progression, déclin, retours, plusieurs vagues, devenus rares. **Définitions mathématiques documentées**, seuils minimaux d'effectif (en tenant compte de l'arrondi à 5), lissage.
- Géographie : choroplèthes, classements territoriaux, comparaisons, popularité relative, régions de prédilection. Lieu de naissance ≠ origine culturelle. Outre-mer à traiter correctement.
- Classements : top 10/50/100/500, par année, décennie, sexe, région, département ; plus rares ; plus fortes progressions. Rangs officiels conservés ; classements calculés identifiés comme tels.

## 8. Modules ludiques (phases ultérieures, architecture modulaire dès le départ)

Machine à remonter le temps ; Pépites oubliées ; Prénoms en devenir (sans prétendre prédire) ; Duels ; Favoris ; Comparateur ; Découverte internationale ; Sélection en couple (export/import de favoris sans serveur).

## 9. Interface

Élégante et chaleureuse ; fond clair, tons crème, couleurs douces ; typographie lisible et raffinée ; cartes aérées ; animations discrètes ; pas de clichés autour de la maternité.
Accessibilité : bon contraste, utilisable par les personnes daltoniennes, navigation clavier, libellés accessibles, états de chargement, gestion d'erreurs, recherche rapide, mobile en priorité. La rapidité prime sur la richesse.

## 10. Architecture et performances

- Index léger des prénoms chargé au démarrage (mesure et indique sa taille réelle, compressée et non compressée).
- Fichiers détaillés par prénom (ou par lot) chargés à la demande.
- Agrégats pré-calculés, cache, fichiers versionnés, chargement progressif.
- Consultation publique sans API externe. Internet nécessaire seulement pour la préparation des données.
- Ne pas publier la base complète si des fichiers statiques suffisent.

## 11. Qualité et vérification

Tests automatiques : intégrité, doublons, accents, variantes, liens prénoms/statistiques, totaux et classements (en tenant compte des arrondis), filtres, tirage aléatoire, JSON, liens entre fiches.

Rapport de qualité : nombre total de prénoms, nombre avec statistiques, fiches enrichies, étymologies sourcées, personnalités, fiches incomplètes, erreurs ou ambiguïtés.

L'interface ne présente jamais comme certaine une information insuffisamment documentée.

## 12. Documentation

README.md, ARCHITECTURE.md, SOURCES.md, DATA_MODEL.md, ROADMAP.md (en français).

Commandes documentées pour : installer les dépendances ; télécharger les données ; construire la base ; lancer les enrichissements ; générer les fichiers statiques ; démarrer le site en local ; construire la production ; publier. Commandes simples et reproductibles (une commande par étape, idéalement regroupées dans un script unique « tout reconstruire »).

## 13. Plan de développement

- **Phase 1 — Fondations (CETTE SESSION UNIQUEMENT)** : inspecter le répertoire ; vérifier les prérequis ; définir l'architecture ; créer la structure ; pipeline INSEE (Parquet) ; import national (et régional/départemental en base, même si l'interface ne les exploite pas encore) ; modèle de données ; premier index complet ; interface minimale de recherche et de filtrage sur les vrais prénoms (sexe, lettres, initiale, terminaison, accents, composé) avec une fiche simple (courbe nationale effectif + rang).
- Phase 2 — Statistiques.
- Phase 3 — Enrichissement encyclopédique.
- Phase 4 — Générateur avancé.
- Phase 5 — Finalisation et déploiement.

## 14. Instructions de travail immédiates

Dans cet ordre :
1. Analyse les exigences ; liste les difficultés techniques et méthodologiques.
2. Vérifie les sources, formats et licences (section 3).
3. Propose l'architecture de fichiers.
4. Crée la documentation initiale.
5. Implémente la phase 1.
6. Télécharge et traite le Parquet INSEE. En cas d'échec réseau, prépare les scripts et explique précisément comment les exécuter.
7. Construis l'interface minimale sur les données réellement importées.
8. Exécute les tests.
9. Commit, puis bilan : éléments terminés, chiffres réellement constatés dans les données (nombre de prénoms, de lignes, années couvertes, anomalies trouvées), taille des fichiers publiés, prochaines étapes. Puis arrête-toi.

**Consignes impératives :**
- Pas de fausse base de prénoms pour simuler le fonctionnement.
- Aucun chiffre, étymologie ou personnalité inventés.
- N'annonce pas qu'une source est intégrée si elle ne l'est pas.
- Pas de limitation arbitraire à quelques centaines de prénoms.
- Pas de scraping contraire aux conditions des sources.
- Absence de données ≠ zéro.
- Fiabilité avant quantité.
- En cas de difficulté : documente-la et poursuis les autres travaux possibles.
- Explique brièvement les décisions techniques importantes.
