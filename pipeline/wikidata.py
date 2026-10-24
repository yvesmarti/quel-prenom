"""Étape 4b : enrichissement par Wikidata (licence CC0).

1. liste des éléments « prénom » (4 types : prénom, prénom féminin, masculin, épicène) ;
2. libellés, nombre de liens Wikipédia et article de Wikipédia en français, par lots ;
3. correspondance avec les prénoms Insee : même graphie exacte (accents compris), type compatible
   avec l'usage ; les cas multiples sont marqués « ambigus » au lieu d'être tranchés au hasard ;
4. variantes (P460 « réputé identique à », P1560 « équivalent dans l'autre genre ») et langues
   d'usage (P407) des éléments retenus ;
5. personnalités : humains dont le prénom (P735, premier prénom si l'ordre est indiqué) est
   l'élément retenu, ayant un article sur Wikipédia en français et au moins N articles au total.

Chaque réponse est mise en cache (data/raw/wikidata/cache/) : relancer le script reprend là où il
s'était arrêté sans réinterroger Wikidata. Les erreurs sont écrites dans data/work/journal_wikidata.log.
Pour repartir de zéro (nouvelles données Wikidata) : supprimer le dossier de cache.

Usage : python pipeline/wikidata.py [--personnalites]
(la récupération des personnalités, très longue, est désactivée par défaut : voir WIKIDATA_PERSONNALITES)
"""
import hashlib
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

import duckdb

import config
import outils

TYPES = {"Q202444": "prenom", "Q11879590": "feminin", "Q12308941": "masculin", "Q3409032": "epicene"}
# Types compatibles avec l'usage Insee (F, M, X = mixte).
COMPATIBLES = {"F": {"feminin", "epicene", "prenom"}, "M": {"masculin", "epicene", "prenom"},
               "X": {"feminin", "masculin", "epicene", "prenom"}}
PERSONNALITES_MIN_LIENS = 10   # au moins 10 éditions de Wikipédia (ou projets) avec un article
PERSONNALITES_MAX = 8          # par élément prénom
CACHE = config.DOSSIER_CACHE_WIKIDATA / "cache"
JOURNAL = config.BASE.parent / "journal_wikidata.log"


class DelaiDepasse(Exception):
    pass


def journal(message):
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {message}\n")


def sparql(requete):
    """Exécute une requête SPARQL (POST), avec cache disque, pauses et nouvelles tentatives."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cle = hashlib.sha1(requete.encode("utf-8")).hexdigest()
    fichier = CACHE / f"{cle}.json"
    if fichier.exists():
        return json.loads(fichier.read_text(encoding="utf-8"))
    corps = urllib.parse.urlencode({"query": requete}).encode()
    for essai in range(5):
        req = urllib.request.Request(config.WIKIDATA_SPARQL, data=corps, headers={
            "User-Agent": config.WIKIDATA_USER_AGENT, "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                try:
                    lignes = [{k: v["value"] for k, v in b.items()} for b in json.load(r)["results"]["bindings"]]
                except (json.JSONDecodeError, http.client.IncompleteRead) as e:
                    # Réponse coupée en cours de transfert (délai dépassé côté serveur) : lot trop lourd.
                    raise DelaiDepasse(f"réponse tronquée : {e}")
            fichier.write_text(json.dumps(lignes, ensure_ascii=False), encoding="utf-8")
            time.sleep(1)  # politesse envers le service public
            return lignes
        except urllib.error.HTTPError as e:
            texte = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 503):
                attente = int(e.headers.get("Retry-After", 30))
                journal(f"HTTP {e.code}, pause {attente} s")
                time.sleep(attente)
                continue
            if "TimeoutException" in texte or e.code == 500:
                raise DelaiDepasse(texte)
            journal(f"HTTP {e.code} : {texte}")
            time.sleep(5 * (essai + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            journal(f"Erreur réseau : {e}")
            time.sleep(5 * (essai + 1))
    raise RuntimeError("Wikidata ne répond pas après 5 tentatives (voir le journal)")


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def par_lots(liste, taille):
    for i in range(0, len(liste), taille):
        yield liste[i:i + taille]


def par_lots_adaptatifs(construire, ids, taille):
    """Exécute construire(lot) par lots ; un lot trop lourd est coupé en deux, récursivement."""
    def executer(lot):
        try:
            return sparql(construire(lot))
        except DelaiDepasse:
            if len(lot) == 1:
                journal(f"{lot[0]} : requête abandonnée (délai dépassé même seul)")
                return []
            milieu = len(lot) // 2
            journal(f"lot de {len(lot)} trop lourd, découpé en deux")
            return executer(lot[:milieu]) + executer(lot[milieu:])
    lignes = []
    for lot in par_lots(ids, taille):
        lignes += executer(lot)
    return lignes


def valeurs(ids):
    return " ".join(f"wd:{i}" for i in ids)


# --- 1-2. Éléments prénoms ----------------------------------------------------

def elements():
    types = defaultdict(set)
    for t, nom in TYPES.items():
        for l in sparql(f"SELECT ?i WHERE {{ ?i wdt:P31 wd:{t} }}"):
            types[qid(l["i"])].add(nom)
    # La liste contient aussi des « sens de lexèmes » (L…-S…) : sans libellé, ils disparaissent à l'étape suivante.
    # (Ne pas les retirer ici : la composition des lots, donc le cache, en dépend.)
    print(f"  {len(types):,} éléments prénoms et sens de lexèmes")
    infos = {}
    ids = sorted(types)
    for n, lot in enumerate(par_lots(ids, 1000)):
        for l in par_lots_adaptatifs(lambda sous_lot: f"""SELECT ?i ?sl ?fr ?mul ?en ?native ?article WHERE {{
              VALUES ?i {{ {valeurs(sous_lot)} }} ?i wikibase:sitelinks ?sl .
              OPTIONAL {{ ?i rdfs:label ?fr FILTER(LANG(?fr) = "fr") }}
              OPTIONAL {{ ?i rdfs:label ?mul FILTER(LANG(?mul) = "mul") }}
              OPTIONAL {{ ?i rdfs:label ?en FILTER(LANG(?en) = "en") }}
              OPTIONAL {{ ?i wdt:P1705 ?native }}
              OPTIONAL {{ ?article schema:about ?i ; schema:isPartOf <https://fr.wikipedia.org/> }} }}""", lot, 1000):
            i = qid(l["i"])
            e = infos.setdefault(i, {"qid": i, "types": sorted(types[i]), "liens": int(l["sl"]),
                                     "libelle": None, "graphies": set(), "article_fr": None})
            for cle in ("fr", "mul", "en", "native"):
                if l.get(cle):
                    e["graphies"].add(l[cle])
            e["libelle"] = e["libelle"] or l.get("fr") or l.get("mul") or l.get("en")
            e["article_fr"] = e["article_fr"] or l.get("article")
        if n % 20 == 0:
            print(f"  libellés : {min((n + 1) * 1000, len(ids)):,} / {len(ids):,}")
    return infos


# --- 3. Correspondances -------------------------------------------------------

def correspondances(con, infos):
    """Associe chaque prénom Insee aux éléments Wikidata de même graphie exacte (insensible à la casse)."""
    par_graphie = defaultdict(set)
    for i, e in infos.items():
        for g in e["graphies"]:
            par_graphie[g.lower()].add(i)
    resultat = []
    for pid, usage in con.execute("SELECT id, sexe_usage FROM prenom").fetchall():
        candidats = sorted(par_graphie.get(pid, ()))
        compatibles = [i for i in candidats if set(infos[i]["types"]) & COMPATIBLES[usage]]
        for i in compatibles:
            statut = "unique" if len(compatibles) == 1 else "ambigu"
            resultat.append((pid, i, "graphie_exacte", statut))
        for i in candidats:
            if i not in compatibles:
                resultat.append((pid, i, "graphie_exacte", "type_incompatible"))
    return resultat


# --- 4. Relations et langues ----------------------------------------------------

def relations(ids):
    variantes, langues = [], []
    for l in par_lots_adaptatifs(lambda lot: f"""SELECT ?i ?prop ?j ?jfr ?jmul WHERE {{
          VALUES ?i {{ {valeurs(lot)} }} VALUES ?prop {{ wdt:P460 wdt:P1560 }} ?i ?prop ?j .
          OPTIONAL {{ ?j rdfs:label ?jfr FILTER(LANG(?jfr) = "fr") }}
          OPTIONAL {{ ?j rdfs:label ?jmul FILTER(LANG(?jmul) = "mul") }} }}""", ids, 400):
        type_ = "equivalent_autre_genre" if l["prop"].endswith("P1560") else "reputee_identique"
        variantes.append((qid(l["i"]), qid(l["j"]), l.get("jfr") or l.get("jmul"), type_))
    for l in par_lots_adaptatifs(lambda lot: f"""SELECT ?i ?l ?lfr WHERE {{
          VALUES ?i {{ {valeurs(lot)} }} ?i wdt:P407 ?l .
          OPTIONAL {{ ?l rdfs:label ?lfr FILTER(LANG(?lfr) = "fr") }} }}""", ids, 400):
        langues.append((qid(l["i"]), qid(l["l"]), l.get("lfr")))
    return variantes, langues


# --- 5. Personnalités -------------------------------------------------------------

def annee(date):
    """Année d'une date Wikidata (« 1821-12-12T00:00:00Z », « -0063-09-23T… ») ; None si illisible.

    Les dates « inconnues » (valeur spéciale) arrivent sous forme d'URI et donnent None.
    """
    if not date or date.startswith("http"):
        return None
    signe = -1 if date.startswith("-") else 1
    chiffres = date.lstrip("+-").split("-", 1)[0]
    return signe * int(chiffres) if chiffres.isdigit() else None


def requete_personnalites(ids, min_liens):
    return f"""SELECT ?prenom ?p ?sl ?label ?desc ?naissance ?deces ?article
          (GROUP_CONCAT(DISTINCT ?occl; separator="|") AS ?occs) WHERE {{
      VALUES ?prenom {{ {valeurs(ids)} }}
      ?p p:P735 ?st . ?st ps:P735 ?prenom . OPTIONAL {{ ?st pq:P1545 ?ord }}
      FILTER(!BOUND(?ord) || STR(?ord) = "1")
      ?p wdt:P31 wd:Q5 ; wikibase:sitelinks ?sl . FILTER(?sl >= {min_liens})
      ?article schema:about ?p ; schema:isPartOf <https://fr.wikipedia.org/> .
      OPTIONAL {{ ?p rdfs:label ?label FILTER(LANG(?label) = "fr") }}
      OPTIONAL {{ ?p schema:description ?desc FILTER(LANG(?desc) = "fr") }}
      OPTIONAL {{ ?p wdt:P569 ?naissance }} OPTIONAL {{ ?p wdt:P570 ?deces }}
      OPTIONAL {{ ?p wdt:P106 ?occ . ?occ rdfs:label ?occl FILTER(LANG(?occl) = "fr") }}
    }} GROUP BY ?prenom ?p ?sl ?label ?desc ?naissance ?deces ?article"""


def personnalites(ids):
    lignes, echecs = [], []
    lots = list(par_lots(ids, 20))
    for n, lot in enumerate(lots):
        try:
            lignes += sparql(requete_personnalites(lot, PERSONNALITES_MIN_LIENS))
        except DelaiDepasse:
            # Lot trop lourd (prénoms très répandus) : on reprend élément par élément,
            # puis avec un seuil de notoriété plus élevé si nécessaire.
            for i in lot:
                for seuil in (PERSONNALITES_MIN_LIENS, 30, 60):
                    try:
                        lignes += sparql(requete_personnalites([i], seuil))
                        if seuil != PERSONNALITES_MIN_LIENS:
                            journal(f"{i} : personnalités limitées à ≥ {seuil} articles (délai dépassé)")
                        break
                    except DelaiDepasse:
                        continue
                else:
                    echecs.append(i)
                    journal(f"{i} : personnalités non récupérées (délai dépassé)")
        if n % 50 == 0:
            print(f"  personnalités : lot {n + 1} / {len(lots)}")

    par_personne = {}
    for l in lignes:
        cle = (qid(l["prenom"]), qid(l["p"]))
        a_n, a_d = annee(l.get("naissance")), annee(l.get("deces"))
        e = par_personne.setdefault(cle, {"liens": int(l["sl"]), "nom": l.get("label"), "description": l.get("desc"),
                                          "naissance": a_n, "deces": a_d, "url": l["article"],
                                          "domaines": l.get("occs") or ""})
        # Plusieurs dates possibles sur Wikidata : on garde la plus ancienne et on ne l'invente jamais.
        if a_n is not None and (e["naissance"] is None or a_n < e["naissance"]):
            e["naissance"] = a_n
        if a_d is not None and (e["deces"] is None or a_d < e["deces"]):
            e["deces"] = a_d
    par_prenom = defaultdict(list)
    for (prenom, personne), e in par_personne.items():
        if e["nom"]:
            par_prenom[prenom].append((personne, e))
    resultat = []
    for prenom, liste in par_prenom.items():
        liste.sort(key=lambda x: (-x[1]["liens"], x[0]))
        for personne, e in liste[:PERSONNALITES_MAX]:
            domaines = "|".join(sorted(e["domaines"].split("|"))[:3]) if e["domaines"] else ""
            resultat.append((prenom, personne, e["nom"], e["description"], e["naissance"], e["deces"],
                             domaines, e["url"], e["liens"]))
    return resultat, echecs


def enrichir(avec_personnalites=config.WIKIDATA_PERSONNALITES):
    debut = datetime.now(timezone.utc).isoformat(timespec="seconds")
    con = duckdb.connect(str(config.BASE))
    print("Éléments prénoms Wikidata…")
    infos = elements()
    lignes_el = [(e["qid"], ",".join(e["types"]), e["libelle"], e["liens"], e["article_fr"],
                  "|".join(sorted(e["graphies"]))) for e in infos.values()]
    outils.inserer(con, "wikidata_prenom", {"qid": "VARCHAR", "types": "VARCHAR", "libelle": "VARCHAR",
                                            "liens": "INTEGER", "article_fr": "VARCHAR", "graphies": "VARCHAR"},
                   lignes_el)

    print("Correspondances avec les prénoms Insee…")
    corr = correspondances(con, infos)
    outils.inserer(con, "correspondance_wikidata", {"prenom_id": "VARCHAR", "qid": "VARCHAR",
                                                    "methode": "VARCHAR", "statut": "VARCHAR"}, corr)
    retenus = sorted({i for _, i, _, s in corr if s != "type_incompatible"})
    print(f"  {len({p for p, _, _, s in corr if s != 'type_incompatible'}):,} prénoms Insee reliés à {len(retenus):,} éléments")

    print("Variantes et langues…")
    variantes, langues = relations(retenus)
    outils.inserer(con, "wikidata_variante", {"qid": "VARCHAR", "qid_associe": "VARCHAR", "libelle": "VARCHAR",
                                              "type": "VARCHAR"}, variantes)
    outils.inserer(con, "wikidata_langue", {"qid": "VARCHAR", "langue_qid": "VARCHAR", "langue": "VARCHAR"}, langues)

    if avec_personnalites:
        print("Personnalités…")
        perso, echecs = personnalites(retenus)
    else:
        print("Personnalités : non récupérées (WIKIDATA_PERSONNALITES = False dans config.py)")
        perso, echecs = [], []
    outils.inserer(con, "wikidata_personnalite", {
        "prenom_qid": "VARCHAR", "qid": "VARCHAR", "nom": "VARCHAR", "description": "VARCHAR",
        "naissance": "INTEGER", "deces": "INTEGER", "domaines": "VARCHAR", "url": "VARCHAR", "liens": "INTEGER"}, perso)

    # Date réelle de l'interrogation : le plus ancien fichier du cache (les relances relisent le cache).
    plus_ancien = min(f.stat().st_mtime for f in CACHE.glob("*.json"))
    resume = {"interrogation": datetime.fromtimestamp(plus_ancien, timezone.utc).isoformat(timespec="seconds"),
              "debut": debut, "fin": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "elements": len(infos), "elements_relies": len(retenus), "variantes": len(variantes),
              "langues": len(langues), "personnalites_recuperees": avec_personnalites,
              "personnalites": len(perso), "echecs_personnalites": echecs}
    (config.DOSSIER_CACHE_WIKIDATA / "resume.json").write_text(json.dumps(resume, indent=2), encoding="utf-8")
    print(f"Wikidata OK : {resume}")
    con.close()


if __name__ == "__main__":
    import sys
    enrichir(avec_personnalites=config.WIKIDATA_PERSONNALITES or "--personnalites" in sys.argv)
