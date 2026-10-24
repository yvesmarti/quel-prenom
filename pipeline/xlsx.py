"""Lecture minimale d'un fichier .xlsx avec la seule bibliothèque standard.

Les classeurs Insee ont des métadonnées que certaines bibliothèques refusent ;
on lit donc directement le XML : texte partagé + cellules de chaque feuille.
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _colonne(ref):
    """« C12 » → 2 (index de colonne à partir de 0)."""
    n = 0
    for c in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(c) - 64
    return n - 1


def lire(chemin):
    """Renvoie {nom_feuille: [lignes]} ; chaque ligne est une liste de valeurs (str, float ou None)."""
    with zipfile.ZipFile(chemin) as z:
        partages = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                partages.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        classeur = ET.fromstring(z.read("xl/workbook.xml"))
        liens = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        feuilles = {}
        for f in classeur.find("m:sheets", NS):
            cible = liens[f.get(f"{{{NS['r']}}}id")].lstrip("/")
            cible = cible if cible.startswith("xl/") else "xl/" + cible
            lignes = []
            for row in ET.fromstring(z.read(cible)).iter(f"{{{NS['m']}}}row"):
                valeurs = {}
                for c in row.findall("m:c", NS):
                    v = c.find("m:v", NS)
                    if c.get("t") == "inlineStr":
                        texte = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
                    elif v is None:
                        continue
                    elif c.get("t") == "s":
                        texte = partages[int(v.text)]
                    elif c.get("t") in ("str", "b", "e"):
                        texte = v.text
                    else:
                        texte = float(v.text)
                    valeurs[_colonne(c.get("r"))] = texte
                if valeurs:
                    lignes.append([valeurs.get(i) for i in range(max(valeurs) + 1)])
            feuilles[f.get("name")] = lignes
        return feuilles
