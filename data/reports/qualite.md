# Rapport de qualité — données Prénoscope

Généré automatiquement par `pipeline/quality_report.py`. Ne pas modifier à la main.

## Fichier source
- URL : https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet
- Taille : 18,946,679 octets — SHA-256 `f78a41de5b4aa77af3f4ba2fbf29fcdf428250ae9a49a019fb61246269075070`
- Récupéré le : 2026-10-24T14:53:37+00:00

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
- Détails : 353 lots, 10 973 Ko brut au total, 3 399 Ko compressé ; plus gros lot : ma.json (857 Ko)
