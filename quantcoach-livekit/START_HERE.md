# 🚀 START HERE - Guide de Lancement Rapide

## ⚠️ IMPORTANT: Activer l'Environnement Conda d'Abord!

Avant de lancer le projet, vous **DEVEZ** avoir l'environnement conda `ttk` activé.

## 📝 Étapes de Lancement (3 minutes)

### 1️⃣ Ouvrir un Terminal avec Conda

**Dans VS Code:**
- Appuyez sur `Ctrl + ù` (ou `Cmd + ù` sur Mac)
- Un terminal devrait s'ouvrir avec le prompt: `(ttk) steph@...`

**Si le prompt ne montre PAS `(ttk)`:**
```bash
conda activate ttk
```

### 2️⃣ Aller dans le Dossier du Projet

```bash
cd /Users/steph/Desktop/Hack/iterateHackathon/quantcoach-livekit
```

### 3️⃣ Installer Concurrently (Première fois seulement)

```bash
npm install
```

### 4️⃣ Lancer le Projet

```bash
./start-with-conda.sh
```

Ou directement:
```bash
npm run dev
```

## ✅ Vérifications

Vous devriez voir:

**Terminal - Backend:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Terminal - Frontend:**
```
➜  Local:   http://localhost:5173/
```

## 🌐 Accès à l'Application

**Ouvrir dans le navigateur:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🐛 En Cas d'Erreur

### Erreur: "ModuleNotFoundError: No module named 'dotenv'"

**Cause:** L'environnement conda `ttk` n'est pas activé.

**Solution:**
```bash
conda activate ttk
npm run dev
```

### Erreur: "concurrently: command not found"

**Solution:**
```bash
npm install
```

### Le Backend Ne Démarre Pas

**Vérifier les dépendances Python:**
```bash
python -c "import fastapi; import dotenv; print('✅ OK')"
```

**Si erreur, installer:**
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Le Frontend Ne Démarre Pas

**Vérifier node_modules:**
```bash
cd frontend
ls node_modules | head
```

**Si vide, installer:**
```bash
npm install
cd ..
```

## 🎯 Utilisation Rapide

### Créer une Interview

1. Aller sur http://localhost:5173
2. Entrer votre nom
3. Choisir "Interviewer" ou "Candidate"
4. Cliquer "Create New Room"
5. Autoriser caméra/micro
6. Partager le nom du room avec l'autre participant

### Rejoindre une Interview

1. Aller sur http://localhost:5173
2. Entrer votre nom
3. Entrer le nom du room
4. Choisir votre rôle
5. Cliquer "Join Existing Room"

## 📚 Documentation Complète

- [DEBUG_NOTES.md](DEBUG_NOTES.md) - Détails des modifications
- [README.md](README.md) - Documentation complète
- [QUICKSTART.md](QUICKSTART.md) - Guide détaillé
- [COMMANDS.md](COMMANDS.md) - Référence des commandes

## 💡 Astuces

### Arrêter le Projet

Appuyez sur `Ctrl + C` dans le terminal.

### Relancer Rapidement

```bash
# Si déjà installé
npm run dev
```

### Vérifier l'Environnement

```bash
# Python actuel
python -c "import sys; print(sys.executable)"
# Devrait contenir: /envs/ttk/

# Modules Python disponibles
python -c "import fastapi, dotenv; print('✅ OK')"
```

---

**Problème résolu:** ✅ Les scripts utilisent maintenant `python` au lieu de `python3`
**Prêt à lancer:** ✅ Oui, avec conda ttk activé
