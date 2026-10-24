"""Petits outils communs au pipeline."""
import csv

import config


def inserer(con, table, colonnes, lignes):
    """Crée la table `table` (colonnes = {nom: type SQL}) et y insère les lignes.

    Passe par un CSV temporaire : bien plus rapide qu'une insertion ligne à ligne.
    """
    if not lignes:  # table vide : on crée seulement sa structure
        con.execute(f"DROP TABLE IF EXISTS {table}")
        con.execute(f"CREATE TABLE {table} ({', '.join(f'{n} {t}' for n, t in colonnes.items())})")
        return
    temporaire = config.BASE.parent / f"{table}_tmp.csv"
    with open(temporaire, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(lignes)
    types = ", ".join(f"'{nom}': '{t}'" for nom, t in colonnes.items())
    con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute(f"""CREATE TABLE {table} AS SELECT * FROM read_csv('{temporaire.as_posix()}',
        header = false, quote = '"', escape = '"', columns = {{{types}}})""")
    temporaire.unlink()
