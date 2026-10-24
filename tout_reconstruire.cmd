@echo off
rem Reconstruit tout le projet : dépendances, données, tests, site de production.
rem Double-cliquer ce fichier ou lancer « tout_reconstruire » dans un terminal à la racine du projet.
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv (
  echo === Création de l'environnement Python ===
  python -m venv .venv || goto erreur
)
echo === Dépendances Python ===
.venv\Scripts\python -m pip install -q -r requirements.txt || goto erreur

echo === Données INSEE : téléchargement, base, JSON, rapport ===
.venv\Scripts\python pipeline\run_all.py || goto erreur

echo === Tests des données ===
.venv\Scripts\python -m pytest -q || goto erreur

echo === Site : dépendances, tests, build ===
cd site
call npm install || goto erreur
call npm test || goto erreur
call npm run build || goto erreur
cd ..

echo.
echo Terminé. Site de production dans site\dist\ ; rapport dans data\reports\qualite.md
exit /b 0

:erreur
echo.
echo *** Une étape a échoué : lire le message ci-dessus. ***
exit /b 1
