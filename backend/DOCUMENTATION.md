# Interview Analysis Backend - Documentation Complète

## 📖 Table des Matières

1. [Vue d'ensemble](#-vue-densemble)
2. [Architecture](#-architecture)
3. [Installation](#-installation)
4. [API Reference](#-api-reference)
5. [Types & Interfaces](#-types--interfaces)
6. [Flux de données](#-flux-de-données)
7. [Testing](#-testing)
8. [Production](#-production)

## 🎯 Vue d'ensemble

Backend Node.js + TypeScript pour l'analyse en temps réel de questions d'entretien technique.

### Fonctionnalités principales

- ✅ **Génération de tokens LiveKit** (fonction simulée)
- ✅ **Communication temps réel** via Socket.IO
- ✅ **Évaluation automatique de difficulté** (LLM simulé)
- ✅ **Calcul de moyenne de difficulté** en temps réel
- ✅ **API REST** pour tokens et statistiques
- ✅ **Stockage en mémoire** (pas de DB pour le MVP)

### Technologies

```
Node.js + TypeScript
├── Express (API REST)
├── Socket.IO (WebSocket)
├── CORS
└── ts-node (dev)
```

## 🏗️ Architecture

### Composants principaux

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT (Frontend)                  │
│                                                       │
│  ┌──────────────┐           ┌──────────────┐       │
│  │   HTTP API   │           │  Socket.IO   │       │
│  └──────┬───────┘           └──────┬───────┘       │
└─────────┼──────────────────────────┼───────────────┘
          │                          │
          │ REST                     │ WebSocket
          │                          │
┌─────────┼──────────────────────────┼───────────────┐
│         ▼                          ▼               │
│  ┌─────────────┐          ┌──────────────┐        │
│  │  Express    │          │  Socket.IO   │        │
│  │  Server     │          │  Server      │        │
│  └─────┬───────┘          └──────┬───────┘        │
│        │                         │                 │
│        │   ┌─────────────────────┘                │
│        │   │                                       │
│        ▼   ▼                                       │
│  ┌──────────────────┐                             │
│  │   State Manager  │                             │
│  │   (In-Memory)    │                             │
│  └────────┬─────────┘                             │
│           │                                        │
│           ▼                                        │
│  ┌──────────────────┐     ┌──────────────────┐   │
│  │  Fake LiveKit    │     │   Fake LLM       │   │
│  │  Token Generator │     │   Evaluator      │   │
│  └──────────────────┘     └──────────────────┘   │
│                                                    │
│              BACKEND (Node.js + TypeScript)        │
└────────────────────────────────────────────────────┘
```

### Structure des fichiers

```
backend/
├── src/
│   ├── server.ts              # Point d'entrée, Express + Socket.IO
│   ├── state.ts               # Gestion état en mémoire
│   └── fake/
│       ├── livekit.ts         # Génération tokens (fake)
│       └── llm.ts             # Évaluation difficulté (fake)
├── dist/                      # Build output (généré)
├── node_modules/              # Dépendances
├── package.json               # Configuration npm
├── tsconfig.json              # Configuration TypeScript
├── .gitignore
├── .env.example
├── README.md                  # Documentation complète
├── QUICKSTART.md              # Guide démarrage rapide
├── test-server.sh             # Tests HTTP
└── test-client.html           # Client test Socket.IO
```

## 📦 Installation

### Prérequis

- Node.js v16+
- npm v8+

### Étapes

```bash
# 1. Aller dans le dossier backend
cd backend

# 2. Installer les dépendances
npm install

# 3. (Optionnel) Copier le fichier .env
cp .env.example .env

# 4. Démarrer le serveur
npm run dev
```

Le serveur démarre sur **http://localhost:3001**

## 🔌 API Reference

### HTTP REST Endpoints

#### 1. Health Check

```http
GET /
```

**Réponse:**
```json
{
  "status": "ok",
  "message": "Interview Analysis Backend is running",
  "timestamp": "2025-11-15T10:30:00.000Z"
}
```

#### 2. Générer un token LiveKit

```http
GET /livekit-token?roomId={roomId}&identity={identity}
```

**Paramètres:**
- `roomId` (string, required) - ID de la room d'entretien
- `identity` (string, required) - Identité de l'utilisateur

**Exemple:**
```bash
curl "http://localhost:3001/livekit-token?roomId=room-123&identity=recruiter"
```

**Réponse:**
```json
{
  "token": "FAKE_LIVEKIT_TOKEN_room-123_recruiter_1700000000",
  "roomId": "room-123",
  "identity": "recruiter",
  "timestamp": 1700000000
}
```

**Erreurs:**
```json
{
  "error": "Missing required parameters",
  "required": ["roomId", "identity"]
}
```

#### 3. Obtenir les statistiques d'un entretien

```http
GET /interview/:roomId/stats
```

**Paramètres:**
- `roomId` (string, path) - ID de la room d'entretien

**Exemple:**
```bash
curl "http://localhost:3001/interview/room-123/stats"
```

**Réponse:**
```json
{
  "roomId": "room-123",
  "questionCount": 5,
  "avgDifficulty": 3.4,
  "timestamp": 1700000000
}
```

### Socket.IO Events

#### Événements Entrants (Client → Serveur)

##### `join:room`

Rejoindre une room d'entretien.

```javascript
socket.emit('join:room', roomId);
```

**Paramètres:**
- `roomId` (string) - ID de la room

**Réponse:** Émet `room:joined`

---

##### `leave:room`

Quitter une room d'entretien.

```javascript
socket.emit('leave:room', roomId);
```

**Paramètres:**
- `roomId` (string) - ID de la room

---

##### `question:new`

Envoyer une nouvelle question à analyser.

```javascript
socket.emit('question:new', {
  roomId: 'room-123',
  text: 'Expliquez-moi la récursivité'
});
```

**Payload:**
```typescript
{
  roomId: string;    // ID de la room
  text: string;      // Texte de la question
}
```

**Réponses:**
- Émet `difficulty:update` à tous les clients de la room
- Émet `question:processed` au client émetteur
- Émet `question:error` en cas d'erreur

---

##### `interview:reset`

Réinitialiser une session d'entretien.

```javascript
socket.emit('interview:reset', roomId);
```

**Paramètres:**
- `roomId` (string) - ID de la room

**Réponse:** Émet `interview:resetted` à tous les clients

---

##### `ping`

Health check de la connexion.

```javascript
socket.emit('ping');
```

**Réponse:** Émet `pong`

---

#### Événements Sortants (Serveur → Client)

##### `room:joined`

Confirmation de room jointe avec les stats actuelles.

```javascript
socket.on('room:joined', (data) => {
  console.log(data);
});
```

**Data:**
```typescript
{
  roomId: string;
  questionCount: number;
  avgDifficulty: number;
}
```

---

##### `difficulty:update`

Mise à jour après l'analyse d'une nouvelle question.

```javascript
socket.on('difficulty:update', (data) => {
  console.log('New difficulty:', data.difficulty);
  console.log('Average:', data.avgDifficulty);
});
```

**Data:**
```typescript
{
  roomId: string;
  question: {
    text: string;
    difficulty: number;      // 1-5
    timestamp: number;
  };
  difficulty: number;        // 1-5
  avgDifficulty: number;     // Moyenne (0-5)
  questionIndex: number;     // Index de la question
}
```

---

##### `question:processed`

Confirmation que la question a été traitée avec succès.

```javascript
socket.on('question:processed', (data) => {
  console.log('Question processed:', data);
});
```

**Data:**
```typescript
{
  success: true;
  questionIndex: number;
  difficulty: number;
  avgDifficulty: number;
}
```

---

##### `question:error`

Erreur lors du traitement d'une question.

```javascript
socket.on('question:error', (data) => {
  console.error('Error:', data.message);
});
```

**Data:**
```typescript
{
  error: string;
  message: string;
}
```

---

##### `interview:resetted`

Confirmation que l'entretien a été réinitialisé.

```javascript
socket.on('interview:resetted', (data) => {
  console.log('Interview reset:', data.roomId);
});
```

**Data:**
```typescript
{
  roomId: string;
  timestamp: number;
}
```

---

##### `pong`

Réponse au ping.

```javascript
socket.on('pong', (data) => {
  console.log('Latency:', Date.now() - data.timestamp);
});
```

**Data:**
```typescript
{
  timestamp: number;
}
```

## 📋 Types & Interfaces

### QuestionEval

Représente une question évaluée.

```typescript
interface QuestionEval {
  text: string;          // Texte de la question
  difficulty: number;    // Difficulté (1-5)
  timestamp: number;     // Timestamp Unix
}
```

### InterviewData

Représente une session d'entretien.

```typescript
interface InterviewData {
  questions: QuestionEval[];
}
```

### State

État global de l'application.

```typescript
const interviews: Record<string, InterviewData>;
```

## 🔄 Flux de données

### Scénario: Nouvelle Question

```
1. Frontend émet: question:new
   ├─ roomId: "room-123"
   └─ text: "Expliquez la récursivité"

2. Backend reçoit l'événement
   └─ server.ts: socket.on('question:new')

3. Évaluation de la difficulté
   └─ fake/llm.ts: evaluateQuestionDifficulty()
      └─ Retourne: 3 (difficulté aléatoire 1-5)

4. Stockage en mémoire
   └─ state.ts: addQuestion()
      └─ Ajoute à interviews["room-123"].questions

5. Calcul de la moyenne
   └─ state.ts: calculateAverageDifficulty()
      └─ Retourne: 3.2 (moyenne de toutes les questions)

6. Broadcast à tous les clients de la room
   └─ io.to("room-123").emit('difficulty:update', {
      roomId: "room-123",
      question: { text, difficulty: 3, timestamp },
      difficulty: 3,
      avgDifficulty: 3.2,
      questionIndex: 5
   })

7. Frontend reçoit: difficulty:update
   └─ Met à jour l'interface
```

### Diagramme de séquence

```
Frontend          Backend          LLM (fake)      State
   │                 │                 │              │
   ├─question:new────>│                 │              │
   │                 ├─evaluate────────>│              │
   │                 │<────3────────────┤              │
   │                 ├─addQuestion──────────────────>│
   │                 ├─calcAverage──────────────────>│
   │                 │<─────3.2──────────────────────┤
   │<─difficulty:up──┤                 │              │
   │   date          │                 │              │
```

## 🧪 Testing

### Tests HTTP

```bash
# Rendre le script exécutable
chmod +x test-server.sh

# Lancer les tests
./test-server.sh
```

### Tests Socket.IO

Ouvrir `test-client.html` dans le navigateur:

```bash
open test-client.html
```

### Tests manuels avec curl

```bash
# Health check
curl http://localhost:3001/

# Token LiveKit
curl "http://localhost:3001/livekit-token?roomId=test&identity=user1"

# Stats
curl http://localhost:3001/interview/test/stats
```

### Tests Socket.IO avec JavaScript

```javascript
const io = require('socket.io-client');
const socket = io('http://localhost:3001');

socket.on('connect', () => {
  console.log('Connected!');
  
  socket.emit('join:room', 'test-room');
  
  socket.emit('question:new', {
    roomId: 'test-room',
    text: 'Test question'
  });
});

socket.on('difficulty:update', (data) => {
  console.log('Update:', data);
  socket.disconnect();
});
```

## 🚀 Production

### Build

```bash
npm run build
```

Génère le dossier `dist/` avec le code JavaScript compilé.

### Démarrage en production

```bash
npm start
```

### Variables d'environnement

Créer un fichier `.env`:

```bash
PORT=3001
NODE_ENV=production

# Pour une vraie production, ajoutez:
# LIVEKIT_API_KEY=...
# LIVEKIT_API_SECRET=...
# LIVEKIT_URL=...
# OPENAI_API_KEY=...
```

### Considérations de production

⚠️ **Ce code est un MVP pour hackathon!**

Pour la production, il faut:

1. **Sécurité**
   - ✅ Ajouter authentification JWT
   - ✅ Valider toutes les entrées
   - ✅ Rate limiting
   - ✅ Helmet.js pour sécurité HTTP
   - ✅ CORS configuré correctement

2. **Scalabilité**
   - ✅ Utiliser Redis pour le state partagé
   - ✅ Load balancer
   - ✅ Clustering Node.js
   - ✅ Socket.IO adapter pour multi-instances

3. **Persistance**
   - ✅ Base de données (PostgreSQL, MongoDB)
   - ✅ Sauvegarder les questions et analyses
   - ✅ Historique des entretiens

4. **Intégrations réelles**
   - ✅ Vraie API LiveKit
   - ✅ Vraie API OpenAI/LLM
   - ✅ ElevenLabs pour TTS
   - ✅ Webhooks

5. **Monitoring**
   - ✅ Logs structurés (Winston, Pino)
   - ✅ Metrics (Prometheus)
   - ✅ Error tracking (Sentry)
   - ✅ APM (New Relic, DataDog)

6. **Tests**
   - ✅ Tests unitaires (Jest)
   - ✅ Tests d'intégration
   - ✅ Tests E2E
   - ✅ CI/CD

### Déploiement

Exemples de déploiement:

**Heroku:**
```bash
git push heroku main
```

**Docker:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
EXPOSE 3001
CMD ["npm", "start"]
```

**PM2:**
```bash
npm install -g pm2
pm2 start dist/server.js --name interview-backend
pm2 save
```

## 📊 Monitoring et Logs

### Types de logs

- `[HTTP]` - Requêtes HTTP
- `[SOCKET]` - Événements Socket.IO
- `[STATE]` - Modifications du store
- `[LIVEKIT]` - Opérations LiveKit
- `[LLM]` - Évaluations de difficulté
- `[ERROR]` - Erreurs

### Exemple de logs

```
[HTTP] GET /livekit-token
[LIVEKIT] Generated fake token for room: room-123, identity: user1
[SOCKET] Client connected: socket-xyz
[SOCKET] Client socket-xyz joined room: room-123
[SOCKET] New question received in room room-123: "Expliquez la récursivité"
[LLM] Evaluating difficulty for question: "Expliquez la récursivité"
[LLM] Difficulty evaluation result: 3/5
[STATE] Added question to room-123. Total questions: 5
[SOCKET] Broadcasting difficulty update for room room-123
[SOCKET] Question 5: Difficulty=3/5, Average=3.2/5
```

## 🐛 Troubleshooting

### Le serveur ne démarre pas

```bash
# Vérifier le port
lsof -i :3001

# Changer le port
PORT=3002 npm run dev
```

### Erreurs TypeScript

```bash
# Nettoyer et rebuilder
rm -rf dist node_modules
npm install
npm run build
```

### Socket.IO ne se connecte pas

1. Vérifier CORS dans `server.ts`
2. Vérifier l'URL côté client
3. Vérifier la console navigateur
4. Tester avec `test-client.html`

## 📚 Ressources

- [Express Documentation](https://expressjs.com/)
- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [LiveKit Documentation](https://docs.livekit.io/)

## 🤝 Contributing

Pour un vrai projet:

1. Fork le repo
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changes (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

MIT

## 🎯 Roadmap

- [x] Backend HTTP basique
- [x] Socket.IO temps réel
- [x] Fake LLM evaluator
- [x] Fake LiveKit tokens
- [x] In-memory state
- [ ] Base de données réelle
- [ ] Vraie intégration LiveKit
- [ ] Vraie intégration OpenAI
- [ ] Authentification
- [ ] Tests unitaires
- [ ] Déploiement

---

**Créé pour le Hackathon MVP - Novembre 2025**
