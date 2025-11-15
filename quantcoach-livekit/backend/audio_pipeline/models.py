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
    flags: List[str] = field(default_factory=list)  # Issues or notable points

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
            "confidence_subject": self.confidence_subject,
            "confidence_difficulty": self.confidence_difficulty,
            "confidence_tone": self.confidence_tone,
            "raw_llm_response": self.raw_llm_response
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
