# Interview Analysis Backend

Backend système d'analyse en temps réel des questions d'entretien technique.

## 🎯 Fonctionnalités

- **Génération de tokens LiveKit** (fonction placeholder)
- **Communication temps réel** via Socket.IO
- **Évaluation automatique de la difficulté** des questions (LLM simulé)
- **Calcul de la difficulté moyenne** de l'entretien
- **API REST** pour les tokens et statistiques
- **Stockage en mémoire** des sessions d'entretien

## 🛠️ Technologies

- Node.js
- TypeScript
- Express (API HTTP)
- Socket.IO (temps réel)
- Pas de base de données (stockage en mémoire)

## 📦 Installation

```bash
# Installer les dépendances
npm install

# Démarrer en mode développement
npm run dev

# Builder pour la production
npm run build

# Démarrer en production
npm start
```

## 🚀 Utilisation

### Démarrage du serveur

```bash
npm run dev
```

Le serveur démarre sur `http://localhost:3001`

### Endpoints HTTP

#### 1. Health Check
```
GET /
```

#### 2. Générer un token LiveKit
```
GET /livekit-token?roomId=<room-id>&identity=<user-name>
```

**Exemple:**
```bash
curl "http://localhost:3001/livekit-token?roomId=interview-123&identity=recruiter"
```

**Réponse:**
```json
{
  "token": "FAKE_LIVEKIT_TOKEN_interview-123_recruiter_1234567890",
  "roomId": "interview-123",
  "identity": "recruiter",
  "timestamp": 1234567890
}
```

#### 3. Obtenir les statistiques d'un entretien
```
GET /interview/:roomId/stats
```

**Exemple:**
```bash
curl "http://localhost:3001/interview/interview-123/stats"
```

**Réponse:**
```json
{
  "roomId": "interview-123",
  "questionCount": 5,
  "avgDifficulty": 3.4,
  "timestamp": 1234567890
}
```

### Événements Socket.IO

#### Événements entrants (du frontend → backend)

##### 1. Rejoindre une room
```javascript
socket.emit('join:room', 'interview-123');
```

##### 2. Nouvelle question
```javascript
socket.emit('question:new', {
  roomId: 'interview-123',
  text: 'Expliquez-moi le principe de la récursivité'
});
```

##### 3. Réinitialiser l'entretien
```javascript
socket.emit('interview:reset', 'interview-123');
```

##### 4. Quitter une room
```javascript
socket.emit('leave:room', 'interview-123');
```

#### Événements sortants (du backend → frontend)

##### 1. Confirmation de room jointe
```javascript
socket.on('room:joined', (data) => {
  // data = { roomId, questionCount, avgDifficulty }
});
```

##### 2. Mise à jour de difficulté
```javascript
socket.on('difficulty:update', (data) => {
  // data = {
  //   roomId,
  //   question: { text, difficulty, timestamp },
  //   difficulty,
  //   avgDifficulty,
  //   questionIndex
  // }
});
```

##### 3. Question traitée
```javascript
socket.on('question:processed', (data) => {
  // data = { success, questionIndex, difficulty, avgDifficulty }
});
```

##### 4. Erreur de traitement
```javascript
socket.on('question:error', (data) => {
  // data = { error, message }
});
```

##### 5. Entretien réinitialisé
```javascript
socket.on('interview:resetted', (data) => {
  // data = { roomId, timestamp }
});
```

## 📁 Structure du projet

```
backend/
├── package.json          # Dépendances et scripts
├── tsconfig.json         # Configuration TypeScript
├── src/
│   ├── server.ts         # Point d'entrée principal (Express + Socket.IO)
│   ├── state.ts          # Stockage en mémoire
│   └── fake/
│       ├── livekit.ts    # Génération de tokens LiveKit (fake)
│       └── llm.ts        # Évaluation de difficulté (fake)
└── README.md
```

## 🔧 Architecture

### Flux de traitement d'une question

1. **Frontend** envoie `question:new` avec le texte de la question
2. **Backend** reçoit la question
3. **Évaluation** de la difficulté via LLM simulé (retourne 1-5)
4. **Stockage** dans le store en mémoire
5. **Calcul** de la nouvelle moyenne de difficulté
6. **Broadcast** de `difficulty:update` à tous les clients de la room

### Stockage en mémoire

Les données sont stockées dans un objet JavaScript simple:

```typescript
{
  "interview-123": {
    questions: [
      {
        text: "Question 1",
        difficulty: 3,
        timestamp: 1234567890
      },
      // ...
    ]
  }
}
```

**Note:** Les données sont perdues au redémarrage du serveur.

## 🎭 Fonctions simulées

### LiveKit Token Generation

```typescript
generateFakeLiveKitToken(roomId, identity)
// Retourne: "FAKE_LIVEKIT_TOKEN_<roomId>_<identity>_<timestamp>"
```

### LLM Difficulty Evaluation

```typescript
evaluateQuestionDifficulty(text)
// Retourne: Un nombre aléatoire entre 1 et 5
// Simule un délai de 100-500ms
```

## 🔐 Sécurité

⚠️ **Ce code est pour un MVP de hackathon uniquement!**

Pour la production, vous devriez:
- Implémenter une vraie authentification
- Valider toutes les entrées utilisateur
- Ajouter des rate limits
- Utiliser des variables d'environnement pour les secrets
- Implémenter les vraies APIs (LiveKit, OpenAI, etc.)
- Ajouter une base de données persistante
- Configurer CORS correctement

## 📝 Configuration

Variables d'environnement disponibles:

```bash
PORT=3001  # Port du serveur (défaut: 3001)
```

## 🧪 Test rapide

Tester avec curl et websocat:

```bash
# 1. Démarrer le serveur
npm run dev

# 2. Tester le endpoint HTTP
curl "http://localhost:3001/livekit-token?roomId=test&identity=user1"

# 3. Tester Socket.IO (avec un client JS dans le navigateur)
const socket = io('http://localhost:3001');
socket.emit('join:room', 'test-room');
socket.emit('question:new', {
  roomId: 'test-room',
  text: 'Quelle est la complexité de quicksort?'
});
socket.on('difficulty:update', console.log);
```

## 📊 Logs

Le serveur affiche des logs détaillés:
- `[HTTP]` - Requêtes HTTP
- `[SOCKET]` - Événements Socket.IO
- `[STATE]` - Modifications du store
- `[LIVEKIT]` - Opérations LiveKit
- `[LLM]` - Évaluations LLM
- `[ERROR]` - Erreurs

## 🚧 Limitations (MVP)

- Pas de persistance des données
- Pas de vraie intégration LiveKit
- Pas de vraie intégration LLM
- Pas d'authentification
- Pas de tests unitaires
- CORS ouvert à tous (*)

## 📄 License

MIT
