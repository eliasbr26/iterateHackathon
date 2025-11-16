"""
CRUD (Create, Read, Update, Delete) operations for database models
Provides helper functions for common database operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

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
    InterviewStatus,
    SpeakerRole,
    CompetencyType,
)


# ============================================================================
# CANDIDATE OPERATIONS (PILLAR 6)
# ============================================================================

def create_candidate(
    db: Session,
    email: str,
    name: str,
    phone: Optional[str] = None,
    cv_text: Optional[str] = None,
    cv_url: Optional[str] = None,
    cv_parsed_data: Optional[Dict] = None,
) -> Candidate:
    """Create a new candidate"""
    candidate = Candidate(
        email=email,
        name=name,
        phone=phone,
        cv_text=cv_text,
        cv_url=cv_url,
        cv_parsed_data=cv_parsed_data,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_candidate_by_email(db: Session, email: str) -> Optional[Candidate]:
    """Get candidate by email"""
    return db.query(Candidate).filter(Candidate.email == email).first()


def get_candidate_by_id(db: Session, candidate_id: int) -> Optional[Candidate]:
    """Get candidate by ID"""
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()


def update_candidate_profile(
    db: Session,
    candidate_id: int,
    profile_data: Dict[str, Any],
) -> Optional[Candidate]:
    """Update candidate profile data (PILLAR 6)"""
    candidate = get_candidate_by_id(db, candidate_id)
    if not candidate:
        return None

    # Update fields
    for key, value in profile_data.items():
        if hasattr(candidate, key):
            setattr(candidate, key, value)

    candidate.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)
    return candidate


def update_candidate(
    db: Session,
    candidate_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    cv_text: Optional[str] = None,
    cv_url: Optional[str] = None,
    cv_parsed_data: Optional[Dict] = None,
) -> Optional[Candidate]:
    """Update candidate information"""
    candidate = get_candidate_by_id(db, candidate_id)
    if not candidate:
        return None

    if name is not None:
        candidate.name = name
    if email is not None:
        candidate.email = email
    if phone is not None:
        candidate.phone = phone
    if cv_text is not None:
        candidate.cv_text = cv_text
    if cv_url is not None:
        candidate.cv_url = cv_url
    if cv_parsed_data is not None:
        candidate.cv_parsed_data = cv_parsed_data

    candidate.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)
    return candidate


# ============================================================================
# INTERVIEWER OPERATIONS (PILLAR 5)
# ============================================================================

def create_interviewer(
    db: Session,
    email: str,
    name: str,
    role: Optional[str] = None,
) -> Interviewer:
    """Create a new interviewer"""
    interviewer = Interviewer(
        email=email,
        name=name,
        role=role,
    )
    db.add(interviewer)
    db.commit()
    db.refresh(interviewer)
    return interviewer


def get_interviewer_by_email(db: Session, email: str) -> Optional[Interviewer]:
    """Get interviewer by email"""
    return db.query(Interviewer).filter(Interviewer.email == email).first()


def get_or_create_interviewer(db: Session, email: str, name: str) -> Interviewer:
    """Get existing interviewer or create new one"""
    interviewer = get_interviewer_by_email(db, email)
    if not interviewer:
        interviewer = create_interviewer(db, email, name)
    return interviewer


# ============================================================================
# INTERVIEW OPERATIONS
# ============================================================================

def create_interview(
    db: Session,
    room_name: str,
    candidate_id: Optional[int] = None,
    interviewer_id: Optional[int] = None,
    job_title: Optional[str] = None,
    job_description: Optional[str] = None,
    livekit_room_sid: Optional[str] = None,
) -> Interview:
    """Create a new interview session"""
    interview = Interview(
        room_name=room_name,
        candidate_id=candidate_id,
        interviewer_id=interviewer_id,
        job_title=job_title,
        job_description=job_description,
        livekit_room_sid=livekit_room_sid,
        status=InterviewStatus.IN_PROGRESS,  # New interviews start as IN_PROGRESS
        actual_start=datetime.utcnow(),  # Set start time
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def get_interview_by_room_name(db: Session, room_name: str) -> Optional[Interview]:
    """Get interview by room name"""
    return db.query(Interview).filter(Interview.room_name == room_name).first()


def get_interview_by_id(db: Session, interview_id: int) -> Optional[Interview]:
    """Get interview by ID"""
    return db.query(Interview).filter(Interview.id == interview_id).first()


def start_interview(db: Session, interview_id: int) -> Optional[Interview]:
    """Mark interview as started"""
    interview = get_interview_by_id(db, interview_id)
    if not interview:
        return None

    interview.status = InterviewStatus.IN_PROGRESS
    interview.actual_start = datetime.utcnow()
    db.commit()
    db.refresh(interview)
    return interview


def end_interview(db: Session, interview_id: int) -> Optional[Interview]:
    """Mark interview as completed"""
    interview = get_interview_by_id(db, interview_id)
    if not interview:
        return None

    interview.status = InterviewStatus.COMPLETED
    interview.actual_end = datetime.utcnow()

    # Calculate duration
    if interview.actual_start:
        duration = (interview.actual_end - interview.actual_start).total_seconds() / 60
        interview.duration_minutes = int(duration)

    db.commit()
    db.refresh(interview)
    return interview


def get_candidate_interviews(db: Session, candidate_id: int) -> List[Interview]:
    """Get all interviews for a candidate"""
    return (
        db.query(Interview)
        .filter(Interview.candidate_id == candidate_id)
        .order_by(desc(Interview.created_at))
        .all()
    )


# ============================================================================
# TRANSCRIPT OPERATIONS (PILLAR 1)
# ============================================================================

def create_transcript(
    db: Session,
    interview_id: int,
    timestamp: datetime,
    speaker: SpeakerRole,
    text: str,
    turn_number: int,
    speaker_name: Optional[str] = None,
    confidence_score: Optional[float] = None,
) -> Transcript:
    """Create a new transcript entry"""
    transcript = Transcript(
        interview_id=interview_id,
        timestamp=timestamp,
        speaker=speaker,
        speaker_name=speaker_name,
        text=text,
        turn_number=turn_number,
        confidence_score=confidence_score,
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def get_interview_transcripts(
    db: Session,
    interview_id: int,
    limit: Optional[int] = None,
) -> List[Transcript]:
    """Get transcripts for an interview"""
    query = (
        db.query(Transcript)
        .filter(Transcript.interview_id == interview_id)
        .order_by(Transcript.timestamp)
    )

    if limit:
        query = query.limit(limit)

    return query.all()


# ============================================================================
# EVALUATION OPERATIONS (PILLAR 2)
# ============================================================================

def create_evaluation(
    db: Session,
    interview_id: int,
    evaluation_data: Dict[str, Any],
) -> Evaluation:
    """Create a new evaluation record"""
    evaluation = Evaluation(
        interview_id=interview_id,
        **evaluation_data
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_interview_evaluations(db: Session, interview_id: int) -> List[Evaluation]:
    """Get all evaluations for an interview"""
    return (
        db.query(Evaluation)
        .filter(Evaluation.interview_id == interview_id)
        .order_by(Evaluation.timestamp)
        .all()
    )


# ============================================================================
# COMPETENCY SCORE OPERATIONS (PILLAR 2)
# ============================================================================

def create_competency_score(
    db: Session,
    interview_id: int,
    competency: CompetencyType,
    overall_score: float,
    depth_score: float,
    clarity_score: float,
    relevance_score: float,
    evidence_score: float,
    evidence_quotes: Optional[Dict] = None,
    reasoning: Optional[str] = None,
) -> CompetencyScore:
    """Create a competency score"""
    score = CompetencyScore(
        interview_id=interview_id,
        competency=competency,
        overall_score=overall_score,
        depth_score=depth_score,
        clarity_score=clarity_score,
        relevance_score=relevance_score,
        evidence_score=evidence_score,
        evidence_quotes=evidence_quotes,
        reasoning=reasoning,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def get_competency_scores(db: Session, interview_id: int) -> List[CompetencyScore]:
    """Get all competency scores for an interview"""
    return (
        db.query(CompetencyScore)
        .filter(CompetencyScore.interview_id == interview_id)
        .all()
    )


# Alias for backwards compatibility
def get_interview_competency_scores(db: Session, interview_id: int) -> List[CompetencyScore]:
    """Alias for get_competency_scores"""
    return get_competency_scores(db, interview_id)


# ============================================================================
# STAR ANALYSIS OPERATIONS (PILLAR 2.2)
# ============================================================================

def create_star_analysis(
    db: Session,
    interview_id: int,
    question: str,
    answer: str,
    has_situation: bool,
    has_task: bool,
    has_action: bool,
    has_result: bool,
    situation_text: Optional[str] = None,
    task_text: Optional[str] = None,
    action_text: Optional[str] = None,
    result_text: Optional[str] = None,
    star_completion_percentage: float = 0.0,
    result_quantified: bool = False,
    quality_rating: str = "unknown",
    star_score: float = 0.0,
) -> STARAnalysis:
    """Create a STAR method analysis"""
    analysis = STARAnalysis(
        interview_id=interview_id,
        question=question,
        answer=answer,
        has_situation=has_situation,
        has_task=has_task,
        has_action=has_action,
        has_result=has_result,
        situation_text=situation_text,
        task_text=task_text,
        action_text=action_text,
        result_text=result_text,
        star_completion_percentage=star_completion_percentage,
        result_quantified=result_quantified,
        quality_rating=quality_rating,
        star_score=star_score,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def get_star_analyses(db: Session, interview_id: int) -> List[STARAnalysis]:
    """Get all STAR analyses for an interview"""
    return (
        db.query(STARAnalysis)
        .filter(STARAnalysis.interview_id == interview_id)
        .order_by(STARAnalysis.created_at)
        .all()
    )


# Alias for backwards compatibility
def get_interview_star_analyses(db: Session, interview_id: int) -> List[STARAnalysis]:
    """Alias for get_star_analyses"""
    return get_star_analyses(db, interview_id)


# ============================================================================
# RED FLAG OPERATIONS (PILLAR 1 & 2)
# ============================================================================

def create_red_flag(
    db: Session,
    interview_id: int,
    flag_type: str,
    severity: str,
    description: str,
    context: Optional[str] = None,
    transcript_id: Optional[int] = None,
) -> RedFlag:
    """Create a red flag alert"""
    red_flag = RedFlag(
        interview_id=interview_id,
        timestamp=datetime.utcnow(),
        flag_type=flag_type,
        severity=severity,
        description=description,
        context=context,
        transcript_id=transcript_id,
    )
    db.add(red_flag)
    db.commit()
    db.refresh(red_flag)
    return red_flag


def get_interview_red_flags(db: Session, interview_id: int) -> List[RedFlag]:
    """Get all red flags for an interview"""
    return (
        db.query(RedFlag)
        .filter(RedFlag.interview_id == interview_id)
        .order_by(RedFlag.timestamp)
        .all()
    )


# ============================================================================
# FOLLOW-UP SUGGESTION OPERATIONS (PILLAR 1)
# ============================================================================

def create_follow_up_suggestion(
    db: Session,
    interview_id: int,
    suggestion: str,
    category: str,
    priority: int = 1,
    context: Optional[str] = None,
    related_competency: Optional[CompetencyType] = None,
) -> FollowUpSuggestion:
    """Create a follow-up suggestion"""
    suggestion_obj = FollowUpSuggestion(
        interview_id=interview_id,
        timestamp=datetime.utcnow(),
        suggestion=suggestion,
        category=category,
        priority=priority,
        context=context,
        related_competency=related_competency,
    )
    db.add(suggestion_obj)
    db.commit()
    db.refresh(suggestion_obj)
    return suggestion_obj


def get_pending_suggestions(db: Session, interview_id: int, limit: Optional[int] = None) -> List[FollowUpSuggestion]:
    """Get pending (not yet displayed) follow-up suggestions"""
    query = (
        db.query(FollowUpSuggestion)
        .filter(
            and_(
                FollowUpSuggestion.interview_id == interview_id,
                FollowUpSuggestion.displayed_to_interviewer == False
            )
        )
        .order_by(desc(FollowUpSuggestion.priority), FollowUpSuggestion.timestamp)
    )

    if limit:
        query = query.limit(limit)

    return query.all()


# ============================================================================
# SUMMARY OPERATIONS (PILLAR 3)
# ============================================================================

def create_interview_summary(
    db: Session,
    interview_id: int,
    summary_type: str,
    title: str,
    content: str,
    strengths: Optional[Dict] = None,
    weaknesses: Optional[Dict] = None,
    highlights: Optional[Dict] = None,
    next_steps: Optional[Dict] = None,
    hiring_recommendation: Optional[str] = None,
    recommendation_confidence: Optional[float] = None,
    recommendation_reasoning: Optional[str] = None,
    overall_score: Optional[float] = None,
    format: str = "text",
) -> InterviewSummary:
    """Create an interview summary"""
    summary = InterviewSummary(
        interview_id=interview_id,
        summary_type=summary_type,
        title=title,
        content=content,
        strengths=strengths,
        weaknesses=weaknesses,
        highlights=highlights,
        next_steps=next_steps,
        hiring_recommendation=hiring_recommendation,
        recommendation_confidence=recommendation_confidence,
        recommendation_reasoning=recommendation_reasoning,
        overall_score=overall_score,
        format=format,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_interview_statistics(db: Session, interview_id: int) -> Dict[str, Any]:
    """Get comprehensive statistics for an interview"""
    interview = get_interview_by_id(db, interview_id)
    if not interview:
        return {}

    stats = {
        "interview_id": interview_id,
        "status": interview.status.value,
        "duration_minutes": interview.duration_minutes,
        "transcript_count": db.query(Transcript).filter(Transcript.interview_id == interview_id).count(),
        "evaluation_count": db.query(Evaluation).filter(Evaluation.interview_id == interview_id).count(),
        "red_flag_count": db.query(RedFlag).filter(RedFlag.interview_id == interview_id).count(),
        "competency_scores": db.query(CompetencyScore).filter(CompetencyScore.interview_id == interview_id).count(),
    }

    return stats


# ============================================================================
# QUESTION BANK OPERATIONS (PILLAR 3)
# ============================================================================

def create_question_bank_entry(
    db: Session,
    question_text: str,
    competency: str,
    difficulty: str,
    question_type: str,
    topics: Optional[List[str]] = None,
    follow_up_questions: Optional[List[str]] = None,
    evaluation_criteria: Optional[List[str]] = None,
    expected_star_components: Optional[List[str]] = None,
    generated_for_candidate_id: Optional[int] = None,
    generated_by_model: Optional[str] = None,
) -> QuestionBankEntry:
    """Create a new question bank entry"""
    entry = QuestionBankEntry(
        question_text=question_text,
        competency=competency,
        difficulty=difficulty,
        question_type=question_type,
        topics={"topics": topics} if topics else None,
        follow_up_questions={"questions": follow_up_questions} if follow_up_questions else None,
        evaluation_criteria={"criteria": evaluation_criteria} if evaluation_criteria else None,
        expected_star_components={"components": expected_star_components} if expected_star_components else None,
        generated_for_candidate_id=generated_for_candidate_id,
        generated_by_model=generated_by_model,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_question_by_id(db: Session, question_id: int) -> Optional[QuestionBankEntry]:
    """Get question by ID"""
    return db.query(QuestionBankEntry).filter(QuestionBankEntry.id == question_id).first()


def get_questions_by_criteria(
    db: Session,
    competency: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 10,
) -> List[QuestionBankEntry]:
    """Get questions matching criteria"""
    query = db.query(QuestionBankEntry)

    if competency:
        query = query.filter(QuestionBankEntry.competency == competency)
    if difficulty:
        query = query.filter(QuestionBankEntry.difficulty == difficulty)
    if question_type:
        query = query.filter(QuestionBankEntry.question_type == question_type)

    return query.order_by(desc(QuestionBankEntry.success_rate)).limit(limit).all()


def update_question_stats(
    db: Session,
    question_id: int,
    used: bool = True,
    star_completion: Optional[float] = None,
    led_to_insights: Optional[bool] = None,
) -> Optional[QuestionBankEntry]:
    """Update question usage statistics"""
    question = get_question_by_id(db, question_id)
    if not question:
        return None

    if used:
        question.used_count += 1

    if star_completion is not None:
        # Update rolling average
        if question.avg_star_completion is None:
            question.avg_star_completion = star_completion
        else:
            # Weighted average favoring recent data
            question.avg_star_completion = (
                0.7 * question.avg_star_completion + 0.3 * star_completion
            )

    if led_to_insights is not None:
        # Update success rate
        if question.success_rate is None:
            question.success_rate = 1.0 if led_to_insights else 0.0
        else:
            # Weighted average
            insight_score = 1.0 if led_to_insights else 0.0
            question.success_rate = (
                0.7 * question.success_rate + 0.3 * insight_score
            )

    db.commit()
    db.refresh(question)
    return question


def create_interview_question(
    db: Session,
    interview_id: int,
    question_text: str,
    difficulty: str,
    competency: str,
    question_type: str,
    question_bank_id: Optional[int] = None,
    was_ai_suggested: bool = True,
    selection_reasoning: Optional[str] = None,
    coverage_at_time: Optional[Dict] = None,
) -> InterviewQuestion:
    """Create an interview question record"""
    question = InterviewQuestion(
        interview_id=interview_id,
        question_bank_id=question_bank_id,
        question_text=question_text,
        difficulty=difficulty,
        competency=competency,
        question_type=question_type,
        was_ai_suggested=was_ai_suggested,
        selection_reasoning=selection_reasoning,
        coverage_at_time=coverage_at_time,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def mark_question_used(
    db: Session,
    question_id: int,
    was_actually_asked: bool = True,
    was_modified: bool = False,
) -> Optional[InterviewQuestion]:
    """Mark an interview question as used"""
    question = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
    if not question:
        return None

    question.was_actually_asked = was_actually_asked
    question.was_modified = was_modified

    # Update question bank stats if linked
    if question.question_bank_id and was_actually_asked:
        update_question_stats(db, question.question_bank_id, used=True)

    db.commit()
    db.refresh(question)
    return question


def update_question_performance(
    db: Session,
    question_id: int,
    star_completion: Optional[float] = None,
    led_to_good_insights: Optional[bool] = None,
    interviewer_rating: Optional[int] = None,
) -> Optional[InterviewQuestion]:
    """Update performance metrics for an interview question"""
    question = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
    if not question:
        return None

    if star_completion is not None:
        question.star_completion = star_completion
    if led_to_good_insights is not None:
        question.led_to_good_insights = led_to_good_insights
    if interviewer_rating is not None:
        question.interviewer_rating = interviewer_rating

    # Update question bank stats if linked
    if question.question_bank_id:
        update_question_stats(
            db,
            question.question_bank_id,
            used=False,  # Don't increment usage count
            star_completion=star_completion,
            led_to_insights=led_to_good_insights,
        )

    db.commit()
    db.refresh(question)
    return question


def get_interview_questions(db: Session, interview_id: int) -> List[InterviewQuestion]:
    """Get all questions for an interview"""
    return (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.interview_id == interview_id)
        .order_by(InterviewQuestion.suggested_at)
        .all()
    )


def get_question_bank_stats(db: Session) -> Dict[str, Any]:
    """Get question bank statistics"""
    total_questions = db.query(QuestionBankEntry).count()

    # By competency
    competency_counts = {}
    for competency in ["leadership", "communication", "technical_depth", "problem_solving",
                       "ownership", "adaptability", "strategic_thinking", "creativity",
                       "teamwork", "culture_fit"]:
        count = db.query(QuestionBankEntry).filter(
            QuestionBankEntry.competency == competency
        ).count()
        if count > 0:
            competency_counts[competency] = count

    # By difficulty
    difficulty_counts = {}
    for difficulty in ["easy", "medium", "hard"]:
        count = db.query(QuestionBankEntry).filter(
            QuestionBankEntry.difficulty == difficulty
        ).count()
        if count > 0:
            difficulty_counts[difficulty] = count

    # Most effective questions (top 10)
    most_effective = (
        db.query(QuestionBankEntry)
        .filter(QuestionBankEntry.success_rate.isnot(None))
        .order_by(desc(QuestionBankEntry.success_rate))
        .limit(10)
        .all()
    )

    return {
        "total_questions": total_questions,
        "by_competency": competency_counts,
        "by_difficulty": difficulty_counts,
        "most_effective": [
            {
                "id": q.id,
                "question": q.question_text[:100],
                "competency": q.competency,
                "difficulty": q.difficulty,
                "success_rate": round(q.success_rate, 2) if q.success_rate else None,
                "used_count": q.used_count,
            }
            for q in most_effective
        ],
    }


def get_interviews(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
) -> List[Interview]:
    """Get list of all interviews with pagination and optional status filter"""
    query = db.query(Interview)

    if status:
        try:
            status_enum = InterviewStatus(status)
            query = query.filter(Interview.status == status_enum)
        except ValueError:
            pass  # Invalid status, ignore filter

    return (
        query.order_by(desc(Interview.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_interview_summaries(db: Session, interview_id: int) -> List[InterviewSummary]:
    """Get all summaries for an interview, ordered by most recent first"""
    return (
        db.query(InterviewSummary)
        .filter(InterviewSummary.interview_id == interview_id)
        .order_by(desc(InterviewSummary.generated_at))
        .all()
    )


def get_interview_summary(db: Session, interview_id: int) -> Optional[InterviewSummary]:
    """Get the most recent summary for an interview"""
    return (
        db.query(InterviewSummary)
        .filter(InterviewSummary.interview_id == interview_id)
        .order_by(desc(InterviewSummary.generated_at))
        .first()
    )


# ============================================================================
# ADDITIONAL CANDIDATE OPERATIONS (PILLAR 6)
# ============================================================================

def get_all_candidates(db: Session, skip: int = 0, limit: int = 100) -> List[Candidate]:
    """Get all candidates with pagination"""
    return (
        db.query(Candidate)
        .order_by(desc(Candidate.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_candidate(db: Session, candidate_id: int) -> Optional[Candidate]:
    """Get candidate by ID (alias for get_candidate_by_id)"""
    return get_candidate_by_id(db, candidate_id)


def get_transcripts_by_interview(db: Session, interview_id: int) -> List[Transcript]:
    """Get all transcripts for an interview (alias for get_interview_transcripts)"""
    return get_interview_transcripts(db, interview_id)
