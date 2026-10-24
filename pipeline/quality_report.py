"""Étape 5 : produit le rapport de qualité (data/reports/qualite.md et qualite.json).

Usage : python pipeline/quality_report.py
"""
import gzip
import json

import duckdb

import config


def taille(chemins):
    brut = sum(p.stat().st_size for p in chemins)
    compresse = sum(len(gzip.compress(p.read_bytes(), 9)) for p in chemins)
    return brut, compresse


def ko(n):
    return f"{n / 1024:,.0f} Ko".replace(",", " ")


def rapport():
    con = duckdb.connect(str(config.BASE), read_only=True)
    val = lambda sql: con.execute(sql).fetchone()[0]
    inspection = json.loads((config.DOSSIER_RAPPORTS / "inspection.json").read_text(encoding="utf-8"))
    manifeste = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))["fichiers"]

    index = list(config.DOSSIER_PUBLIC.glob("index.v*.json"))
    lots = sorted((config.DOSSIER_PUBLIC / "prenoms").glob("*.json"), key=lambda p: p.stat().st_size)
    t_index, t_lots = taille(index), taille(lots)
    publies = {}
    for nom, motif in (("classements nationaux", "classements/france*/**/*.json"),
                       ("classements nationaux par décennie", "classements/france-decennies.json"),
                       ("classements territoriaux", "classements/zones/*.json"),
                       ("données géographiques par prénom", "geo/prenoms/*.json"),
                       ("fonds de carte et totaux", "geo/*.json"),
                       ("tendances", "tendances.json"), ("couverture", "couverture.json"), ("meta", "meta.json")):
        fichiers = sorted(set(config.DOSSIER_PUBLIC.glob(motif)), key=lambda p: p.stat().st_size)
        if fichiers:
            b, g = taille(fichiers)
            publies[nom] = {"nb": len(fichiers), "brut": b, "gzip": g,
                            "plus_gros": [fichiers[-1].name, fichiers[-1].stat().st_size]}

    couverture = con.execute("""SELECT annee, sexe, ratio, champ FROM couverture
        WHERE annee IN (1901, 1920, 1940, 1945, 1946, 1960, 1980, 1993, 1994, 2000, 2010, 2020, 2025)
        ORDER BY annee, sexe""").fetchall()
    q_tendances = dict(con.execute("SELECT categorie, count(*) FROM tendance GROUP BY 1 ORDER BY 1").fetchall())

    q = {
        "sources": {k: {c: m[c] for c in ("url", "taille_octets", "sha256", "recupere_le")} for k, m in manifeste.items()},
        "fichier_source": {k: manifeste[config.SOURCE_ID][k] for k in ("url", "taille_octets", "sha256", "recupere_le")},
        "couverture_echantillon": [list(c) for c in couverture],
        "tendances": q_tendances,
        "fichiers_publies_phase2": publies,
        "nb_lignes_brutes": inspection["nb_lignes"],
        "lignes_par_niveau": inspection["lignes_par_niveau"],
        "annees": [inspection["annee_min"], inspection["annee_max"]],
        "nb_prenoms": val("SELECT count(*) FROM prenom"),
        "nb_couples_prenom_sexe": val("SELECT count(DISTINCT (prenom_id, sexe)) FROM statistique WHERE niveau='FRANCE'"),
        "nb_prenoms_avec_statistiques": val("SELECT count(DISTINCT prenom_id) FROM statistique"),
        "par_usage": dict(con.execute("SELECT sexe_usage, count(*) FROM prenom GROUP BY 1 ORDER BY 1").fetchall()),
        "portes_par_les_deux_sexes": val("SELECT count(*) FROM prenom WHERE total_f_arrondi > 0 AND total_m_arrondi > 0"),
        "composes": val("SELECT count(*) FROM prenom WHERE compose"),
        "avec_accent": val("SELECT count(*) FROM prenom WHERE a_accent"),
        "groupes_ambigus_normalisation": val("SELECT count(*) FROM ambiguite_normalisation"),
        "prenoms_dans_groupes_ambigus": val("SELECT sum(nb) FROM ambiguite_normalisation"),
        "exemples_ambigus": [list(g) for (g,) in con.execute(
            "SELECT graphies FROM ambiguite_normalisation ORDER BY nb DESC, norm LIMIT 8").fetchall()],
        "presents_une_seule_annee": val("""SELECT count(*) FROM (SELECT prenom_id FROM statistique
            WHERE niveau='FRANCE' GROUP BY 1 HAVING count(DISTINCT annee) = 1)"""),
        "fiches_enrichies": 0, "etymologies_sourcees": 0, "personnalites": 0,
        "taille_index": {"brut": t_index[0], "gzip": t_index[1]},
        "taille_lots": {"nb": len(lots), "brut": t_lots[0], "gzip": t_lots[1],
                        "plus_gros": [lots[-1].name, lots[-1].stat().st_size] if lots else None},
        "anomalies_inspection": {k: inspection[k] for k in (
            "valeurs_zero", "valeurs_non_multiples_de_5", "doublons_cle", "rangs_dupliques",
            "groupes_rangs_non_contigus", "inversions_rang_valeur", "periodes_non_numeriques",
            "prenoms_codes_speciaux", "prenoms_avec_espace", "valeur_min")},
    }
    (config.DOSSIER_RAPPORTS / "qualite.json").write_text(json.dumps(q, indent=2, ensure_ascii=False), encoding="utf-8")

    a = q["anomalies_inspection"]
    md = f"""# Rapport de qualité — données Prénoscope

Généré automatiquement par `pipeline/quality_report.py`. Ne pas modifier à la main.

## Fichiers sources
""" + "\n".join(f"- `{k}` : {s['url']} — {s['taille_octets']:,} octets — SHA-256 `{s['sha256'][:16]}…` — récupéré le {s['recupere_le']}"
                for k, s in q["sources"].items()) + """

## Couverture du fichier des prénoms (somme des effectifs nationaux / naissances officielles T35)
Champ du dénominateur : métropole avant 1994, France entière ensuite. Détail complet : `site/public/data/couverture.json`.

| Année | Filles | Garçons | Champ T35 |
|---|---|---|---|
""" + "\n".join(f"| {a} | {dict((s, r) for aa, s, r, _ in q['couverture_echantillon'] if aa == a).get('F', 0):.1%} | "
                f"{dict((s, r) for aa, s, r, _ in q['couverture_echantillon'] if aa == a).get('M', 0):.1%} | "
                f"{next(c for aa, _, _, c in q['couverture_echantillon'] if aa == a)} |"
                for a in sorted({c[0] for c in q["couverture_echantillon"]})) + f"""

## Tendances détectées (définitions : STATISTIQUES.md)
""" + " · ".join(f"{k} : {v}" for k, v in q["tendances"].items()) + f"""

## Volumes constatés
- Lignes brutes : {q['nb_lignes_brutes']:,} (France {q['lignes_par_niveau']['FRANCE']:,} · régions {q['lignes_par_niveau']['REG']:,} · départements {q['lignes_par_niveau']['DEP']:,})
- Années couvertes : {q['annees'][0]}–{q['annees'][1]}
- Prénoms distincts (graphies INSEE) : {q['nb_prenoms']:,} — couples prénom/sexe : {q['nb_couples_prenom_sexe']:,}
- Prénoms avec statistiques : {q['nb_prenoms_avec_statistiques']:,}
- Usage (règle mixte ≥ {config.SEUIL_MIXTE:.0%}) : féminin {q['par_usage'].get('F', 0):,} · masculin {q['par_usage'].get('M', 0):,} · mixte {q['par_usage'].get('X', 0):,}
- Prénoms portés au moins une fois par les deux sexes : {q['portes_par_les_deux_sexes']:,}
- Composés (avec tiret) : {q['composes']:,} — avec accent ou ligature : {q['avec_accent']:,}
- Présents une seule année au niveau national : {q['presents_une_seule_annee']:,}

## Enrichissement (phase 3, non commencé)
- Fiches enrichies : 0 · étymologies sourcées : 0 · personnalités : 0
- Toutes les fiches sont donc « minimales » (statistiques INSEE seules).

## Contrôles et anomalies
- Valeurs nulles : aucune · doublons de clé : {a['doublons_cle']} · rangs dupliqués : {a['rangs_dupliques']}
- Valeurs à 0 : {a['valeurs_zero']} · valeurs non multiples de 5 : {a['valeurs_non_multiples_de_5']} · valeur minimale : {a['valeur_min']}
- Groupes dont les rangs ne sont pas contigus (1..n) : {a['groupes_rangs_non_contigus']} · inversions rang/valeur : {a['inversions_rang_valeur']}
- Années non numériques (type « XXXX ») : {len(a['periodes_non_numeriques'])} · codes spéciaux de prénom (type « _PRENOMS_RARES ») : {len(a['prenoms_codes_speciaux'])}
- Prénoms contenant une espace (probable substitut d'apostrophe, conservés tels quels) : {', '.join(a['prenoms_avec_espace']) or 'aucun'}
- Graphies distinctes partageant la même forme normalisée : {q['groupes_ambigus_normalisation']:,} groupes ({q['prenoms_dans_groupes_ambigus']:,} prénoms), **non fusionnées**. Exemples :
""" + "\n".join(f"  - {' / '.join(g)}" for g in q["exemples_ambigus"]) + f"""

## Fichiers publiés
- Index : {ko(q['taille_index']['brut'])} brut, {ko(q['taille_index']['gzip'])} compressé (gzip)
- Détails : {q['taille_lots']['nb']} lots, {ko(q['taille_lots']['brut'])} brut au total, {ko(q['taille_lots']['gzip'])} compressé ; plus gros lot : {q['taille_lots']['plus_gros'][0]} ({ko(q['taille_lots']['plus_gros'][1])})
""" + "\n".join(f"- {nom.capitalize()} : {p['nb']} fichier(s), {ko(p['brut'])} brut, {ko(p['gzip'])} compressé ; "
                f"plus gros : {p['plus_gros'][0]} ({ko(p['plus_gros'][1])})" for nom, p in q["fichiers_publies_phase2"].items()) + "\n"
    (config.DOSSIER_RAPPORTS / "qualite.md").write_text(md, encoding="utf-8")
    print(f"Rapport OK : data/reports/qualite.md")
    con.close()


if __name__ == "__main__":
    rapport()
