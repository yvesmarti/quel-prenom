"""Étape 5 : génère les fichiers JSON publiés par le site (site/public/data/).

- meta.json                          : sources, licences, années, naissances officielles, règles ;
- index.v1.json                      : index léger de tous les prénoms (chargé au démarrage) ;
- prenoms/<lot>.json                 : séries nationales + indicateurs, chargés à l'ouverture d'une fiche ;
- tendances.json                     : prénoms classés par tendance (définitions : STATISTIQUES.md) ;
- classements/france/<annee>.json    : classement officiel national de l'année (top + fin de classement) ;
- classements/france-decennies.json  : classement calculé par décennie (somme des effectifs arrondis) ;
- classements/zones/<NIV>-<code>.json : classements officiels d'une région ou d'un département ;
- geo/prenoms/g_<lot3>.json          : effectifs par région et département et par décennie
                                       (lot de 3 lettres, ces données étant plus lourdes) ;
- geo/totaux.json                    : total des effectifs du fichier par zone et décennie (dénominateur des parts).

Un lot = les prénoms dont la forme normalisée commence par les mêmes 2 lettres.
Toutes les requêtes ont un ordre fixe : deux exécutions produisent des fichiers identiques.

Usage : python pipeline/export_json.py
"""
import json
import shutil
from collections import defaultdict

import duckdb

import config
import normalize

COLONNES_INDEX = ["id", "affichage", "norm", "sexe", "total_f", "total_m",
                  "premiere_annee", "derniere_annee", "lettres", "accent", "compose", "lot", "qualite"]


def ecrire(chemin, donnees):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def exporter_index_et_lots(con, sortie):
    # Qualité de la fiche : c = complète, p = partielle, m = minimale (règle : pipeline/encyclo.py).
    qualite = ("left(q.niveau, 1)" if table_existe(con, "fiche_qualite") else "'m'")
    jointure = "LEFT JOIN fiche_qualite q ON q.prenom_id = p.id" if table_existe(con, "fiche_qualite") else ""
    lignes = con.execute(f"""
        SELECT p.id, graphie_affichage, norm, sexe_usage, total_f_arrondi, total_m_arrondi,
               premiere_annee, derniere_annee, nb_lettres, a_accent::INTEGER, compose::INTEGER, lot,
               coalesce({qualite}, 'm')
        FROM prenom p {jointure} ORDER BY total_f_arrondi + total_m_arrondi DESC, p.id""").fetchall()
    ecrire(sortie / f"index.v{config.VERSION_FORMAT}.json",
           {"version": config.VERSION_FORMAT, "colonnes": COLONNES_INDEX, "lignes": [list(l) for l in lignes]})

    lots = defaultdict(dict)
    for lot, prenom_id, sexe, serie in con.execute("""
            SELECT p.lot, s.prenom_id, s.sexe, list([s.annee, s.valeur_arrondie, s.rang_officiel] ORDER BY s.annee)
            FROM statistique s JOIN prenom p ON p.id = s.prenom_id
            WHERE s.niveau = 'FRANCE' GROUP BY ALL ORDER BY s.prenom_id, s.sexe""").fetchall():
        lots[lot].setdefault(prenom_id, {})[sexe] = serie
    # Seuls les résultats des tendances et les sommets de vagues sont publiés avec les séries :
    # les indicateurs descriptifs (record, évolutions…) sont recalculés par le site à partir des séries
    # (même définition, vérifiée par les tests grâce à l'échantillon exporté ci-dessous).
    for lot, prenom_id, sexe, donnees in con.execute("""
            SELECT p.lot, i.prenom_id, i.sexe, i.donnees FROM indicateur i JOIN prenom p ON p.id = i.prenom_id
            ORDER BY i.prenom_id, i.sexe""").fetchall():
        ind = json.loads(donnees)
        if ind["tendances"]:
            lots[lot][prenom_id].setdefault("tendances", {})[sexe] = ind["tendances"]
        if ind["vagues"]:
            lots[lot][prenom_id].setdefault("vagues", {})[sexe] = ind["vagues"]
    for lot, contenu in lots.items():
        ecrire(sortie / "prenoms" / f"{lot}.json",
               {"version": config.VERSION_FORMAT, "format_serie": ["annee", "valeur_arrondie", "rang_officiel"],
                "prenoms": contenu})
    exporter_echantillon_indicateurs(con)
    return len(lignes), len(lots)


def exporter_echantillon_indicateurs(con):
    """Indicateurs calculés en Python pour un échantillon fixe de séries : référence des tests du site."""
    echantillon = con.execute("""
        SELECT i.prenom_id, i.sexe, i.donnees FROM indicateur i JOIN (
          SELECT prenom_id, sexe, row_number() OVER (ORDER BY total DESC, prenom_id, sexe) n FROM (
            SELECT prenom_id, sexe, sum(valeur_arrondie) total
            FROM statistique WHERE niveau = 'FRANCE' GROUP BY ALL)) t
          ON t.prenom_id = i.prenom_id AND t.sexe = i.sexe
        WHERE t.n <= 150 OR t.n % 250 = 0
        ORDER BY t.n""").fetchall()
    sortie = config.RACINE / "site" / "tests" / "fixtures" / "indicateurs_python.json"
    ecrire(sortie, [{"id": pid, "sexe": sexe, "indicateurs": {
        k: v for k, v in json.loads(d).items() if k not in ("tendances", "tendances_details", "vagues")}}
        for pid, sexe, d in echantillon])


def exporter_tendances(con, sortie):
    categories = defaultdict(list)
    for cat, pid, sexe, score, details in con.execute("""
            SELECT categorie, prenom_id, sexe, score, details FROM tendance
            ORDER BY categorie, score DESC, prenom_id, sexe""").fetchall():
        categories[cat].append([pid, sexe, round(score, 3), json.loads(details)])
    ecrire(sortie / "tendances.json", {"version": config.VERSION_FORMAT, "parametres": config.TENDANCES,
                                       "categories": categories})
    return {c: len(v) for c, v in categories.items()}


def exporter_classements(con, sortie):
    dossier = sortie / "classements"
    nb_publies = {(a, s): n for a, s, n in con.execute(
        "SELECT annee, sexe, count(*) FROM statistique WHERE niveau = 'FRANCE' GROUP BY ALL").fetchall()}

    # National, par année : rangs officiels (top et fin de classement).
    par_annee = defaultdict(lambda: {"F": {"top": [], "fin": []}, "M": {"top": [], "fin": []}})
    for annee, sexe, pid, v, r in con.execute(f"""
            SELECT s.annee, s.sexe, s.prenom_id, s.valeur_arrondie, s.rang_officiel FROM statistique s
            JOIN (SELECT annee, sexe, count(*) n FROM statistique WHERE niveau = 'FRANCE' GROUP BY ALL) t
              ON t.annee = s.annee AND t.sexe = s.sexe
            WHERE s.niveau = 'FRANCE'
              AND (s.rang_officiel <= {config.CLASSEMENT_NATIONAL_TOP}
                   OR s.rang_officiel > t.n - {config.CLASSEMENT_NATIONAL_FIN})
            ORDER BY s.annee, s.sexe, s.rang_officiel""").fetchall():
        partie = "top" if r <= config.CLASSEMENT_NATIONAL_TOP else "fin"
        par_annee[annee][sexe][partie].append([pid, v] if partie == "top" else [pid, v, r])
    for annee, contenu in par_annee.items():
        for sexe in ("F", "M"):
            contenu[sexe]["nb_publies"] = nb_publies[(annee, sexe)]
        ecrire(dossier / "france" / f"{annee}.json", {"annee": annee, "rang": "officiel", **contenu})

    # National, par décennie : classement calculé sur la somme des effectifs arrondis.
    decennies = defaultdict(lambda: {"F": [], "M": []})
    for dec, sexe, pid, v in con.execute(f"""
            SELECT dec, sexe, prenom_id, v FROM (
              SELECT *, row_number() OVER (PARTITION BY dec, sexe ORDER BY v DESC, prenom_id) n FROM (
                SELECT (annee // 10) * 10 dec, sexe, prenom_id, sum(valeur_arrondie) v
                FROM statistique WHERE niveau = 'FRANCE' GROUP BY ALL))
            WHERE n <= {config.CLASSEMENT_DECENNIE_TOP} ORDER BY dec, sexe, n""").fetchall():
        decennies[dec][sexe].append([pid, v])
    ecrire(dossier / "france-decennies.json", {"rang": "calcule", "decennies": decennies})

    # Zones : classements officiels annuels (top limité) + classement calculé par décennie.
    zones = defaultdict(lambda: {"annees": defaultdict(lambda: {"F": [], "M": []}),
                                 "decennies": defaultdict(lambda: {"F": [], "M": []})})
    for niveau, top in config.CLASSEMENT_TERRITORIAL_TOP.items():
        for code, annee, sexe, pid, v in con.execute(f"""
                SELECT territoire, annee, sexe, prenom_id, valeur_arrondie FROM statistique
                WHERE niveau = '{niveau}' AND rang_officiel <= {top}
                ORDER BY territoire, annee, sexe, rang_officiel""").fetchall():
            zones[(niveau, code)]["annees"][annee][sexe].append([pid, v])
        for code, dec, sexe, pid, v in con.execute(f"""
                SELECT territoire, decennie, sexe, prenom_id, valeur FROM (
                  SELECT territoire, decennie, sexe, prenom_id, valeur,
                         row_number() OVER (PARTITION BY territoire, decennie, sexe
                                            ORDER BY valeur DESC, prenom_id) n
                  FROM geo_decennie WHERE niveau = '{niveau}')
                WHERE n <= {top} ORDER BY territoire, decennie, sexe, n""").fetchall():
            zones[(niveau, code)]["decennies"][dec][sexe].append([pid, v])
    for (niveau, code), contenu in zones.items():
        ecrire(dossier / "zones" / f"{niveau}-{code}.json",
               {"niveau": niveau, "code": code, "top_annuel": config.CLASSEMENT_TERRITORIAL_TOP[niveau], **contenu})
    return len(par_annee), len(zones)


def exporter_geo(con, sortie):
    lots = defaultdict(dict)
    for pid, graphie, sexe, niveau, lignes in con.execute("""
            SELECT g.prenom_id, p.graphie_insee, g.sexe, g.niveau,
                   list([g.territoire, g.decennie::VARCHAR, g.valeur::VARCHAR] ORDER BY g.territoire, g.decennie)
            FROM geo_decennie g JOIN prenom p ON p.id = g.prenom_id
            GROUP BY ALL ORDER BY g.prenom_id, g.sexe, g.niveau""").fetchall():
        lot = normalize.cle_lot(graphie, 3)
        lots[lot].setdefault(pid, {}).setdefault(sexe, {})[niveau] = [[c, int(d), int(v)] for c, d, v in lignes]
    for lot, contenu in lots.items():
        # Préfixe « g_ » : certains noms de 3 lettres (aux, con, nul, prn) sont interdits sous Windows.
        ecrire(sortie / "geo" / "prenoms" / f"g_{lot}.json",
               {"format": ["territoire", "decennie", "valeur_arrondie"], "prenoms": contenu})

    totaux = defaultdict(lambda: defaultdict(lambda: {"F": {}, "M": {}}))
    for niveau, code, dec, sexe, total in con.execute("""
            SELECT niveau, territoire, (annee // 10) * 10, sexe, sum(total) FROM total_fichier
            WHERE niveau IN ('REG', 'DEP') GROUP BY ALL ORDER BY 1, 2, 3, 4""").fetchall():
        totaux[niveau][code][sexe][dec] = int(total)
    ecrire(sortie / "geo" / "totaux.json", {"note": "Somme des effectifs arrondis publiés dans le fichier des prénoms",
                                            "totaux": totaux})
    return len(lots)


def table_existe(con, nom):
    return con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [nom]).fetchone()[0] > 0


def exporter_encyclopedie(con, sortie):
    """Fichiers d'enrichissement, séparés par licence :
    - encyclo/<lot>.json      : Wikidata (CC0) — éléments, langues d'usage, variantes, personnalités, liens ;
    - wiktionnaire/<lot>.json : Wiktionnaire (CC BY-SA 4.0) — étymologie, origine, prononciation, variantes.
    """
    if not table_existe(con, "fiche_qualite"):
        print("  (enrichissement absent : lancer wiktionnaire.py, wikidata.py puis encyclo.py)")
        return 0, 0
    lot_de = dict(con.execute("SELECT id, lot FROM prenom").fetchall())
    encyclo = defaultdict(lambda: defaultdict(dict))
    wikt = defaultdict(lambda: defaultdict(dict))

    def ajouter(cible, pid, cle, valeur):
        cible[lot_de[pid]][pid].setdefault(cle, []).append(valeur)

    for pid, q, statut, lib, art in con.execute("""SELECT c.prenom_id, c.qid, c.statut, w.libelle, w.article_fr
            FROM correspondance_wikidata c JOIN wikidata_prenom w ON w.qid = c.qid
            WHERE c.statut <> 'type_incompatible' ORDER BY 1, 2""").fetchall():
        ajouter(encyclo, pid, "wikidata", {"qid": q, "libelle": lib, "statut": statut, "article": art})
    for pid, langue in con.execute("SELECT prenom_id, langue FROM langue_usage ORDER BY 1, 2").fetchall():
        ajouter(encyclo, pid, "langues", langue)
    for pid, lib, assoc, type_, langue, source, url in con.execute("""SELECT prenom_id, libelle, prenom_associe_id,
            type, langue, source_id, url_source FROM variante ORDER BY prenom_id, type, langue NULLS FIRST, libelle""").fetchall():
        v = {"libelle": lib, "type": type_}
        if assoc:
            v["id"] = assoc
        if langue:
            v["langue"] = langue
        if source == "wikidata":
            ajouter(encyclo, pid, "variantes", {**v, "url": url})
        else:
            ajouter(wikt, pid, "variantes", v)
    for pid, q, nom, pres, n, d, dom, url, liens in con.execute("""SELECT prenom_id, qid, nom, presentation, naissance,
            deces, domaines, url, nb_liens FROM personnalite ORDER BY prenom_id, nb_liens DESC, qid""").fetchall():
        ajouter(encyclo, pid, "personnalites", {"qid": q, "nom": nom, "presentation": pres, "naissance": n, "deces": d,
                                                "domaines": [x for x in (dom or "").split("|") if x], "url": url,
                                                "liens": liens})
    for pid, mot, section, etym, ipa, orig, url in con.execute("""SELECT prenom_id, mot, titre_section, etymologie,
            ipa, origines, url FROM wiktionnaire_entree ORDER BY prenom_id, titre_section""").fetchall():
        ajouter(wikt, pid, "entrees", {"mot": mot, "section": section, "etymologie": etym, "api": json.loads(ipa),
                                       "origines": json.loads(orig), "url": url})
    for pid, *compteurs, niveau in con.execute("""SELECT prenom_id, n_etym, n_orig, n_pron, n_var, n_lang, n_perso,
            niveau FROM fiche_qualite WHERE niveau <> 'minimale' ORDER BY 1""").fetchall():
        encyclo[lot_de[pid]][pid]["qualite"] = niveau

    for lot, contenu in encyclo.items():
        ecrire(sortie / "encyclo" / f"{lot}.json", {
            "licence": "Données Wikidata : CC0 1.0 (domaine public)",
            "source": "https://www.wikidata.org/", "prenoms": contenu})
    for lot, contenu in wikt.items():
        ecrire(sortie / "wiktionnaire" / f"{lot}.json", {
            "licence": "CC BY-SA 4.0 — https://creativecommons.org/licenses/by-sa/4.0/deed.fr",
            "attribution": "Textes issus du Wiktionnaire (fr.wiktionary.org), contributeurs du Wiktionnaire ; "
                           "extraction wiktextract (kaikki.org). Chaque entrée renvoie à sa page source, dont "
                           "l'historique liste les auteurs.",
            "prenoms": contenu})
    return len(encyclo), len(wikt)


def exporter_meta(con, sortie, nb_prenoms, nb_lots):
    colonnes = [d[0] for d in con.execute("SELECT * FROM source ORDER BY id").description]
    sources = [dict(zip(colonnes, s)) for s in con.execute("SELECT * FROM source ORDER BY id").fetchall()]
    resume_wd = config.DOSSIER_CACHE_WIKIDATA / "resume.json"
    if resume_wd.exists():
        wd = json.loads(resume_wd.read_text(encoding="utf-8"))
        sources.append({**{k: config.SOURCE_WIKIDATA[k] for k in ("id", "organisme", "titre", "licence")},
                        "url": config.SOURCE_WIKIDATA["page"], "fichier_url": config.SOURCE_WIKIDATA["url"],
                        "publication": "base vivante", "date_recuperation": wd["debut"], "sha256": None})
    prenoms = next(s for s in sources if s["id"] == config.SOURCE_ID)
    annees = con.execute("SELECT min(annee), max(annee) FROM statistique").fetchone()
    naissances = defaultdict(dict)
    for annee, sexe, n, champ in con.execute(
            "SELECT annee, sexe, naissances, champ FROM denominateur ORDER BY annee, sexe").fetchall():
        naissances[annee][sexe] = n
        naissances[annee]["champ"] = champ
    nb_publies = defaultdict(dict)
    for annee, sexe, n in con.execute("""SELECT annee, sexe, count(*) FROM statistique
            WHERE niveau = 'FRANCE' GROUP BY ALL ORDER BY 1, 2""").fetchall():
        nb_publies[annee][sexe] = n
    couverture = [list(l) for l in con.execute("""SELECT annee, sexe, fichier_france, naissances_metropole,
            naissances_france, ratio, champ FROM couverture ORDER BY annee, sexe""").fetchall()]
    ecrire(sortie / "couverture.json", {
        "colonnes": ["annee", "sexe", "fichier_france", "naissances_metropole", "naissances_france", "ratio", "champ"],
        "lignes": couverture})
    ecrire(sortie / "meta.json", {
        "version": config.VERSION_FORMAT,
        "source": {**prenoms, "millesime": config.MILLESIME},
        "sources": sources,
        "annee_min": annees[0], "annee_max": annees[1],
        "nb_prenoms": nb_prenoms,
        "nb_lots": nb_lots,
        "naissances": naissances,
        "nb_publies": nb_publies,
        "regles": {
            "seuil_mixte": config.SEUIL_MIXTE,
            "arrondi": "Effectifs arrondis par l'Insee au multiple de 5 le plus proche.",
            "rang": "Rang officiel Insee, calculé sur les effectifs non arrondis (par sexe, année et zone).",
            "annee_debut_frequences": config.ANNEE_DEBUT_FREQUENCES,
            "annee_debut_france_entiere": config.ANNEE_DEBUT_FRANCE_ENTIERE,
            "evolutions": config.EVOLUTIONS,
            "evolution_min": config.EVOLUTION_MIN,
            "geo_min_indice": config.GEO_MIN_INDICE,
            "classement_territorial_top": config.CLASSEMENT_TERRITORIAL_TOP,
            "tendances": config.TENDANCES,
        },
    })


def exporter():
    con = duckdb.connect(str(config.BASE), read_only=True)
    sortie = config.DOSSIER_PUBLIC
    for nom in ("prenoms", "classements", "geo", "encyclo", "wiktionnaire"):  # dossiers entièrement générés
        shutil.rmtree(sortie / nom, ignore_errors=True)
    nb_prenoms, nb_lots = exporter_index_et_lots(con, sortie)
    nb_encyclo, nb_wikt = exporter_encyclopedie(con, sortie)
    print(f"  enrichissement : {nb_encyclo} lots Wikidata, {nb_wikt} lots Wiktionnaire")
    tendances = exporter_tendances(con, sortie)
    nb_annees, nb_zones = exporter_classements(con, sortie)
    nb_lots_geo = exporter_geo(con, sortie)
    exporter_meta(con, sortie, nb_prenoms, nb_lots)
    print(f"Export OK : {nb_prenoms:,} prénoms, {nb_lots} lots, tendances {tendances}, "
          f"classements {nb_annees} années + {nb_zones} zones, {nb_lots_geo} lots géographiques")
    con.close()


if __name__ == "__main__":
    exporter()
