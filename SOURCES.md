# Sources

Seules les sources marquées **intégrée** sont réellement utilisées par le site.

## 1. Insee — Fichier des prénoms, édition 2025 — **intégrée (phase 1)**

| | |
|---|---|
| Producteur | Insee (Institut national de la statistique et des études économiques), d'après l'état civil |
| Page | https://www.insee.fr/fr/statistiques/8595130 |
| Fichier utilisé | https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet |
| Date de publication | 16/07/2026 |
| Date de récupération | 24/10/2026 (heure exacte et SHA-256 dans `data/raw/manifest.json` et `data/reports/qualite.md`) |
| Taille | 18 946 679 octets — SHA-256 `f78a41de5b4aa77af3f4ba2fbf29fcdf428250ae9a49a019fb61246269075070` |
| Licence | **Licence Ouverte / Open Licence 2.0 (Etalab)** — conditions générales de réutilisation de l'Insee (https://www.insee.fr/fr/information/2008466), vérifiées le 24/10/2026 : réutilisation libre, y compris commerciale, sous réserve de citer « Source : Insee », d'indiquer la date de mise à jour et de ne pas dénaturer les données. |
| Périmètre | Premier prénom des personnes nées en France, 1900–2025, par sexe ; France, 18 régions, 101 départements |
| Champs | `sexe` (1 masculin, 2 féminin), `prenom`, `periode` (année), `niveau_geographique` (FRANCE / REG / DEP), `geographie` (F ou code), `valeur` (effectif arrondi), `rang` |

Autres fichiers de la même page (non utilisés, le Parquet les contient tous) : CSV national, régional,
départemental ; liste des prénoms attribués au moins 3 fois depuis 1900 **sans effectifs**.

### Particularités méthodologiques (documentées par l'Insee)

1. **Effectifs arrondis au multiple de 5 le plus proche.** Le site affiche toujours « environ ». Les petits effectifs sont peu fiables.
2. **Rang calculé par l'Insee sur les effectifs non arrondis** (par sexe, année, zone ; tirage aléatoire en cas d'égalité). Prénoscope reprend ce rang tel quel, sans jamais le recalculer.
3. Les sommes départementales peuvent différer des valeurs régionales ou nationales (arrondis). Aucun écart n'est « corrigé ».
4. **Géographie du dernier millésime** : une naissance de 1949 à Issy-les-Moulineaux est codée 92 ; Corse en 2A/2B sur toute la période ; Saint-Barthélemy et Saint-Martin ne sont plus inclus dans la Guadeloupe.
5. Avant 2012, les données concernent la France hors Mayotte.
6. Une absence de ligne ne signifie pas zéro naissance. Un effectif de naissances n'est pas un nombre de personnes vivantes.

### Constats faits en inspectant réellement le fichier (24/10/2026)

Détail complet : `data/reports/inspection.json`.

- 6 622 949 lignes : 724 645 nationales, 1 928 764 régionales, 3 969 540 départementales.
- Années 1900 à 2025, toutes numériques. **Aucune année « XXXX »** et **aucun code spécial de prénom** (pas de « _PRENOMS_RARES ») dans ce fichier Parquet, contrairement aux anciennes éditions.
- Aucune valeur nulle, aucun doublon de clé, aucun rang dupliqué ; les rangs vont de 1 à n sans trou dans chacun des 29 792 groupes (sexe × année × zone).
- **Effectif minimal : 5 ; aucune valeur 0.** Les prénoms dont l'effectif arrondi serait 0 (1 ou 2 naissances) sont donc absents de l'année et de la zone concernées.
- Toutes les valeurs sont des multiples de 5. Le classement par rang ne contredit jamais l'ordre des valeurs arrondies.
- 49 163 graphies distinctes au niveau national (52 340 couples prénom/sexe) ; tout prénom présent en région ou département l'est aussi au niveau national.
- Prénoms **tous en majuscules**, accents conservés. Caractères rencontrés : A–Z, `À Â Ä Æ Ç È É Ê Ë Î Ï Ô Ö Ù Û Ü Ÿ`, tiret, apostrophe, espace.
- 3 593 prénoms avec tiret, 92 avec apostrophe, 4 avec une espace (`M BAREK`, `M BARKA`, `M HAMED`, `N DEYE` — probablement des apostrophes perdues ; conservés tels quels, distincts de `M'HAMED` etc.).
- Longueur de 2 à 20 caractères.
- Mayotte (976) présente à partir de 2012, conformément à la documentation.
- 4 750 groupes de graphies différentes ayant la même forme sans accents (ex. ELEA / ELÈA / ELÉA / ELËA / ÉLEA / ÉLÉA) : **non fusionnées**, l'Insee les comptant séparément.

### Dénominateur pour les taux

Le fichier ne fournit pas le nombre total de naissances : voir la source n° 2 ci-dessous et `STATISTIQUES.md`.

## 2. Insee — Naissances vivantes selon le sexe (tableau T35) — **intégrée (phase 2)**

| | |
|---|---|
| Producteur | Insee, statistiques de l'état civil |
| Page | https://www.insee.fr/fr/statistiques/9000187?sommaire=9000195 (« Les naissances en 2025 et en séries longues ») |
| Fichier utilisé | https://www.insee.fr/fr/statistiques/fichier/9000187/t35.xlsx (seul format proposé pour ce tableau) |
| Date de publication | 06/07/2026 |
| Date de récupération | 24/10/2026 (SHA-256 dans `data/raw/manifest.json`) |
| Licence | Licence Ouverte 2.0 (Etalab) — conditions générales de l'Insee |
| Périmètre | Naissances vivantes (et enfants sans vie, non utilisés) par sexe : feuille FM = France métropolitaine 1901–2025 ; feuille FR = France (hors Mayotte jusqu'en 2013) 1994–2025 ; cellules « nd » avant 1994 |
| Usage | Dénominateur des fréquences pour 1 000 naissances, **à partir de 1946** |
| Limites | Pas de série par département ou région selon le **lieu de naissance** (les tableaux départementaux de l'Insee sont selon le domicile de la mère et par millésime) : aucune fréquence territoriale officielle n'est donc calculée ; la géographie utilise un indice relatif (voir `STATISTIQUES.md`). |

Lecture du fichier : le classeur Insee est refusé par la bibliothèque `openpyxl` (métadonnées non standard) ; il est lu
par `pipeline/xlsx.py`, qui n'utilise que la bibliothèque standard de Python.

**Constat de couverture** (somme des effectifs du fichier des prénoms / naissances T35) : 42 % (garçons) et 57 % (filles)
en 1901, 73 à 95 % de 1920 à 1945, 100 à 103 % de 1946 à 1993 (dénominateur métropolitain), 91 à 97 % depuis 1994.
D'où le choix de ne calculer les fréquences qu'à partir de 1946.

## 3. IGN — Contours des régions et départements — **intégrée (phase 2)**

| | |
|---|---|
| Producteur | IGN, Admin Express COG édition 2018 (contours) ; Insee, Code officiel géographique 2018 (codes, noms) |
| Mise en forme | Dépôt « france-geojson » de Grégoire David : https://github.com/gregoiredavid/france-geojson |
| Fichiers utilisés | `regions-avec-outre-mer.geojson`, `departements-avec-outre-mer.geojson` |
| Licence | Licence Ouverte (Etalab), conditions d'Admin Express (indiquées par le dépôt) |
| Périmètre | 18 régions et 101 départements, dont les 5 DROM ; découpage inchangé depuis 2016 (Corse en 2A/2B) |
| Traitement | Simplification (Douglas-Peucker, ≈ 1 km), DROM replacés en encarts, coordonnées arrondies (`pipeline/geo.py`) |
| Contrôle | Les codes de la carte correspondent exactement à ceux du fichier des prénoms (test automatique) |

## 4. Wikidata — prévue (phase 3), non intégrée

https://www.wikidata.org/ — licence CC0. Origines, variantes, personnalités, liens Wikipédia.

## 5. Wiktionnaire — prévue (phase 3), non intégrée

https://fr.wiktionary.org/ — licence CC BY-SA (et GFDL) : attribution et partage dans les mêmes conditions.
**Décision à soumettre en phase 3** : licence compatible pour les données publiées, ou non-reprise des textes.

## 6. Autres sources — à étudier

Statistiques de prénoms d'autres pays légalement réutilisables (à recenser en phase 3 avec URL, producteur,
licence, périmètre, dates, champs, limites). Aucune n'est intégrée.
