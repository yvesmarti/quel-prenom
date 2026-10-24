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
