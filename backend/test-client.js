/**
 * Client de test Node.js pour le backend Interview Analysis
 * Usage: node test-client.js
 * 
 * Ce script permet de tester rapidement les fonctionnalités Socket.IO
 * sans avoir besoin d'un navigateur.
 */

// Pour utiliser ce script, installez socket.io-client:
// npm install socket.io-client

const io = require('socket.io-client');

// Configuration
const SERVER_URL = 'http://localhost:3001';
const ROOM_ID = 'test-room-node-client';

// Questions de test
const TEST_QUESTIONS = [
  "Expliquez-moi comment fonctionne la récursivité en programmation.",
  "Quelle est la différence entre une liste et un tuple en Python ?",
  "Comment optimiseriez-vous une requête SQL lente ?",
  "Qu'est-ce qu'un closure en JavaScript ?",
  "Expliquez le principe de l'injection de dépendances.",
  "Comment gérer les erreurs dans une application asynchrone ?",
  "Quelle est la complexité temporelle de quicksort ?",
  "Expliquez le pattern MVC.",
  "Comment fonctionne le garbage collector en Java ?",
  "Qu'est-ce que REST et comment concevoir une API RESTful ?"
];

// Stats
let questionsCount = 0;
let avgDifficulty = 0;

// Couleurs pour la console
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m'
};

function log(message, color = colors.reset) {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`${color}[${timestamp}] ${message}${colors.reset}`);
}

function logSuccess(message) {
  log(`✅ ${message}`, colors.green);
}

function logInfo(message) {
  log(`ℹ️  ${message}`, colors.blue);
}

function logError(message) {
  log(`❌ ${message}`, colors.red);
}

function logData(message) {
  log(`📊 ${message}`, colors.cyan);
}

function logSeparator() {
  console.log(colors.bright + '━'.repeat(60) + colors.reset);
}

// Connexion au serveur
log('🚀 Démarrage du client de test...', colors.bright);
log(`📡 Connexion à ${SERVER_URL}`, colors.yellow);
logSeparator();

const socket = io(SERVER_URL, {
  transports: ['websocket', 'polling']
});

// Événement: Connexion
socket.on('connect', () => {
  logSuccess(`Connecté au serveur! (ID: ${socket.id})`);
  
  // Rejoindre la room
  logInfo(`Tentative de rejoindre la room: ${ROOM_ID}`);
  socket.emit('join:room', ROOM_ID);
});

// Événement: Déconnexion
socket.on('disconnect', (reason) => {
  logError(`Déconnecté du serveur. Raison: ${reason}`);
});

// Événement: Room jointe
socket.on('room:joined', (data) => {
  logSuccess(`Room jointe: ${data.roomId}`);
  logData(`Questions existantes: ${data.questionCount}`);
  logData(`Difficulté moyenne: ${data.avgDifficulty}`);
  
  questionsCount = data.questionCount;
  avgDifficulty = data.avgDifficulty;
  
  logSeparator();
  
  // Démarrer l'envoi de questions après 1 seconde
  setTimeout(() => {
    sendNextQuestion();
  }, 1000);
});

// Événement: Mise à jour de difficulté
socket.on('difficulty:update', (data) => {
  logSeparator();
  logSuccess('📈 Nouvelle mise à jour de difficulté reçue!');
  console.log('');
  
  console.log(`${colors.cyan}Question #${data.questionIndex}:${colors.reset}`);
  console.log(`  Text: "${data.question.text}"`);
  console.log(`  Difficulté: ${getDifficultyBar(data.difficulty)} ${data.difficulty}/5`);
  console.log(`  Timestamp: ${new Date(data.question.timestamp).toLocaleString()}`);
  console.log('');
  
  console.log(`${colors.bright}Statistiques globales:${colors.reset}`);
  console.log(`  Total questions: ${data.questionIndex}`);
  console.log(`  Difficulté moyenne: ${getDifficultyBar(data.avgDifficulty)} ${data.avgDifficulty.toFixed(2)}/5`);
  
  questionsCount = data.questionIndex;
  avgDifficulty = data.avgDifficulty;
});

// Événement: Question traitée
socket.on('question:processed', (data) => {
  logSuccess(`Question traitée avec succès (Index: ${data.questionIndex})`);
});

// Événement: Erreur de question
socket.on('question:error', (data) => {
  logError(`Erreur lors du traitement: ${data.message}`);
});

// Événement: Entretien réinitialisé
socket.on('interview:resetted', (data) => {
  logInfo(`Entretien réinitialisé pour la room: ${data.roomId}`);
  questionsCount = 0;
  avgDifficulty = 0;
});

// Événement: Pong
socket.on('pong', (data) => {
  const latency = Date.now() - data.timestamp;
  logInfo(`Pong reçu! Latence: ${latency}ms`);
});

// Événement: Erreur de connexion
socket.on('connect_error', (error) => {
  logError(`Erreur de connexion: ${error.message}`);
  logError('Assurez-vous que le serveur est démarré sur le port 3001');
  process.exit(1);
});

// Fonction pour envoyer une question
let questionIndex = 0;

function sendNextQuestion() {
  if (questionIndex >= TEST_QUESTIONS.length) {
    logSeparator();
    logSuccess('✨ Toutes les questions ont été envoyées!');
    showFinalStats();
    
    // Attendre 2 secondes puis se déconnecter
    setTimeout(() => {
      logInfo('Déconnexion...');
      socket.disconnect();
      process.exit(0);
    }, 2000);
    return;
  }
  
  const question = TEST_QUESTIONS[questionIndex];
  questionIndex++;
  
  logSeparator();
  log(`📝 Envoi de la question ${questionIndex}/${TEST_QUESTIONS.length}...`, colors.yellow);
  console.log(`   "${question}"`);
  
  socket.emit('question:new', {
    roomId: ROOM_ID,
    text: question
  });
  
  // Envoyer la prochaine question après 3 secondes
  setTimeout(() => {
    sendNextQuestion();
  }, 3000);
}

// Fonction pour afficher une barre de difficulté
function getDifficultyBar(difficulty) {
  const rounded = Math.round(difficulty);
  const filled = '█'.repeat(rounded);
  const empty = '░'.repeat(5 - rounded);
  
  let color;
  if (difficulty <= 2) {
    color = colors.green;
  } else if (difficulty <= 3.5) {
    color = colors.yellow;
  } else {
    color = colors.red;
  }
  
  return `${color}${filled}${colors.reset}${empty}`;
}

// Fonction pour afficher les stats finales
function showFinalStats() {
  console.log('');
  console.log(`${colors.bright}╔════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.bright}║     📊 STATISTIQUES FINALES           ║${colors.reset}`);
  console.log(`${colors.bright}╚════════════════════════════════════════╝${colors.reset}`);
  console.log('');
  console.log(`  Total de questions envoyées: ${colors.cyan}${questionIndex}${colors.reset}`);
  console.log(`  Questions dans le système:   ${colors.cyan}${questionsCount}${colors.reset}`);
  console.log(`  Difficulté moyenne:          ${getDifficultyBar(avgDifficulty)} ${colors.cyan}${avgDifficulty.toFixed(2)}/5${colors.reset}`);
  console.log('');
  
  // Interprétation
  let interpretation;
  if (avgDifficulty <= 2) {
    interpretation = `${colors.green}Entretien plutôt facile${colors.reset}`;
  } else if (avgDifficulty <= 3.5) {
    interpretation = `${colors.yellow}Entretien de difficulté moyenne${colors.reset}`;
  } else {
    interpretation = `${colors.red}Entretien difficile${colors.reset}`;
  }
  
  console.log(`  Interprétation: ${interpretation}`);
  console.log('');
}

// Gestion des signaux pour fermeture propre
process.on('SIGINT', () => {
  console.log('');
  logInfo('Interruption détectée. Fermeture...');
  socket.disconnect();
  process.exit(0);
});

process.on('SIGTERM', () => {
  socket.disconnect();
  process.exit(0);
});

// Menu interactif (optionnel)
if (process.argv.includes('--interactive')) {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  console.log('');
  console.log('Mode interactif activé. Commandes disponibles:');
  console.log('  - "q" ou "quit": Quitter');
  console.log('  - "r" ou "reset": Réinitialiser l\'entretien');
  console.log('  - "s" ou "stats": Afficher les stats');
  console.log('  - "p" ou "ping": Tester la latence');
  console.log('');
  
  rl.on('line', (input) => {
    const cmd = input.trim().toLowerCase();
    
    switch (cmd) {
      case 'q':
      case 'quit':
        logInfo('Fermeture...');
        socket.disconnect();
        rl.close();
        process.exit(0);
        break;
        
      case 'r':
      case 'reset':
        logInfo('Réinitialisation de l\'entretien...');
        socket.emit('interview:reset', ROOM_ID);
        break;
        
      case 's':
      case 'stats':
        showFinalStats();
        break;
        
      case 'p':
      case 'ping':
        logInfo('Envoi du ping...');
        socket.emit('ping');
        break;
        
      default:
        if (cmd) {
          logError(`Commande inconnue: ${cmd}`);
        }
    }
  });
}
