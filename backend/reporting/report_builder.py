"""
Report Builder - PILLAR 5.2
Builds structured reports for different audiences
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportBuilder:
    """
    Builds structured reports for different audiences

    Report Types:
    - ATS Summary: For applicant tracking systems
    - Hiring Manager Report: Detailed technical assessment
    - Recruiter Brief: High-level overview
    - Full Report: Complete data dump
    """

    def __init__(self):
        """Initialize report builder"""
        logger.info("✅ ReportBuilder initialized")

    def build_report(
        self,
        report_type: str,
        summary: Dict,
        interview_data: Dict,
        candidate_data: Dict,
        competency_scores: List[Dict],
        include_transcript: bool = False,
        transcripts: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Build structured report based on type

        Args:
            report_type: "ats", "hiring_manager", "recruiter", or "full"
            summary: Comprehensive summary from SummaryGenerator
            interview_data: Interview record
            candidate_data: Candidate record
            competency_scores: List of competency evaluations
            include_transcript: Whether to include full transcript
            transcripts: Transcript entries (if include_transcript=True)

        Returns:
            Structured report dict
        """
        logger.info(f"📄 Building {report_type} report")

        if report_type == "ats":
            return self._build_ats_summary(summary, interview_data, candidate_data, competency_scores)
        elif report_type == "hiring_manager":
            return self._build_hiring_manager_report(summary, interview_data, candidate_data, competency_scores)
        elif report_type == "recruiter":
            return self._build_recruiter_brief(summary, interview_data, candidate_data)
        elif report_type == "full":
            return self._build_full_report(
                summary, interview_data, candidate_data, competency_scores,
                include_transcript, transcripts
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _build_ats_summary(
        self,
        summary: Dict,
        interview: Dict,
        candidate: Dict,
        competencies: List[Dict]
    ) -> Dict:
        """Build ATS-compatible summary"""
        overall_score = summary.get("metadata", {}).get("overall_score", 0)

        return {
            "report_type": "ats",
            "generated_at": datetime.now().isoformat(),
            "candidate": {
                "name": candidate.get("name"),
                "email": candidate.get("email"),
                "id": candidate.get("id")
            },
            "position": interview.get("job_title"),
            "interview_date": interview.get("scheduled_start", datetime.now()).strftime("%Y-%m-%d"),
            "overall_score": round(overall_score, 1),
            "recommendation": summary.get("hiring_recommendation"),
            "recommendation_confidence": summary.get("recommendation_confidence"),
            "competency_scores": {
                comp.get("competency", "unknown"): comp.get("overall_score", 0)
                for comp in competencies
            },
            "pass_fail_criteria": {
                "overall": "PASS" if overall_score >= 70 else "FAIL",
                "technical_competence": self._assess_technical(competencies),
                "cultural_fit": "PASS"  # Placeholder
            },
            "summary": summary.get("executive_summary", "")[:500],  # Truncate for ATS
            "next_steps": summary.get("next_steps", [])
        }

    def _build_hiring_manager_report(
        self,
        summary: Dict,
        interview: Dict,
        candidate: Dict,
        competencies: List[Dict]
    ) -> Dict:
        """Build detailed hiring manager report"""
        return {
            "report_type": "hiring_manager",
            "generated_at": datetime.now().isoformat(),
            "candidate_overview": {
                "name": candidate.get("name"),
                "position_applied": interview.get("job_title"),
                "interview_date": interview.get("scheduled_start", datetime.now()).strftime("%Y-%m-%d"),
                "overall_score": summary.get("metadata", {}).get("overall_score")
            },
            "executive_summary": summary.get("executive_summary"),
            "key_highlights": summary.get("key_highlights", []),
            "detailed_assessment": {
                "strengths": summary.get("strengths", []),
                "weaknesses": summary.get("weaknesses", []),
                "standout_moments": summary.get("standout_moments", [])
            },
            "competency_breakdown": [
                {
                    "competency": comp.get("competency"),
                    "overall_score": comp.get("overall_score"),
                    "depth": comp.get("depth_score"),
                    "clarity": comp.get("clarity_score"),
                    "evidence": comp.get("evidence_score"),
                    "reasoning": comp.get("reasoning")
                }
                for comp in competencies
            ],
            "concerns_and_risks": summary.get("concerns", []),
            "hiring_recommendation": {
                "decision": summary.get("hiring_recommendation"),
                "confidence": summary.get("recommendation_confidence"),
                "reasoning": summary.get("recommendation_reasoning")
            },
            "next_steps": summary.get("next_steps", []),
            "interview_quality": summary.get("interview_quality_notes", "")
        }

    def _build_recruiter_brief(
        self,
        summary: Dict,
        interview: Dict,
        candidate: Dict
    ) -> Dict:
        """Build high-level recruiter brief"""
        return {
            "report_type": "recruiter",
            "generated_at": datetime.now().isoformat(),
            "candidate": {
                "name": candidate.get("name"),
                "email": candidate.get("email")
            },
            "position": interview.get("job_title"),
            "quick_assessment": {
                "overall_score": summary.get("metadata", {}).get("overall_score"),
                "recommendation": summary.get("hiring_recommendation"),
                "confidence": summary.get("recommendation_confidence")
            },
            "key_takeaways": summary.get("key_highlights", [])[:5],
            "top_strengths": [s.get("area") for s in summary.get("strengths", [])[:3]],
            "main_concerns": [c.get("concern") for c in summary.get("concerns", [])[:3]],
            "next_steps": summary.get("next_steps", []),
            "candidate_experience_notes": summary.get("interview_quality_notes", "")
        }

    def _build_full_report(
        self,
        summary: Dict,
        interview: Dict,
        candidate: Dict,
        competencies: List[Dict],
        include_transcript: bool,
        transcripts: Optional[List[Dict]]
    ) -> Dict:
        """Build complete evaluation report"""
        report = {
            "report_type": "full",
            "generated_at": datetime.now().isoformat(),
            "interview_details": interview,
            "candidate_details": candidate,
            "comprehensive_summary": summary,
            "competency_scores": competencies,
            "metadata": summary.get("metadata", {})
        }

        if include_transcript and transcripts:
            report["full_transcript"] = transcripts

        return report

    def _assess_technical(self, competencies: List[Dict]) -> str:
        """Assess overall technical competence"""
        technical_comps = [
            c for c in competencies
            if "technical" in c.get("competency", "").lower() or
               "problem" in c.get("competency", "").lower()
        ]

        if not technical_comps:
            return "N/A"

        avg_score = sum(c.get("overall_score", 0) for c in technical_comps) / len(technical_comps)
        return "PASS" if avg_score >= 70 else "FAIL"
