# Missing endpoints to add to server.py

MISSING_ENDPOINTS = """

# Add these endpoints after line 1690 in server.py (after the question bank endpoints)

@app.get("/interviews/{interview_id}/copilot/suggestions")
async def get_copilot_suggestions(
    interview_id: int,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get AI Co-Pilot suggestions for the interview

    PILLAR 1: Live Co-Pilot
    Returns follow-up suggestions and coverage status
    \"\"\"
    if not followup_suggester:
        raise HTTPException(
            status_code=503,
            detail="Co-Pilot not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"

        # Get coverage tracker
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        # Get pending follow-up suggestions
        pending_suggestions = crud.get_pending_suggestions(db, interview_id, limit=5)

        # Format suggestions
        follow_up_suggestions = [
            {
                "question": s.suggestion,
                "reason": s.context or "Recommended based on interview progress",
                "priority": "high" if s.priority >= 3 else "medium" if s.priority >= 2 else "low",
                "competency": s.category or "general"
            }
            for s in pending_suggestions
        ]

        # Get competency coverage status
        competency_scores = crud.get_interview_competency_scores(db, interview_id)
        covered_competencies = {score.competency.value for score in competency_scores}

        all_competencies = ["leadership", "communication", "technical_depth", "problem_solving",
                           "ownership", "adaptability", "strategic_thinking", "creativity",
                           "teamwork", "culture_fit"]

        coverage_status = []
        for comp in all_competencies:
            if comp in covered_competencies:
                score = next((s for s in competency_scores if s.competency.value == comp), None)
                coverage_status.append({
                    "competency": comp,
                    "current_score": score.overall_score if score else 0,
                    "target_score": 70,
                    "coverage_percentage": min(100, (score.overall_score / 70) * 100) if score else 0,
                    "status": "well_covered" if (score and score.overall_score >= 70) else "in_progress",
                    "suggested_questions_count": 0
                })
            else:
                coverage_status.append({
                    "competency": comp,
                    "current_score": 0,
                    "target_score": 70,
                    "coverage_percentage": 0,
                    "status": "not_started",
                    "suggested_questions_count": 2
                })

        # Calculate overall progress
        covered_count = len(covered_competencies)
        overall_progress = (covered_count / len(all_competencies)) * 100

        # Determine interview phase and recommended next step
        duration = 0
        if interview.actual_start:
            duration = (datetime.now() - interview.actual_start).total_seconds() / 60

        if duration < 10:
            interview_phase = "Opening (Building Rapport)"
            recommended_next_step = "Focus on ice-breaker questions and candidate background"
        elif duration < 30:
            interview_phase = "Core Assessment"
            recommended_next_step = "Deep dive into technical and behavioral competencies"
        elif duration < 45:
            interview_phase = "Advanced Evaluation"
            recommended_next_step = "Probe for depth and address any coverage gaps"
        else:
            interview_phase = "Closing"
            recommended_next_step = "Final clarifications and candidate questions"

        time_remaining = max(0, 60 - duration)

        return {
            "follow_up_suggestions": follow_up_suggestions,
            "coverage_status": coverage_status,
            "overall_progress": round(overall_progress, 1),
            "recommended_next_step": recommended_next_step,
            "interview_phase": interview_phase,
            "time_remaining_minutes": round(time_remaining, 1)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get co-pilot suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/copilot/coverage")
async def get_copilot_coverage(
    interview_id: int,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get detailed coverage status for the interview

    PILLAR 1: Live Co-Pilot - Coverage Tracker
    \"\"\"
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        return {
            "interview_id": interview_id,
            **coverage
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/questions/suggestions")
async def get_question_suggestions(
    interview_id: int,
    request: Dict = {},
    db: Session = Depends(get_db)
):
    \"\"\"
    Get AI-suggested questions based on interview context

    PILLAR 3: Question Bank - Smart Suggestions
    \"\"\"
    if not question_generator:
        raise HTTPException(
            status_code=503,
            detail="Question Generator not available - check ANTHROPIC_API_KEY"
        )

    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get coverage to determine what to focus on
        room_name = f"interview-{interview_id}"
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        # Find uncovered competencies
        competency_scores = crud.get_interview_competency_scores(db, interview_id)
        covered = {score.competency.value for score in competency_scores}

        all_competencies = ["leadership", "communication", "technical_depth", "problem_solving",
                           "ownership", "adaptability", "strategic_thinking", "creativity",
                           "teamwork", "culture_fit"]

        uncovered = [c for c in all_competencies if c not in covered]
        target_competency = uncovered[0] if uncovered else all_competencies[0]

        # Generate 3-5 question suggestions
        questions = await question_generator.generate_questions(
            competency=target_competency,
            difficulty="medium",
            question_type="behavioral",
            count=3
        )

        # Format for frontend
        suggested_questions = []
        for q in questions:
            suggested_questions.append({
                "question_text": q["question"],
                "question_type": "behavioral",
                "competency": target_competency,
                "difficulty": "medium",
                "reason": f"Helps assess {target_competency} competency",
                "expected_answer_outline": "STAR format response demonstrating the competency",
                "follow_up_questions": q.get("follow_up_questions", []),
                "evaluation_criteria": q.get("evaluation_criteria", []),
                "average_response_time_seconds": 180,
                "success_rate": 0.75
            })

        return {
            "interview_id": interview_id,
            "suggested_questions": suggested_questions,
            "target_competency": target_competency,
            "coverage_gaps": uncovered
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get question suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions")
async def get_all_questions(
    job_title: Optional[str] = None,
    competency: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get questions from the question bank

    PILLAR 3: Question Bank - Browse All Questions
    \"\"\"
    try:
        # Get questions from database
        questions_db = crud.get_questions_by_criteria(
            db=db,
            competency=competency,
            difficulty=difficulty,
            limit=limit
        )

        # Format for frontend
        questions = []
        for q in questions_db:
            questions.append({
                "question_text": q.question_text,
                "question_type": q.question_type or "behavioral",
                "competency": q.competency or "general",
                "difficulty": q.difficulty or "medium",
                "reason": f"From question bank (ID: {q.id})",
                "expected_answer_outline": "STAR format response",
                "follow_up_questions": q.follow_up_questions or [],
                "evaluation_criteria": q.evaluation_criteria or [],
                "average_response_time_seconds": q.average_response_time or 180,
                "success_rate": q.success_rate or 0.75
            })

        return {
            "questions": questions,
            "total": len(questions),
            "filters": {
                "job_title": job_title,
                "competency": competency,
                "difficulty": difficulty
            }
        }

    except Exception as e:
        logger.error(f"❌ Failed to get questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews")
async def list_all_interviews(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get list of all interviews

    PILLAR 5: Interviews Management
    \"\"\"
    try:
        # Get interviews from database
        interviews = crud.get_interviews(
            db=db,
            skip=(page - 1) * limit,
            limit=limit,
            status=status
        )

        # Format for frontend
        interviews_list = []
        for interview in interviews:
            # Calculate duration
            duration_minutes = interview.duration_minutes
            if not duration_minutes and interview.actual_start and interview.actual_end:
                duration_minutes = (interview.actual_end - interview.actual_start).total_seconds() / 60

            # Get summary if exists
            summaries = crud.get_interview_summaries(db, interview.id)
            overall_score = summaries[0].overall_score if summaries else None

            interviews_list.append({
                "id": interview.id,
                "candidate_name": interview.candidate.name if interview.candidate else "Unknown",
                "candidate_email": interview.candidate.email if interview.candidate else "",
                "job_title": interview.job_title or "Unknown Position",
                "scheduled_at": interview.scheduled_start.isoformat() if interview.scheduled_start else datetime.now().isoformat(),
                "started_at": interview.actual_start.isoformat() if interview.actual_start else None,
                "completed_at": interview.actual_end.isoformat() if interview.actual_end else None,
                "duration_minutes": round(duration_minutes) if duration_minutes else None,
                "status": interview.status.value,
                "overall_score": overall_score,
                "summary_generated": len(summaries) > 0
            })

        return {
            "interviews": interviews_list,
            "page": page,
            "limit": limit,
            "total": len(interviews_list)
        }

    except Exception as e:
        logger.error(f"❌ Failed to list interviews: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}")
async def get_interview_details(
    interview_id: int,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get detailed information about an interview

    PILLAR 5: Interview Details
    \"\"\"
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get summary if exists
        summaries = crud.get_interview_summaries(db, interview_id)
        summary = None
        if summaries:
            s = summaries[0]
            summary = {
                "executive_summary": s.content,
                "key_highlights": s.highlights.get("highlights", []) if s.highlights else [],
                "strengths": s.strengths.get("strengths", []) if s.strengths else [],
                "weaknesses": s.weaknesses.get("weaknesses", []) if s.weaknesses else [],
                "hiring_recommendation": s.hiring_recommendation,
                "recommendation_confidence": s.recommendation_confidence,
                "recommendation_reasoning": s.recommendation_reasoning,
                "overall_score": s.overall_score,
                "concerns": s.weaknesses.get("concerns", []) if s.weaknesses else [],
                "standout_moments": s.highlights.get("standout_moments", []) if s.highlights else []
            }

        return {
            "id": interview.id,
            "candidate": {
                "id": interview.candidate.id if interview.candidate else None,
                "name": interview.candidate.name if interview.candidate else "Unknown",
                "email": interview.candidate.email if interview.candidate else ""
            },
            "job_title": interview.job_title,
            "scheduled_at": interview.scheduled_start.isoformat() if interview.scheduled_start else None,
            "started_at": interview.actual_start.isoformat() if interview.actual_start else None,
            "completed_at": interview.actual_end.isoformat() if interview.actual_end else None,
            "duration_minutes": interview.duration_minutes,
            "status": interview.status.value,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get interview details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
"""

print(MISSING_ENDPOINTS)
