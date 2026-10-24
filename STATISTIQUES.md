# Méthodes statistiques (phase 2)

Toutes les règles ci-dessous sont appliquées par `pipeline/stats.py` (tendances, agrégats) et
`site/src/lib/` (indicateurs affichés, géographie). Les seuils sont réglables dans `pipeline/config.py`
(`TENDANCES`, `EVOLUTIONS`, `GEO_MIN_INDICE`…) et repris automatiquement par le site via `meta.json`.

Notations : **Y** = dernière année du millésime (2025) ; *effectif* = valeur arrondie au multiple de 5 publiée
par l'Insee ; *rang* = rang officiel Insee (jamais recalculé).

## 1. Effectifs absolus et fréquences relatives

- **Effectif** : toujours présenté comme « environ ». Les sommes d'effectifs (totaux, décennies) sont des sommes
  de valeurs arrondies, donc des ordres de grandeur.
- **Fréquence** = effectif / naissances vivantes du même sexe × 1 000 (« pour 1 000 naissances »).
  - Dénominateur : Insee, état civil, tableau **T35** (naissances vivantes selon le sexe).
  - Publiée **à partir de 1946** seulement : avant, le fichier des prénoms ne retrouve que 42 à 95 % des naissances
    officielles (voir § 6), ce qui fausserait les fréquences.
  - 1946–1993 : dénominateur = **France métropolitaine** (seule série disponible) alors que le fichier inclut
    l'outre-mer → fréquences surestimées d'environ 1 à 3 %.
  - Depuis 1994 : dénominateur = **France entière** (hors Mayotte jusqu'en 2013 ; le fichier des prénoms l'inclut dès
    2012 → légère surestimation en 2012–2013).

## 2. Indicateurs d'une fiche (par sexe)

| Indicateur | Définition |
|---|---|
| Dernière année | Rang officiel en Y, nombre de prénoms publiés cette année-là pour ce sexe, effectif et fréquence. « Absent » si le prénom n'a pas de ligne en Y. |
| Meilleur rang | Plus petit rang officiel ; en cas d'égalité, la première année. |
| Année la plus forte | Plus grand effectif (toutes années) ; en cas d'égalité, la première année. |
| Fréquence record | Plus grande fréquence depuis 1946. |
| Évolution sur k ans (k = 5, 10, 20) | Fréquence moyenne sur [Y-2..Y] divisée par la fréquence moyenne sur [Y-k-2..Y-k], moins 1. Non calculée si l'effectif moyen est inférieur à **10 naissances/an** dans l'une des deux fenêtres (arrondi à 5 trop grossier). |
| Sommets de popularité | Voir « vagues » ci-dessous. |

Ces indicateurs sont calculés par le site à partir des séries publiées. Le même calcul existe en Python ;
le test `site/tests/statistiques.test.js` vérifie que les deux donnent le même résultat sur un échantillon de
358 séries exporté par le pipeline (`site/tests/fixtures/indicateurs_python.json`).

## 3. Tendances

Catégories non exclusives, calculées par prénom **et par sexe**. Une année absente du fichier compte pour
**0** dans les moyennes (elle correspond à un effectif arrondi à 0, soit au plus 2 naissances) ; elle n'est jamais
affichée comme 0. Fenêtres : *récente* = [Y-4..Y] (2021–2025), *ancienne* = [Y-14..Y-10] (2011–2015).

| Catégorie | Règle (valeurs actuelles) |
|---|---|
| **Émergent** | Première apparition nationale en Y-19 (2006) ou après, et effectif moyen ≥ 20/an sur la fenêtre récente. |
| **Forte progression** | Fréquence moyenne récente ≥ 2 × fréquence moyenne ancienne ; effectif récent ≥ 50/an et ancien ≥ 10/an (sinon c'est un émergent). |
| **En déclin** | Fréquence récente ≤ 0,5 × fréquence ancienne, pour un effectif ancien ≥ 50/an. |
| **Devenu rare** | Moyenne mobile sur 5 ans de l'effectif ≥ 500/an à son maximum, et effectif récent ≤ 20/an. |
| **Plusieurs vagues** | Au moins deux sommets de popularité (définition ci-dessous). |
| **Retour** | Un sommet avant 1960 et un autre depuis Y-14 (2011), tous deux au rang lissé ≤ 100. |

**Sommets de popularité (« vagues »)** — calculés sur le rang, qui ne dépend ni du nombre total de naissances
(baby-boom) ni de la couverture incomplète du fichier avant 1946 :
1. série annuelle du rang officiel, 1900–Y ; une année absente reçoit le rang « nombre de prénoms publiés + 1 » ;
2. lissage : moyenne mobile centrée sur 5 ans de log10(rang) ;
3. un sommet est un maximum local de popularité dont la **proéminence** atteint log10(4) ≈ 0,6, c'est-à-dire que
   le rang doit être au moins 4 fois moins bon dans le creux qui le sépare d'un sommet plus haut ; un côté qui
   atteint le bord de la série sans rencontrer de sommet plus haut est « ouvert » et n'est pas pris en compte
   (la vague peut se poursuivre hors de la période observée) ;
4. seuls les sommets au rang lissé ≤ 300 sont retenus.

Résultats du millésime 2025 : émergents 479 · forte progression 463 · déclin 598 · devenus rares 269 ·
plusieurs vagues 111 · retours 26 (Gabriel, Louise, Louis, Alice, Jules, Arthur, Rose…).

Les tests `tests/test_stats.py` vérifient que chaque prénom classé respecte la définition de sa catégorie et
quelques cas historiques connus (Louise : retour ; Sylvie : devenu rare).

## 4. Classements

- **Par année** (France, régions, départements) : **rangs officiels Insee**. Le fichier publie les rangs de 1 à n
  sans trou ni ex æquo (contrôlé) ; le site affiche le rang = position dans la liste.
  - France : top 500 et les 50 derniers rangs (« fin de classement » = plus petits effectifs publiés).
  - Régions : top 50 par an ; départements : top 20 par an (limite fixée pour la taille du site).
- **Par décennie** : **classement calculé** par Prénoscope (somme des effectifs arrondis de la décennie), signalé
  comme tel ; les ex æquo partagent le même rang. France : top 100 ; régions 50 ; départements 20.
  La décennie 2020 ne couvre que 2020–2025.
- **Plus fortes progressions** : page Tendances, catégorie « Forte progression », triée par rapport de fréquences.

## 5. Géographie

- Niveau régional ou départemental, **lieu de naissance**, découpage territorial actuel (Insee).
- Agrégation par décennie (et « toute la période »).
- **Part locale** = effectif du prénom dans la zone / somme des effectifs publiés dans la zone (même sexe, même période).
- **Indice de spécificité** = part locale / part dans l'ensemble des zones du même niveau × 100. 100 = comme ailleurs ;
  200 = deux fois plus fréquent. Les deux parts reposent sur le même type de dénominateur (effectifs publiés au même
  niveau), ce qui limite le biais des prénoms rares non publiés, plus nombreux à l'échelle départementale (selon l'année et le sexe, la somme des
  effectifs départementaux ne représente que 73 à 98 % de la somme nationale).
- Indice **non calculé sous 20 naissances** dans la zone et la période (zone grise).
- **Zones de prédilection** : les 5 zones à l'indice le plus élevé parmi celles où il est calculé.
- Outre-mer : les cinq DROM sont affichés en encarts à l'ouest de la métropole (position et échelle conventionnelles).
- Limites : un département affiché peut ne pas avoir existé à l'époque (géographie actuelle) ; Mayotte n'est présente
  qu'à partir de 2012 ; le lieu de naissance n'est pas une origine culturelle.

## 6. Couverture du fichier des prénoms

Rapport « somme des effectifs nationaux / naissances officielles T35 », par sexe (détail : `site/public/data/couverture.json`,
graphique sur la page Méthode du site) :

| Période | Filles | Garçons | Interprétation |
|---|---|---|---|
| 1901 | 57 % | 42 % | Fichier incomplet pour les générations anciennes, davantage pour les garçons. |
| 1920–1945 | 81–95 % | 73–92 % | Rattrapage progressif. |
| 1946–1993 | 100–103 % | 100–103 % | Dénominateur métropolitain, numérateur avec outre-mer. |
| 1994–2025 | 91–96 % | 92–97 % | Prénoms trop rares non publiés ; part en baisse avec la diversification des prénoms. |

Hypothèse plausible mais **non documentée par l'Insee** pour l'écart d'avant 1946 : le fichier serait constitué à partir
de personnes encore en vie lors de la constitution des répertoires (mortalité, notamment masculine pendant les guerres).
Prénoscope se contente de constater l'écart et de ne pas calculer de fréquence sur cette période.
