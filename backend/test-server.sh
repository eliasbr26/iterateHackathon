#!/bin/bash

# Script de test rapide pour le backend
# Usage: ./test-server.sh

echo "🧪 Testing Interview Analysis Backend"
echo "======================================"
echo ""

# Test 1: Health Check
echo "📍 Test 1: Health Check"
echo "GET /"
curl -s http://localhost:3001/ | jq
echo ""
echo ""

# Test 2: LiveKit Token Generation
echo "📍 Test 2: LiveKit Token Generation"
echo "GET /livekit-token?roomId=test-room&identity=recruiter"
curl -s "http://localhost:3001/livekit-token?roomId=test-room&identity=recruiter" | jq
echo ""
echo ""

# Test 3: Interview Stats (empty room)
echo "📍 Test 3: Interview Stats"
echo "GET /interview/test-room/stats"
curl -s "http://localhost:3001/interview/test-room/stats" | jq
echo ""
echo ""

echo "✅ Tests completed!"
echo ""
echo "💡 To test Socket.IO events, use a Socket.IO client or the test-client.html file"
