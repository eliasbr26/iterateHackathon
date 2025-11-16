"""
Data models for audio pipeline
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


@dataclass
class Transcript:
    """Represents a speech transcript with speaker information"""
    text: str
    speaker: str  # "recruiter" or "candidate"
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    is_final: bool = True
    timestamp: Optional[datetime] = None  # Wall-clock time when received

    def __repr__(self) -> str:
        duration = ""
        if self.start_ms is not None and self.end_ms is not None:
            duration = f" [{self.start_ms}ms - {self.end_ms}ms]"
        final_marker = "✓" if self.is_final else "~"
        return f"[{self.speaker}]{duration} {final_marker} {self.text}"


class QuestionDifficulty(str, Enum):
    """Difficulty level of interview questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


class InterviewerTone(str, Enum):
    """Tone assessment for interviewer behavior"""
    HARSH = "harsh"
    NEUTRAL = "neutral"
    ENCOURAGING = "encouraging"
    UNKNOWN = "unknown"


class SubjectRelevance(str, Enum):
    """Whether content is on-topic for the interview"""
    ON_TOPIC = "on_topic"
    OFF_TOPIC = "off_topic"
    PARTIALLY_RELEVANT = "partially_relevant"
    UNKNOWN = "unknown"


class InterviewerTechniqueQuality(str, Enum):
    """Quality assessment for interviewer techniques"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"
    UNKNOWN = "unknown"


class CoachingFlagType(str, Enum):
    """Types of coaching feedback for the interviewer"""
    LEADING_QUESTION = "leading_question"
    MISSED_FOLLOWUP = "missed_followup"
    CLOSED_QUESTION = "closed_question"
    POSITIVE = "positive"
    SPEAKING_TOO_MUCH = "speaking_too_much"
    DIFFICULTY_TOO_LOW = "difficulty_too_low"
    UNCLEAR_QUESTION = "unclear_question"
    GREAT_PROBING = "great_probing"


@dataclass
class CoachingFlag:
    """Specific coaching feedback for the interviewer"""
    type: CoachingFlagType
    severity: str  # "info", "warning", "critical"
    message: str
    suggestion: Optional[str] = None
    example_good: Optional[str] = None
    example_bad: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context_quote: Optional[str] = None  # Relevant quote from transcript

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "severity": self.severity,
            "message": self.message,
            "suggestion": self.suggestion,
            "example_good": self.example_good,
            "example_bad": self.example_bad,
            "timestamp": self.timestamp.isoformat(),
            "context_quote": self.context_quote
        }


@dataclass
class InterviewerTechniqueAssessment:
    """Assessment of interviewer's questioning techniques"""
    open_ended_ratio: float  # 0.0-1.0
    question_quality: InterviewerTechniqueQuality
    follow_up_effectiveness: InterviewerTechniqueQuality
    confidence: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "open_ended_ratio": self.open_ended_ratio,
            "question_quality": self.question_quality.value,
            "follow_up_effectiveness": self.follow_up_effectiveness.value,
            "confidence": self.confidence
        }


@dataclass
class CoachingPoint:
    """A strength or improvement area for the interviewer"""
    category: str  # "question_quality", "follow_up", "tone", "difficulty", "speaking_balance"
    title: str
    description: str
    examples: List[str] = field(default_factory=list)
    score: Optional[float] = None
    suggestions: Optional[List[str]] = None
    severity: Optional[str] = None  # "low", "medium", "high"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "examples": self.examples,
            "score": self.score,
            "suggestions": self.suggestions,
            "severity": self.severity
        }


@dataclass
class EvaluationResult:
    """LLM evaluation result for a transcript window"""
    timestamp: datetime
    window_start: datetime
    window_end: datetime
    transcripts_evaluated: int

    # Question analysis
    subject_relevance: SubjectRelevance
    question_difficulty: QuestionDifficulty
    interviewer_tone: InterviewerTone

    # Detailed assessments
    summary: str  # Brief summary of the interaction
    key_topics: List[str]  # Topics discussed
    flags: List[str] = field(default_factory=list)  # Legacy generic flags

    # NEW: Interviewer coaching
    coaching_flags: List[CoachingFlag] = field(default_factory=list)
    interviewer_technique: Optional[InterviewerTechniqueAssessment] = None

    # Confidence scores (0-1)
    confidence_subject: float = 0.0
    confidence_difficulty: float = 0.0
    confidence_tone: float = 0.0

    # Raw LLM response for debugging
    raw_llm_response: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "transcripts_evaluated": self.transcripts_evaluated,
            "subject_relevance": self.subject_relevance.value,
            "question_difficulty": self.question_difficulty.value,
            "interviewer_tone": self.interviewer_tone.value,
            "summary": self.summary,
            "key_topics": self.key_topics,
            "flags": self.flags,
            "coaching_flags": [cf.to_dict() for cf in self.coaching_flags],
            "interviewer_technique": self.interviewer_technique.to_dict() if self.interviewer_technique else None,
            "confidence_subject": self.confidence_subject,
            "confidence_difficulty": self.confidence_difficulty,
            "confidence_tone": self.confidence_tone,
            "raw_llm_response": self.raw_llm_response
        }


@dataclass
class InterviewerPerformanceReport:
    """Comprehensive performance report for the interviewer across the entire session"""
    overall_score: float  # 0.0-10.0
    session_duration_seconds: float
    total_questions_asked: int

    strengths: List[CoachingPoint] = field(default_factory=list)
    improvements: List[CoachingPoint] = field(default_factory=list)

    # Aggregated metrics
    metrics: dict = field(default_factory=dict)  # open_ended_ratio, follow_up_rate, speaking_time_ratio, etc.

    # Detailed breakdowns
    question_quality_breakdown: dict = field(default_factory=dict)
    topic_coverage: dict = field(default_factory=dict)
    tone_analysis: dict = field(default_factory=dict)

    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "overall_score": self.overall_score,
            "session_duration_seconds": self.session_duration_seconds,
            "total_questions_asked": self.total_questions_asked,
            "strengths": [s.to_dict() for s in self.strengths],
            "improvements": [i.to_dict() for i in self.improvements],
            "metrics": self.metrics,
            "question_quality_breakdown": self.question_quality_breakdown,
            "topic_coverage": self.topic_coverage,
            "tone_analysis": self.tone_analysis,
            "generated_at": self.generated_at.isoformat()
        }


@dataclass
class BufferedWindow:
    """A window of transcripts for evaluation"""
    transcripts: List[Transcript]
    window_start: datetime
    window_end: datetime
    speaker_turns: int  # Number of speaker changes

    def get_text(self, include_speakers: bool = True) -> str:
        """Format transcripts as conversation text"""
        lines = []
        for t in self.transcripts:
            if include_speakers:
                lines.append(f"{t.speaker.upper()}: {t.text}")
            else:
                lines.append(t.text)
        return "\n".join(lines)

    def duration_seconds(self) -> float:
        """Get window duration in seconds"""
        return (self.window_end - self.window_start).total_seconds()

    def __len__(self) -> int:
        return len(self.transcripts)
