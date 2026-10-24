"""Règles de normalisation et de description d'un prénom.

Ces règles sont reproduites à l'identique dans site/src/lib/normalize.js
(les tests vérifient la cohérence). La graphie INSEE d'origine n'est jamais modifiée :
on calcule seulement des champs dérivés à côté.
"""
import unicodedata

# Ligatures non décomposées par Unicode (NFD) : traitées à la main.
LIGATURES = {"æ": "ae", "œ": "oe"}


def identifiant(prenom_insee):
    """Identifiant stable : la graphie INSEE en minuscules (Léa ≠ Lea)."""
    return prenom_insee.lower()


def normaliser(texte):
    """Minuscules, sans accents ni ligatures — sert uniquement à la recherche."""
    texte = texte.lower()
    for lig, rempl in LIGATURES.items():
        texte = texte.replace(lig, rempl)
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def affichage(prenom_insee):
    """Graphie d'affichage dérivée (l'INSEE publie tout en majuscules).

    Règle : majuscule initiale et après un tiret ou une espace ; après une
    apostrophe, majuscule seulement si elle suit une lettre isolée en début de
    segment (M'Hamed, N'Deye, O'Bryan) ; sinon minuscule (William's, Gwenc'hlan).
    Cette mise en casse est une convention d'affichage, pas une donnée INSEE.
    """
    sortie = []
    debut_segment = 0
    for i, c in enumerate(prenom_insee.lower()):
        if i == debut_segment:
            sortie.append(c.upper())
        elif sortie and sortie[-1] == "'" and i - debut_segment == 2:
            sortie.append(c.upper())
        else:
            sortie.append(c)
        if c in "- ":
            debut_segment = i + 1
    return "".join(sortie)


def nb_lettres(prenom_insee):
    """Nombre de lettres (tirets, apostrophes et espaces exclus ; Æ compte pour 1)."""
    return sum(1 for c in prenom_insee if c.isalpha())


def a_accent(prenom_insee):
    """Vrai si le prénom contient une lettre accentuée ou une ligature (É, Ë, Ç, Æ…)."""
    return any(c.isalpha() and not ("A" <= c.upper() <= "Z") for c in prenom_insee)


def est_compose(prenom_insee):
    """Prénom composé = contient un tiret (Marie-Claire). Règle documentée dans DATA_MODEL.md."""
    return "-" in prenom_insee


def cle_lot(prenom_insee, longueur=2):
    """Nom du fichier de détails : premières lettres normalisées (ex. « le » pour Léa).

    Les séries utilisent 2 lettres, les données géographiques (plus lourdes) 3 lettres.
    """
    lettres = [c for c in normaliser(prenom_insee) if "a" <= c <= "z"]
    return "".join(lettres[:longueur]) or "_"


_VOYELLES = "aeiouyàâäéèêëîïôöùûüœæ"


def nb_syllabes(prenom):
    """Estimation du nombre de syllabes (règles simples du français, tiret = mots séparés).

    Approximative : sert uniquement aux suggestions (sonorité), jamais présentée comme exacte.
    """
    total = 0
    for mot in prenom.lower().split("-"):
        lettres = [c for c in mot if c.isalpha()]
        # e final muet (Alice, Anne, Jade, Jules, Renée), si une voyelle précède.
        if len(lettres) > 3 and lettres[-2:] == ["e", "s"] and lettres[-3] not in _VOYELLES:
            lettres = lettres[:-2]
        elif len(lettres) > 2 and lettres[-1] == "e" and (lettres[-2] not in _VOYELLES or lettres[-2] == "é") \
                and any(c in _VOYELLES for c in lettres[:-2]):
            lettres = lettres[:-1]
        # y devant une voyelle est une consonne (Yanis, Maya).
        sons = [("v" if c in _VOYELLES and not (c == "y" and i + 1 < len(lettres) and lettres[i + 1] in _VOYELLES)
                 else "c") for i, c in enumerate(lettres)]
        n, i = 0, 0
        while i < len(lettres):
            if sons[i] == "v":
                debut = i
                while i < len(lettres) and sons[i] == "v":
                    i += 1
                suite = lettres[debut:i]
                suivante = lettres[i] if i < len(lettres) else ""
                n += 1 + sum(_hiatus(suite[k], suite[k + 1], suite[k + 2] if k + 2 < len(suite) else suivante)
                             for k in range(len(suite) - 1))
            else:
                i += 1
        total += max(n, 1)
    return total


def _hiatus(x, y, suivante=""):
    """Vrai si deux voyelles contiguës se prononcent en deux syllabes (Léa, Noël, Zoé, Mia, Noa, Gabriel)."""
    if x == "u" and y == "e":
        return False
    if x == "i" and y == "e":  # Gabriel, Daniel (ga-bri-el) mais Olivier, Marie
        return suivante == "l"
    return (x in "éèêëï" or y in "éèëïü" or (x in "iu" and y in "aoeé")
            or (x == "o" and y == "a") or (x == "a" and y == "o"))
