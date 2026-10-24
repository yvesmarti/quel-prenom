# Rapport de qualité — données Prénoscope

Généré automatiquement par `pipeline/quality_report.py`. Ne pas modifier à la main.

## Fichiers sources
- `insee-prenoms-2025` : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet — 18,946,679 octets — SHA-256 `f78a41de5b4aa77a…` — récupéré le 2026-10-24T14:53:37+00:00
- `insee-naissances-t35-2025` : https://www.insee.fr/fr/statistiques/fichier/9000187/t35.xlsx — 33,548 octets — SHA-256 `d14c2cc2faa18eb7…` — récupéré le 2026-10-24T15:14:36+00:00
- `ign-contours-departements-2018` : https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson — 3,722,544 octets — SHA-256 `0c331e85eef244d8…` — récupéré le 2026-10-24T15:14:36+00:00
- `ign-contours-regions-2018` : https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-avec-outre-mer.geojson — 1,746,989 octets — SHA-256 `a573b672264184d1…` — récupéré le 2026-10-24T15:14:36+00:00

## Couverture du fichier des prénoms (somme des effectifs nationaux / naissances officielles T35)
Champ du dénominateur : métropole avant 1994, France entière ensuite. Détail complet : `site/public/data/couverture.json`.

| Année | Filles | Garçons | Champ T35 |
|---|---|---|---|
| 1901 | 57.0% | 41.6% | metropole |
| 1920 | 81.0% | 73.3% | metropole |
| 1940 | 92.9% | 89.5% | metropole |
| 1945 | 92.8% | 89.6% | metropole |
| 1946 | 102.5% | 102.2% | metropole |
| 1960 | 103.1% | 103.0% | metropole |
| 1980 | 100.8% | 100.6% | metropole |
| 1993 | 100.3% | 100.4% | metropole |
| 1994 | 96.1% | 96.3% | france |
| 2000 | 95.9% | 96.6% | france |
| 2010 | 93.8% | 94.5% | france |
| 2020 | 91.8% | 92.6% | france |
| 2025 | 91.0% | 92.0% | france |

## Tendances détectées (définitions : STATISTIQUES.md)
declin : 598 · devenu_rare : 269 · emergent : 479 · progression : 463 · retour : 26 · vagues : 111

## Volumes constatés
- Lignes brutes : 6,622,949 (France 724,645 · régions 1,928,764 · départements 3,969,540)
- Années couvertes : 1900–2025
- Prénoms distincts (graphies INSEE) : 49,163 — couples prénom/sexe : 52,340
- Prénoms avec statistiques : 49,163
- Usage (règle mixte ≥ 10%) : féminin 25,881 · masculin 21,755 · mixte 1,527
- Prénoms portés au moins une fois par les deux sexes : 3,177
- Composés (avec tiret) : 3,593 — avec accent ou ligature : 7,151
- Présents une seule année au niveau national : 13,218

## Enrichissement (phase 3, non commencé)
- Fiches enrichies : 0 · étymologies sourcées : 0 · personnalités : 0
- Toutes les fiches sont donc « minimales » (statistiques INSEE seules).

## Contrôles et anomalies
- Valeurs nulles : aucune · doublons de clé : 0 · rangs dupliqués : 0
- Valeurs à 0 : 0 · valeurs non multiples de 5 : 0 · valeur minimale : 5
- Groupes dont les rangs ne sont pas contigus (1..n) : 0 · inversions rang/valeur : 0
- Années non numériques (type « XXXX ») : 0 · codes spéciaux de prénom (type « _PRENOMS_RARES ») : 0
- Prénoms contenant une espace (probable substitut d'apostrophe, conservés tels quels) : M BAREK, M BARKA, M HAMED, N DEYE
- Graphies distinctes partageant la même forme normalisée : 4,750 groupes (10,454 prénoms), **non fusionnées**. Exemples :
  - EDEN / EDÈN / EDÉN / EDËN / ÉDEN / ËDEN
  - ELEA / ELÈA / ELÉA / ELËA / ÉLEA / ÉLÉA
  - ELENA / ELÈNA / ELÉNA / ÉLENA / ÉLÈNA / ÉLÉNA
  - ELEONORE / ELÈONORE / ELÉONORE / ÉLEONORE / ÉLÈONORE / ÉLÉONORE
  - ENES / ENÈS / ÈNES / ÈNÈS / ÉNES / ÉNÈS
  - ESTEBAN / ESTEBÀN / ESTÈBAN / ESTÉBAN / ESTÉBÀN / ÉSTÉBAN
  - GWENAELLE / GWENAËLLE / GWENÄELLE / GWÉNAELLE / GWÉNAËLLE / GWËNAELLE
  - HELENA / HELÉNA / HÈLÉNA / HÉLENA / HÉLÈNA / HÉLÉNA

## Fichiers publiés
- Index : 2 942 Ko brut, 675 Ko compressé (gzip)
- Détails : 353 lots, 11 085 Ko brut au total, 3 434 Ko compressé ; plus gros lot : ma.json (868 Ko)
- Classements nationaux : 126 fichier(s), 2 136 Ko brut, 741 Ko compressé ; plus gros : 1950.json (17 Ko)
- Classements nationaux par décennie : 1 fichier(s), 44 Ko brut, 14 Ko compressé ; plus gros : france-decennies.json (44 Ko)
- Classements territoriaux : 119 fichier(s), 11 900 Ko brut, 2 249 Ko compressé ; plus gros : REG-11.json (219 Ko)
- Données géographiques par prénom : 2638 fichier(s), 18 666 Ko brut, 4 004 Ko compressé ; plus gros : g_mar.json (862 Ko)
- Fonds de carte et totaux : 4 fichier(s), 353 Ko brut, 103 Ko compressé ; plus gros : departements.json (211 Ko)
- Tendances : 1 fichier(s), 188 Ko brut, 28 Ko compressé ; plus gros : tendances.json (188 Ko)
- Couverture : 1 fichier(s), 12 Ko brut, 4 Ko compressé ; plus gros : couverture.json (12 Ko)
- Meta : 1 fichier(s), 10 Ko brut, 3 Ko compressé ; plus gros : meta.json (10 Ko)
