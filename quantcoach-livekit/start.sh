#!/bin/bash

echo "🚀 Starting QuantCoach LiveKit Interview Platform"
echo ""

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env - Please edit it with your LiveKit credentials"
    echo ""
fi

# Check if frontend .env exists
if [ ! -f "frontend/.env" ]; then
    echo "⚠️  frontend/.env not found. Copying from .env.example..."
    cp frontend/.env.example frontend/.env
    echo "✅ Created frontend/.env"
    echo ""
fi

echo "📦 Checking dependencies..."
echo ""

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Check if Python packages are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    cd backend && pip install -r requirements.txt && cd ..
fi

echo ""
echo "✅ All dependencies installed!"
echo ""
echo "Starting servers..."
echo "  - Frontend: http://localhost:5173"
echo "  - Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start both servers
npm run dev
