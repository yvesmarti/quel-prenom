"""Étape 1 : télécharge le fichier Parquet INSEE et enregistre sa somme de contrôle.

Usage : python pipeline/download.py [--force]
"""
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone

import config

USER_AGENT = "Prenoscope/0.1 (projet personnel non commercial)"


def sha256(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def telecharger(force=False):
    config.DOSSIER_RAW.mkdir(parents=True, exist_ok=True)
    if config.FICHIER_PARQUET.exists() and config.MANIFESTE.exists() and not force:
        print(f"Déjà présent : {config.FICHIER_PARQUET.name} (utiliser --force pour retélécharger)")
        return json.loads(config.MANIFESTE.read_text(encoding="utf-8"))

    print(f"Téléchargement de {config.URL_PARQUET} …")
    requete = urllib.request.Request(config.URL_PARQUET, headers={"User-Agent": USER_AGENT})
    temporaire = config.FICHIER_PARQUET.with_suffix(".part")
    with urllib.request.urlopen(requete, timeout=120) as reponse, open(temporaire, "wb") as f:
        while bloc := reponse.read(1 << 20):
            f.write(bloc)
    temporaire.replace(config.FICHIER_PARQUET)

    manifeste = {
        "source": config.SOURCE_ID,
        "url": config.URL_PARQUET,
        "page": config.PAGE_INSEE,
        "fichier": config.FICHIER_PARQUET.name,
        "taille_octets": config.FICHIER_PARQUET.stat().st_size,
        "sha256": sha256(config.FICHIER_PARQUET),
        "recupere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    config.MANIFESTE.write_text(json.dumps(manifeste, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK : {manifeste['taille_octets']:,} octets, sha256 {manifeste['sha256'][:16]}…")
    return manifeste


if __name__ == "__main__":
    telecharger(force="--force" in sys.argv)
