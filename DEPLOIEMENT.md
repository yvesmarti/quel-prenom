# Mettre Prénoscope en ligne (GitHub Pages)

Le site est entièrement statique : GitHub le construit et le publie automatiquement à chaque envoi
sur la branche `main` (fichier `.github/workflows/deploy.yml`). Aucun serveur, aucun abonnement.

Adresse finale : `https://VOTRE-COMPTE.github.io/prenoscope/`

## Avant de commencer : ce qui deviendra public

Avec un compte GitHub gratuit, GitHub Pages exige un dépôt **public** : tout le dépôt sera lisible par tous
(code, documentation, données publiées, cahier des charges `PROMPT_PRENOSCOPE.md`, rapports de qualité).
Ne sont **pas** envoyés : les données brutes (`data/raw/`), la base de travail (`data/work/`), l'environnement Python.

**Adresse e-mail des commits** : chaque commit enregistre le nom et l'adresse configurés dans Git ; ils seront
visibles publiquement. Vérifier avec :

```
git log --format="%an <%ae>" | sort -u
```

Pour publier sous une adresse anonyme fournie par GitHub, la remplacer **avant le premier envoi** (voir la fin de ce guide).

## Étape 1 — Créer le dépôt sur GitHub (une seule fois)

1. Se connecter sur https://github.com, puis cliquer sur **New** (ou https://github.com/new).
2. Nom du dépôt : `prenoscope` (un autre nom change l'adresse du site, rien d'autre).
3. Choisir **Public**.
4. **Ne rien cocher** dans « Initialize this repository » (pas de README, pas de .gitignore, pas de licence :
   ils existent déjà dans le projet).
5. Cliquer sur **Create repository** et copier l'adresse affichée, du type
   `https://github.com/VOTRE-COMPTE/prenoscope.git`.

## Étape 2 — Activer GitHub Pages (une seule fois)

Dans le dépôt : **Settings** → **Pages** → rubrique *Build and deployment* → **Source : GitHub Actions**.

## Étape 3 — Envoyer le projet (une seule fois)

Dans un terminal ouvert à la racine du projet (`C:\Users\yvesm\Downloads\prenoms`) :

```
git remote add origin https://github.com/VOTRE-COMPTE/prenoscope.git
```

(relie le projet local au dépôt GitHub ; remplacer VOTRE-COMPTE)

```
git push -u origin main
```

(envoie tout l'historique ; au premier envoi, une fenêtre de connexion GitHub s'ouvre dans le navigateur.
Environ 17 Mo une fois compressé : une à quelques minutes selon la connexion.)

## Étape 4 — Vérifier la mise en ligne

1. Onglet **Actions** du dépôt : le travail « Publier le site » s'exécute (tests, construction, publication),
   en 2 à 4 minutes. Une coche verte = en ligne.
2. Ouvrir `https://VOTRE-COMPTE.github.io/prenoscope/`.
3. Si l'envoi a eu lieu avant l'étape 2 : **Actions** → « Publier le site » → **Run workflow**.

En cas de croix rouge : cliquer dessus pour lire l'erreur. Une erreur dans l'étape `npm test` signifie qu'un
test du site a échoué : rien n'est publié, l'ancienne version reste en ligne.

## Mises à jour suivantes

Après une modification (code ou données régénérées par `pipeline/run_all.py`) :

```
git add -A
```

```
git commit -m "Description de la modification"
```

```
git push
```

Le site se met à jour tout seul quelques minutes après.

## Option : publier avec une adresse e-mail anonyme

À faire **avant le premier `git push`**. Sur GitHub : **Settings** (du compte) → **Emails** → cocher
*Keep my email addresses private* et copier l'adresse du type `12345678+compte@users.noreply.github.com`. Puis :

```
git config user.email "12345678+compte@users.noreply.github.com"
```

(les futurs commits utiliseront cette adresse)

```
git rebase --root --exec "git commit --amend --reset-author --no-edit"
```

(réécrit les commits existants avec la nouvelle adresse ; à ne faire que tant que rien n'a été envoyé)

## Ce que contient cette première version (MVP)

- Recherche et filtres sur les 49 163 prénoms de l'Insee (1900–2025).
- Fiches : courbes (naissances, fréquence pour 1 000, rang), comparaison, chiffres clés, tendances, cartes
  régionales et départementales, étymologies, origines, prononciations et variantes (Wiktionnaire, Wikidata).
- Pages Classements, Tendances, Méthode.
- Pas encore : personnalités, générateur avancé, favoris, modules ludiques (voir `ROADMAP.md`).
