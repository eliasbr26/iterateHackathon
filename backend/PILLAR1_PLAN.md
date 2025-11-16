# PILLAR 1: Live Interview Co-Pilot - Implementation Plan

## Overview

Build real-time AI assistance for interviewers during live interviews. The system will provide intelligent suggestions, track coverage, detect issues, and score interview quality in real-time.

---

## Architecture

### **1. Real-Time Pipeline Flow**

```
Live Interview Audio
    ↓
[Transcription] → [Buffered Windows]
    ↓
[Interview Evaluator] → Basic Analysis (existing)
    ↓
[PILLAR 1 Co-Pilot] → Enhanced Real-Time Analysis
    ↓
    ├─→ [Follow-Up Suggester] → Smart question recommendations
    ├─→ [Coverage Tracker] → Topic/competency coverage monitoring
    ├─→ [Red Flag Detector] → Live issue alerts
    └─→ [Quality Scorer] → Real-time interview quality metrics
    ↓
[SSE Stream] → Frontend Dashboard
```

### **2. Components to Build**

#### **Component 1: Follow-Up Question Suggester**
**File**: `copilot/followup_suggester.py`

**Purpose**: Generate intelligent follow-up questions based on candidate answers

**Features**:
- Analyze candidate's response depth
- Identify missing STAR components
- Suggest probing questions for vague answers
- Recommend deeper technical questions
- Suggest behavioral follow-ups

**Example Output**:
```json
{
  "suggestions": [
    {
      "question": "Can you quantify the impact of that optimization?",
      "reason": "Candidate didn't provide metrics",
      "priority": "high",
      "category": "clarification"
    },
    {
      "question": "What specific challenges did you face during implementation?",
      "reason": "Missing 'Task' component in STAR",
      "priority": "medium",
      "category": "star_completion"
    }
  ]
}
```

#### **Component 2: Coverage Tracker**
**File**: `copilot/coverage_tracker.py`

**Purpose**: Track what topics/competencies have been covered and what's missing

**Features**:
- Monitor competencies discussed (Leadership, Communication, etc.)
- Track technical topics covered
- Identify gaps in coverage
- Suggest areas to explore
- Provide coverage percentage

**Example Output**:
```json
{
  "competencies_covered": {
    "leadership": 80,
    "communication": 60,
    "technical_depth": 90,
    "problem_solving": 40
  },
  "gaps": ["ownership", "adaptability"],
  "coverage_percentage": 65,
  "recommendations": [
    "Ask about ownership and accountability",
    "Explore adaptability with change scenarios"
  ]
}
```

#### **Component 3: Live Red Flag Detector**
**File**: `copilot/live_red_flag_detector.py`

**Purpose**: Detect issues in real-time during the interview

**Features**:
- Spot vague/evasive answers immediately
- Detect topic drift (going off-topic)
- Identify incomplete STAR answers
- Flag potential inconsistencies
- Alert on harsh/biased interviewer behavior

**Example Output**:
```json
{
  "flags": [
    {
      "type": "vague_answer",
      "severity": "medium",
      "message": "Candidate avoided technical details",
      "suggestion": "Ask for specific implementation details"
    },
    {
      "type": "off_topic",
      "severity": "low",
      "message": "Discussion drifted to unrelated topic",
      "suggestion": "Redirect to role requirements"
    }
  ]
}
```

#### **Component 4: Interview Quality Scorer**
**File**: `copilot/quality_scorer.py`

**Purpose**: Provide real-time quality metrics for the ongoing interview

**Features**:
- Overall interview quality score (0-100)
- Question quality assessment
- Candidate engagement level
- Interviewer effectiveness
- Time management tracking

**Example Output**:
```json
{
  "overall_quality": 75,
  "metrics": {
    "question_quality": 80,
    "candidate_engagement": 70,
    "interviewer_effectiveness": 75,
    "time_management": 65,
    "coverage_breadth": 60
  },
  "recommendations": [
    "Improve time management - spending too long on one topic",
    "Increase technical depth in questions"
  ]
}
```

---

## Database Integration

All real-time suggestions will be stored in existing tables:

1. **`follow_up_suggestions`** - Store all suggestions generated
2. **`red_flags`** - Store detected issues
3. **`interviewer_metrics`** - Store quality scores
4. **`evaluations`** - Enhanced with coverage tracking

---

## API Endpoints

### **New Endpoints**:

1. **`GET /interviews/{id}/live-suggestions`**
   - Get pending follow-up suggestions
   - Returns suggestions not yet displayed

2. **`GET /interviews/{id}/coverage`**
   - Get current topic/competency coverage
   - Returns gaps and recommendations

3. **`GET /interviews/{id}/live-quality`**
   - Get real-time quality metrics
   - Returns current interview quality score

4. **`POST /interviews/{id}/mark-suggestion-used`**
   - Mark a suggestion as used by interviewer
   - Updates `displayed_to_interviewer` flag

### **Enhanced Existing Endpoints**:

- **`GET /rooms/{room_name}/stream`** (SSE)
  - Add new event types:
    - `follow_up` - New suggestion available
    - `red_flag` - Issue detected
    - `coverage_update` - Coverage changed
    - `quality_update` - Quality score updated

---

## Implementation Steps

### **Phase 1: Core Modules** (Files to create)

1. `copilot/__init__.py`
2. `copilot/followup_suggester.py`
3. `copilot/coverage_tracker.py`
4. `copilot/live_red_flag_detector.py`
5. `copilot/quality_scorer.py`

### **Phase 2: Integration**

1. Update `interview_evaluator.py` to call PILLAR 1 modules
2. Enhance event callback to emit new event types
3. Store results in database via CRUD functions

### **Phase 3: API Endpoints**

1. Add 4 new endpoints to `server.py`
2. Update SSE stream to include new event types
3. Add Pydantic models for responses

### **Phase 4: Testing**

1. Test with sample interview transcripts
2. Verify real-time suggestions generation
3. Test SSE streaming of suggestions
4. Verify database storage

---

## Example Integration Flow

```python
# In interview_evaluator.py or agent callback

# 1. Basic evaluation (existing)
evaluation = await evaluator.evaluate(window)

# 2. Generate follow-up suggestions
suggestions = await followup_suggester.generate(
    question=last_question,
    answer=last_answer,
    evaluation=evaluation
)

# 3. Update coverage tracking
coverage = coverage_tracker.update(
    evaluation=evaluation,
    competencies_discussed=evaluation.key_topics
)

# 4. Detect red flags
flags = await red_flag_detector.detect_live(
    window=window,
    evaluation=evaluation
)

# 5. Calculate quality score
quality = quality_scorer.calculate(
    evaluation=evaluation,
    coverage=coverage,
    duration=window.duration_seconds()
)

# 6. Store in database
for suggestion in suggestions:
    crud.create_follow_up_suggestion(db, interview_id, suggestion)

for flag in flags:
    crud.create_red_flag(db, interview_id, flag)

# 7. Stream to frontend via SSE
await event_callback({
    "type": "follow_up",
    "data": suggestions[0] if suggestions else None
})

await event_callback({
    "type": "coverage_update",
    "data": coverage
})

await event_callback({
    "type": "quality_update",
    "data": quality
})
```

---

## Frontend Integration Points

The frontend will need to:

1. **Listen to SSE events**:
   - `follow_up` → Show suggestion notification
   - `red_flag` → Display alert banner
   - `coverage_update` → Update coverage dashboard
   - `quality_update` → Update quality meter

2. **Display Components**:
   - Suggestion panel (right sidebar)
   - Coverage tracker (circular progress charts)
   - Red flag alerts (top banner)
   - Quality score (top-right corner)

3. **Interviewer Actions**:
   - Click "Use" on suggestion → Mark as used
   - Dismiss red flag
   - View coverage gaps

---

## Performance Considerations

- **Follow-Up Suggester**: ~2-3 seconds per suggestion
- **Coverage Tracker**: <100ms (in-memory tracking)
- **Red Flag Detector**: ~1-2 seconds per window
- **Quality Scorer**: <100ms (calculation-based)

**Optimization**:
- Generate suggestions asynchronously (don't block evaluation)
- Update coverage in-memory, persist periodically
- Batch database writes
- Use caching for common suggestions

---

## Success Metrics

After implementation, we should be able to:

✅ Generate 2-3 follow-up suggestions per candidate answer
✅ Track coverage of 10 competencies in real-time
✅ Detect 3-5 types of red flags during interviews
✅ Provide quality score updates every 30 seconds
✅ Stream all data to frontend via SSE with <3s latency
✅ Store all suggestions and flags in database

---

## Next Steps After PILLAR 1

Once complete, we'll have a powerful live co-pilot. The interviewer will see:

- **Smart suggestions** for what to ask next
- **Coverage gaps** showing what's not been discussed
- **Red flags** when issues arise
- **Quality metrics** showing how the interview is going

This creates a **world-class AI interviewing assistant**! 🚀

---

**Status**: Planning Complete - Ready to Implement
**Estimated Implementation Time**: 3-4 hours
**Complexity**: Medium-High (real-time integration)
