import sys
from pathlib import Path

# Permet d'importer les modules du dossier pipeline/ dans les tests.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
