"""
Database package for QuantCoach LiveKit Interview Platform
Provides comprehensive data persistence for all 7 pillars
"""

from .db import get_db, init_db, SessionLocal, engine, check_db_health, get_db_context, reset_db, get_table_counts
from .models import (
    Candidate,
    Interviewer,
    Interview,
    Transcript,
    Evaluation,
    CompetencyScore,
    InterviewerMetrics,
    RedFlag,
    FollowUpSuggestion,
    ContradictionEntry,
    EvidenceEntry,
    InterviewSummary,
    STARAnalysis,
    CandidateProfile,
    QuestionBankEntry,
    InterviewQuestion,
    InterviewerFeedbackAlert,
    InterviewStatus,
    SpeakerRole,
    CompetencyType,
    SubjectRelevance,
    QuestionDifficulty,
    InterviewerTone,
    RedFlagSeverity,
)
from . import crud

__all__ = [
    # Database functions
    "get_db",
    "init_db",
    "SessionLocal",
    "engine",
    "check_db_health",
    "get_db_context",
    "reset_db",
    "get_table_counts",
    # Models
    "Candidate",
    "Interviewer",
    "Interview",
    "Transcript",
    "Evaluation",
    "CompetencyScore",
    "InterviewerMetrics",
    "RedFlag",
    "FollowUpSuggestion",
    "ContradictionEntry",
    "EvidenceEntry",
    "InterviewSummary",
    "STARAnalysis",
    "CandidateProfile",
    "QuestionBankEntry",
    "InterviewQuestion",
    "InterviewerFeedbackAlert",
    # Enums
    "InterviewStatus",
    "SpeakerRole",
    "CompetencyType",
    "SubjectRelevance",
    "QuestionDifficulty",
    "InterviewerTone",
    "RedFlagSeverity",
    # CRUD operations
    "crud",
]
