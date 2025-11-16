# PILLAR 3 - AI-Powered Question Bank
## Implementation Plan

### Overview
PILLAR 3 provides intelligent, context-aware question suggestions during live interviews. It generates questions dynamically based on:
- Candidate's CV/background
- Current interview coverage
- Question difficulty progression
- Competency gaps
- Candidate performance so far

This pillar works seamlessly with PILLAR 1 to provide both question suggestions AND follow-up suggestions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PILLAR 3 Components                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │      1. Question Generator                    │     │
│  │  • Generates questions using Claude           │     │
│  │  • Types: behavioral, technical, situational  │     │
│  │  • Customized to candidate background         │     │
│  │  • STAR-friendly behavioral questions         │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │      2. Difficulty Calibrator                 │     │
│  │  • Tracks candidate performance               │     │
│  │  • Adjusts difficulty dynamically             │     │
│  │  • Easy → Medium → Hard progression           │     │
│  │  • Prevents overwhelming/boring candidates    │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────┐     │
│  │      3. Contextual Question Selector          │     │
│  │  • Selects best question from bank            │     │
│  │  • Considers coverage gaps                    │     │
│  │  • Balances behavioral/technical              │     │
│  │  • Avoids repetition                          │     │
│  └──────────────────────────────────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Component 1: Question Generator

### Purpose
Generates high-quality interview questions tailored to:
- Specific competencies (e.g., leadership, problem-solving)
- Technical topics (e.g., algorithms, system design)
- Candidate's experience level and background
- Interview stage (opening, middle, closing)

### Implementation: `question_bank/question_generator.py`

```python
class QuestionGenerator:
    """
    Generates tailored interview questions using Claude
    """

    async def generate_questions(
        self,
        competency: str,
        difficulty: str,  # easy/medium/hard
        candidate_background: Optional[Dict] = None,
        count: int = 3
    ) -> List[Dict]:
        """
        Generate questions for a specific competency

        Returns:
        [
            {
                "question": "Tell me about a time when...",
                "competency": "leadership",
                "difficulty": "medium",
                "type": "behavioral",
                "follow_ups": ["What was the outcome?", "..."],
                "evaluation_criteria": ["Specific actions", "Impact", "..."],
                "expected_star_components": ["Situation", "Task", "Action", "Result"]
            }
        ]
        """
```

**Prompt Strategy:**
- Uses candidate CV data to personalize questions
- Specifies STAR format requirements for behavioral questions
- Includes evaluation criteria for each question
- Generates follow-up question ideas

---

## Component 2: Difficulty Calibrator

### Purpose
Dynamically adjusts question difficulty based on candidate performance to:
- Start with easier questions to build confidence
- Gradually increase difficulty as candidate succeeds
- Maintain optimal challenge level (not too easy, not too hard)
- Adapt if candidate struggles

### Implementation: `question_bank/difficulty_calibrator.py`

```python
class DifficultyCalibrator:
    """
    Tracks performance and recommends difficulty adjustments
    """

    def __init__(self):
        self.performance_history = []
        self.current_difficulty = "easy"

    def update_performance(
        self,
        question_difficulty: str,
        star_completion: float,
        competency_score: float,
        response_quality: str
    ):
        """Track performance on latest question"""

    def get_next_difficulty(self) -> str:
        """
        Recommend difficulty for next question

        Logic:
        - Start: easy
        - 2+ good answers → medium
        - 2+ good medium answers → hard
        - 2+ poor answers → decrease difficulty
        """
```

**Difficulty Progression Rules:**
1. **Opening (0-10 min)**: Start with 2-3 easy questions
2. **Middle (10-30 min)**: Progress to medium if candidate performing well
3. **Deep Dive (30-45 min)**: Hard questions for strong candidates
4. **Adaptive**: Step down if candidate struggling

---

## Component 3: Contextual Question Selector

### Purpose
Selects the most appropriate question from the question bank based on:
- Coverage gaps (missing competencies)
- Difficulty level (from calibrator)
- Interview balance (behavioral vs technical)
- Candidate background
- Already-asked questions (avoid repetition)

### Implementation: `question_bank/question_selector.py`

```python
class QuestionSelector:
    """
    Intelligently selects questions based on context
    """

    def __init__(self):
        self.asked_questions = set()  # Track what's been asked

    async def select_question(
        self,
        coverage: Dict,  # From CoverageTracker
        difficulty: str,  # From DifficultyCalibrator
        candidate_profile: Optional[Dict] = None,
        question_bank: List[Dict] = None
    ) -> Dict:
        """
        Select best question for current interview state

        Selection criteria (prioritized):
        1. Competency gaps (coverage < 30%)
        2. Target difficulty level
        3. Type balance (behavioral/technical)
        4. Candidate background relevance
        5. Not already asked
        """
```

---

## Database Schema

### QuestionBank Table
```python
class QuestionBankEntry(Base):
    __tablename__ = "question_bank"

    id = Column(Integer, primary_key=True)
    question_text = Column(String, nullable=False)
    competency = Column(String)  # leadership, problem_solving, etc.
    difficulty = Column(String)  # easy, medium, hard
    question_type = Column(String)  # behavioral, technical, situational
    topics = Column(JSON)  # ["algorithms", "data_structures"]
    follow_up_questions = Column(JSON)  # List of follow-ups
    evaluation_criteria = Column(JSON)  # What to look for
    created_at = Column(DateTime, default=datetime.utcnow)
    generated_for_candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    used_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Track effectiveness
```

### InterviewQuestions Table
```python
class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question_bank_id = Column(Integer, ForeignKey("question_bank.id"), nullable=True)
    question_text = Column(String, nullable=False)
    difficulty = Column(String)
    competency = Column(String)
    asked_at = Column(DateTime, default=datetime.utcnow)
    was_suggested = Column(Boolean, default=True)  # AI suggested vs manual
    interviewer_used = Column(Boolean, default=False)
```

---

## API Endpoints

### 1. Generate Questions
```
POST /question-bank/generate
Body:
{
  "competency": "leadership",
  "difficulty": "medium",
  "candidate_id": 123,
  "count": 3
}

Response:
{
  "questions": [
    {
      "id": 456,
      "question": "Tell me about a time when you had to lead a team through a difficult project...",
      "competency": "leadership",
      "difficulty": "medium",
      "type": "behavioral",
      "follow_ups": [...],
      "evaluation_criteria": [...]
    }
  ]
}
```

### 2. Get Next Question Suggestion
```
GET /interviews/{interview_id}/suggest-question

Response:
{
  "question": {
    "id": 789,
    "question": "Describe a situation where you had to solve a complex technical problem...",
    "competency": "problem_solving",
    "difficulty": "hard",
    "type": "behavioral",
    "reasoning": "Targeting problem_solving competency (current coverage: 20%). Difficulty increased to 'hard' based on strong performance on last 3 questions."
  },
  "alternatives": [...]  // 2-3 alternative questions
}
```

### 3. Mark Question as Used
```
POST /interviews/{interview_id}/questions/{question_id}/use
Body:
{
  "actually_asked": true,
  "modified": false
}

Response:
{
  "status": "success",
  "next_suggestion": {...}  // Immediately suggest next question
}
```

### 4. Update Question Performance
```
POST /question-bank/{question_id}/feedback
Body:
{
  "interview_id": 123,
  "candidate_response_quality": "excellent",
  "star_completion": 85,
  "led_to_good_insights": true
}

Response:
{
  "status": "updated",
  "question_success_rate": 0.82
}
```

### 5. Get Question Bank Stats
```
GET /question-bank/stats

Response:
{
  "total_questions": 1247,
  "by_competency": {
    "leadership": 145,
    "problem_solving": 198,
    ...
  },
  "by_difficulty": {
    "easy": 412,
    "medium": 563,
    "hard": 272
  },
  "most_effective": [...]  // Top questions by success rate
}
```

---

## Integration with PILLAR 1

### Workflow During Live Interview

```
1. Interview starts
   ↓
2. Get candidate background (CV parsed data)
   ↓
3. QuestionSelector suggests opening question (easy difficulty)
   ↓
4. Interviewer asks question
   ↓
5. Candidate answers
   ↓
6. PILLAR 1 FollowUpSuggester provides follow-ups
   ↓
7. CoverageTracker updates (PILLAR 1)
   ↓
8. DifficultyCalibrator updates performance
   ↓
9. QuestionSelector suggests NEXT question
   ├─ Based on coverage gaps
   ├─ Adjusted difficulty
   └─ Avoiding repetition
   ↓
10. Repeat steps 4-9
```

---

## Smart Features

### 1. Adaptive Difficulty
```python
Performance Pattern → Recommended Action
───────────────────────────────────────
3 good answers → Increase difficulty
2 poor answers → Decrease difficulty
Mixed results → Maintain current level
Struggling on hard → Step down to medium
```

### 2. Coverage-Driven Questions
```python
Coverage Status → Question Priority
──────────────────────────────────────
< 20% coverage → URGENT (suggest immediately)
20-50% coverage → HIGH (suggest if no urgent)
50-80% coverage → MEDIUM (round out interview)
> 80% coverage → LOW (optional depth questions)
```

### 3. Interview Stage Awareness
```python
Stage           → Question Characteristics
────────────────────────────────────────────
Opening (0-10m) → Easy, warm-up, build rapport
Middle (10-30m) → Core competencies, balanced difficulty
Deep Dive (30-45m) → Hard questions, probe depth
Closing (45m+)  → Candidate questions, wrap-up
```

### 4. Question Diversity
```python
Maintain balance:
- 60% behavioral (STAR format)
- 30% technical (problem-solving)
- 10% situational (hypothetical)

Avoid:
- Asking same competency 3+ times in a row
- Too many hard questions consecutively
- Repetitive question patterns
```

---

## Performance Optimization

### Caching Strategy
```python
# Pre-generate question pool for common scenarios
Cache:
- 50 questions per competency × 10 competencies = 500 questions
- 3 difficulty levels each
- Refresh cache daily with new AI-generated questions

Result: <100ms question suggestion response time
```

### Batch Generation
```python
# Generate questions in batches during idle time
Background task:
- Generate 10 questions every 5 minutes
- Store in question_bank table
- Build diverse inventory
```

---

## Success Metrics

### Question Quality
- **STAR Completion**: % of behavioral questions that elicit complete STAR answers
- **Insight Generation**: % of questions that reveal valuable competency insights
- **Difficulty Accuracy**: How well predicted difficulty matches actual candidate performance

### System Performance
- **Suggestion Speed**: Time to suggest next question (<100ms target)
- **Relevance Score**: % of suggested questions actually used by interviewer
- **Coverage Improvement**: Reduction in competency gaps over interview duration

### User Experience
- **Adoption Rate**: % of suggested questions used vs manual questions
- **Interviewer Satisfaction**: Feedback on question quality and relevance
- **Time Saved**: Reduction in interview prep time

---

## Implementation Checklist

- [ ] Create `question_bank/` module directory
- [ ] Implement `QuestionGenerator` class
- [ ] Implement `DifficultyCalibrator` class
- [ ] Implement `QuestionSelector` class
- [ ] Add database tables (QuestionBank, InterviewQuestions)
- [ ] Create CRUD functions for question bank
- [ ] Add 5 API endpoints
- [ ] Pre-generate initial question pool (500 questions)
- [ ] Integrate with PILLAR 1 CoverageTracker
- [ ] Test question suggestion flow
- [ ] Measure performance metrics

---

## Example Question Types

### Behavioral (STAR Format)
```
Easy:
- "Tell me about a recent project you worked on."
- "Describe a time when you collaborated with a team."

Medium:
- "Tell me about a time when you had to deal with a difficult stakeholder."
- "Describe a situation where you had to make a decision with incomplete information."

Hard:
- "Tell me about the most complex system you've architected and why you made those design choices."
- "Describe a time when you had to lead organizational change. How did you overcome resistance?"
```

### Technical
```
Easy:
- "What's your approach to debugging a production issue?"
- "How do you ensure code quality in your projects?"

Medium:
- "Design a rate limiter for an API service."
- "How would you optimize a slow database query?"

Hard:
- "Design a distributed caching system that can handle 1M requests/sec."
- "Explain how you would architect a real-time trading platform."
```

### Situational
```
Medium:
- "If you joined our team tomorrow, what would you focus on in your first 30 days?"
- "How would you handle a conflict between two senior engineers on your team?"

Hard:
- "Your team just lost their best engineer. How do you keep the project on track?"
- "You discover a critical security vulnerability 2 days before launch. What do you do?"
```

---

## Future Enhancements

1. **Question Learning**: Use ML to learn which questions are most effective
2. **Industry-Specific Banks**: Pre-built question sets for different industries
3. **Multi-Round Support**: Questions that build on previous interview rounds
4. **Candidate Feedback**: Allow candidates to rate question relevance
5. **Interview Templates**: Pre-configured question sequences for common roles
