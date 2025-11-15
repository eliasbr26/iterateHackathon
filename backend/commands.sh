#!/bin/bash

# ============================================================================
# Script de commandes utiles pour le Backend Interview Analysis
# Usage: source commands.sh (pour charger les alias)
#        ou consulter ce fichier pour les commandes
# ============================================================================

echo "🎉 Backend Interview Analysis - Commandes Utiles"
echo "=================================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# SECTION 1: Démarrage
# ============================================================================

echo -e "${BLUE}📦 Installation & Démarrage${NC}"
echo ""
echo "  Installation des dépendances:"
echo "    npm install"
echo ""
echo "  Démarrage en développement:"
echo "    npm run dev"
echo ""
echo "  Build TypeScript:"
echo "    npm run build"
echo ""
echo "  Démarrage en production:"
echo "    npm start"
echo ""

# ============================================================================
# SECTION 2: Tests
# ============================================================================

echo -e "${BLUE}🧪 Tests${NC}"
echo ""
echo "  Tests HTTP (avec curl):"
echo "    chmod +x test-server.sh && ./test-server.sh"
echo ""
echo "  Tests Socket.IO (web):"
echo "    open test-client.html"
echo ""
echo "  Tests Socket.IO (node):"
echo "    npm install socket.io-client && node test-client.js"
echo ""
echo "  Test manuel - Health check:"
echo "    curl http://localhost:3001/"
echo ""
echo "  Test manuel - Token LiveKit:"
echo "    curl 'http://localhost:3001/livekit-token?roomId=test&identity=user1'"
echo ""
echo "  Test manuel - Stats:"
echo "    curl http://localhost:3001/interview/test/stats"
echo ""

# ============================================================================
# SECTION 3: Développement
# ============================================================================

echo -e "${BLUE}💻 Développement${NC}"
echo ""
echo "  Vérifier les erreurs TypeScript:"
echo "    npm run build"
echo ""
echo "  Nettoyer le build:"
echo "    rm -rf dist"
echo ""
echo "  Réinstaller les dépendances:"
echo "    rm -rf node_modules package-lock.json && npm install"
echo ""
echo "  Vérifier le port 3001:"
echo "    lsof -i :3001"
echo ""
echo "  Tuer le processus sur le port 3001:"
echo "    lsof -ti :3001 | xargs kill -9"
echo ""

# ============================================================================
# SECTION 4: Monitoring
# ============================================================================

echo -e "${BLUE}📊 Monitoring${NC}"
echo ""
echo "  Suivre les logs (si le serveur tourne):"
echo "    # Les logs s'affichent directement dans le terminal"
echo ""
echo "  Tester la latence Socket.IO:"
echo "    # Utiliser test-client.html et envoyer un ping"
echo ""
echo "  Vérifier la mémoire utilisée:"
echo "    ps aux | grep node"
echo ""

# ============================================================================
# SECTION 5: Docker (Optionnel)
# ============================================================================

echo -e "${BLUE}🐳 Docker (Optionnel)${NC}"
echo ""
echo "  Créer une image Docker:"
echo "    docker build -t interview-backend ."
echo ""
echo "  Lancer le conteneur:"
echo "    docker run -p 3001:3001 interview-backend"
echo ""

# ============================================================================
# SECTION 6: Git
# ============================================================================

echo -e "${BLUE}📝 Git${NC}"
echo ""
echo "  Status des fichiers:"
echo "    git status"
echo ""
echo "  Commit rapide:"
echo "    git add . && git commit -m 'Backend complet' && git push"
echo ""

# ============================================================================
# SECTION 7: Raccourcis Utiles (Alias)
# ============================================================================

echo -e "${BLUE}⚡ Raccourcis Utiles${NC}"
echo ""
echo "  Pour charger ces alias dans votre terminal:"
echo "    source commands.sh"
echo ""

# Définir les alias
alias backend-start="npm run dev"
alias backend-build="npm run build"
alias backend-test="./test-server.sh"
alias backend-clean="rm -rf dist node_modules"
alias backend-reset="rm -rf dist node_modules && npm install"
alias backend-port="lsof -i :3001"
alias backend-kill="lsof -ti :3001 | xargs kill -9"

echo "  Alias disponibles:"
echo "    backend-start     → npm run dev"
echo "    backend-build     → npm run build"
echo "    backend-test      → ./test-server.sh"
echo "    backend-clean     → Nettoyer dist et node_modules"
echo "    backend-reset     → Réinstaller tout"
echo "    backend-port      → Voir qui utilise le port 3001"
echo "    backend-kill      → Tuer le processus sur 3001"
echo ""

# ============================================================================
# SECTION 8: Exemples de Code
# ============================================================================

echo -e "${BLUE}📝 Exemples de Code${NC}"
echo ""
echo "  Client Socket.IO simple (JavaScript):"
echo "    const io = require('socket.io-client');"
echo "    const socket = io('http://localhost:3001');"
echo "    socket.on('connect', () => {"
echo "      socket.emit('join:room', 'test-room');"
echo "      socket.emit('question:new', {"
echo "        roomId: 'test-room',"
echo "        text: 'Test question'"
echo "      });"
echo "    });"
echo "    socket.on('difficulty:update', console.log);"
echo ""

# ============================================================================
# SECTION 9: Troubleshooting
# ============================================================================

echo -e "${YELLOW}🔧 Troubleshooting${NC}"
echo ""
echo "  Problème: Le serveur ne démarre pas"
echo "  Solution: Vérifier si le port 3001 est libre"
echo "    lsof -i :3001"
echo "    # Si occupé: lsof -ti :3001 | xargs kill -9"
echo ""
echo "  Problème: Erreurs TypeScript"
echo "  Solution: Nettoyer et rebuilder"
echo "    rm -rf dist && npm run build"
echo ""
echo "  Problème: Socket.IO ne se connecte pas"
echo "  Solution: Vérifier CORS et que le serveur tourne"
echo "    curl http://localhost:3001/"
echo ""
echo "  Problème: Dépendances manquantes"
echo "  Solution: Réinstaller"
echo "    rm -rf node_modules package-lock.json && npm install"
echo ""

# ============================================================================
# SECTION 10: Documentation
# ============================================================================

echo -e "${GREEN}📚 Documentation${NC}"
echo ""
echo "  Guide de démarrage rapide:"
echo "    cat QUICKSTART.md"
echo ""
echo "  Documentation API complète:"
echo "    cat DOCUMENTATION.md"
echo ""
echo "  Résumé du projet:"
echo "    cat PROJECT_SUMMARY.md"
echo ""
echo "  Status du projet:"
echo "    cat PROJECT_STATUS.txt"
echo ""

echo "=================================================="
echo -e "${GREEN}✅ Tout est prêt! Bon développement! 🚀${NC}"
echo "=================================================="
