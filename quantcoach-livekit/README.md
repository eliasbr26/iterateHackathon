# QuantCoach LiveKit - Interview Platform

Plateforme d'interview complète combinant l'interface QuantCoach avec l'intégration vidéo LiveKit.

## 🎯 Caractéristiques

- ✅ Interface utilisateur moderne basée sur QuantCoach (React + shadcn/ui)
- ✅ Intégration vidéo temps réel via LiveKit
- ✅ Backend FastAPI complet avec gestion des rooms
- ✅ Transcription audio en temps réel avec ElevenLabs
- ✅ Analyse et métriques d'interview en direct
- ✅ Dashboard interactif avec profils et reviews

## 📦 Structure du Projet

```
quantcoach-livekit/
├── frontend/           # Application React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── video/  # Composants vidéo LiveKit
│   │   │   ├── dashboard/
│   │   │   └── ui/     # shadcn/ui components
│   │   ├── hooks/      # Custom hooks (useLiveKit)
│   │   ├── services/   # API services
│   │   └── pages/
│   └── package.json
│
└── backend/            # API FastAPI + LiveKit
    ├── server.py       # Serveur FastAPI
    ├── room_manager.py # Gestion des rooms LiveKit
    ├── audio_pipeline/ # Pipeline de transcription
    └── requirements.txt
```

## 🚀 Installation

### Prérequis

- Node.js 18+ et npm
- Python 3.9+
- Compte LiveKit (pour les clés API)
- Compte ElevenLabs (optionnel, pour la transcription)

### Installation Complète

```bash
# Installer toutes les dépendances (frontend + backend)
npm run install:all
```

### Installation Séparée

```bash
# Frontend uniquement
cd frontend
npm install

# Backend uniquement
cd backend
pip install -r requirements.txt
```

## ⚙️ Configuration

### Frontend

1. Créer le fichier `.env` dans le dossier `frontend/`:

```bash
cp frontend/.env.example frontend/.env
```

2. Éditer `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

### Backend

1. Créer le fichier `.env` dans le dossier `backend/`:

```bash
cp backend/.env.example backend/.env
```

2. Éditer `backend/.env` avec vos clés LiveKit:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Optionnel: pour la transcription audio
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### Obtenir les Clés LiveKit

1. Aller sur [LiveKit Cloud](https://cloud.livekit.io/)
2. Créer un projet
3. Copier l'URL WebSocket, API Key et API Secret

## 🏃 Lancement

### Lancement Complet (Frontend + Backend)

```bash
# Depuis la racine du projet
npm run dev
```

Cette commande lance simultanément:
- Frontend sur `http://localhost:5173`
- Backend sur `http://localhost:8000`

### Lancement Séparé

```bash
# Terminal 1 - Backend
npm run dev:backend
# ou directement: cd backend && python3 server.py

# Terminal 2 - Frontend
npm run dev:frontend
# ou directement: cd frontend && npm run dev
```

## 📖 Utilisation

### Créer une Interview

1. Ouvrir `http://localhost:5173`
2. Dans l'onglet "Live Session", section vidéo en haut:
   - Entrer votre nom
   - Choisir votre rôle (Interviewer / Candidate)
   - Cliquer sur "Create New Room"
3. Autoriser l'accès caméra/micro quand demandé
4. Partager le nom du room avec l'autre participant

### Rejoindre une Interview

1. Ouvrir `http://localhost:5173`
2. Entrer votre nom et le nom du room fourni
3. Choisir votre rôle
4. Cliquer sur "Join Existing Room"

### Fonctionnalités du Dashboard

- **Live Session**: Vue en direct avec vidéo, transcription, métriques et alertes
- **Interviewer Profile**: Profil détaillé de l'interviewer avec historique
- **AI Reviews**: Analyse IA de la performance de l'interview

## 🎥 Composants Vidéo

### VideoArea

Composant principal gérant:
- Création/rejoindre des rooms
- Affichage des participants (local + remote)
- Contrôles audio/vidéo
- Gestion de la connexion LiveKit

### ParticipantView

Affiche un participant individuel avec:
- Flux vidéo
- Flux audio (pour participants distants)
- Label avec nom/identité

## 🔌 API Backend

### Endpoints Principaux

```
POST /rooms/create
- Créer une nouvelle room
- Retourne les tokens pour interviewer, candidate et agent

POST /tokens/generate
- Générer un token pour rejoindre une room existante

GET /rooms
- Lister toutes les rooms actives

GET /rooms/{room_name}/participants
- Obtenir la liste des participants d'une room

DELETE /rooms/{room_name}
- Supprimer une room
```

## 🛠️ Développement

### Frontend

```bash
cd frontend
npm run dev      # Mode développement
npm run build    # Build production
npm run preview  # Prévisualiser le build
```

### Backend

```bash
cd backend
python3 server.py           # Lancer le serveur
python3 validate_setup.py   # Valider la configuration
```

### Structure des Composants Vidéo

```tsx
// Hook personnalisé pour LiveKit
useLiveKit() -> {
  room, isConnected, connect(), disconnect(),
  toggleAudio(), toggleVideo()
}

// Service API
api.createRoom() -> CreateRoomResponse
api.generateToken() -> GenerateTokenResponse
```

## 🔒 Sécurité

- Les tokens LiveKit sont générés côté serveur avec expiration
- CORS configuré (à adapter pour production)
- Ne jamais exposer les clés API dans le frontend
- Utiliser HTTPS en production

## 📝 Scripts Disponibles

```bash
# Racine du projet
npm run dev              # Lance frontend + backend
npm run install:all      # Installe toutes les dépendances
npm run dev:frontend     # Lance seulement le frontend
npm run dev:backend      # Lance seulement le backend
npm run build:frontend   # Build le frontend pour production

# Frontend (dans frontend/)
npm run dev              # Serveur de développement
npm run build            # Build production
npm run lint             # Linter le code

# Backend (dans backend/)
python3 server.py                    # Lancer le serveur
python3 utils/generate_livekit_token.py  # Générer un token manuellement
```

## 🐛 Troubleshooting

### Le frontend ne se connecte pas au backend

- Vérifier que le backend tourne sur le port 8000
- Vérifier `VITE_API_URL` dans `frontend/.env`
- Vérifier les erreurs CORS dans la console

### Erreur de connexion LiveKit

- Vérifier les clés dans `backend/.env`
- Vérifier que l'URL LiveKit est correcte (format: `wss://...`)
- Vérifier que le projet LiveKit est actif

### Caméra/Micro ne fonctionnent pas

- Autoriser l'accès dans les paramètres du navigateur
- Utiliser HTTPS ou localhost (requis pour WebRTC)
- Vérifier les permissions système

### Port déjà utilisé

```bash
# Changer le port frontend dans frontend/vite.config.ts
# Changer le port backend dans backend/server.py (ligne uvicorn.run)
```

## 🔄 Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│   Frontend   │────────▶│   Backend   │
│  (React)    │  HTTP   │  (Vite/React)│   API   │  (FastAPI)  │
└─────────────┘         └──────────────┘         └─────────────┘
      │                                                   │
      │                                                   │
      │            ┌─────────────────────┐               │
      └───────────▶│   LiveKit Server    │◀──────────────┘
         WebRTC    │  (Video/Audio)      │    Tokens
                   └─────────────────────┘
```

## 📄 License

MIT

## 👥 Contribution

Ce projet intègre:
- **quantcoach-ai-main**: Interface UI/UX
- **jawad-livekit**: Backend et logique vidéo

## 📧 Support

Pour toute question:
- Consulter la documentation LiveKit: https://docs.livekit.io/
- Consulter la documentation FastAPI: https://fastapi.tiangolo.com/

---

**Version**: 1.0.0
**Dernière mise à jour**: 2025-11-15
