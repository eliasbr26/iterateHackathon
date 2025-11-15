# 🚀 Quick Start - QuantCoach LiveKit

Guide de démarrage rapide en 5 minutes.

## 1. Installation (première fois seulement)

```bash
cd quantcoach-livekit
npm run install:all
```

## 2. Configuration LiveKit

### Obtenir vos clés LiveKit (GRATUIT)

1. Aller sur https://cloud.livekit.io/
2. Créer un compte (gratuit)
3. Créer un nouveau projet
4. Copier:
   - WebSocket URL (format: `wss://xyz.livekit.cloud`)
   - API Key
   - API Secret

### Configurer le backend

```bash
# Copier le fichier exemple
cp backend/.env.example backend/.env

# Éditer avec vos clés
nano backend/.env  # ou ouvrir avec votre éditeur
```

Remplacer:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=votre_clé_api
LIVEKIT_API_SECRET=votre_secret
```

## 3. Lancer l'Application

### Méthode 1: Script automatique (recommandé)

```bash
./start.sh
```

### Méthode 2: Commande npm

```bash
npm run dev
```

### Méthode 3: Lancement manuel

```bash
# Terminal 1 - Backend
cd backend
python3 server.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## 4. Utiliser l'Application

1. Ouvrir le navigateur: http://localhost:5173
2. Dans la section vidéo:
   - Entrer votre nom: "Jean"
   - Choisir "Interviewer" ou "Candidate"
   - Cliquer "Create New Room"
3. Autoriser caméra/micro
4. **Partager le nom du room** avec l'autre participant
5. L'autre participant rejoint en entrant le même nom de room

## 🎯 Fonctionnalités

### Onglet "Live Session"
- **Zone vidéo** (en haut): Voir tous les participants
- **Metrics Panel** (gauche): Métriques de performance
- **Transcript Feed** (centre): Transcriptions en temps réel
- **Alert Panel** (droite): Suggestions IA en direct

### Onglet "Interviewer Profile"
- Profil détaillé de l'interviewer
- Historique et spécialisations
- Insights comportementaux

### Onglet "AI Reviews"
- Score global de performance
- Points forts identifiés
- Axes d'amélioration avec suggestions

## 🎮 Contrôles Vidéo

- 🎤 **Toggle Microphone**: Activer/désactiver le micro
- 📹 **Toggle Camera**: Activer/désactiver la caméra
- 📞 **Leave Room**: Quitter la session

## ⚙️ Ports Utilisés

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 🐛 Résolution de Problèmes

### "Cannot connect to backend"
```bash
# Vérifier que le backend tourne
curl http://localhost:8000
```

### "LiveKit connection failed"
- Vérifier les clés dans `backend/.env`
- Vérifier que l'URL commence par `wss://`
- Vérifier votre projet LiveKit sur cloud.livekit.io

### "Camera/Mic not working"
- Autoriser dans les paramètres du navigateur
- Chrome/Firefox: Cliquer sur le cadenas dans la barre d'adresse
- Safari: Paramètres → Sites web → Caméra/Microphone

### "Port already in use"

Frontend (5173):
```bash
# Dans frontend/vite.config.ts, changer le port
export default defineConfig({
  server: { port: 5174 }
})
```

Backend (8000):
```bash
# Dans backend/server.py, ligne uvicorn.run
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## 📱 Test avec 2 Participants

### Méthode 1: 2 Fenêtres de navigateur
1. Ouvrir 2 onglets de `localhost:5173`
2. Onglet 1: Create room as "Interviewer"
3. Noter le nom du room (ex: `interview-20250115-143022`)
4. Onglet 2: Join room avec ce nom as "Candidate"

### Méthode 2: 2 Appareils sur le même réseau
1. Trouver l'IP locale de votre machine:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
2. Appareil 1: `http://localhost:5173`
3. Appareil 2: `http://[VOTRE_IP]:5173`

## 🔒 Mode Production

Pour déployer en production:

1. Build le frontend:
```bash
cd frontend
npm run build
```

2. Servir avec un serveur web (nginx, etc.)

3. Mettre à jour les CORS dans `backend/server.py`:
```python
allow_origins=["https://votre-domaine.com"]
```

4. Utiliser HTTPS (requis pour WebRTC)

## 📚 Plus d'Informations

- README complet: `README.md`
- Documentation Backend: http://localhost:8000/docs
- LiveKit Docs: https://docs.livekit.io/

---

**Besoin d'aide?** Consultez le [README.md](README.md) complet.
