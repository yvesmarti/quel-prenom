"""Étape 4a : extraction des prénoms français du Wiktionnaire (textes sous licence CC BY-SA 4.0).

Source : extraction structurée « wiktextract » publiée par kaikki.org à partir du dump officiel
du Wiktionnaire en français (pas d'interrogation du site lui-même).

- extraire() : parcourt le fichier (≈ 6 Go décompressé, ≈ 1 min) et garde les entrées
  « Prénom » en français → data/work/wiktionnaire_prenoms.jsonl ;
- importer() : relie ces entrées aux prénoms Insee (même graphie exacte, accents compris)
  et remplit la table `wiktionnaire_entree`.

Les textes repris (étymologie, prononciation) restent attribués au Wiktionnaire, avec le lien
vers la page d'origine, et sont publiés sous CC BY-SA 4.0 (voir SOURCES.md).

Usage : python pipeline/wiktionnaire.py
"""
import gzip
import json
import re
import urllib.parse

import duckdb

import config
import outils

EXTRAIT = config.BASE.parent / "wiktionnaire_prenoms.jsonl"
CHAMPS = ("word", "pos_title", "etymology_texts", "sounds", "forms", "derived", "related",
          "translations", "categories", "tags")
ORIGINE = re.compile(r"issus? d[’'](?:un|une) (?:mot|nom|prénom)s? en (.+)$")


def extraire():
    source = config.chemin_source("wiktionnaire-kaikki")
    n = 0
    with gzip.open(source, "rt", encoding="utf-8") as f, open(EXTRAIT, "w", encoding="utf-8") as sortie:
        for ligne in f:
            # Filtre rapide sur le texte brut avant de décoder le JSON (le fichier fait plusieurs Go).
            if '"lang_code": "fr"' not in ligne or '"pos": "name"' not in ligne or '"Prénom' not in ligne:
                continue
            e = json.loads(ligne)
            if e.get("lang_code") != "fr" or e.get("pos") != "name" or not e.get("pos_title", "").startswith("Prénom"):
                continue
            sortie.write(json.dumps({k: e[k] for k in CHAMPS if k in e}, ensure_ascii=False) + "\n")
            n += 1
    print(f"Wiktionnaire : {n:,} entrées « Prénom » en français extraites")


QUALIFICATIF = re.compile(r"^\(([^()]*)\)\s*")


def etymologie_du_prenom(textes, titre_section="Prénom"):
    """Garde les paragraphes d'étymologie qui concernent ce prénom.

    Le Wiktionnaire regroupe parfois sur une même page les étymologies de plusieurs sens, avec
    des qualificatifs en tête de paragraphe : « (Prénom) De jade. » / « (Cours d'eau…) De
    l'allemand Jade. », ou « (Prénom 1) (Nom de famille) De l'arabe… ». Règle :
    - paragraphe sans qualificatif : gardé ;
    - sinon gardé seulement si un qualificatif désigne le prénom, et, s'il est numéroté
      (« Prénom 1 »), seulement pour l'entrée de même numéro ;
    - les qualificatifs sont retirés du texte gardé.
    """
    numero = titre_section.removeprefix("Prénom").strip()
    gardes = []
    for texte in textes:
        for paragraphe in texte.split("\n"):
            paragraphe = paragraphe.strip()
            qualificatifs = []
            while m := QUALIFICATIF.match(paragraphe):
                qualificatifs.append(m.group(1).strip())
                paragraphe = paragraphe[m.end():]
            if qualificatifs:
                prenoms = [q.removeprefix("Prénom").strip() for q in qualificatifs if q.startswith("Prénom")]
                if not prenoms or not any(n == "" or numero == "" or n == numero for n in prenoms):
                    continue
            if paragraphe:
                gardes.append(paragraphe)
    return "\n".join(gardes) or None


def url_page(mot):
    return "https://fr.wiktionary.org/wiki/" + urllib.parse.quote(mot.replace(" ", "_"))


def importer(con):
    ids = {i for (i,) in con.execute("SELECT id FROM prenom").fetchall()}
    lignes = []
    for ligne in open(EXTRAIT, encoding="utf-8"):
        e = json.loads(ligne)
        pid = e["word"].lower()
        if pid not in ids:
            continue
        ipa = []
        for s in e.get("sounds", []):
            if s.get("ipa") and s["ipa"] not in ipa:
                ipa.append(s["ipa"])
        etymologie = etymologie_du_prenom(e.get("etymology_texts", []), e.get("pos_title", "Prénom"))
        # Langue d'origine : catégorie « … issus d'un mot en X », retenue seulement si X figure dans
        # l'étymologie du prénom (les catégories valent pour toute la page, tous sens confondus).
        origines = []
        for c in e.get("categories", []):
            m = ORIGINE.search(c)
            if m and m.group(1) not in origines and etymologie and m.group(1).lower() in etymologie.lower():
                origines.append(m.group(1))
        variantes = []
        for f in e.get("forms", []):
            tags = set(f.get("tags", []))
            type_ = ("equivalent_autre_genre" if tags & {"feminine", "masculine"}
                     else "diminutif" if "diminutive" in tags else "orthographique")
            variantes.append([f["form"], type_, None])
        variantes += [[d["word"], "compose", None] for d in e.get("derived", []) if "word" in d]
        variantes += [[d["word"], "apparente", None] for d in e.get("related", []) if "word" in d]
        variantes += [[t["word"], "traduction", t.get("lang")] for t in e.get("translations", []) if t.get("word")]
        lignes.append((pid, e["word"], e["pos_title"], etymologie,
                       json.dumps(ipa, ensure_ascii=False), json.dumps(origines, ensure_ascii=False),
                       json.dumps(variantes, ensure_ascii=False), ",".join(e.get("tags", [])), url_page(e["word"])))
    outils.inserer(con, "wiktionnaire_entree", {
        "prenom_id": "VARCHAR", "mot": "VARCHAR", "titre_section": "VARCHAR", "etymologie": "VARCHAR",
        "ipa": "JSON", "origines": "JSON", "variantes": "JSON", "tags": "VARCHAR", "url": "VARCHAR"}, lignes)
    print(f"Wiktionnaire : {len(lignes):,} entrées reliées à {len({l[0] for l in lignes}):,} prénoms Insee")


if __name__ == "__main__":
    if not EXTRAIT.exists():
        extraire()
    con = duckdb.connect(str(config.BASE))
    importer(con)
    con.close()
