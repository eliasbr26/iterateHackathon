#!/bin/bash
# Script to run the LiveKit Interview Platform

echo "==================================="
echo "LiveKit Interview Platform Startup"
echo "==================================="
echo ""

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your LiveKit credentials"
    echo "Copy from .env.example and fill in your credentials"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source ../iterate-hack/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import livekit" 2>/dev/null || {
    echo "❌ livekit not installed. Installing dependencies..."
    pip install "livekit-agents[openai,silero,deepgram]" livekit livekit-api python-dotenv fastapi uvicorn
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "==================================="
echo "Starting FastAPI Server..."
echo "==================================="
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "To start the agent (in another terminal):"
echo "  cd jawad-livekit"
echo "  source ../iterate-hack/bin/activate"
echo "  python interview_agent.py dev"
echo ""
echo "Then open client.html in your browser"
echo "==================================="
echo ""

# Start the server
python server.py
