"""
SQLAlchemy Database Models for QuantCoach LiveKit Interview Platform

Comprehensive schema supporting all 7 pillars:
- PILLAR 1: Live Interview Support (Real-Time Co-Pilot)
- PILLAR 2: Candidate Evaluation & Scoring (Deep Analyst)
- PILLAR 3: Recruiter Workflow Automation
- PILLAR 4: Advanced Recruiter Tools
- PILLAR 5: Interviewer Evaluation (Quality, Fairness, Bias)
- PILLAR 6: AI-Generated Candidate Profiles
- PILLAR 7: LLM + RAG Conversational Q&A Engine
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class InterviewStatus(str, enum.Enum):
    """Interview session status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SpeakerRole(str, enum.Enum):
    """Speaker role in interview"""
    INTERVIEWER = "interviewer"
    CANDIDATE = "candidate"
    AGENT = "agent"
    UNKNOWN = "unknown"


class SubjectRelevance(str, enum.Enum):
    """Subject relevance classification"""
    ON_TOPIC = "on_topic"
    PARTIALLY_RELEVANT = "partially_relevant"
    OFF_TOPIC = "off_topic"
    UNKNOWN = "unknown"


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty level"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


class InterviewerTone(str, enum.Enum):
    """Interviewer tone classification"""
    HARSH = "harsh"
    NEUTRAL = "neutral"
    ENCOURAGING = "encouraging"
    UNKNOWN = "unknown"


class RedFlagSeverity(str, enum.Enum):
    """Red flag severity level"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CompetencyType(str, enum.Enum):
    """Competency categories for evaluation"""
    LEADERSHIP = "leadership"
    COMMUNICATION = "communication"
    TECHNICAL_DEPTH = "technical_depth"
    PROBLEM_SOLVING = "problem_solving"
    OWNERSHIP = "ownership"
    ADAPTABILITY = "adaptability"
    STRATEGIC_THINKING = "strategic_thinking"
    CREATIVITY = "creativity"
    TEAMWORK = "teamwork"
    CULTURE_FIT = "culture_fit"


# ============================================================================
# PILLAR 6: CANDIDATE PROFILES
# ============================================================================

class Candidate(Base):
    """
    Candidate master record
    PILLAR 6: AI-Generated Candidate Profiles
    """
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic Information
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    # CV & Resume
    cv_text: Mapped[Optional[str]] = mapped_column(Text)  # Extracted CV text
    cv_url: Mapped[Optional[str]] = mapped_column(String(500))  # Original CV file URL
    cv_parsed_data: Mapped[Optional[dict]] = mapped_column(JSON)  # Structured CV data

    # Pre-Interview AI Profile (PILLAR 6.1)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    career_summary: Mapped[Optional[str]] = mapped_column(Text)
    seniority_level: Mapped[Optional[str]] = mapped_column(String(50))
    skill_graph: Mapped[Optional[dict]] = mapped_column(JSON)  # {skill: proficiency}
    experience_matrix: Mapped[Optional[dict]] = mapped_column(JSON)  # Role x skill matrix
    predicted_culture_fit: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    predicted_behavior: Mapped[Optional[dict]] = mapped_column(JSON)  # Behavioral predictions
    risk_flags_pre_interview: Mapped[Optional[dict]] = mapped_column(JSON)  # Pre-interview risks

    # Post-Interview Enrichment (PILLAR 6.3)
    overall_hiring_recommendation: Mapped[Optional[str]] = mapped_column(String(50))  # hire/no_hire/maybe
    culture_fit_analysis: Mapped[Optional[str]] = mapped_column(Text)
    long_term_potential_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    leadership_projection: Mapped[Optional[str]] = mapped_column(Text)
    future_seniority_prediction: Mapped[Optional[str]] = mapped_column(String(50))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interviews: Mapped[List["Interview"]] = relationship("Interview", back_populates="candidate")
    profiles: Mapped[List["CandidateProfile"]] = relationship("CandidateProfile", back_populates="candidate")


class Interviewer(Base):
    """
    Interviewer master record
    PILLAR 5: Interviewer Evaluation & Bias Detection
    """
    __tablename__ = "interviewers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic Information
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Optional[str]] = mapped_column(String(100))  # Recruiter, Hiring Manager, etc.

    # Historical Performance (PILLAR 5.6)
    avg_fairness_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    avg_professionalism_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    avg_bias_score: Mapped[Optional[float]] = mapped_column(Float)  # Lower is better
    total_interviews_conducted: Mapped[int] = mapped_column(Integer, default=0)

    # Calibration Data (PILLAR 4.2)
    calibration_factor: Mapped[Optional[float]] = mapped_column(Float, default=1.0)  # Adjust scores
    tends_harsh: Mapped[bool] = mapped_column(Boolean, default=False)
    tends_lenient: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interviews: Mapped[List["Interview"]] = relationship("Interview", back_populates="interviewer")
    metrics: Mapped[List["InterviewerMetrics"]] = relationship("InterviewerMetrics", back_populates="interviewer")


# ============================================================================
# CORE INTERVIEW DATA
# ============================================================================

class Interview(Base):
    """
    Interview session record
    Central entity connecting all pillars
    """
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Session Information
    room_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    livekit_room_sid: Mapped[Optional[str]] = mapped_column(String(255))

    # Participants
    candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"), index=True)
    interviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("interviewers.id"), index=True)

    # Job Information
    job_title: Mapped[Optional[str]] = mapped_column(String(255))
    job_description: Mapped[Optional[str]] = mapped_column(Text)
    role_requirements: Mapped[Optional[dict]] = mapped_column(JSON)  # Competencies required

    # Session Timing
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # Status
    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus),
        default=InterviewStatus.SCHEDULED
    )

    # PILLAR 1: Live Interview Flow (Topic Coverage, Time Allocation)
    topic_coverage: Mapped[Optional[dict]] = mapped_column(JSON)  # {topic: coverage_percentage}
    time_allocation: Mapped[Optional[dict]] = mapped_column(JSON)  # {topic: minutes_spent}
    pacing_status: Mapped[Optional[str]] = mapped_column(String(50))  # on_track/behind/ahead

    # PILLAR 6: Role Fit Analysis
    role_fit_percentage: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    skill_gaps: Mapped[Optional[dict]] = mapped_column(JSON)  # Missing skills

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="interviews")
    interviewer: Mapped[Optional["Interviewer"]] = relationship("Interviewer", back_populates="interviews")
    transcripts: Mapped[List["Transcript"]] = relationship("Transcript", back_populates="interview", cascade="all, delete-orphan")
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="interview", cascade="all, delete-orphan")
    competency_scores: Mapped[List["CompetencyScore"]] = relationship("CompetencyScore", back_populates="interview", cascade="all, delete-orphan")
    interviewer_metrics: Mapped[List["InterviewerMetrics"]] = relationship("InterviewerMetrics", back_populates="interview", cascade="all, delete-orphan")
    red_flags: Mapped[List["RedFlag"]] = relationship("RedFlag", back_populates="interview", cascade="all, delete-orphan")
    follow_up_suggestions: Mapped[List["FollowUpSuggestion"]] = relationship("FollowUpSuggestion", back_populates="interview", cascade="all, delete-orphan")
    contradictions: Mapped[List["ContradictionEntry"]] = relationship("ContradictionEntry", back_populates="interview", cascade="all, delete-orphan")
    evidence_entries: Mapped[List["EvidenceEntry"]] = relationship("EvidenceEntry", back_populates="interview", cascade="all, delete-orphan")
    summaries: Mapped[List["InterviewSummary"]] = relationship("InterviewSummary", back_populates="interview", cascade="all, delete-orphan")
    star_analyses: Mapped[List["STARAnalysis"]] = relationship("STARAnalysis", back_populates="interview", cascade="all, delete-orphan")
    interview_questions: Mapped[List["InterviewQuestion"]] = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")
    feedback_alerts: Mapped[List["InterviewerFeedbackAlert"]] = relationship("InterviewerFeedbackAlert", back_populates="interview", cascade="all, delete-orphan")


class Transcript(Base):
    """
    Real-time transcription records
    PILLAR 1: Live Interview Support
    """
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Transcript Data
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    speaker: Mapped[SpeakerRole] = mapped_column(SQLEnum(SpeakerRole))
    speaker_name: Mapped[Optional[str]] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    turn_number: Mapped[int] = mapped_column(Integer)  # Sequential turn in conversation

    # Audio Metadata
    audio_duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # STT confidence

    # Analysis Flags
    contains_buzzwords: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vague: Mapped[bool] = mapped_column(Boolean, default=False)
    is_quantified: Mapped[bool] = mapped_column(Boolean, default=False)  # Contains metrics/numbers

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="transcripts")


# ============================================================================
# PILLAR 2: EVALUATION & SCORING
# ============================================================================

class Evaluation(Base):
    """
    LLM-powered evaluation results
    PILLAR 2: Candidate Evaluation & Scoring
    """
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Window Information
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)
    transcripts_evaluated: Mapped[int] = mapped_column(Integer)

    # Core Evaluation (existing)
    subject_relevance: Mapped[SubjectRelevance] = mapped_column(SQLEnum(SubjectRelevance))
    question_difficulty: Mapped[QuestionDifficulty] = mapped_column(SQLEnum(QuestionDifficulty))
    interviewer_tone: Mapped[InterviewerTone] = mapped_column(SQLEnum(InterviewerTone))

    # Analysis Results
    summary: Mapped[str] = mapped_column(Text)
    key_topics: Mapped[dict] = mapped_column(JSON)  # List of topics discussed
    flags: Mapped[dict] = mapped_column(JSON)  # List of flags/concerns

    # Confidence Scores
    confidence_subject: Mapped[float] = mapped_column(Float)
    confidence_difficulty: Mapped[float] = mapped_column(Float)
    confidence_tone: Mapped[float] = mapped_column(Float)

    # Raw LLM Response
    raw_llm_response: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="evaluations")


class CompetencyScore(Base):
    """
    Detailed competency scoring per interview
    PILLAR 2.1: Competency Scoring
    """
    __tablename__ = "competency_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Competency Information
    competency: Mapped[CompetencyType] = mapped_column(SQLEnum(CompetencyType), index=True)

    # Scoring Dimensions (PILLAR 2.1)
    overall_score: Mapped[float] = mapped_column(Float)  # 0-100
    depth_score: Mapped[float] = mapped_column(Float)  # 0-100
    clarity_score: Mapped[float] = mapped_column(Float)  # 0-100
    relevance_score: Mapped[float] = mapped_column(Float)  # 0-100
    evidence_score: Mapped[float] = mapped_column(Float)  # 0-100 (how well they prove it)

    # Supporting Data
    evidence_quotes: Mapped[Optional[dict]] = mapped_column(JSON)  # List of supporting quotes
    reasoning: Mapped[Optional[str]] = mapped_column(Text)  # Why this score?

    # Timestamp
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="competency_scores")


class STARAnalysis(Base):
    """
    STAR Method evaluation for behavioral answers
    PILLAR 2.2: STAR Method Evaluation
    """
    __tablename__ = "star_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Question & Answer
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    # STAR Components (PILLAR 2.2)
    has_situation: Mapped[bool] = mapped_column(Boolean)
    has_task: Mapped[bool] = mapped_column(Boolean)
    has_action: Mapped[bool] = mapped_column(Boolean)
    has_result: Mapped[bool] = mapped_column(Boolean)

    # STAR Details
    situation_text: Mapped[Optional[str]] = mapped_column(Text)
    task_text: Mapped[Optional[str]] = mapped_column(Text)
    action_text: Mapped[Optional[str]] = mapped_column(Text)
    result_text: Mapped[Optional[str]] = mapped_column(Text)

    # STAR Completion Score (PILLAR 2.2)
    star_completion_percentage: Mapped[float] = mapped_column(Float)  # 0-100
    result_quantified: Mapped[bool] = mapped_column(Boolean)  # Did they give numbers?

    # Quality Assessment
    quality_rating: Mapped[Optional[str]] = mapped_column(String(50))  # shallow/partial/decent/excellent

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="star_analyses")


# ============================================================================
# PILLAR 5: INTERVIEWER EVALUATION
# ============================================================================

class InterviewerMetrics(Base):
    """
    Interviewer performance and bias metrics
    PILLAR 5: Interviewer Evaluation (Quality, Fairness, Bias)
    """
    __tablename__ = "interviewer_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("interviewers.id"), index=True)

    # PILLAR 5.1: Bias Detection
    interrupt_count: Mapped[int] = mapped_column(Integer, default=0)
    tone_changes: Mapped[int] = mapped_column(Integer, default=0)  # Positive/negative shifts
    skeptical_followups: Mapped[int] = mapped_column(Integer, default=0)
    friendly_followups: Mapped[int] = mapped_column(Integer, default=0)
    detected_biases: Mapped[Optional[dict]] = mapped_column(JSON)  # List of bias types detected

    # PILLAR 5.2: Fairness Score
    fairness_score: Mapped[float] = mapped_column(Float)  # 0-100
    time_distribution_fairness: Mapped[float] = mapped_column(Float)  # Even time per topic
    question_consistency: Mapped[float] = mapped_column(Float)  # Consistent depth

    # PILLAR 5.3: Professionalism Score
    professionalism_score: Mapped[float] = mapped_column(Float)  # 0-100
    politeness_score: Mapped[float] = mapped_column(Float)
    empathy_score: Mapped[float] = mapped_column(Float)
    clarity_score: Mapped[float] = mapped_column(Float)

    # PILLAR 5.4: Company Value Alignment
    value_alignment_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    values_demonstrated: Mapped[Optional[dict]] = mapped_column(JSON)  # List of values shown

    # PILLAR 5.5: Feedback for Interviewer
    strengths: Mapped[Optional[dict]] = mapped_column(JSON)  # What they did well
    improvement_areas: Mapped[Optional[dict]] = mapped_column(JSON)  # Areas to improve
    coaching_tips: Mapped[Optional[dict]] = mapped_column(JSON)  # Actionable suggestions

    # Timestamp
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="interviewer_metrics")
    interviewer: Mapped["Interviewer"] = relationship("Interviewer", back_populates="metrics")


# ============================================================================
# PILLAR 1: LIVE INTERVIEW SUPPORT
# ============================================================================

class RedFlag(Base):
    """
    Real-time red flags and alerts
    PILLAR 1 & 2: Live Support + Risk Analysis
    """
    __tablename__ = "red_flags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Flag Information
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    flag_type: Mapped[str] = mapped_column(String(100))  # off_topic, vague, contradiction, etc.
    severity: Mapped[RedFlagSeverity] = mapped_column(SQLEnum(RedFlagSeverity))

    # Details
    description: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text)  # Surrounding transcript
    transcript_id: Mapped[Optional[int]] = mapped_column(Integer)  # Link to specific transcript

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="red_flags")


class FollowUpSuggestion(Base):
    """
    Real-time follow-up question suggestions
    PILLAR 1.2: Smart Follow-Up Suggestions
    """
    __tablename__ = "follow_up_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Suggestion Data
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    suggestion: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))  # probe_deeper, ask_example, quantify, etc.
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1-5, higher is more urgent

    # Context
    context: Mapped[Optional[str]] = mapped_column(Text)  # What triggered this suggestion
    related_competency: Mapped[Optional[CompetencyType]] = mapped_column(SQLEnum(CompetencyType))

    # Status
    displayed_to_interviewer: Mapped[bool] = mapped_column(Boolean, default=False)
    was_followed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="follow_up_suggestions")


# ============================================================================
# PILLAR 4: ADVANCED RECRUITER TOOLS
# ============================================================================

class ContradictionEntry(Base):
    """
    Detected contradictions in candidate responses
    PILLAR 4.1: Contradiction Map
    """
    __tablename__ = "contradictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Contradiction Data
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    contradiction_type: Mapped[str] = mapped_column(String(100))  # answer_to_answer, cv_to_answer, etc.

    # Conflicting Statements
    statement_1: Mapped[str] = mapped_column(Text)
    statement_2: Mapped[str] = mapped_column(Text)
    statement_1_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    statement_2_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Analysis
    severity: Mapped[str] = mapped_column(String(50))  # minor/moderate/major
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="contradictions")


class EvidenceEntry(Base):
    """
    Extracted evidence for specific competencies
    PILLAR 4.3: Evidence Extractor
    """
    __tablename__ = "evidence_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Evidence Data
    competency: Mapped[CompetencyType] = mapped_column(SQLEnum(CompetencyType), index=True)
    evidence_type: Mapped[str] = mapped_column(String(100))  # ownership, leadership, metrics, etc.

    # Evidence Details
    quote: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    context: Mapped[Optional[str]] = mapped_column(Text)

    # Quality
    strength: Mapped[str] = mapped_column(String(50))  # weak/moderate/strong
    is_quantified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="evidence_entries")


# ============================================================================
# PILLAR 3: WORKFLOW AUTOMATION
# ============================================================================

class InterviewSummary(Base):
    """
    Auto-generated interview summaries and reports
    PILLAR 3.1 & 3.2: Auto-Generated Summaries & Reports
    PILLAR 5: Post-Interview Analysis & Reporting
    """
    __tablename__ = "interview_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Summary Types
    summary_type: Mapped[str] = mapped_column(String(50))  # bullet_summary, full_report, ats_summary

    # Content
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)

    # Structured Data
    strengths: Mapped[Optional[dict]] = mapped_column(JSON)
    weaknesses: Mapped[Optional[dict]] = mapped_column(JSON)
    highlights: Mapped[Optional[dict]] = mapped_column(JSON)
    next_steps: Mapped[Optional[dict]] = mapped_column(JSON)

    # PILLAR 5: Hiring Recommendation
    hiring_recommendation: Mapped[Optional[str]] = mapped_column(String(50))  # strong_hire, hire, maybe, no_hire
    recommendation_confidence: Mapped[Optional[float]] = mapped_column(Float)  # 0.0-1.0
    recommendation_reasoning: Mapped[Optional[str]] = mapped_column(Text)  # Detailed explanation
    overall_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100 aggregate score

    # Metadata
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    format: Mapped[str] = mapped_column(String(50))  # text, html, pdf, json

    # Export Status
    exported_to_ats: Mapped[bool] = mapped_column(Boolean, default=False)
    ats_name: Mapped[Optional[str]] = mapped_column(String(100))
    exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="summaries")


# ============================================================================
# PILLAR 6: CANDIDATE PROFILES (EXTENDED)
# ============================================================================

class CandidateProfile(Base):
    """
    Time-based candidate profile snapshots
    PILLAR 6: AI-Generated Candidate Profiles (Before/During/After)
    """
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), index=True)
    interview_id: Mapped[Optional[int]] = mapped_column(ForeignKey("interviews.id"))

    # Profile Type
    profile_type: Mapped[str] = mapped_column(String(50))  # pre_interview, live, post_interview

    # Snapshot Data
    snapshot_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile_data: Mapped[dict] = mapped_column(JSON)  # Complete profile snapshot

    # Change Tracking
    changes_from_previous: Mapped[Optional[dict]] = mapped_column(JSON)  # What changed

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="profiles")


# ============================================================================
# PILLAR 3: AI-POWERED QUESTION BANK
# ============================================================================

class QuestionBankEntry(Base):
    """
    AI-generated interview question bank
    PILLAR 3: AI-Powered Question Bank
    """
    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Question Content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    competency: Mapped[str] = mapped_column(String(100), index=True)  # leadership, problem_solving, etc.
    difficulty: Mapped[str] = mapped_column(String(50), index=True)  # easy, medium, hard
    question_type: Mapped[str] = mapped_column(String(50), index=True)  # behavioral, technical, situational

    # Topics & Keywords
    topics: Mapped[Optional[dict]] = mapped_column(JSON)  # ["algorithms", "data_structures"]
    keywords: Mapped[Optional[dict]] = mapped_column(JSON)  # Search/match keywords

    # Supporting Data
    follow_up_questions: Mapped[Optional[dict]] = mapped_column(JSON)  # List of follow-ups
    evaluation_criteria: Mapped[Optional[dict]] = mapped_column(JSON)  # What to look for
    expected_star_components: Mapped[Optional[dict]] = mapped_column(JSON)  # For behavioral questions

    # Generation Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    generated_for_candidate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("candidates.id"))
    generated_by_model: Mapped[Optional[str]] = mapped_column(String(100))  # Model name
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage Tracking
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)  # % of times it led to good insights
    avg_star_completion: Mapped[Optional[float]] = mapped_column(Float)  # Avg STAR % for this question

    # Relationships
    interview_questions: Mapped[List["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="question_bank_entry"
    )


class InterviewQuestion(Base):
    """
    Questions asked/suggested during interviews
    PILLAR 3: Question Bank Usage Tracking
    """
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)
    question_bank_id: Mapped[Optional[int]] = mapped_column(ForeignKey("question_bank.id"))

    # Question Data
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50))  # easy, medium, hard
    competency: Mapped[str] = mapped_column(String(100))  # Target competency
    question_type: Mapped[str] = mapped_column(String(50))  # behavioral, technical, situational

    # Usage Tracking
    suggested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    was_ai_suggested: Mapped[bool] = mapped_column(Boolean, default=True)
    was_actually_asked: Mapped[bool] = mapped_column(Boolean, default=False)
    was_modified: Mapped[bool] = mapped_column(Boolean, default=False)  # Did interviewer modify it?

    # Selection Context
    selection_reasoning: Mapped[Optional[str]] = mapped_column(Text)  # Why was this suggested?
    coverage_at_time: Mapped[Optional[dict]] = mapped_column(JSON)  # Coverage state when suggested

    # Performance Tracking
    star_completion: Mapped[Optional[float]] = mapped_column(Float)  # How well candidate answered
    led_to_good_insights: Mapped[Optional[bool]] = mapped_column(Boolean)  # Interviewer feedback
    interviewer_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="interview_questions")
    question_bank_entry: Mapped[Optional["QuestionBankEntry"]] = relationship(
        "QuestionBankEntry",
        back_populates="interview_questions"
    )


# ============================================================================
# PILLAR 4: REAL-TIME INTERVIEWER FEEDBACK
# ============================================================================

class InterviewerFeedbackAlert(Base):
    """
    Real-time feedback alerts for interviewers
    PILLAR 4: Real-Time Interviewer Feedback
    """
    __tablename__ = "interviewer_feedback_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"), index=True)

    # Alert Information
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), index=True)  # pacing, tone, quality, bias
    severity: Mapped[str] = mapped_column(String(20))  # low, medium, high

    # Alert Details
    message: Mapped[str] = mapped_column(Text)  # Human-readable alert message
    data: Mapped[Optional[dict]] = mapped_column(JSON)  # Full analysis data

    # Status
    was_displayed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    interview: Mapped["Interview"] = relationship("Interview", back_populates="feedback_alerts")
