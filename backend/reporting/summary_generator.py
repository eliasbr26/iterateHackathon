"""
Summary Generator - PILLAR 5.1
Generates comprehensive interview summaries using all available data
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

import anthropic

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Generates comprehensive interview summaries using Claude AI

    Features:
    - Executive summary (2-3 paragraphs)
    - Bullet-point highlights
    - Strengths and weaknesses analysis
    - Key moments and quotes
    - Overall hiring recommendation
    """

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.4  # Balanced between creativity and consistency

    SUMMARY_PROMPT = """Generate a comprehensive interview summary based on the following data:

CANDIDATE: {candidate_name}
ROLE: {job_title}
DURATION: {duration_minutes} minutes
QUESTIONS ASKED: {total_questions}
INTERVIEW DATE: {interview_date}

CONVERSATION TRANSCRIPT (key exchanges):
{transcript_text}

COMPETENCY SCORES (0-100):
{competency_scores}

STAR METHOD ANALYSES:
{star_analyses}

RED FLAGS/CONCERNS:
{red_flags}

CULTURAL FIT SCORE: {cultural_fit_score}/100

COVERAGE METRICS:
{coverage_metrics}

Generate a structured interview summary in JSON format:
{{
    "executive_summary": "2-3 paragraph professional overview highlighting key aspects of the interview and candidate performance",
    "key_highlights": [
        "5-7 most important takeaways from the interview"
    ],
    "strengths": [
        {{
            "area": "Specific competency or skill",
            "evidence": "Concrete example or quote from interview",
            "score": 0-100,
            "significance": "Why this strength matters for the role"
        }}
    ],
    "weaknesses": [
        {{
            "area": "Specific competency gap or concern",
            "evidence": "Concrete example or observed gap",
            "severity": "low" | "medium" | "high",
            "mitigation": "Possible ways to address or verify this weakness"
        }}
    ],
    "standout_moments": [
        {{
            "moment": "Description of impressive answer or unique insight",
            "quote": "Direct quote from candidate",
            "significance": "Why this demonstrates exceptional quality"
        }}
    ],
    "concerns": [
        {{
            "concern": "Specific issue or red flag",
            "severity": "low" | "medium" | "high",
            "evidence": "What was observed",
            "recommendation": "How to address or verify before hiring"
        }}
    ],
    "hiring_recommendation": "strong_hire" | "hire" | "maybe" | "no_hire",
    "recommendation_confidence": 0.0-1.0,
    "recommendation_reasoning": "Detailed 2-3 sentence explanation balancing strengths and weaknesses",
    "next_steps": [
        "Suggested actions (reference checks, technical exercise, etc.)"
    ],
    "interview_quality_notes": "Brief assessment of interview quality (coverage, depth, etc.)"
}}

Be specific and evidence-based. Focus on job-relevant insights."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize summary generator

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        logger.info(f"✅ SummaryGenerator initialized with model: {model}")

    async def generate(
        self,
        interview_data: Dict,
        candidate_data: Dict,
        competency_scores: List[Dict],
        star_analyses: List[Dict],
        red_flags: List[Dict],
        transcripts: List[Dict],
        cultural_fit_score: Optional[float] = None,
        coverage_metrics: Optional[Dict] = None
    ) -> Dict:
        """
        Generate comprehensive interview summary

        Args:
            interview_data: Interview record data
            candidate_data: Candidate record data
            competency_scores: List of competency evaluations
            star_analyses: List of STAR method analyses
            red_flags: List of red flags/concerns
            transcripts: List of transcript entries
            cultural_fit_score: Cultural fit assessment (0-100)
            coverage_metrics: Topic/competency coverage data

        Returns:
            Comprehensive summary dict
        """
        try:
            logger.info(f"📝 Generating summary for interview {interview_data.get('id', 'unknown')}")

            # Prepare data for prompt
            candidate_name = candidate_data.get("name", "Unknown")
            job_title = interview_data.get("job_title", "Unknown Position")
            duration_minutes = interview_data.get("duration_minutes", 0)
            total_questions = len([t for t in transcripts if t.get("speaker") == "interviewer"])
            interview_date = interview_data.get("scheduled_start", datetime.now()).strftime("%Y-%m-%d")

            # Format transcript (limit to key exchanges)
            transcript_text = self._format_transcript_highlights(transcripts, limit=20)

            # Format competency scores
            competency_text = self._format_competency_scores(competency_scores)

            # Format STAR analyses
            star_text = self._format_star_analyses(star_analyses)

            # Format red flags
            red_flags_text = self._format_red_flags(red_flags)

            # Format coverage metrics
            coverage_text = self._format_coverage_metrics(coverage_metrics or {})

            # Build prompt
            prompt = self.SUMMARY_PROMPT.format(
                candidate_name=candidate_name,
                job_title=job_title,
                duration_minutes=duration_minutes,
                total_questions=total_questions,
                interview_date=interview_date,
                transcript_text=transcript_text,
                competency_scores=competency_text,
                star_analyses=star_text,
                red_flags=red_flags_text,
                cultural_fit_score=cultural_fit_score or "N/A",
                coverage_metrics=coverage_text
            )

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            summary = json.loads(response_text)

            # Calculate overall score from competencies
            overall_score = self._calculate_overall_score(competency_scores, summary)

            # Add metadata
            summary["metadata"] = {
                "interview_id": interview_data.get("id"),
                "candidate_id": candidate_data.get("id"),
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "overall_score": overall_score,
                "duration_minutes": duration_minutes,
                "total_questions": total_questions
            }

            logger.info(
                f"✅ Summary generated: {summary['hiring_recommendation']} "
                f"(confidence: {summary['recommendation_confidence']:.2f}, score: {overall_score:.1f})"
            )

            return summary

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse summary JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return self._fallback_summary(interview_data, candidate_data, competency_scores)

        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}", exc_info=True)
            return self._fallback_summary(interview_data, candidate_data, competency_scores)

    # Private helper methods

    def _format_transcript_highlights(self, transcripts: List[Dict], limit: int = 20) -> str:
        """Format transcript highlights (key exchanges)"""
        if not transcripts:
            return "No transcript available"

        # Select key exchanges (interviewer questions + candidate responses)
        highlights = []
        current_q = None

        for t in transcripts[-limit*2:]:  # Get recent exchanges
            speaker = t.get("speaker", "unknown")
            text = t.get("text", "")

            if speaker == "interviewer" and len(text) > 10:
                current_q = text
            elif speaker == "candidate" and current_q and len(text) > 20:
                highlights.append(f"Q: {current_q[:150]}...\nA: {text[:300]}...")
                current_q = None

        if not highlights:
            return "Limited transcript data available"

        return "\n\n".join(highlights[-10:])  # Last 10 Q&A pairs

    def _format_competency_scores(self, competencies: List[Dict]) -> str:
        """Format competency scores for prompt"""
        if not competencies:
            return "No competency scores available"

        lines = []
        for comp in competencies:
            name = comp.get("competency", "Unknown")
            score = comp.get("overall_score", 0)
            reasoning = comp.get("reasoning", "N/A")[:200]
            lines.append(f"- {name}: {score}/100\n  Reasoning: {reasoning}")

        return "\n".join(lines)

    def _format_star_analyses(self, analyses: List[Dict]) -> str:
        """Format STAR analyses for prompt"""
        if not analyses:
            return "No STAR analyses available"

        lines = []
        for star in analyses:
            question = star.get("question", "Unknown")[:100]
            completion = star.get("star_completion_percentage", 0)
            quality = star.get("quality_rating", "unknown")
            has_result = "Yes" if star.get("has_result") else "No"
            lines.append(
                f"- Q: {question}...\n"
                f"  STAR Completion: {completion}%, Quality: {quality}, Has Result: {has_result}"
            )

        return "\n".join(lines[:5])  # Top 5 analyses

    def _format_red_flags(self, red_flags: List[Dict]) -> str:
        """Format red flags for prompt"""
        if not red_flags:
            return "No red flags detected"

        lines = []
        for flag in red_flags:
            flag_type = flag.get("flag_type", "unknown")
            description = flag.get("description", "")[:150]
            severity = flag.get("severity", "info")
            lines.append(f"- [{severity.upper()}] {flag_type}: {description}")

        return "\n".join(lines)

    def _format_coverage_metrics(self, metrics: Dict) -> str:
        """Format coverage metrics for prompt"""
        if not metrics:
            return "No coverage metrics available"

        competencies = metrics.get("competencies", {})
        overall = metrics.get("overall_coverage", 0)

        lines = [f"Overall Coverage: {overall}%"]

        if competencies:
            lines.append("\nCompetency Coverage:")
            for comp, pct in competencies.items():
                status = "✓" if pct >= 80 else "!" if pct < 50 else "~"
                lines.append(f"  {status} {comp}: {pct}%")

        return "\n".join(lines)

    def _calculate_overall_score(self, competencies: List[Dict], summary: Dict) -> float:
        """Calculate overall candidate score"""
        if not competencies:
            # Use recommendation as fallback
            rec = summary.get("hiring_recommendation", "maybe")
            rec_map = {
                "strong_hire": 90,
                "hire": 75,
                "maybe": 55,
                "no_hire": 30
            }
            return rec_map.get(rec, 50)

        # Average of all competency scores
        scores = [c.get("overall_score", 0) for c in competencies]
        return sum(scores) / len(scores) if scores else 0.0

    def _fallback_summary(
        self,
        interview_data: Dict,
        candidate_data: Dict,
        competency_scores: List[Dict]
    ) -> Dict:
        """Generate basic summary when AI fails"""
        logger.warning("⚠️ Using fallback summary generation")

        overall_score = self._calculate_overall_score(competency_scores, {})

        # Determine recommendation based on score
        if overall_score >= 80:
            recommendation = "hire"
            confidence = 0.7
        elif overall_score >= 60:
            recommendation = "maybe"
            confidence = 0.6
        else:
            recommendation = "no_hire"
            confidence = 0.65

        return {
            "executive_summary": (
                f"Interview conducted for {interview_data.get('job_title', 'Unknown Position')}. "
                f"Candidate demonstrated {len(competency_scores)} evaluated competencies with "
                f"an average score of {overall_score:.1f}/100. "
                "Detailed AI analysis was unavailable for this interview."
            ),
            "key_highlights": [
                f"Overall competency score: {overall_score:.1f}/100",
                f"Number of competencies evaluated: {len(competency_scores)}",
                "AI-generated detailed analysis unavailable"
            ],
            "strengths": [
                {
                    "area": c.get("competency", "Unknown"),
                    "evidence": c.get("reasoning", "See detailed scores"),
                    "score": c.get("overall_score", 0),
                    "significance": "Demonstrated competency"
                }
                for c in sorted(competency_scores, key=lambda x: x.get("overall_score", 0), reverse=True)[:3]
            ],
            "weaknesses": [],
            "standout_moments": [],
            "concerns": [],
            "hiring_recommendation": recommendation,
            "recommendation_confidence": confidence,
            "recommendation_reasoning": (
                f"Based on average competency score of {overall_score:.1f}/100. "
                "Detailed analysis unavailable due to processing error."
            ),
            "next_steps": [
                "Review detailed competency scores",
                "Conduct reference checks",
                "Consider technical assessment if needed"
            ],
            "interview_quality_notes": "Standard interview process completed",
            "metadata": {
                "interview_id": interview_data.get("id"),
                "candidate_id": candidate_data.get("id"),
                "generated_at": datetime.now().isoformat(),
                "model_used": "fallback",
                "overall_score": overall_score,
                "duration_minutes": interview_data.get("duration_minutes", 0),
                "total_questions": 0,
                "fallback": True
            }
        }
