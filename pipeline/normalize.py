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
