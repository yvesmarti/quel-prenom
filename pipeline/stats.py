"""Étape 4 : statistiques dérivées (indicateurs par prénom, tendances, agrégats géographiques).

Toutes les définitions et seuils sont décrits dans STATISTIQUES.md et réglables dans config.py.
Rappels :
- effectifs = valeurs arrondies au multiple de 5 par l'Insee ;
- rangs = rangs officiels Insee (jamais recalculés) ;
- fréquence = effectif / naissances officielles (T35) × 1000, seulement à partir de 1946 ;
- une année absente du fichier compte pour 0 dans les moyennes de tendances
  (elle correspond à un effectif arrondi à 0, soit au plus 2 naissances) mais n'est jamais affichée comme 0.

Usage : python pipeline/stats.py
"""
import json
import math
from collections import defaultdict

import duckdb

import config
import outils

T = config.TENDANCES


# --- Dénominateurs ----------------------------------------------------------

def denominateurs(con):
    """{(annee, sexe): (naissances, champ)} pour les années où la fréquence est publiée."""
    res = {}
    for annee, sexe, champ, n in con.execute(
            "SELECT annee, sexe, champ, naissances FROM naissances_officielles").fetchall():
        if annee < config.ANNEE_DEBUT_FREQUENCES:
            continue
        voulu = "france" if annee >= config.ANNEE_DEBUT_FRANCE_ENTIERE else "metropole"
        if champ == voulu:
            res[(annee, sexe)] = (n, champ)
    return res


# --- Outils de calcul (testés dans tests/test_stats.py) ---------------------

def moyenne(serie, debut, fin):
    """Moyenne annuelle sur [debut..fin] ; année absente = 0."""
    return sum(serie.get(a, 0) for a in range(debut, fin + 1)) / (fin - debut + 1)


def moyenne_mobile(valeurs, largeur):
    """Moyenne mobile centrée (fenêtre tronquée aux bords)."""
    demi = largeur // 2
    return [sum(valeurs[max(0, i - demi):i + demi + 1]) / len(valeurs[max(0, i - demi):i + demi + 1])
            for i in range(len(valeurs))]


def sommets(y, prominence_min):
    """Indices des sommets de y dont la proéminence atteint prominence_min.

    Proéminence : hauteur du sommet au-dessus du « col » qui le sépare d'un point plus haut.
    Un côté qui atteint le bord de la série sans rencontrer de point plus haut est « ouvert » :
    on ne sait pas ce qui se passe au-delà des années observées, il est donc ignoré.
    Si les deux côtés sont ouverts (sommet le plus haut de la série), on retient la plus forte
    des deux descentes.
    """
    n = len(y)
    resultat = []
    for i in range(n):
        if (i > 0 and y[i - 1] > y[i]) or (i < n - 1 and y[i + 1] > y[i]):
            continue
        if (i > 0 and y[i - 1] == y[i]):  # plateau : on ne garde que le premier point
            continue
        fermes, ouverts = [], []
        for pas in (-1, 1):
            j, mini = i + pas, y[i]
            while 0 <= j < n and y[j] <= y[i]:
                mini = min(mini, y[j])
                j += pas
            (fermes if 0 <= j < n else ouverts).append(mini)
        prominence = y[i] - max(fermes) if fermes else y[i] - min(ouverts)
        if prominence >= prominence_min:
            resultat.append(i)
    return resultat


# --- Indicateurs d'une série (un prénom, un sexe) ---------------------------

def indicateurs(points, nb_publies, denom, annee_min, annee_max):
    """points = [(annee, valeur, rang)] ; nb_publies[(annee)] = nombre de prénoms publiés cette année-là."""
    Y = annee_max
    valeur = {a: v for a, v, _ in points}
    rang = {a: r for a, _, r in points}
    freq = {a: valeur.get(a, 0) / denom[a] * 1000 for a in denom}

    record = max(points, key=lambda p: (p[1], -p[0]))
    meilleur = min(points, key=lambda p: (p[2], p[0]))
    annees_freq = [a for a in denom if a in valeur]
    record_freq = max(annees_freq, key=lambda a: (freq[a], -a)) if annees_freq else None

    ind = {
        "total": sum(valeur.values()),
        "nb_annees": len(points),
        "premiere_annee": points[0][0],
        "derniere_annee": points[-1][0],
        "record_effectif": [record[0], record[1]],
        "meilleur_rang": [meilleur[0], meilleur[2]],
        "record_frequence": [record_freq, round(freq[record_freq], 3)] if record_freq else None,
        "derniere": ({"annee": Y, "valeur": valeur[Y], "rang": rang[Y], "nb_publies": nb_publies[Y],
                      "frequence": round(freq[Y], 3) if Y in freq else None} if Y in valeur else None),
        "evolutions": {},
        "tendances": [],
    }

    # Évolutions : fréquence moyenne sur 3 ans [Y-2..Y] comparée à [Y-k-2..Y-k].
    for k in config.EVOLUTIONS:
        avant, apres = (Y - k - 2, Y - k), (Y - 2, Y)
        e_avant, e_apres = moyenne(valeur, *avant), moyenne(valeur, *apres)
        if avant[0] < config.ANNEE_DEBUT_FREQUENCES:
            continue
        evo = {"avant": list(avant), "apres": list(apres),
               "effectif_avant": round(e_avant, 1), "effectif_apres": round(e_apres, 1)}
        if e_avant >= config.EVOLUTION_MIN and e_apres >= config.EVOLUTION_MIN:
            f_avant, f_apres = moyenne(freq, *avant), moyenne(freq, *apres)
            evo["variation"] = round(f_apres / f_avant - 1, 3)
        ind["evolutions"][str(k)] = evo

    # --- Tendances (catégories non exclusives) ---
    L, d = T["fenetre"], T["decalage_progression"]
    recent, ancien = (Y - L + 1, Y), (Y - d - L + 1, Y - d)
    e_recent, e_ancien = moyenne(valeur, *recent), moyenne(valeur, *ancien)
    f_recent, f_ancien = moyenne(freq, *recent), moyenne(freq, *ancien)
    details = {"effectif_recent": round(e_recent, 1), "effectif_ancien": round(e_ancien, 1)}
    if f_ancien > 0:
        details["ratio_frequence"] = round(f_recent / f_ancien, 3)

    if points[0][0] >= Y - T["emergent_depuis"] + 1 and e_recent >= T["emergent_min"]:
        ind["tendances"].append(("emergent", e_recent, details))
    if (e_recent >= T["progression_min"] and e_ancien >= T["progression_min_avant"]
            and f_recent >= T["progression_facteur"] * f_ancien):
        ind["tendances"].append(("progression", f_recent / f_ancien, details))
    if e_ancien >= T["declin_min_avant"] and f_recent <= T["declin_facteur"] * f_ancien:
        ind["tendances"].append(("declin", f_recent / f_ancien, details))

    annees = list(range(annee_min, Y + 1))
    eff = [valeur.get(a, 0) for a in annees]
    pic5 = max(moyenne_mobile(eff, 5))
    if pic5 >= T["rare_pic_min"] and e_recent <= T["rare_recent_max"]:
        ind["tendances"].append(("devenu_rare", pic5, {**details, "pic_moyen_5_ans": round(pic5, 1)}))

    # Vagues : sommets du rang lissé (année absente = au-delà du dernier rang publié).
    r = [rang.get(a, nb_publies[a] + 1) for a in annees]
    lisse = moyenne_mobile([math.log10(x) for x in r], T["lissage_rang"])
    y = [-v for v in lisse]
    pics = [i for i in sommets(y, T["vague_prominence"]) if 10 ** lisse[i] <= T["vague_rang_max"]]
    ind["vagues"] = [[annees[i], round(10 ** lisse[i])] for i in pics]
    if len(pics) >= 2:
        ind["tendances"].append(("vagues", len(pics), {**details, "sommets": ind["vagues"]}))
    anciens = [v for v in ind["vagues"] if v[0] < T["retour_avant"] and v[1] <= T["retour_rang_max"]]
    recents = [v for v in ind["vagues"] if v[0] > Y - T["retour_recent"] and v[1] <= T["retour_rang_max"]]
    if anciens and recents:
        ind["tendances"].append(("retour", -recents[-1][1], {
            **details, "sommet_ancien": anciens[0], "sommet_recent": recents[-1]}))

    ind["tendances_details"] = {cat: det for cat, _, det in ind["tendances"]}
    ind["scores"] = {cat: score for cat, score, _ in ind["tendances"]}
    ind["tendances"] = [cat for cat, _, _ in ind["tendances"]]
    return ind


def calculer():
    con = duckdb.connect(str(config.BASE))
    denom_champ = denominateurs(con)
    annee_min, annee_max = con.execute("SELECT min(annee), max(annee) FROM statistique").fetchone()

    con.execute("DROP TABLE IF EXISTS denominateur")
    con.execute("CREATE TABLE denominateur (annee INTEGER, sexe VARCHAR, naissances INTEGER, champ VARCHAR)")
    con.executemany("INSERT INTO denominateur VALUES (?, ?, ?, ?)",
                    [(a, s, n, c) for (a, s), (n, c) in sorted(denom_champ.items())])

    nb_publies = defaultdict(dict)
    for annee, sexe, n in con.execute("""SELECT annee, sexe, count(*) FROM statistique
            WHERE niveau = 'FRANCE' GROUP BY ALL""").fetchall():
        nb_publies[sexe][annee] = n

    print("Indicateurs et tendances par prénom…")
    series = defaultdict(list)
    for pid, sexe, annee, v, r in con.execute("""SELECT prenom_id, sexe, annee, valeur_arrondie, rang_officiel
            FROM statistique WHERE niveau = 'FRANCE' ORDER BY prenom_id, sexe, annee""").fetchall():
        series[(pid, sexe)].append((annee, v, r))

    denom_sexe = {s: {a: n for (a, x), (n, _) in denom_champ.items() if x == s} for s in ("F", "M")}
    lignes_ind, lignes_tend = [], []
    for (pid, sexe), points in series.items():
        ind = indicateurs(points, nb_publies[sexe], denom_sexe[sexe], annee_min, annee_max)
        for cat in ind["tendances"]:
            lignes_tend.append((cat, pid, sexe, ind["scores"][cat], json.dumps(ind["tendances_details"][cat])))
        del ind["scores"]
        lignes_ind.append((pid, sexe, json.dumps(ind, ensure_ascii=False)))

    outils.inserer(con, "indicateur", {"prenom_id": "VARCHAR", "sexe": "VARCHAR", "donnees": "JSON"}, lignes_ind)
    outils.inserer(con, "tendance", {"categorie": "VARCHAR", "prenom_id": "VARCHAR", "sexe": "VARCHAR",
                                     "score": "DOUBLE", "details": "JSON"}, lignes_tend)

    print("Agrégats géographiques par décennie…")
    con.execute("DROP TABLE IF EXISTS geo_decennie")
    con.execute("""CREATE TABLE geo_decennie AS
        SELECT prenom_id, sexe, niveau, territoire, (annee // 10) * 10 AS decennie, sum(valeur_arrondie) AS valeur
        FROM statistique WHERE niveau IN ('REG', 'DEP') GROUP BY ALL""")
    con.execute("DROP TABLE IF EXISTS total_fichier")
    con.execute("""CREATE TABLE total_fichier AS
        SELECT niveau, territoire, annee, sexe, sum(valeur_arrondie) AS total, count(*) AS nb_prenoms
        FROM statistique GROUP BY ALL""")

    print("Couverture du fichier par rapport aux naissances officielles…")
    con.execute("DROP TABLE IF EXISTS couverture")
    con.execute("""CREATE TABLE couverture AS
        SELECT f.annee, f.sexe, f.total AS fichier_france,
               m.naissances AS naissances_metropole, fr.naissances AS naissances_france,
               round(f.total / coalesce(fr.naissances, m.naissances), 4) AS ratio,
               CASE WHEN fr.naissances IS NOT NULL THEN 'france' WHEN m.naissances IS NOT NULL THEN 'metropole' END AS champ
        FROM total_fichier f
        LEFT JOIN naissances_officielles m ON m.annee = f.annee AND m.sexe = f.sexe AND m.champ = 'metropole'
        LEFT JOIN naissances_officielles fr ON fr.annee = f.annee AND fr.sexe = f.sexe AND fr.champ = 'france'
        WHERE f.niveau = 'FRANCE' ORDER BY f.annee, f.sexe""")

    resume = dict(con.execute("SELECT categorie, count(*) FROM tendance GROUP BY 1 ORDER BY 1").fetchall())
    print(f"Statistiques OK : {len(lignes_ind):,} séries prénom/sexe ; tendances : {resume}")
    con.close()


if __name__ == "__main__":
    calculer()
