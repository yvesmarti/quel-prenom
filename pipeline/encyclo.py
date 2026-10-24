"""Étape 4c : consolide l'enrichissement encyclopédique dans les tables du modèle de données.

Entrées : wiktionnaire_entree (pipeline/wiktionnaire.py) et tables wikidata_* (pipeline/wikidata.py).
Sorties : origine, etymologie, prononciation, variante, langue_usage, personnalite, lien_externe,
fiche_qualite. Aucune information n'est créée ici : on ne fait que reprendre, relier et dédoublonner.

Niveau de qualité d'une fiche (règle documentée dans DATA_MODEL.md) :
- complète  : étymologie sourcée + au moins une variante + au moins une personnalité ;
- partielle : au moins un élément encyclopédique sourcé (étymologie, origine, prononciation,
              variante, langue d'usage ou personnalité) ;
- minimale  : statistiques Insee seulement.

Usage : python pipeline/encyclo.py
"""
import json
from collections import defaultdict

import duckdb

import config
import outils

SOURCE_WIKT = "wiktionnaire-kaikki"
SOURCE_WD = "wikidata"
MAX_PERSONNALITES = 8


def consolider():
    con = duckdb.connect(str(config.BASE))
    ids = {i for (i,) in con.execute("SELECT id FROM prenom").fetchall()}
    relie = lambda libelle: libelle.lower() if libelle and libelle.lower() in ids else None

    # --- Wiktionnaire : étymologie, origine, prononciation, variantes ---
    etymologies, origines, prononciations, variantes, liens = [], [], [], [], []
    for pid, mot, titre, etym, ipa, orig, var, url in con.execute("""SELECT prenom_id, mot, titre_section, etymologie,
            ipa, origines, variantes, url FROM wiktionnaire_entree ORDER BY prenom_id, titre_section""").fetchall():
        liens.append((pid, "wiktionnaire", url, f"{mot} sur le Wiktionnaire"))
        if etym:
            etymologies.append((pid, etym, SOURCE_WIKT, url, config.LICENCE_WIKTIONNAIRE, "source citée, non relue"))
        for langue in json.loads(orig):
            origines.append((pid, langue, f"Catégorie du Wiktionnaire : « issu d'un mot en {langue} »",
                             SOURCE_WIKT, url, "déclarée par la source"))
        for i in json.loads(ipa):
            prononciations.append((pid, i, SOURCE_WIKT, url))
        for libelle, type_, langue in json.loads(var):
            if libelle.lower() != pid:
                variantes.append((pid, libelle, relie(libelle), type_, langue, SOURCE_WIKT, url))

    # --- Wikidata : variantes, langues d'usage, personnalités, liens ---
    corr = defaultdict(list)
    for pid, q, statut in con.execute("""SELECT prenom_id, qid, statut FROM correspondance_wikidata
            WHERE statut <> 'type_incompatible' ORDER BY prenom_id, qid""").fetchall():
        corr[pid].append(q)
    elements = {q: (lib, art) for q, lib, art in con.execute(
        "SELECT qid, libelle, article_fr FROM wikidata_prenom").fetchall()}
    var_wd = defaultdict(list)
    for q, q2, lib, type_ in con.execute("SELECT qid, qid_associe, libelle, type FROM wikidata_variante ORDER BY 1, 2").fetchall():
        var_wd[q].append((q2, lib, type_))
    lang_wd = defaultdict(list)
    for q, l in con.execute("SELECT qid, langue FROM wikidata_langue WHERE langue IS NOT NULL ORDER BY 1, 2").fetchall():
        lang_wd[q].append(l)
    perso_wd = defaultdict(list)
    for row in con.execute("""SELECT prenom_qid, qid, nom, description, naissance, deces, domaines, url, liens
            FROM wikidata_personnalite ORDER BY prenom_qid, liens DESC, qid""").fetchall():
        perso_wd[row[0]].append(row[1:])

    langues, personnalites = [], []
    for pid, qids in corr.items():
        vues_lang, vues_perso = set(), {}
        for q in qids:
            url_wd = f"https://www.wikidata.org/wiki/{q}"
            liens.append((pid, "wikidata", url_wd, f"Élément Wikidata {q}"))
            lib, article = elements.get(q, (None, None))
            if article:
                liens.append((pid, "wikipedia", article, f"Article « {article.rsplit('/', 1)[-1].replace('_', ' ')} » sur Wikipédia"))
            for q2, libelle, type_ in var_wd[q]:
                if libelle and libelle.lower() != pid:
                    variantes.append((pid, libelle, relie(libelle), type_, None, SOURCE_WD, f"https://www.wikidata.org/wiki/{q2}"))
            for l in lang_wd[q]:
                if l not in vues_lang:
                    vues_lang.add(l)
                    langues.append((pid, l, SOURCE_WD, url_wd))
            for p in perso_wd[q]:
                if p[0] not in vues_perso or p[7] > vues_perso[p[0]][7]:
                    vues_perso[p[0]] = p
        for p in sorted(vues_perso.values(), key=lambda p: (-p[7], p[0]))[:MAX_PERSONNALITES]:
            q_p, nom, desc, naissance, deces, domaines, url, nb_liens = p
            personnalites.append((pid, q_p, nom, desc, naissance, deces, domaines, url, nb_liens, nb_liens, SOURCE_WD))

    # Variantes : une seule ligne par (prénom, libellé, type, langue).
    variantes = sorted(set(variantes), key=lambda v: (v[0], v[3], v[4] or "", v[1]))

    con.execute("DROP TABLE IF EXISTS origine")
    con.execute("DROP TABLE IF EXISTS etymologie")
    con.execute("DROP TABLE IF EXISTS variante")
    con.execute("DROP TABLE IF EXISTS personnalite")
    outils.inserer(con, "etymologie", {"prenom_id": "VARCHAR", "texte": "VARCHAR", "source_id": "VARCHAR",
                                       "url_source": "VARCHAR", "licence": "VARCHAR", "statut_verification": "VARCHAR"},
                   etymologies)
    outils.inserer(con, "origine", {"prenom_id": "VARCHAR", "langue": "VARCHAR", "justification": "VARCHAR",
                                    "source_id": "VARCHAR", "url_source": "VARCHAR", "confiance": "VARCHAR"}, origines)
    outils.inserer(con, "prononciation", {"prenom_id": "VARCHAR", "api": "VARCHAR", "source_id": "VARCHAR",
                                          "url_source": "VARCHAR"}, prononciations)
    outils.inserer(con, "variante", {"prenom_id": "VARCHAR", "libelle": "VARCHAR", "prenom_associe_id": "VARCHAR",
                                     "type": "VARCHAR", "langue": "VARCHAR", "source_id": "VARCHAR",
                                     "url_source": "VARCHAR"}, variantes)
    outils.inserer(con, "langue_usage", {"prenom_id": "VARCHAR", "langue": "VARCHAR", "source_id": "VARCHAR",
                                         "url_source": "VARCHAR"}, langues)
    outils.inserer(con, "personnalite", {
        "prenom_id": "VARCHAR", "qid": "VARCHAR", "nom": "VARCHAR", "presentation": "VARCHAR", "naissance": "INTEGER",
        "deces": "INTEGER", "domaines": "VARCHAR", "url": "VARCHAR", "nb_liens": "INTEGER",
        "score_pertinence": "INTEGER", "source_id": "VARCHAR"}, personnalites)
    outils.inserer(con, "lien_externe", {"prenom_id": "VARCHAR", "type": "VARCHAR", "url": "VARCHAR",
                                         "libelle": "VARCHAR"}, sorted(set(liens)))

    # --- Qualité des fiches ---
    con.execute("DROP TABLE IF EXISTS fiche_qualite")
    con.execute("""CREATE TABLE fiche_qualite AS
        WITH c AS (
          SELECT p.id,
            (SELECT count(*) FROM etymologie e WHERE e.prenom_id = p.id) AS n_etym,
            (SELECT count(*) FROM origine o WHERE o.prenom_id = p.id) AS n_orig,
            (SELECT count(*) FROM prononciation x WHERE x.prenom_id = p.id) AS n_pron,
            (SELECT count(*) FROM variante v WHERE v.prenom_id = p.id) AS n_var,
            (SELECT count(*) FROM langue_usage l WHERE l.prenom_id = p.id) AS n_lang,
            (SELECT count(*) FROM personnalite s WHERE s.prenom_id = p.id) AS n_perso
          FROM prenom p)
        SELECT id AS prenom_id, n_etym, n_orig, n_pron, n_var, n_lang, n_perso,
          CASE WHEN n_etym > 0 AND n_var > 0 AND n_perso > 0 THEN 'complete'
               WHEN n_etym + n_orig + n_pron + n_var + n_lang + n_perso > 0 THEN 'partielle'
               ELSE 'minimale' END AS niveau
        FROM c""")
    con.execute("UPDATE prenom SET statut_validation = 'enrichi' WHERE id IN "
                "(SELECT prenom_id FROM fiche_qualite WHERE niveau <> 'minimale')")
    resume = dict(con.execute("SELECT niveau, count(*) FROM fiche_qualite GROUP BY 1 ORDER BY 1").fetchall())
    print(f"Encyclopédie OK : {len(etymologies):,} étymologies, {len(origines):,} origines, {len(variantes):,} variantes, "
          f"{len(personnalites):,} personnalités ; fiches {resume}")
    con.close()


if __name__ == "__main__":
    consolider()
