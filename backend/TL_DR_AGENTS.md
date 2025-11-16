# TL;DR - Audio Agents Added

## ✅ What's New

**3 nouveaux fichiers** ajoutés depuis jawad-livekit:

1. `interview_evaluator.py` (11 KB) - Évaluateur LLM Claude
2. `run_audio_agent_with_storage.py` (5.9 KB) - Agent transcription
3. `run_audio_agent_with_evaluation.py` (11 KB) - Agent transcription + éval
4. `AUDIO_AGENTS_GUIDE.md` (13 KB) - Guide complet

**Total:** 41 KB de nouveau code + docs

---

## 🚀 Utilisation Ultra-Rapide

### 1. Configuration (une seule fois)

```bash
# Éditer .env
nano backend/.env

# Ajouter (si pas déjà fait):
ANTHROPIC_API_KEY=your_key_here  # Pour évaluation LLM
LIVEKIT_ROOM=test1               # Nom de la room

# Installer dépendances
pip install anthropic
```

### 2. Lancer un Agent

**Option A: Transcription seule**
```bash
cd backend
python run_audio_agent_with_storage.py
```

**Option B: Transcription + Évaluation LLM**
```bash
cd backend
python run_audio_agent_with_evaluation.py
```

### 3. Utiliser

1. Agent se connecte à la room `test1`
2. Ouvrir frontend et rejoindre `test1`
3. Parler normalement
4. Les transcriptions apparaissent en temps réel
5. Stopper avec `Ctrl+C`

### 4. Voir les Résultats

```bash
ls transcripts/test1_*/
# transcripts.json - Données structurées
# transcripts.txt  - Format lisible
# evaluations.json - Analyses LLM (si évaluation)
# evaluations.txt  - Format lisible
```

---

## 📊 Ce que Vous Obtenez

### Terminal en Direct

```
👔 [RECRUITER] ✓ Can you explain cross-validation?
👤 [CANDIDATE] ✓ Cross-validation is a technique...

────────────────────────────────────────────────────
🤖 EVALUATION [14:32:15]
────────────────────────────────────────────────────
📊 Subject: ON_TOPIC (conf: 0.95)
🎯 Difficulty: MEDIUM (conf: 0.85)
💬 Tone: NEUTRAL (conf: 0.90)
📝 Discussing cross-validation and model validation
🔑 Topics: CV_TECHNIQUES, REGULARIZATION
────────────────────────────────────────────────────
```

### Fichiers Sauvegardés

**transcripts.txt:**
```
[14:30:12] 👔 RECRUITER: Can you explain cross-validation?
[14:30:18] 👤 CANDIDATE: Cross-validation is a technique...
```

**evaluations.txt:**
```
================================================================================
[14:32:15] EVALUATION
================================================================================
📊 Subject Relevance: ON_TOPIC (confidence: 0.95)
🎯 Question Difficulty: MEDIUM (confidence: 0.85)
💬 Interviewer Tone: NEUTRAL (confidence: 0.90)
📝 Summary: Discussing cross-validation and model validation
🔑 Key Topics: CV_TECHNIQUES, REGULARIZATION
```

---

## 🎯 Fonctionnalités

### Agent Transcription
- ✅ Transcription temps réel (ElevenLabs STT)
- ✅ Identification des speakers (interviewer, candidate)
- ✅ Sauvegarde JSON + TXT
- ✅ Horodatage automatique

### Agent Évaluation (+ Transcription)
- ✅ Tout ce qui précède +
- ✅ Analyse LLM avec Claude
- ✅ Évaluation tous les 20s
- ✅ Détection de topics Quant Finance
- ✅ Évaluation de:
  - Pertinence du sujet (on/off topic)
  - Difficulté des questions (easy/medium/hard)
  - Tone de l'interviewer (harsh/neutral/encouraging)
  - Topics clés couverts
  - Flags de problèmes

---

## 📁 Topics Quant Finance Détectés

L'évaluateur reconnaît automatiquement ces thèmes:

- `CV_TECHNIQUES` - Cross-validation, K-Fold, Walk-Forward
- `REGULARIZATION` - L1/L2, Lasso, Ridge
- `FEATURE_SELECTION` - SHAP, LIME, PCA
- `STATIONARITY` - Tests de racine unitaire
- `TIME_SERIES_MODELS` - ARIMA, GARCH, VAR
- `OPTIMIZATION_PYTHON` - Vectorization, NumPy
- `LOOKAHEAD_BIAS` - Future data leakage
- `DATA_PIPELINE` - ETL, data cleaning
- `BEHAVIORAL_*` - Questions comportementales
- `EXTRA` - Hors-sujet

---

## 🔧 Configuration Avancée

### Changer de Room

```bash
# Option 1: Variable d'environnement
export LIVEKIT_ROOM=interview-candidate-1
python run_audio_agent_with_storage.py

# Option 2: Éditer .env
LIVEKIT_ROOM=interview-candidate-1
```

### Ajuster la Fenêtre d'Évaluation

Éditer `run_audio_agent_with_evaluation.py`:

```python
buffer = TranscriptBuffer(
    window_size_seconds=30.0,   # 30s au lieu de 20s
    overlap_seconds=15.0,       # 15s au lieu de 10s
    min_transcripts_for_evaluation=3
)
```

---

## 🐛 Dépannage Rapide

### "ANTHROPIC_API_KEY not set"
```bash
# Ajouter dans .env:
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

### "Only 1 participant found"
1. Lancer l'agent d'abord
2. Rejoindre la room avec 2+ personnes via frontend
3. Activer les micros

### Pas de transcriptions finales
- Parler plus fort/clairement
- Vérifier crédits ElevenLabs
- Vérifier qualité micro

---

## 💡 Bonnes Pratiques

1. **Lancer l'agent AVANT** que les participants rejoignent
2. **Parler clairement** une personne à la fois
3. **Vérifier les logs** dans le terminal (emojis)
4. **Tester d'abord** avec une room de test
5. **Sauvegarder** le dossier `transcripts/` après chaque session

---

## 📚 Documentation Complète

**Guide détaillé (20 KB):** [AUDIO_AGENTS_GUIDE.md](AUDIO_AGENTS_GUIDE.md)

Contient:
- Explications détaillées
- Exemples d'utilisation
- Configuration avancée
- Analyse des résultats
- Troubleshooting complet
- Cas d'usage

---

## ✅ Résumé

**Avant:**
- Backend avec REST API uniquement
- Pas d'agents audio
- Pas d'évaluation LLM

**Maintenant:**
- ✅ REST API (FastAPI)
- ✅ 2 agents audio (storage + evaluation)
- ✅ Évaluateur LLM (Claude)
- ✅ Détection topics Quant Finance
- ✅ Sauvegarde automatique
- ✅ 13 KB de documentation

**Vous pouvez maintenant faire TOUT ce que fait jawad-livekit! 🎉**

---

## 🚀 Commandes Essentielles

```bash
# API REST
python server.py

# Transcription seule
python run_audio_agent_with_storage.py

# Transcription + Évaluation
python run_audio_agent_with_evaluation.py

# Voir résultats
ls transcripts/
cat transcripts/test1_*/transcripts.txt
cat transcripts/test1_*/evaluations.txt
```

---

**Pour tout savoir:** Lire [AUDIO_AGENTS_GUIDE.md](AUDIO_AGENTS_GUIDE.md)

*Audio agents ajoutés - 15 novembre 2024*
