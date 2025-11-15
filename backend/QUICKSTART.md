# 🚀 Quick Start Guide - Backend

Guide rapide pour démarrer le backend de l'application Interview Analysis.

## 📋 Prérequis

- Node.js (v16 ou supérieur)
- npm (généralement installé avec Node.js)

## ⚡ Installation et Démarrage (3 étapes)

### 1️⃣ Installer les dépendances

```bash
cd backend
npm install
```

### 2️⃣ Démarrer le serveur

```bash
npm run dev
```

Le serveur démarre sur **http://localhost:3001**

Vous devriez voir:
```
========================================
🚀 Interview Analysis Backend Started
========================================
📡 HTTP Server: http://localhost:3001
🔌 WebSocket Server: ws://localhost:3001
========================================
```

### 3️⃣ Tester le serveur

Ouvrez un nouveau terminal et lancez:

```bash
# Test simple avec curl
curl http://localhost:3001/

# Ou ouvrez dans votre navigateur
open http://localhost:3001/
```

## 🧪 Tests Complets

### Option A: Tests HTTP avec curl

```bash
# Rendre le script exécutable
cd

# Lancer les tests
./test-server.sh
```

### Option B: Tests Socket.IO avec l'interface web

1. Ouvrir `test-client.html` dans votre navigateur:
   ```bash
   open test-client.html
   ```

2. Cliquer sur **"Connect to Server"**

3. Cliquer sur **"Send Question"** pour envoyer une question test

4. Observer les logs en temps réel et les statistiques

## 📡 Endpoints Disponibles

### HTTP REST API

| Method | Endpoint | Description | Exemple |
|--------|----------|-------------|---------|
| GET | `/` | Health check | `curl http://localhost:3001/` |
| GET | `/livekit-token` | Générer un token LiveKit | `curl "http://localhost:3001/livekit-token?roomId=room1&identity=user1"` |
| GET | `/interview/:roomId/stats` | Stats d'un entretien | `curl http://localhost:3001/interview/room1/stats` |

### Socket.IO Events

**Événements entrants (client → serveur):**
- `join:room` - Rejoindre une room
- `leave:room` - Quitter une room
- `question:new` - Nouvelle question à analyser
- `interview:reset` - Réinitialiser l'entretien

**Événements sortants (serveur → client):**
- `room:joined` - Confirmation de room jointe
- `difficulty:update` - Mise à jour de difficulté
- `question:processed` - Question traitée avec succès
- `question:error` - Erreur lors du traitement
- `interview:resetted` - Entretien réinitialisé

## 💡 Exemples d'Utilisation

### Exemple 1: Obtenir un token LiveKit

```bash
curl "http://localhost:3001/livekit-token?roomId=interview-123&identity=recruiter"
```

**Réponse:**
```json
{
  "token": "FAKE_LIVEKIT_TOKEN_interview-123_recruiter_1700000000000",
  "roomId": "interview-123",
  "identity": "recruiter",
  "timestamp": 1700000000000
}
```

### Exemple 2: Socket.IO avec JavaScript

```html
<script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
<script>
  const socket = io('http://localhost:3001');
  
  // Connexion
  socket.on('connect', () => {
    console.log('Connected!');
    
    // Rejoindre une room
    socket.emit('join:room', 'my-room');
    
    // Envoyer une question
    socket.emit('question:new', {
      roomId: 'my-room',
      text: 'Expliquez la récursivité'
    });
  });
  
  // Recevoir les mises à jour
  socket.on('difficulty:update', (data) => {
    console.log('New difficulty:', data.difficulty);
    console.log('Average:', data.avgDifficulty);
  });
</script>
```

### Exemple 3: Envoyer plusieurs questions

```bash
# Créer un fichier test-questions.sh
cat > test-questions.sh << 'EOF'
#!/bin/bash
ROOM="test-room-001"

# Question 1
echo "Question 1..."
curl -X POST http://localhost:3001/question \
  -H "Content-Type: application/json" \
  -d "{\"roomId\":\"$ROOM\",\"text\":\"Comment fonctionne un hash table?\"}"

sleep 1

# Question 2
echo "Question 2..."
curl -X POST http://localhost:3001/question \
  -H "Content-Type: application/json" \
  -d "{\"roomId\":\"$ROOM\",\"text\":\"Expliquez le pattern Observer.\"}"

# Voir les stats
echo "Stats:"
curl http://localhost:3001/interview/$ROOM/stats
EOF

chmod +x test-questions.sh
./test-questions.sh
```

## 🏗️ Structure du Code

```
backend/
├── src/
│   ├── server.ts           # Point d'entrée principal
│   ├── state.ts            # Gestion de l'état en mémoire
│   └── fake/
│       ├── livekit.ts      # Token LiveKit (fake)
│       └── llm.ts          # Évaluation difficulté (fake)
├── package.json
├── tsconfig.json
├── test-client.html        # Client de test Socket.IO
└── test-server.sh          # Script de test HTTP
```

## 🔧 Scripts npm Disponibles

```bash
npm run dev      # Démarrer en mode développement (avec ts-node)
npm run build    # Compiler TypeScript → JavaScript
npm start        # Démarrer en production (depuis dist/)
```

## 🐛 Dépannage

### Le serveur ne démarre pas

```bash
# Vérifier que le port 3001 n'est pas utilisé
lsof -i :3001

# Si occupé, tuer le processus
kill -9 <PID>

# Ou changer le port
PORT=3002 npm run dev
```

### Erreurs de dépendances

```bash
# Supprimer node_modules et réinstaller
rm -rf node_modules package-lock.json
npm install
```

### Problèmes de compilation TypeScript

```bash
# Vérifier les erreurs
npm run build

# Nettoyer et recompiler
rm -rf dist
npm run build
```

## 📊 Monitoring

Le serveur affiche des logs détaillés dans la console:

- `[HTTP]` - Requêtes HTTP
- `[SOCKET]` - Événements Socket.IO
- `[STATE]` - Modifications du store
- `[LIVEKIT]` - Opérations LiveKit
- `[LLM]` - Évaluations de difficulté

## 🔒 Notes de Sécurité

⚠️ **Ce backend est un MVP pour hackathon!**

Pour la production:
- ✅ Ajouter l'authentification
- ✅ Valider toutes les entrées
- ✅ Configurer CORS correctement
- ✅ Utiliser HTTPS
- ✅ Ajouter rate limiting
- ✅ Implémenter les vraies APIs (LiveKit, OpenAI)
- ✅ Utiliser une vraie base de données

## 🎯 Prochaines Étapes

1. ✅ Backend démarré
2. 🔄 Développer le frontend
3. 🔄 Intégrer LiveKit pour le streaming audio
4. 🔄 Intégrer un vrai LLM pour l'analyse
5. 🔄 Ajouter une base de données

## 📚 Documentation Complète

Pour plus de détails, consultez [README.md](README.md)

## 🆘 Besoin d'Aide ?

- 📖 Consulter le [README.md](README.md) complet
- 🔍 Vérifier les logs du serveur
- 🧪 Utiliser `test-client.html` pour déboguer
- 💬 Vérifier la console du navigateur pour les erreurs Socket.IO
