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

### Dénominateur pour les taux (phase 2)

Le fichier ne fournit pas le nombre total de naissances, et la somme des effectifs arrondis ne le reconstitue pas.
Les taux « pour 1 000 naissances » nécessiteront une série officielle séparée (Insee, état civil, naissances par
année, sexe et territoire), à identifier en phase 2. **En phase 1, seuls effectifs et rangs sont affichés.**

## 2. Wikidata — prévue (phase 3), non intégrée

https://www.wikidata.org/ — licence CC0. Origines, variantes, personnalités, liens Wikipédia.

## 3. Wiktionnaire — prévue (phase 3), non intégrée

https://fr.wiktionary.org/ — licence CC BY-SA (et GFDL) : attribution et partage dans les mêmes conditions.
**Décision à soumettre en phase 3** : licence compatible pour les données publiées, ou non-reprise des textes.

## 4. Autres sources — à étudier

Statistiques de prénoms d'autres pays légalement réutilisables (à recenser en phase 3 avec URL, producteur,
licence, périmètre, dates, champs, limites). Aucune n'est intégrée.
