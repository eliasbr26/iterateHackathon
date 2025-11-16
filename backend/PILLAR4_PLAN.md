# PILLAR 4: Real-Time Interviewer Feedback
## Implementation Plan

**Status**: In Development
**Priority**: High
**Integration**: Works with PILLAR 1 (Co-Pilot) for live feedback loop

---

## Overview

Provides real-time feedback to interviewers during live sessions to improve interview quality, reduce bias, and maintain optimal pacing.

## Architecture

```
interviewer_feedback/
├── __init__.py                    # Module exports
├── pacing_monitor.py              # Tracks interview pacing and timing
├── tone_analyzer.py               # Monitors interviewer tone (via Claude)
├── question_quality_checker.py    # Evaluates question quality (via Claude)
└── bias_detector.py               # Detects bias in questions (via Claude)
```

---

## Module 1: Pacing Monitor

**Purpose**: Tracks interview pacing and provides alerts for timing issues

**Key Features**:
- Questions per minute tracking
- Silent period detection (candidate struggling or interviewer not asking)
- Interview stage awareness (opening/middle/deep-dive/closing)
- Pacing alerts (too fast, too slow, appropriate)

**Algorithm**:
```python
class PacingMonitor:
    def __init__(self):
        self.questions = []  # [(timestamp, question)]
        self.start_time = None
        self.last_question_time = None

    def track_question(self, question: str, timestamp: datetime) -> Dict:
        """Track a question and analyze pacing"""
        # Calculate metrics
        - questions_per_minute
        - time_since_last_question
        - total_questions
        - interview_duration

        # Determine pacing status
        - "too_fast" if qpm > 2.5
        - "too_slow" if qpm < 0.5
        - "silent_period" if time_since_last > 3 minutes
        - "appropriate" otherwise

        return {
            "status": str,
            "questions_per_minute": float,
            "total_questions": int,
            "duration_minutes": float,
            "recommendation": str
        }

    def get_stage_recommendation(self, duration: float) -> str:
        """Get pacing recommendation based on interview stage"""
        # 0-10 min: Opening (slower, 1-1.5 qpm)
        # 10-40 min: Middle (normal, 1.5-2 qpm)
        # 40-50 min: Deep-dive (slower, 1-1.5 qpm)
        # 50-60 min: Closing (faster, 2-2.5 qpm)
```

**No AI Required**: Pure algorithmic tracking

---

## Module 2: Tone Analyzer

**Purpose**: Monitors interviewer tone to ensure professional, encouraging atmosphere

**Key Features**:
- Real-time tone classification (harsh, neutral, encouraging)
- Trend analysis (tone improving/declining over time)
- Alerts for consistently harsh tone
- Integration with existing InterviewerMetrics

**Claude Prompt**:
```python
TONE_ANALYSIS_PROMPT = """
Analyze the tone of this interviewer's question:

Question: {question}
Context: This is question #{question_num} in a {duration}-minute interview.

Classify the tone as one of:
- harsh: Critical, dismissive, or aggressive
- neutral: Professional, matter-of-fact
- encouraging: Supportive, warm, positive

Respond in JSON:
{
    "tone": "harsh" | "neutral" | "encouraging",
    "confidence": 0.0-1.0,
    "indicators": ["specific phrases that indicate this tone"],
    "suggestion": "How to improve if not encouraging"
}
"""
```

**Usage**:
```python
async def analyze_tone(question: str, context: Dict) -> Dict:
    result = await claude_api.call(prompt)
    return {
        "tone": result["tone"],
        "confidence": result["confidence"],
        "indicators": result["indicators"],
        "suggestion": result["suggestion"],
        "trend": self.calculate_trend()  # Last 5 questions
    }
```

---

## Module 3: Question Quality Checker

**Purpose**: Evaluates the quality of interviewer questions in real-time

**Key Features**:
- Detects leading questions ("Don't you think...?")
- Identifies yes/no questions (low quality for behavioral)
- Flags unclear/compound questions
- Suggests improvements
- Quality score (0-100)

**Claude Prompt**:
```python
QUALITY_CHECK_PROMPT = """
Evaluate the quality of this interview question:

Question: "{question}"
Interview Type: Behavioral/Technical
Expected Answer Type: {expected_type}

Check for these quality issues:
1. Leading question (suggests desired answer)
2. Yes/No question (for behavioral, these are low quality)
3. Compound question (asks multiple things at once)
4. Unclear/ambiguous phrasing
5. Too broad/vague
6. Too narrow/specific

Respond in JSON:
{
    "quality_score": 0-100,
    "quality_rating": "poor" | "fair" | "good" | "excellent",
    "issues": [
        {
            "type": "leading" | "yes_no" | "compound" | "unclear" | "too_broad" | "too_narrow",
            "severity": "low" | "medium" | "high",
            "explanation": "Why this is an issue"
        }
    ],
    "improved_version": "Suggested rewrite if issues found",
    "strengths": ["Positive aspects of the question"]
}
"""
```

**Quality Scoring**:
- Excellent (90-100): Open-ended, clear, STAR-friendly
- Good (70-89): Minor issues, mostly effective
- Fair (50-69): Some issues, needs improvement
- Poor (0-49): Major issues, ineffective

---

## Module 4: Bias Detector

**Purpose**: Identifies potential bias in interviewer questions

**Key Features**:
- Detects demographic bias (age, gender, race)
- Identifies assumption-based questions
- Flags culturally insensitive phrasing
- Provides bias-free alternatives
- Tracks bias patterns over time

**Claude Prompt**:
```python
BIAS_DETECTION_PROMPT = """
Analyze this interview question for potential bias:

Question: "{question}"

Check for these bias types:
1. Age bias (assumptions about generation, tech familiarity, etc.)
2. Gender bias (assumptions about roles, capabilities, family)
3. Cultural bias (assumptions about background, customs, holidays)
4. Ability bias (assumptions about physical/mental capabilities)
5. Socioeconomic bias (assumptions about education, resources)
6. Implicit assumptions (any unstated assumptions about the candidate)

Respond in JSON:
{
    "has_bias": true/false,
    "bias_score": 0.0-1.0,  // 0 = no bias, 1 = strong bias
    "bias_types": [
        {
            "type": "age" | "gender" | "cultural" | "ability" | "socioeconomic" | "implicit",
            "severity": "low" | "medium" | "high",
            "explanation": "Specific bias detected",
            "problematic_phrase": "The exact phrase that's problematic"
        }
    ],
    "bias_free_version": "Rewritten question without bias",
    "recommendation": "How to avoid this in future"
}
"""
```

**Severity Levels**:
- High: Clear discriminatory language, legal risk
- Medium: Implicit bias, could disadvantage candidates
- Low: Minor phrasing issues, easily fixable

---

## Database Schema (Use Existing)

We'll use the existing `InterviewerMetrics` table and add a new table:

```sql
-- New table for real-time feedback alerts
CREATE TABLE interviewer_feedback_alerts (
    id INTEGER PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    timestamp TIMESTAMP,
    alert_type VARCHAR(50),  -- 'pacing', 'tone', 'quality', 'bias'
    severity VARCHAR(20),     -- 'low', 'medium', 'high'
    message TEXT,
    data JSONB,              -- Full details
    was_displayed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMP
);
```

---

## API Endpoints

### 1. Analyze Question (Real-time)
```
POST /interviews/{interview_id}/analyze-question

Request:
{
    "question": "Can you tell me about a time...",
    "context": {
        "question_number": 5,
        "duration_minutes": 15,
        "expected_answer_type": "behavioral"
    }
}

Response:
{
    "pacing": {
        "status": "appropriate",
        "questions_per_minute": 1.8,
        "recommendation": "Good pace for middle stage"
    },
    "tone": {
        "tone": "encouraging",
        "confidence": 0.92,
        "trend": "improving"
    },
    "quality": {
        "quality_score": 85,
        "quality_rating": "good",
        "issues": [],
        "strengths": ["Open-ended", "STAR-friendly"]
    },
    "bias": {
        "has_bias": false,
        "bias_score": 0.05
    },
    "overall_feedback": "Excellent question - well-paced, encouraging tone, high quality",
    "alerts": []  // Any issues that need attention
}
```

### 2. Get Real-Time Feedback
```
GET /interviews/{interview_id}/feedback/current

Response:
{
    "interview_id": 123,
    "duration_minutes": 25,
    "total_questions": 12,
    "current_pacing": {...},
    "tone_trend": {...},
    "quality_average": 78.5,
    "bias_alerts": [],
    "active_alerts": [
        {
            "type": "pacing",
            "severity": "low",
            "message": "Consider slowing down slightly - you're at 2.3 qpm"
        }
    ]
}
```

### 3. Get Feedback History
```
GET /interviews/{interview_id}/feedback/history

Response:
{
    "interview_id": 123,
    "feedback_timeline": [
        {
            "timestamp": "2024-01-15T10:05:00Z",
            "question_num": 3,
            "pacing": {...},
            "tone": {...},
            "quality": {...},
            "bias": {...}
        }
    ],
    "summary": {
        "total_alerts": 2,
        "pacing_alerts": 1,
        "tone_alerts": 0,
        "quality_alerts": 0,
        "bias_alerts": 1
    }
}
```

### 4. Dismiss Alert
```
POST /interviews/{interview_id}/feedback/dismiss/{alert_id}

Response:
{
    "status": "success",
    "alert_id": 456
}
```

### 5. Get Interviewer Performance Summary
```
GET /interviewers/{interviewer_id}/performance

Response:
{
    "interviewer_id": 1,
    "total_interviews": 45,
    "average_pacing_score": 85,
    "average_tone_score": 92,
    "average_question_quality": 78,
    "bias_incidents": 2,
    "improvement_trend": "improving",
    "recommendations": [
        "Maintain encouraging tone - you're doing great!",
        "Watch for compound questions - 15% of questions have this issue"
    ]
}
```

---

## Integration Points

### With PILLAR 1 (Co-Pilot)
- Use Coverage Tracker to inform pacing recommendations
- Question suggestions consider interviewer's past quality scores
- Feedback influences follow-up suggestions

### With PILLAR 3 (Question Bank)
- Quality scores feed back to question effectiveness
- Bias-free questions preferred in selection
- Learn from interviewer's question style

### Real-Time Pipeline
```
Interviewer asks question
    ↓
Transcription (existing)
    ↓
[NEW] Analyze question in parallel:
    - Pacing Monitor (instant)
    - Tone Analyzer (Claude, ~500ms)
    - Quality Checker (Claude, ~500ms)
    - Bias Detector (Claude, ~500ms)
    ↓
Aggregate feedback
    ↓
Send to frontend via SSE (existing event stream)
    ↓
Display alerts/feedback in UI
```

---

## Success Metrics

1. **Pacing Improvement**
   - Target: 80% of interviews maintain "appropriate" pacing
   - Measure: Pacing status distribution

2. **Tone Quality**
   - Target: 90% encouraging or neutral tone
   - Measure: Tone classification over time

3. **Question Quality**
   - Target: Average quality score > 75
   - Measure: Quality scores across all questions

4. **Bias Reduction**
   - Target: < 1% high-severity bias incidents
   - Measure: Bias detection events

5. **Interviewer Satisfaction**
   - Target: Feedback helpful in 85%+ cases
   - Measure: Alert dismissal rate (low dismissal = helpful)

---

## Implementation Order

1. ✅ Create implementation plan
2. Build PacingMonitor (no AI, fastest)
3. Build ToneAnalyzer (simple Claude call)
4. Build QuestionQualityChecker (moderate complexity)
5. Build BiasDetector (most complex prompting)
6. Add database models (if needed beyond InterviewerMetrics)
7. Create API endpoints
8. Test integration with existing pipeline
9. Add SSE streaming for real-time alerts

---

## Technical Considerations

**Performance**:
- Claude calls run in parallel (all ~500ms each)
- Total analysis time: ~500-700ms (acceptable for real-time)
- Cache recent analyses to avoid re-analyzing same question

**Error Handling**:
- If Claude fails, fallback to basic algorithmic checks
- PacingMonitor always works (no AI dependency)
- Graceful degradation for each module

**Privacy**:
- All analysis happens server-side
- No question data sent to third parties beyond Claude API
- Feedback data tied to interview_id, anonymizable

**Scalability**:
- Stateless modules (can scale horizontally)
- Per-interview state in dictionaries (similar to PILLAR 1)
- Database writes batched to reduce I/O

---

## Future Enhancements (Post-MVP)

1. **ML Model Integration**: Train custom models for faster feedback (no Claude dependency)
2. **Personalized Coaching**: Interviewer-specific improvement plans
3. **Benchmarking**: Compare interviewer to company averages
4. **Video Analysis**: Add visual cues (if video available)
5. **Multi-language Support**: Feedback in interviewer's language
6. **Integration with LMS**: Export to learning management systems

---

## File Structure Summary

```
backend/
├── interviewer_feedback/
│   ├── __init__.py
│   ├── pacing_monitor.py          (~250 lines)
│   ├── tone_analyzer.py            (~200 lines)
│   ├── question_quality_checker.py (~300 lines)
│   └── bias_detector.py            (~350 lines)
├── database/
│   └── models.py                   (add InterviewerFeedbackAlert model)
│   └── crud.py                     (add feedback CRUD functions)
└── server.py                       (add 5 new endpoints)
```

**Estimated Total**: ~1,500 lines of new code
