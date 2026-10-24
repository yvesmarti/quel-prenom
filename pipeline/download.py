"""Étape 1 : télécharge les fichiers sources et enregistre leur somme de contrôle.

Sources : voir config.SOURCES. Le manifeste data/raw/manifest.json garde, pour chaque
fichier, l'URL, la taille, le SHA-256 et la date de récupération.

Usage : python pipeline/download.py [--force]
"""
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone

import config

USER_AGENT = "Prenoscope/0.2 (projet personnel non commercial)"


def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def lire_manifeste():
    if not config.MANIFESTE.exists():
        return {}
    contenu = json.loads(config.MANIFESTE.read_text(encoding="utf-8"))
    if "fichiers" not in contenu:  # ancien format (phase 1) : une seule source
        contenu = {"fichiers": {contenu["source"]: contenu}}
    return contenu["fichiers"]


def telecharger(force=False):
    manifeste = lire_manifeste()
    for source in config.SOURCES:
        chemin = config.chemin_source(source["id"])
        if chemin.exists() and source["id"] in manifeste and not force:
            print(f"Déjà présent : {source['fichier']}")
            continue
        print(f"Téléchargement de {source['url']} …")
        chemin.parent.mkdir(parents=True, exist_ok=True)
        requete = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
        temporaire = chemin.with_suffix(chemin.suffix + ".part")
        with urllib.request.urlopen(requete, timeout=120) as reponse, open(temporaire, "wb") as f:
            while bloc := reponse.read(1 << 20):
                f.write(bloc)
        temporaire.replace(chemin)
        manifeste[source["id"]] = {
            "source": source["id"],
            "url": source["url"],
            "page": source["page"],
            "fichier": source["fichier"],
            "taille_octets": chemin.stat().st_size,
            "sha256": sha256(chemin),
            "recupere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"  OK : {manifeste[source['id']]['taille_octets']:,} octets")
    config.MANIFESTE.write_text(json.dumps({"fichiers": manifeste}, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifeste


if __name__ == "__main__":
    telecharger(force="--force" in sys.argv)
