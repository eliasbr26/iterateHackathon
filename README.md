# BetterVue — Quick Start

#### You don’t want your recruiters to be like Pierre Chartrier.

BetterVue gives companies real-time visibility into how their recruiters perform during technical interviews. The platform analyzes candidates’ résumés, helps recruiters ask smarter questions, and evaluates each question’s relevance, difficulty, and coverage of key technical topics. It also ensures recruiters stay professional and aligned with company values. After each interview, BetterVue generates an AI-powered summary with a performance score, strengths, red flags, and improvement suggestions. In short, BetterVue makes interviews fairer, more consistent, and more effective for everyone.
![demo](demo.jpeg)
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
