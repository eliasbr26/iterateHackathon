# BetterVue — Quick Start

![texte alternatif](chemin/vers/image.png)
BetterVue provides real-time visibility into the quality of technical interviews: question relevance and difficulty, topic coverage, tone, red flags, and AI-generated summaries.  
This quick guide explains how to install, configure, and run the app in the `quantcoach-livekit` directory.

⚠️ **Never commit API keys.** Use a local `.env` or a secrets manager.

---

## Table of Contents
- Overview  
- Requirements  
- Project Structure  
- Setup  
  - Backend (FastAPI + agent)  
  - Frontend (React/Vite)  
- Key Environment Variables  
- Common Commands  
- Usage (room creation / SSE stream)  
- Debugging  
- Deployment Notes  
- Resources & Contact  

---

## Overview
BetterVue:
- Analyzes a candidate’s résumé and suggests questions.
- Scores each question (relevance, difficulty, coverage).
- Streams real-time indicators: difficulty bar, topic radar, tone, timeline, red flags.
- Generates an AI interview summary.

Main components in `quantcoach-livekit/`:
- **Backend:** FastAPI, agents, SSE endpoints.  
- **Frontend:** React/TypeScript dashboard with live visuals.

---

## Requirements
- Python **3.11+**  
- Node.js **18+**  
- LiveKit instance (cloud or self-hosted)  
- API keys: OpenAI/Anthropic, ElevenLabs/Deepgram, etc.  
- Local `.env` files for secrets  

---

## Project Structure
