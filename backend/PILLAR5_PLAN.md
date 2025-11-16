# PILLAR 5: Post-Interview Analysis & Reporting
## Implementation Plan

**Status**: In Development
**Priority**: High
**Integration**: Aggregates data from all previous pillars

---

## Overview

Provides comprehensive post-interview analysis, structured reports, hiring recommendations, and candidate comparison tools. Synthesizes all interview data into actionable insights for hiring decisions.

## Architecture

```
reporting/
├── __init__.py                      # Module exports
├── summary_generator.py             # Comprehensive interview summaries
├── report_builder.py                # Structured report generation
├── candidate_comparator.py          # Multi-candidate comparison
└── export_formatter.py              # Export to various formats
```

---

## Module 1: Summary Generator

**Purpose**: Generate comprehensive interview summaries using all available data

**Key Features**:
- Executive summary (2-3 paragraphs)
- Bullet-point highlights
- Strengths and weaknesses analysis
- Key moments and quotes
- Overall hiring recommendation

**Data Sources**:
- Transcripts (full conversation)
- Competency scores (PILLAR 2)
- STAR analyses (PILLAR 2)
- Bluffing detection (PILLAR 2)
- Cultural fit (PILLAR 2)
- Question quality metrics (PILLAR 4)
- Coverage gaps (PILLAR 1)

**Claude Prompt**:
```python
SUMMARY_PROMPT = """Generate a comprehensive interview summary based on the following data:

CANDIDATE: {candidate_name}
ROLE: {job_title}
DURATION: {duration_minutes} minutes
QUESTIONS ASKED: {total_questions}

CONVERSATION TRANSCRIPT:
{transcript_text}

COMPETENCY SCORES:
{competency_scores}

STAR ANALYSES:
{star_analyses}

RED FLAGS:
{red_flags}

CULTURAL FIT SCORE: {cultural_fit_score}/100

Generate a structured summary in JSON format:
{{
    "executive_summary": "2-3 paragraph overview of the interview",
    "key_highlights": ["5-7 most important points"],
    "strengths": [
        {{
            "area": "Competency or skill",
            "evidence": "Specific example from interview",
            "score": 0-100
        }}
    ],
    "weaknesses": [
        {{
            "area": "Competency or skill gap",
            "evidence": "Specific example or lack thereof",
            "severity": "low" | "medium" | "high"
        }}
    ],
    "standout_moments": [
        {{
            "moment": "Description of impressive answer or insight",
            "quote": "Direct quote from candidate",
            "significance": "Why this matters"
        }}
    ],
    "concerns": [
        {{
            "concern": "Specific issue identified",
            "severity": "low" | "medium" | "high",
            "recommendation": "How to address or verify"
        }}
    ],
    "hiring_recommendation": "strong_hire" | "hire" | "maybe" | "no_hire",
    "recommendation_confidence": 0.0-1.0,
    "recommendation_reasoning": "Detailed explanation of recommendation"
}}"""
```

**Output Format**:
```python
{
    "interview_id": 123,
    "summary_type": "comprehensive",
    "generated_at": "2024-01-15T10:30:00Z",
    "executive_summary": "...",
    "key_highlights": [...],
    "strengths": [...],
    "weaknesses": [...],
    "standout_moments": [...],
    "concerns": [...],
    "hiring_recommendation": "hire",
    "recommendation_confidence": 0.85,
    "recommendation_reasoning": "..."
}
```

---

## Module 2: Report Builder

**Purpose**: Build structured reports for different audiences (ATS, hiring manager, recruiter)

**Report Types**:

### 1. **ATS Summary** (Applicant Tracking System)
- Structured fields for ATS import
- Pass/fail on key competencies
- Numeric scores
- Recommendation (hire/no hire)

### 2. **Hiring Manager Report**
- Focus on technical competencies and role fit
- Deep-dive on strengths/weaknesses
- Comparison to job requirements
- Next steps recommendations

### 3. **Recruiter Brief**
- High-level overview
- Red flags and concerns
- Candidate experience quality
- Interview metrics (pacing, coverage, etc.)

### 4. **Full Evaluation Report**
- Complete data dump
- All competency scores
- All STAR analyses
- Full transcript
- All metrics and analytics

**Report Structure**:
```python
class ReportBuilder:
    async def generate_report(
        self,
        interview_id: int,
        report_type: str,  # "ats", "hiring_manager", "recruiter", "full"
        include_transcript: bool = False,
        include_metrics: bool = True
    ) -> Dict:
        """Generate structured report"""
        # Gather all data
        interview = get_interview(interview_id)
        candidate = interview.candidate
        transcripts = get_transcripts(interview_id)
        competencies = get_competency_scores(interview_id)
        star_analyses = get_star_analyses(interview_id)
        red_flags = get_red_flags(interview_id)

        # Build report based on type
        if report_type == "ats":
            return self._build_ats_summary(...)
        elif report_type == "hiring_manager":
            return self._build_hiring_manager_report(...)
        elif report_type == "recruiter":
            return self._build_recruiter_brief(...)
        else:
            return self._build_full_report(...)
```

---

## Module 3: Candidate Comparator

**Purpose**: Compare multiple candidates for the same role

**Features**:
- Side-by-side competency comparison
- Relative ranking
- Strengths/weaknesses matrix
- Decision support scoring

**Comparison Dimensions**:
1. Overall scores (0-100 for each candidate)
2. Competency breakdown (radar chart data)
3. STAR completion rates
4. Cultural fit scores
5. Red flag counts
6. Interview quality metrics

**Claude Prompt for Comparison**:
```python
COMPARISON_PROMPT = """Compare these {n} candidates for the {job_title} role:

{candidate_summaries}

Provide a detailed comparison in JSON format:
{{
    "overall_ranking": [
        {{
            "rank": 1,
            "candidate_name": "...",
            "overall_score": 0-100,
            "reasoning": "Why they ranked here"
        }}
    ],
    "competency_comparison": {{
        "leadership": {{
            "best": "candidate_name",
            "scores": {{"candidate1": 85, "candidate2": 72}},
            "analysis": "Comparison notes"
        }}
    }},
    "unique_strengths": {{
        "candidate1": ["strength1", "strength2"],
        "candidate2": ["strength1", "strength2"]
    }},
    "hiring_recommendation": {{
        "first_choice": "candidate_name",
        "reasoning": "...",
        "second_choice": "candidate_name",
        "reasoning": "..."
    }},
    "risk_analysis": {{
        "candidate1": {{"risk_level": "low", "concerns": []}},
        "candidate2": {{"risk_level": "medium", "concerns": [...]}}
    }}
}}"""
```

---

## Module 4: Export Formatter

**Purpose**: Export reports to various formats (JSON, PDF, HTML, ATS integrations)

**Supported Formats**:

### 1. **JSON**
- Raw structured data
- API-friendly
- Easy integration

### 2. **HTML**
- Styled report with CSS
- Print-friendly
- Email-friendly

### 3. **PDF** (using reportlab or weasyprint)
- Professional formatting
- Company branding
- Archival format

### 4. **Markdown**
- Human-readable
- Version control friendly
- Documentation-ready

### 5. **ATS Integration** (Greenhouse, Lever, Workday)
- API payloads for popular ATS
- Field mapping
- Automated posting

**Export Interface**:
```python
class ExportFormatter:
    def export_to_json(self, report: Dict) -> str:
        """Export to JSON string"""

    def export_to_html(self, report: Dict, template: str = "default") -> str:
        """Export to styled HTML"""

    def export_to_pdf(self, report: Dict, output_path: str) -> str:
        """Export to PDF file"""

    def export_to_markdown(self, report: Dict) -> str:
        """Export to Markdown"""

    async def export_to_ats(
        self,
        report: Dict,
        ats_type: str,  # "greenhouse", "lever", "workday"
        api_credentials: Dict
    ) -> Dict:
        """Export to ATS via API"""
```

---

## Database Schema Updates

We'll use the existing `InterviewSummary` table but add more specific fields:

```python
# Update InterviewSummary model
class InterviewSummary(Base):
    # ... existing fields ...

    # Add new fields for PILLAR 5
    hiring_recommendation: str  # "strong_hire", "hire", "maybe", "no_hire"
    recommendation_confidence: float  # 0.0-1.0
    recommendation_reasoning: str  # Detailed explanation
    overall_score: float  # 0-100 aggregate score

    # Comparisons
    compared_to_candidate_ids: List[int]  # If part of comparison
    rank_in_comparison: int  # Ranking if part of multi-candidate comparison
```

---

## API Endpoints

### 1. Generate Comprehensive Summary
```
POST /interviews/{interview_id}/generate-summary

Request:
{
    "include_transcript": false,
    "include_detailed_scores": true
}

Response:
{
    "interview_id": 123,
    "summary": {
        "executive_summary": "...",
        "key_highlights": [...],
        "strengths": [...],
        "weaknesses": [...],
        "hiring_recommendation": "hire",
        "overall_score": 78.5
    }
}
```

### 2. Generate Structured Report
```
POST /interviews/{interview_id}/generate-report

Request:
{
    "report_type": "hiring_manager",  # or "ats", "recruiter", "full"
    "include_transcript": false,
    "format": "json"  # or "html", "pdf", "markdown"
}

Response:
{
    "report_id": 456,
    "report_type": "hiring_manager",
    "format": "json",
    "content": {...},
    "download_url": "/reports/456/download"
}
```

### 3. Compare Candidates
```
POST /candidates/compare

Request:
{
    "candidate_ids": [1, 2, 3],
    "job_title": "Senior Quantitative Analyst",
    "comparison_dimensions": ["competencies", "cultural_fit", "star_completion"]
}

Response:
{
    "comparison_id": 789,
    "candidates": [
        {
            "candidate_id": 1,
            "name": "John Doe",
            "overall_score": 85,
            "rank": 1
        },
        ...
    ],
    "competency_comparison": {...},
    "recommendation": {
        "first_choice": "John Doe",
        "reasoning": "..."
    }
}
```

### 4. Export Report
```
POST /reports/{report_id}/export

Request:
{
    "format": "pdf",  # or "html", "json", "markdown"
    "template": "professional"  # or "minimal", "detailed"
}

Response:
{
    "export_id": 999,
    "format": "pdf",
    "download_url": "/exports/999/download.pdf",
    "expires_at": "2024-01-16T10:30:00Z"
}
```

### 5. Export to ATS
```
POST /reports/{report_id}/export-to-ats

Request:
{
    "ats_type": "greenhouse",
    "application_id": "app-123",
    "api_credentials": {
        "api_key": "...",
        "endpoint": "https://harvest.greenhouse.io/v1/"
    }
}

Response:
{
    "status": "success",
    "ats_type": "greenhouse",
    "ats_record_id": "candidate-789",
    "message": "Report exported to Greenhouse successfully"
}
```

### 6. Get All Reports for Interview
```
GET /interviews/{interview_id}/reports

Response:
{
    "interview_id": 123,
    "reports": [
        {
            "report_id": 456,
            "report_type": "hiring_manager",
            "generated_at": "2024-01-15T10:30:00Z",
            "format": "json"
        },
        ...
    ]
}
```

---

## Integration Points

### With Previous Pillars

**PILLAR 1 (Co-Pilot)**:
- Coverage metrics → Report completeness section
- Quality scores → Interview quality assessment

**PILLAR 2 (Evaluation)**:
- Competency scores → Core of report
- STAR analyses → Evidence for strengths/weaknesses
- Bluffing detection → Risk section
- Cultural fit → Fit assessment

**PILLAR 3 (Question Bank)**:
- Question effectiveness → Interview quality metrics
- Coverage achieved → Completeness score

**PILLAR 4 (Interviewer Feedback)**:
- Interviewer quality scores → Interview process quality
- Bias incidents → Process improvement notes

**PILLAR 6 (Candidate Profiles)**:
- Pre-interview predictions vs. actual performance
- Profile enrichment with interview insights

---

## Success Metrics

1. **Report Completeness**
   - Target: 100% of interviews have comprehensive summary within 5 minutes
   - Measure: Time from interview end to report generation

2. **Hiring Decision Accuracy**
   - Target: Reports correctly predict hire/no-hire 85%+ of time
   - Measure: Correlation between recommendation and actual hiring decision

3. **Report Satisfaction**
   - Target: 90%+ of hiring managers find reports useful
   - Measure: Survey feedback

4. **Time Savings**
   - Target: 80% reduction in report writing time (from 30 min to 6 min)
   - Measure: Before/after comparison

5. **ATS Integration Success**
   - Target: 95%+ successful exports to ATS
   - Measure: Export success rate

---

## Implementation Order

1. ✅ Create implementation plan
2. Build SummaryGenerator (most critical)
3. Build ReportBuilder (second most critical)
4. Build CandidateComparator (multi-candidate scenarios)
5. Build ExportFormatter (output flexibility)
6. Update database models (if needed)
7. Create API endpoints
8. Test integration with existing data
9. Add export functionality (PDF, ATS)

---

## Technical Considerations

**Performance**:
- Summary generation: ~10-15 seconds (Claude API call)
- Report building: ~2-3 seconds (data aggregation)
- Candidate comparison: ~15-20 seconds (Claude API call for n candidates)
- Export formatting: <1 second (JSON/HTML), ~3 seconds (PDF)

**Caching**:
- Cache generated summaries (invalidate if interview data changes)
- Cache report builds for 24 hours
- Pre-generate common report types on interview completion

**Error Handling**:
- If Claude fails, use template-based summary
- Fallback to basic scoring if detailed analysis fails
- Queue failed ATS exports for retry

**Privacy & Security**:
- All reports contain sensitive candidate data
- Implement access controls (who can view reports)
- Auto-expire download URLs (24-48 hours)
- Option to redact personal information for anonymized comparisons

---

## Future Enhancements

1. **Custom Report Templates**: Allow companies to define their own report formats
2. **Automated Email Distribution**: Send reports to stakeholders automatically
3. **Dashboard View**: Visual dashboard for multi-candidate comparisons
4. **Video Integration**: Link to specific video moments for key quotes
5. **Benchmarking**: Compare candidates to historical hire data
6. **Predictive Analytics**: ML model to predict long-term success

---

## File Structure Summary

```
backend/
├── reporting/
│   ├── __init__.py
│   ├── summary_generator.py       (~400 lines)
│   ├── report_builder.py          (~500 lines)
│   ├── candidate_comparator.py    (~350 lines)
│   └── export_formatter.py        (~400 lines)
├── database/
│   └── models.py                   (update InterviewSummary)
│   └── crud.py                     (add reporting CRUD functions)
└── server.py                       (add 6 new endpoints)
```

**Estimated Total**: ~2,000 lines of new code
