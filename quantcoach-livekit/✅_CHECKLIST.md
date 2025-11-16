# ✅ Checklist de Lancement - QuantCoach LiveKit

## 📋 Avant de Lancer

### Environnement
- [ ] Terminal VS Code ouvert
- [ ] Prompt affiche `(ttk)` 
- [ ] Si non: `conda activate ttk`

### Vérifications Python
```bash
# Copier-coller cette ligne dans le terminal
python -c "import sys; import fastapi; import dotenv; print('✅ Environnement OK:', sys.executable)"
```
- [ ] Affiche "✅ Environnement OK" avec chemin contenant "ttk"

### Dossier du Projet
```bash
cd /Users/steph/Desktop/Hack/iterateHackathon/quantcoach-livekit
pwd
```
- [ ] Affiche le chemin correct

## 🚀 Installation (Première fois)

```bash
# Installer concurrently
npm install
```
- [ ] Pas d'erreurs
- [ ] Dossier `node_modules` créé

```bash
# Vérifier concurrently
npm list concurrently
```
- [ ] Affiche `concurrently@8.2.2`

## ⚙️ Configuration Backend

```bash
# Vérifier .env existe
ls backend/.env
```
- [ ] Fichier existe
- [ ] Contient les clés LiveKit

Si le fichier n'existe pas:
```bash
cp backend/.env.example backend/.env
nano backend/.env  # Éditer avec vos clés
```

## 🎬 Lancement

```bash
# Lancer le projet
npm run dev
```

### Vérifications Pendant le Lancement

**Attendez 5-10 secondes**, puis vérifiez:

#### Backend (Terminal ligne [1])
- [ ] Affiche: `INFO:     Uvicorn running on http://0.0.0.0:8000`
- [ ] Pas d'erreur "ModuleNotFoundError"
- [ ] Pas d'erreur "dotenv"

#### Frontend (Terminal ligne [0])
- [ ] Affiche: `VITE v5.4.19  ready in XXX ms`
- [ ] Affiche: `➜  Local:   http://localhost:5173/`
- [ ] Pas d'erreur de compilation

## 🌐 Test dans le Navigateur

### Ouvrir l'Application
```
http://localhost:5173
```
- [ ] Page charge correctement
- [ ] Pas d'erreur dans la console navigateur (F12)
- [ ] Interface QuantCoach visible

### Tester la Zone Vidéo

1. **Créer une Room**
   - [ ] Entrer votre nom (ex: "Jean")
   - [ ] Choisir "Interviewer"
   - [ ] Cliquer "Create New Room"
   - [ ] Autoriser caméra/micro dans le popup
   - [ ] Votre vidéo apparaît
   - [ ] Contrôles visibles (🎤 📹 📞)

2. **Test Multi-Participant**
   - [ ] Noter le nom du room (ex: `interview-20250115-194500`)
   - [ ] Ouvrir un 2ème onglet: http://localhost:5173
   - [ ] Entrer un autre nom (ex: "Marie")
   - [ ] Choisir "Candidate"
   - [ ] Entrer le même nom de room
   - [ ] Cliquer "Join Existing Room"
   - [ ] Les deux vidéos sont visibles dans chaque onglet

## 🐛 Si Problème

### Erreur: "ModuleNotFoundError: No module named 'dotenv'"

**Cause:** Environnement conda pas activé

**Solution:**
```bash
# Ctrl+C pour arrêter
conda activate ttk
npm run dev
```

### Erreur: "concurrently: command not found"

**Solution:**
```bash
npm install
npm run dev
```

### Backend Ne Démarre Pas

**Solution:**
```bash
# Terminal avec (ttk) activé
cd backend
python server.py
# Observer les erreurs
```

### Frontend Ne Démarre Pas

**Solution:**
```bash
cd frontend
npm run dev
# Observer les erreurs
```

### Port Déjà Utilisé

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
npm run dev
```

**Frontend (5173):**
```bash
lsof -ti:5173 | xargs kill -9
npm run dev
```

## ✅ Succès!

Si tous les checks sont ✅:
- Frontend: http://localhost:5173 ✅
- Backend: http://localhost:8000 ✅
- API Docs: http://localhost:8000/docs ✅
- Vidéo fonctionne ✅
- Multi-participant fonctionne ✅

**Vous êtes prêt à utiliser l'application!** 🎉

## 📚 Prochaines Étapes

- [ ] Configurer les clés LiveKit (si pas fait)
- [ ] Tester avec 2 appareils différents
- [ ] Consulter [README.md](README.md) pour plus de fonctionnalités

## 🆘 Besoin d'Aide?

Consultez dans cet ordre:
1. [START_HERE.md](START_HERE.md) - Guide rapide
2. [DEBUG_NOTES.md](DEBUG_NOTES.md) - Détails debug
3. [QUICKSTART.md](QUICKSTART.md) - Guide complet

---

**Créé le:** 2025-11-15
**Status:** ✅ Prêt à utiliser
