# Modèle de données

## Base de travail DuckDB (`data/work/prenoscope.duckdb`, non versionnée)

### Tables remplies en phase 1

**`raw_prenoms`** — copie fidèle du Parquet Insee (6 622 949 lignes), colonnes d'origine.

**`source`** — une ligne par source : `id`, `organisme`, `titre`, `url`, `fichier_url`, `licence`, `millesime`, `date_recuperation`, `sha256`.

**`prenom`** — une ligne par graphie Insee (49 163).

| Colonne | Signification |
|---|---|
| `id` | Identifiant stable = graphie Insee en minuscules (`léa`, `lea`, `marie-claire`, `m'hamed`). Léa et Lea ont deux identifiants. |
| `graphie_insee` | Graphie exacte du fichier (majuscules) — jamais modifiée |
| `graphie_affichage` | Mise en casse pour l'affichage (règle ci-dessous) |
| `norm` | Forme normalisée pour la recherche : minuscules, sans accents, Æ→ae, Œ→oe |
| `nb_lettres` | Lettres seulement (tirets, apostrophes, espaces exclus ; Æ = 1 lettre) |
| `initiale` | Première lettre de `norm` |
| `compose` | Contient un tiret |
| `a_accent` | Contient une lettre accentuée ou une ligature |
| `sexe_usage` | `F`, `M` ou `X` (mixte) — règle ci-dessous |
| `total_f_arrondi`, `total_m_arrondi` | Somme des effectifs nationaux arrondis 1900–2025 (ordre de grandeur, pas un total exact) |
| `premiere_annee`, `derniere_annee` | Première et dernière année présentes au niveau national |
| `lot` | Fichier de détails (2 premières lettres de `norm`) |
| `statut_validation` | `statistique_seule` en phase 1 (aucun enrichissement) |

**`statistique`** — une ligne par prénom × sexe × année × territoire (6 622 949 lignes) :
`prenom_id`, `sexe` (`F`/`M`), `annee`, `niveau` (`FRANCE`/`REG`/`DEP`), `territoire` (`F` ou code Insee),
`valeur_arrondie`, `rang_officiel`, `source_id`, `millesime`.

**`ambiguite_normalisation`** — graphies distinctes partageant la même forme normalisée (4 750 groupes), pour contrôle.

### Tables créées vides (phases suivantes)

| Table | Colonnes principales |
|---|---|
| `origine` | prenom_id, langue, culture, region_pays, justification, source_id, confiance |
| `etymologie` | prenom_id, signification, evolution, alternatives, source_id, statut_verification |
| `variante` | prenom_id, prenom_associe_id, type (orthographique, traduction, diminutif, forme historique…), source_id |
| `personnalite` | nom, prenom_id, wikidata_id, domaine, periode, presentation, url, score_pertinence |
| `anecdote` | prenom_id, titre, texte, categorie, source_id, statut_editorial |

Relations plusieurs-à-plusieurs : un prénom peut avoir plusieurs origines, étymologies, variantes, personnalités.

## Règles documentées

- **Pas de fusion par ressemblance.** Deux graphies différentes chez l'Insee restent deux prénoms, même si leur forme normalisée est identique.
- **Mixte** : un prénom est `X` si les deux sexes l'ont porté et si le sexe le moins représenté atteint **au moins 10 %** du cumul national 1900–2025 (effectifs arrondis). Sinon il prend le sexe majoritaire. Seuil réglable : `SEUIL_MIXTE` dans `pipeline/config.py`. Limite connue : la règle porte sur toute la période (un prénom mixte autrefois mais genré aujourd'hui reste mixte) ; à affiner en phase 2.
- **Filtre « Féminin » / « Masculin »** du site : usage `F` / `M` strict ; les mixtes ont leur propre option.
- **Composé** : contient un tiret. Les prénoms avec apostrophe ou espace ne sont pas comptés comme composés.
- **Affichage** : majuscule initiale et après tiret ou espace ; après une apostrophe, majuscule seulement si elle suit une lettre isolée en début de segment (M'Hamed, O'Bryan) ; sinon minuscule (William's, Gwenc'hlan). C'est une convention d'affichage, la graphie Insee reste la référence.
- **Effectifs** : toujours présentés comme « environ ». Les totaux sont des sommes de valeurs arrondies.
- **Rangs** : rang officiel Insee uniquement. Les éventuels classements calculés (phase 2) seront signalés comme tels.
- **Années absentes** : laissées vides dans les courbes, jamais remplacées par zéro.

## Fichiers publiés (`site/public/data/`)

### `meta.json`
Source (organisme, titre, URL, licence, millésime, date de récupération, SHA-256), années couvertes, nombre de prénoms et de lots, règles.

### `index.v1.json`
```json
{ "version": 1,
  "colonnes": ["id","affichage","norm","sexe","total_f","total_m","premiere_annee","derniere_annee","lettres","accent","compose","lot"],
  "lignes": [["marie","Marie","marie","F",2230220,26755,1900,2025,5,0,0,"ma"], ...] }
```
Une ligne par prénom, triées par total décroissant. `accent` et `compose` valent 0 ou 1.

### `prenoms/<lot>.json`
```json
{ "version": 1,
  "format_serie": ["annee","valeur_arrondie","rang_officiel"],
  "prenoms": { "léa": { "F": [[1900,935,51],[1901,1100,48], ...] } } }
```
Séries **nationales**. Depuis la phase 2, chaque prénom peut aussi porter `"tendances": {"F": ["retour", "vagues"]}`
et `"vagues": {"F": [[1900, 5], [2024, 1]]}` (année et rang lissé des sommets). Les autres indicateurs sont
recalculés par le site (voir `STATISTIQUES.md`).

## Ajouts de la phase 2

### Tables DuckDB

| Table | Contenu |
|---|---|
| `naissances_officielles` | Insee T35 : annee, sexe, champ (`metropole` / `france`), naissances |
| `denominateur` | Dénominateur retenu pour chaque année ≥ 1946 et sexe (métropole avant 1994, France ensuite) |
| `total_fichier` | Somme des effectifs publiés et nombre de prénoms par niveau, territoire, année, sexe |
| `couverture` | Somme nationale du fichier / naissances officielles, par année et sexe |
| `indicateur` | Par prénom et sexe : indicateurs et tendances (JSON) |
| `tendance` | Une ligne par prénom × sexe × catégorie : score de tri et détails chiffrés (JSON) |
| `geo_decennie` | Effectifs par prénom, sexe, niveau (REG/DEP), territoire et décennie |

La table `source` contient désormais une ligne par source (prénoms, T35, contours des régions et des départements).

### Fichiers publiés

| Fichier | Contenu |
|---|---|
| `meta.json` | + `sources` (toutes), `naissances` (dénominateurs par année ≥ 1946), `nb_publies` (prénoms publiés par année et sexe), règles et seuils (`regles.tendances`…) |
| `tendances.json` | `categories.<cat>` = liste `[id, sexe, score, détails]` triée par score décroissant |
| `couverture.json` | Colonnes `annee, sexe, fichier_france, naissances_metropole, naissances_france, ratio, champ` |
| `classements/france/<annee>.json` | `F`/`M` : `top` = `[[id, effectif]…]` (rang = position), `fin` = `[[id, effectif, rang]…]`, `nb_publies` |
| `classements/france-decennies.json` | `decennies.<dec>.F/M` = `[[id, somme des effectifs]…]` (classement calculé) |
| `classements/zones/<REG|DEP>-<code>.json` | `annees.<a>.F/M` (rangs officiels, top 50 régions / 20 départements) et `decennies.<dec>.F/M` (calculé) |
| `geo/prenoms/g_<lot3>.json` | `prenoms.<id>.F/M.REG/DEP` = `[[code, decennie, effectif]…]` ; lot de 3 lettres, préfixe `g_` car `aux`, `con`, `nul`, `prn` sont des noms de fichiers interdits sous Windows |
| `geo/totaux.json` | `totaux.REG/DEP.<code>.F/M.<decennie>` = somme des effectifs publiés (dénominateur des parts locales) |
| `geo/regions.json`, `geo/departements.json` | GeoJSON simplifiés, propriétés `code`, `name`, `outre_mer` |
| `geo/zones.json` | Noms des régions et départements par code |

Fixture de test : `site/tests/fixtures/indicateurs_python.json` (indicateurs Python d'un échantillon de séries).

## Profils de suggestion (`profils.v1.json`)

Un prénom par ligne (≈ 10 000 : au moins 60 naissances depuis 2011, ou tendance « retour »), colonnes compactes comme
`index.v1.json` : `id, affichage, sexe, rec_f, rec_m, rang_f, rang_m, pic, debut, lettres, syllabes, accent, compose, tend, orig, qualite`.

- `rec_f` / `rec_m` : naissances par an, moyenne des 5 dernières années (effectifs arrondis) ;
- `rang_f` / `rang_m` : rang officiel de la dernière année (vide si absent) ;
- `pic` : décennie du record ; `debut` : première année à au moins 50 naissances ;
- `syllabes` : **estimation** par règles (`normalize.nb_syllabes`) ;
- `tend` : codes des tendances (`e` émergent, `p` progression, `r` retour, `v` vagues, `d` déclin, `x` devenu rare) ;
- `orig` : familles d'origine (Wiktionnaire, `config.GROUPES_ORIGINE`) séparées par `|`, vide si inconnue.

Les classes de popularité et de style sont calculées par le site (`lib/suggestions.js`) et documentées dans la page Méthode.

## Ajouts de la phase 3 (enrichissement encyclopédique)

### Tables DuckDB

Tables intermédiaires :

| Table | Contenu |
|---|---|
| `wiktionnaire_entree` | Entrées « Prénom » du Wiktionnaire reliées à un prénom Insee : mot, section, étymologie (texte), API, origines, variantes (JSON), URL |
| `wikidata_prenom` | Éléments Wikidata de type prénom : qid, types, libellé, nombre de liens, article Wikipédia en français, graphies (libellés fr/mul/en et libellé natif) |
| `correspondance_wikidata` | prenom_id, qid, méthode (`graphie_exacte`), statut (`unique`, `ambigu`, `type_incompatible`) |
| `wikidata_variante`, `wikidata_langue`, `wikidata_personnalite` | Relations P460/P1560, P407 et personnes (P735) des éléments retenus |

Tables du modèle (remplies par `pipeline/encyclo.py`) — elles remplacent les tables vides créées en phase 1 :

| Table | Colonnes |
|---|---|
| `etymologie` | prenom_id, texte, source_id, url_source, licence, statut_verification (« source citée, non relue ») |
| `origine` | prenom_id, langue, justification, source_id, url_source, confiance (« déclarée par la source ») |
| `prononciation` | prenom_id, api, source_id, url_source |
| `variante` | prenom_id, libelle, prenom_associe_id (prénom Insee de même graphie, sinon vide), type (`orthographique`, `equivalent_autre_genre`, `diminutif`, `compose`, `apparente`, `reputee_identique`, `traduction`), langue, source_id, url_source |
| `langue_usage` | prenom_id, langue, source_id, url_source (Wikidata P407 : langue d'usage, pas d'origine) |
| `personnalite` | prenom_id, qid, nom, presentation (description Wikidata), naissance, deces, domaines, url (Wikipédia en français), nb_liens, score_pertinence (= nb_liens), source_id |
| `lien_externe` | prenom_id, type (`wiktionnaire`, `wikidata`, `wikipedia`), url, libelle |
| `fiche_qualite` | prenom_id, nombres d'éléments par type, niveau (`complete`, `partielle`, `minimale`) |
| `anecdote` | inchangée, vide : aucune source ouverte et fiable retenue |

`prenom.statut_validation` vaut `enrichi` pour les fiches partielles ou complètes, `statistique_seule` sinon.

**Règle de qualité** : *complète* = au moins une étymologie, une variante et une personnalité ; *partielle* = au moins
un élément encyclopédique sourcé ; *minimale* = statistiques Insee seulement.

**Règle des personnalités** : humains (Q5) dont P735 pointe vers un élément prénom retenu, en premier prénom quand
l'ordre (qualificatif P1545) est indiqué ; article sur Wikipédia en français ; au moins 10 liens vers des projets
Wikimédia ; les 8 plus liés par élément, puis par prénom Insee (dédoublonnés). Score de pertinence = nombre de liens.

### Fichiers publiés

| Fichier | Contenu | Licence |
|---|---|---|
| `index.v1.json` | + colonne `qualite` : `c`, `p` ou `m` | Etalab |
| `encyclo/<lot>.json` | `prenoms.<id>` : `wikidata` [{qid, libelle, statut, article}], `langues`, `variantes` [{libelle, type, id?, url}], `personnalites` [{qid, nom, presentation, naissance, deces, domaines, url, liens}], `qualite` | CC0 |
| `wiktionnaire/<lot>.json` | `prenoms.<id>` : `entrees` [{mot, section, etymologie, api, origines, url}], `variantes` [{libelle, type, id?, langue?}] ; en-tête `licence` et `attribution` | CC BY-SA 4.0 |
