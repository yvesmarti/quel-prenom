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
Séries **nationales** uniquement en phase 1. Le régional et le départemental sont en base, publiés en phase 2.
