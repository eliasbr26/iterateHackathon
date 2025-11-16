# 🐛 Debug Notes - QuantCoach LiveKit

## Date: 2025-11-15

## Problème Initial

**Erreur:** `ModuleNotFoundError: No module named 'dotenv'`

**Cause:** Le script `package.json` utilise `python3` (Python système) au lieu de `python` (Python de l'environnement conda ttk où toutes les dépendances sont installées).

## Modifications Apportées

### 1. Fichier `package.json` (Racine)

**Ligne 9 - Modifiée:**
```json
// AVANT
"dev:backend": "cd backend && python3 server.py"

// APRÈS
"dev:backend": "cd backend && python server.py"
```

**Raison:** Utiliser `python` au lieu de `python3` pour pointer vers le Python de l'environnement conda ttk.

### 2. Fichier `start.sh`

**Ligne 32 - Modifiée:**
```bash
# AVANT
if ! python3 -c "import fastapi" 2>/dev/null; then

# APRÈS
if ! python -c "import fastapi" 2>/dev/null; then
```

**Raison:** Cohérence avec l'utilisation de `python` au lieu de `python3`.

### 3. Nouveau Fichier `start-with-conda.sh`

**Créé:** Script alternatif avec vérification de l'environnement conda.

**Fonctionnalités:**
- Vérifie que l'environnement conda ttk est activé
- Affiche un avertissement si ce n'est pas le cas
- Demande confirmation avant de continuer
- Installe les dépendances manquantes (concurrently, npm packages, pip packages)
- Lance le projet avec `npm run dev`

**Utilisation recommandée:**
```bash
# 1. Activer l'environnement conda
conda activate ttk

# 2. Lancer le script
./start-with-conda.sh
```

## Problèmes Identifiés

### 1. Dépendance `concurrently` Manquante

**Statut:** ⚠️ À installer

Le package `concurrently` n'est pas installé dans le dossier racine.

**Solution:**
```bash
# Depuis la racine du projet (avec conda ttk activé)
npm install
```

### 2. Terminal Bash vs Terminal Conda

**Problème:** Le terminal Bash intégré de Claude Code n'a pas accès direct à l'environnement conda.

**Solution:** L'utilisateur doit lancer les scripts depuis un terminal où conda est déjà activé (terminal VS Code intégré avec (ttk) dans le prompt).

## Instructions de Lancement Correctes

### Méthode 1: Avec start-with-conda.sh (Recommandée)

```bash
# Terminal 1 (dans VS Code, avec prompt (ttk))
cd /Users/steph/Desktop/Hack/iterateHackathon/quantcoach-livekit

# Vérifier que conda ttk est activé
# Le prompt devrait afficher: (ttk) steph@...

# Installer concurrently si nécessaire
npm install

# Lancer le projet
./start-with-conda.sh
```

### Méthode 2: Avec npm directement

```bash
# Terminal avec (ttk) activé
cd /Users/steph/Desktop/Hack/iterateHackathon/quantcoach-livekit

# Installer concurrently
npm install

# Lancer
npm run dev
```

### Méthode 3: Lancement Manuel (2 terminaux)

```bash
# Terminal 1 - Backend (avec ttk activé)
cd quantcoach-livekit/backend
python server.py

# Terminal 2 - Frontend
cd quantcoach-livekit/frontend
npm run dev
```

## Vérifications à Effectuer

### 1. Vérifier l'environnement Python

```bash
# Dans le terminal avec (ttk) activé
python -c "import sys; print(sys.executable)"
# Devrait afficher: .../envs/ttk/bin/python

python -c "import dotenv; import fastapi; print('✅ OK')"
# Devrait afficher: ✅ OK
```

### 2. Vérifier que npm/node sont accessibles

```bash
which node
which npm
node --version
npm --version
```

### 3. Vérifier concurrently

```bash
npm list concurrently
# Devrait afficher: concurrently@8.2.2
```

## État Actuel du Projet

### ✅ Complété

- [x] Modification de `package.json` (python au lieu de python3)
- [x] Modification de `start.sh` (python au lieu de python3)
- [x] Création de `start-with-conda.sh` avec vérifications
- [x] Documentation des modifications dans DEBUG_NOTES.md

### ⚠️ Nécessite Action Utilisateur

- [ ] Activer l'environnement conda ttk dans le terminal VS Code
- [ ] Installer concurrently: `npm install`
- [ ] Lancer le projet avec `./start-with-conda.sh` ou `npm run dev`
- [ ] Vérifier que:
  - Backend démarre sur http://0.0.0.0:8000
  - Frontend démarre sur http://localhost:5173

## Résultats Attendus

### Backend (Port 8000)

```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Frontend (Port 5173)

```
VITE v5.4.19  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

## Commandes de Diagnostic

### Si le backend ne démarre pas

```bash
cd backend
python server.py
# Observer les erreurs

# Vérifier les dépendances
pip list | grep fastapi
pip list | grep dotenv
pip list | grep livekit
```

### Si le frontend ne démarre pas

```bash
cd frontend
npm run dev
# Observer les erreurs

# Vérifier node_modules
ls -la node_modules | head
```

### Si concurrently ne fonctionne pas

```bash
# Réinstaller
rm -rf node_modules package-lock.json
npm install

# Ou installer globalement
npm install -g concurrently
```

## Notes Additionnelles

### Environnement Conda

L'environnement conda `ttk` contient:
- Python avec toutes les dépendances backend (FastAPI, LiveKit, dotenv, etc.)
- Node.js et npm pour le frontend

**Important:** Tous les scripts doivent être lancés depuis un terminal où `conda activate ttk` a été exécuté.

### Alternative: Utiliser python3 avec pip install

Si vous préférez utiliser python3 (Python système):

```bash
# Installer les dépendances dans Python système
cd backend
pip3 install -r requirements.txt

# Puis utiliser python3 dans package.json (revert les changements)
```

Mais cette approche n'est **pas recommandée** car elle ne respecte pas l'isolation des environnements.

## Prochaines Étapes

1. **L'utilisateur doit:**
   - Ouvrir un terminal VS Code avec conda ttk activé
   - Exécuter `npm install` à la racine du projet
   - Lancer `./start-with-conda.sh` ou `npm run dev`

2. **Vérifications:**
   - Backend accessible sur http://localhost:8000
   - Frontend accessible sur http://localhost:5173
   - Pas d'erreurs dans les logs

3. **Test fonctionnel:**
   - Créer une room d'interview
   - Vérifier que la vidéo fonctionne
   - Vérifier que les contrôles audio/vidéo fonctionnent

---

**Fichiers modifiés:** 2 (package.json, start.sh)
**Fichiers créés:** 2 (start-with-conda.sh, DEBUG_NOTES.md)
**Status:** ✅ Corrections effectuées, en attente de test utilisateur
