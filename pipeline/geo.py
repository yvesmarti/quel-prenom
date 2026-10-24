"""Étape 6 : prépare les fonds de carte (site/public/data/geo/).

- simplifie les contours IGN (algorithme de Douglas-Peucker, tolérance ≈ 1 km) et arrondit
  les coordonnées pour alléger les fichiers ;
- replace les cinq départements et régions d'outre-mer dans des encarts à l'ouest de la
  métropole (position et échelle conventionnelles, indiquées sur la carte) ;
- écrit regions.json, departements.json (GeoJSON) et zones.json (codes et noms).

Usage : python pipeline/geo.py
"""
import json

import config

TOLERANCE = 0.01   # degrés (≈ 1 km)
DECIMALES = 3
# Encarts : (code département, code région, nom) de haut en bas.
OUTRE_MER = [("971", "01", "Guadeloupe"), ("972", "02", "Martinique"), ("973", "03", "Guyane"),
             ("974", "04", "La Réunion"), ("976", "06", "Mayotte")]
ENCART_X, ENCART_LARGEUR = -9.6, 2.6
ENCART_Y_HAUT, ENCART_HAUTEUR, ENCART_ECART = 50.6, 1.45, 0.25


def douglas_peucker(points, tol):
    if len(points) < 3:
        return points
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    norme = (dx * dx + dy * dy) ** 0.5
    dmax, imax = 0, 0
    for i in range(1, len(points) - 1):
        x, y = points[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / norme if norme else ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        if d > dmax:
            dmax, imax = d, i
    if dmax <= tol:
        return [points[0], points[-1]]
    return douglas_peucker(points[:imax + 1], tol)[:-1] + douglas_peucker(points[imax:], tol)


def polygones(geometrie):
    """Liste de polygones (liste d'anneaux) quelle que soit la géométrie."""
    if geometrie["type"] == "Polygon":
        return [geometrie["coordinates"]]
    return geometrie["coordinates"]


def simplifier(polys, tol):
    resultat = []
    for poly in polys:
        anneaux = []
        for anneau in poly:
            s = douglas_peucker(anneau, tol)
            if len(s) >= 4:
                anneaux.append(s)
        if anneaux:
            resultat.append(anneaux)
    return resultat


def deplacer(polys, rang):
    """Met à l'échelle et déplace un territoire d'outre-mer dans l'encart n° rang."""
    xs = [x for p in polys for a in p for x, _ in a]
    ys = [y for p in polys for a in p for _, y in a]
    largeur, hauteur = max(xs) - min(xs), max(ys) - min(ys)
    echelle = min(ENCART_LARGEUR / largeur, ENCART_HAUTEUR / hauteur)
    haut = ENCART_Y_HAUT - rang * (ENCART_HAUTEUR + ENCART_ECART)
    x0 = ENCART_X + (ENCART_LARGEUR - largeur * echelle) / 2
    y0 = haut - ENCART_HAUTEUR + (ENCART_HAUTEUR - hauteur * echelle) / 2
    return [[[[x0 + (x - min(xs)) * echelle, y0 + (y - min(ys)) * echelle] for x, y in a] for a in p]
            for p in polys]


def arrondir(polys):
    return [[[[round(x, DECIMALES), round(y, DECIMALES)] for x, y in a] for a in p] for p in polys]


def preparer(source_id, colonne_outre_mer):
    brut = json.loads(config.chemin_source(source_id).read_text(encoding="utf-8"))
    rangs = {om[colonne_outre_mer]: i for i, om in enumerate(OUTRE_MER)}
    entites, zones = [], {}
    for f in sorted(brut["features"], key=lambda f: f["properties"]["code"]):
        code, nom = f["properties"]["code"], f["properties"]["nom"]
        polys = polygones(f["geometry"])
        if code in rangs:
            # Simplification proportionnelle à l'agrandissement de l'encart.
            polys = deplacer(simplifier(polys, TOLERANCE / 4), rangs[code])
        else:
            polys = simplifier(polys, TOLERANCE)
        entites.append({"type": "Feature", "properties": {"code": code, "name": nom, "outre_mer": code in rangs},
                        "geometry": {"type": "MultiPolygon", "coordinates": arrondir(polys)}})
        zones[code] = nom
    return {"type": "FeatureCollection", "features": entites}, zones


def generer():
    dossier = config.DOSSIER_PUBLIC / "geo"
    dossier.mkdir(parents=True, exist_ok=True)
    regions, noms_reg = preparer("ign-contours-regions-2018", 1)
    departements, noms_dep = preparer("ign-contours-departements-2018", 0)
    for nom, contenu in (("regions", regions), ("departements", departements)):
        (dossier / f"{nom}.json").write_text(json.dumps(contenu, ensure_ascii=False, separators=(",", ":")),
                                             encoding="utf-8")
    (dossier / "zones.json").write_text(json.dumps(
        {"REG": noms_reg, "DEP": noms_dep, "encarts": [om[2] for om in OUTRE_MER]},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Fonds de carte OK : {len(noms_reg)} régions, {len(noms_dep)} départements")


if __name__ == "__main__":
    generer()
