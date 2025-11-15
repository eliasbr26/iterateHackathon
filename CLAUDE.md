# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Iterate Hackathon project in early development stages. The project appears to be building an AI-powered application using FastAPI and integrating with LiveKit for real-time communication capabilities.

## Development Environment

### Python Environment
- Python 3.12 via Conda/Miniconda
- Virtual environment: `iterate-hack/`
- Activate with: `source iterate-hack/bin/activate`

### Key Dependencies
The virtual environment includes:
- **Web Framework**: FastAPI (0.121.0)
- **AI/LLM**: OpenAI (2.6.1), Anthropic
- **ML/AI**: accelerate, transformers, torch (via conda base)
- **Real-time**: LiveKit integration (inferred from branch name)

## Project Structure

```
├── iterate-hack/          # Python virtual environment
├── tools/                 # Utility scripts and tools
├── jawad-livekit/         # LiveKit integration work (branch: jawad-livekit)
└── README.md
```

## Development Workflow

### Running the LiveKit Interview Application

The main application is in `jawad-livekit/` directory:

```bash
# Start API server
cd jawad-livekit
python server.py

# Start web client server (for remote access)
python -m http.server 8080 --bind 0.0.0.0

# Start agent (optional - requires OpenAI/Deepgram API keys)
python interview_agent.py dev
```

**Server IP:** 129.104.252.67
- API: http://129.104.252.67:8000
- Client: http://129.104.252.67:8080/client.html
- Docs: http://129.104.252.67:8000/docs

### Installing New Dependencies
```bash
source iterate-hack/bin/activate
pip install <package-name>
```

## Git Workflow

- Main branch: `main`
- Current working branch: `jawad-livekit` (LiveKit integration work)
- Recent commits focus on setup and initial tooling

## Architecture Notes

The project structure suggests a modular architecture:
- `tools/` directory for utility scripts and checklist functionality
- `jawad-livekit/` directory for LiveKit real-time communication features
- Expected FastAPI backend for API endpoints

When adding new features:
1. Keep modular structure with separate directories for distinct functionality
2. Use FastAPI routing patterns for API endpoints
3. Consider async/await patterns for LiveKit real-time operations
