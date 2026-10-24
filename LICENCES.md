# Licences des données publiées

Décision du 24/10/2026 (phase 3) : les textes du Wiktionnaire sont **repris** et publiés sous **CC BY-SA 4.0**,
dans des fichiers séparés, avec attribution. Le reste des données garde la licence de sa source.

| Fichiers publiés (`site/public/data/`) | Contenu | Licence |
|---|---|---|
| `index.v1.json`, `meta.json`, `prenoms/`, `classements/`, `tendances.json`, `couverture.json`, `geo/prenoms/`, `geo/totaux.json` | Données Insee et calculs de Prénoscope | Licence Ouverte 2.0 (Etalab) — « Source : Insee » |
| `geo/regions.json`, `geo/departements.json`, `geo/zones.json` | Contours IGN simplifiés, noms Insee | Licence Ouverte 2.0 (Etalab) — « Source : IGN, Insee » |
| `encyclo/` | Éléments Wikidata, langues d'usage, variantes, personnalités | CC0 1.0 (Wikidata) |
| `wiktionnaire/` | Étymologies, langues d'origine, prononciations, variantes extraites du Wiktionnaire | **CC BY-SA 4.0** — attribution : contributeurs du Wiktionnaire, avec lien vers chaque page source (son historique liste les auteurs) ; extraction wiktextract / kaikki.org |

Conséquences pratiques :
- quiconque réutilise les fichiers `wiktionnaire/` doit citer le Wiktionnaire et les redistribuer sous CC BY-SA 4.0 ;
- les autres fichiers restent réutilisables librement (Etalab : mention de la source ; CC0 : sans condition) ;
- sur le site, chaque texte du Wiktionnaire est accompagné de sa source, de la licence et d'un lien vers les auteurs ;
- la licence du **code** du projet n'a pas encore été choisie (à décider avant la publication, phase 5).
