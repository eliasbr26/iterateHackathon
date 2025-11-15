#!/bin/bash

echo "🚀 Starting QuantCoach LiveKit"
echo ""
echo "⚠️  IMPORTANT: Make sure conda environment 'ttk' is activated before running this script!"
echo "   Run: conda activate ttk"
echo ""

# Check if we're in the right Python environment
if ! python -c "import sys; print(sys.executable)" | grep -q "ttk"; then
    echo "⚠️  WARNING: ttk environment may not be activated"
    echo "   Current Python: $(python -c 'import sys; print(sys.executable)')"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Using Python environment"
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

# Install concurrently if not present
if [ ! -d "node_modules" ] || [ ! -d "node_modules/concurrently" ]; then
    echo "Installing concurrently..."
    npm install
fi

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
