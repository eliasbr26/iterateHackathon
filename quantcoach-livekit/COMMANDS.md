# ⚡ Commandes Rapides - QuantCoach LiveKit

## 🚀 Démarrage

```bash
# Lancement automatique (recommandé)
./start.sh

# Ou avec npm
npm run dev

# Ou manuellement
npm run dev:backend &  # Terminal 1
npm run dev:frontend   # Terminal 2
```

## 📦 Installation

```bash
# Tout installer d'un coup
npm run install:all

# Frontend seulement
cd frontend && npm install

# Backend seulement
cd backend && pip install -r requirements.txt
```

## ⚙️ Configuration

```bash
# Créer les fichiers .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Éditer les configs
nano backend/.env      # Ajouter clés LiveKit
nano frontend/.env     # Vérifier API URL
```

## 🔧 Développement Frontend

```bash
cd frontend

npm run dev          # Dev server (http://localhost:5173)
npm run build        # Build production
npm run preview      # Preview build
npm run lint         # Linter
```

## 🐍 Développement Backend

```bash
cd backend

python3 server.py                    # Lancer serveur
python3 validate_setup.py            # Valider config
python3 utils/generate_livekit_token.py  # Générer token manuellement
```

## 🧹 Nettoyage

```bash
# Frontend
cd frontend
rm -rf node_modules dist
npm install

# Backend
cd backend
find . -type d -name "__pycache__" -exec rm -rf {} +
pip install -r requirements.txt --force-reinstall
```

## 🧪 Tests

```bash
# Tester le backend
curl http://localhost:8000
curl http://localhost:8000/rooms

# Tester LiveKit connection
cd backend
python3 validate_setup.py

# Tester le build frontend
cd frontend
npm run build
npm run preview
```

## 📍 URLs Importantes

```
Frontend Dev:      http://localhost:5173
Backend API:       http://localhost:8000
API Docs:          http://localhost:8000/docs
API Redoc:         http://localhost:8000/redoc
```

## 🔍 Debugging

```bash
# Logs backend en détail
cd backend
python3 server.py --reload --log-level debug

# Vérifier ports utilisés
lsof -i :5173  # Frontend
lsof -i :8000  # Backend

# Tuer un processus sur un port
kill -9 $(lsof -ti:5173)
kill -9 $(lsof -ti:8000)
```

## 🌐 Réseau Local

```bash
# Trouver IP locale
ifconfig | grep "inet " | grep -v 127.0.0.1

# Accès depuis autre appareil
http://[VOTRE_IP]:5173
```

## 📦 Build Production

```bash
# Build frontend
cd frontend
npm run build
# Résultat dans: frontend/dist/

# Servir avec un serveur web
npx serve -s dist -p 3000
```

## 🔒 Variables d'Environnement

### Backend (.env)
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxx
LIVEKIT_API_SECRET=xxx
ELEVENLABS_API_KEY=xxx  # Optionnel
PORT=8000
HOST=0.0.0.0
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## 📊 Structure Rapide

```
quantcoach-livekit/
├── frontend/              # React + Vite
│   ├── src/
│   │   ├── components/video/  # Composants vidéo
│   │   ├── hooks/             # useLiveKit
│   │   ├── services/          # API client
│   │   └── pages/             # Index.tsx
│   └── package.json
│
├── backend/               # FastAPI + LiveKit
│   ├── server.py          # API principale
│   ├── room_manager.py    # Gestion LiveKit
│   └── audio_pipeline/    # Transcription
│
├── package.json           # Scripts racine
└── start.sh              # Lancement auto
```

## 🎯 Workflow Typique

```bash
# 1. Première installation
git clone [...]
cd quantcoach-livekit
npm run install:all

# 2. Configuration
cp backend/.env.example backend/.env
# Éditer backend/.env avec clés LiveKit

# 3. Lancement
./start.sh

# 4. Test
# Ouvrir http://localhost:5173
# Créer une room
# Rejoindre avec 2ème onglet

# 5. Développement
# Modifier les fichiers
# Hot reload automatique (frontend et backend)

# 6. Commit
git add .
git commit -m "feat: add new feature"
git push
```

## 🆘 Commandes de Dépannage

```bash
# Réinstaller tout
rm -rf frontend/node_modules frontend/dist
cd frontend && npm install

cd ../backend
pip install -r requirements.txt --force-reinstall

# Vérifier versions
node --version          # Doit être 18+
python3 --version       # Doit être 3.9+
npm --version

# Vérifier dépendances
cd frontend && npm list livekit-client
cd backend && pip list | grep fastapi

# Reset complet
git clean -fdx          # ⚠️  Supprime TOUS les fichiers non versionnés
npm run install:all
```

## 🔄 Hot Reload

Les deux serveurs supportent le hot reload:

**Frontend (Vite):**
- Modification automatique détectée
- Rafraîchissement instantané du navigateur

**Backend (Uvicorn):**
- Détection automatique si lancé avec `--reload`
- Redémarrage automatique du serveur

## 📝 Git Workflow

```bash
# Créer une branche
git checkout -b feature/new-feature

# Faire des changements
# ...

# Commit
git add .
git commit -m "feat: description"

# Push
git push origin feature/new-feature

# Créer PR sur GitHub
```

## 🎨 Customisation

```bash
# Changer port frontend
# Éditer: frontend/vite.config.ts
server: { port: 5174 }

# Changer port backend
# Éditer: backend/server.py
uvicorn.run(app, port=8001)

# Changer couleurs
# Éditer: frontend/src/index.css
```

---

**Astuce**: Créer un alias dans votre shell

```bash
# Dans ~/.zshrc ou ~/.bashrc
alias qc-start='cd /path/to/quantcoach-livekit && ./start.sh'
alias qc-clean='cd /path/to/quantcoach-livekit && rm -rf frontend/node_modules frontend/dist'
```

**Utilisation**:
```bash
qc-start   # Lance le projet de n'importe où
qc-clean   # Nettoyage rapide
```
