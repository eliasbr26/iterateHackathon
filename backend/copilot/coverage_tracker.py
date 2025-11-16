"""
Coverage Tracker - PILLAR 1.2

Tracks topic and competency coverage during live interviews in real-time.

Monitors:
- Which competencies have been discussed (Leadership, Communication, etc.)
- Technical topics covered
- STAR method coverage
- Interview breadth vs depth
- Missing areas that should be explored

Helps interviewers ensure comprehensive candidate evaluation.
"""

import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class CoverageTracker:
    """
    Tracks interview coverage in real-time
    Monitors competencies, topics, and identifies gaps
    """

    # 10 Core Competencies from Phase 2
    CORE_COMPETENCIES = [
        "leadership",
        "communication",
        "technical_depth",
        "problem_solving",
        "ownership",
        "adaptability",
        "strategic_thinking",
        "creativity",
        "teamwork",
        "culture_fit"
    ]

    # Common technical topics for quant/tech interviews
    TECHNICAL_TOPICS = [
        "algorithms",
        "data_structures",
        "system_design",
        "coding",
        "databases",
        "optimization",
        "architecture",
        "testing",
        "deployment",
        "performance"
    ]

    def __init__(self):
        """Initialize coverage tracker"""
        # Competency coverage: competency -> score (0-100)
        self.competency_coverage: Dict[str, float] = {
            comp: 0.0 for comp in self.CORE_COMPETENCIES
        }

        # Topics discussed
        self.topics_covered: Set[str] = set()

        # Question count
        self.questions_asked = 0
        self.behavioral_questions = 0
        self.technical_questions = 0

        # STAR coverage
        self.star_attempts = 0
        self.complete_star_answers = 0

        # Time tracking
        self.start_time = datetime.utcnow()
        self.last_update = datetime.utcnow()

        logger.info("✅ CoverageTracker initialized")

    def update(
        self,
        topics: Optional[List[str]] = None,
        competencies: Optional[Dict[str, float]] = None,
        question_type: Optional[str] = None,
        star_complete: Optional[bool] = None
    ) -> Dict:
        """
        Update coverage based on new information

        Args:
            topics: New topics discussed
            competencies: Competency scores from recent exchange
            question_type: Type of question (behavioral/technical/other)
            star_complete: Whether STAR answer was complete

        Returns:
            Current coverage state
        """
        self.last_update = datetime.utcnow()

        # Update topics
        if topics:
            self.topics_covered.update(topics)

        # Update competencies
        if competencies:
            for comp, score in competencies.items():
                if comp in self.competency_coverage:
                    # Take max score seen so far
                    self.competency_coverage[comp] = max(
                        self.competency_coverage[comp],
                        score
                    )

        # Update question counts
        if question_type:
            self.questions_asked += 1
            if question_type == "behavioral":
                self.behavioral_questions += 1
            elif question_type == "technical":
                self.technical_questions += 1

        # Update STAR tracking
        if star_complete is not None:
            self.star_attempts += 1
            if star_complete:
                self.complete_star_answers += 1

        return self.get_coverage()

    def get_coverage(self) -> Dict:
        """
        Get current coverage state

        Returns:
            Dict with coverage metrics, gaps, and recommendations
        """
        # Calculate overall coverage percentage
        comp_scores = list(self.competency_coverage.values())
        overall_coverage = sum(comp_scores) / len(comp_scores) if comp_scores else 0

        # Identify gaps (competencies with low coverage)
        gaps = [
            comp for comp, score in self.competency_coverage.items()
            if score < 30  # Less than 30% coverage
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps)

        # Calculate duration
        duration_minutes = (self.last_update - self.start_time).total_seconds() / 60

        return {
            "overall_coverage": round(overall_coverage, 1),
            "competency_coverage": {
                comp: round(score, 1)
                for comp, score in self.competency_coverage.items()
            },
            "topics_covered": list(self.topics_covered),
            "topic_count": len(self.topics_covered),
            "gaps": gaps,
            "recommendations": recommendations,
            "metrics": {
                "total_questions": self.questions_asked,
                "behavioral_questions": self.behavioral_questions,
                "technical_questions": self.technical_questions,
                "star_attempts": self.star_attempts,
                "complete_star_answers": self.complete_star_answers,
                "star_completion_rate": round(
                    (self.complete_star_answers / self.star_attempts * 100)
                    if self.star_attempts > 0 else 0,
                    1
                ),
                "duration_minutes": round(duration_minutes, 1)
            },
            "status": self._get_coverage_status(overall_coverage),
            "last_updated": self.last_update.isoformat()
        }

    def _generate_recommendations(self, gaps: List[str]) -> List[str]:
        """
        Generate recommendations based on coverage gaps

        Args:
            gaps: List of competencies with low coverage

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not gaps:
            recommendations.append("✅ Good coverage across all competencies!")
            return recommendations

        # Prioritize top 3 gaps
        top_gaps = gaps[:3]

        recommendation_templates = {
            "leadership": "Ask about times they led a team or made important decisions",
            "communication": "Explore how they explain complex concepts or handle difficult conversations",
            "technical_depth": "Dig deeper into technical implementations and trade-offs",
            "problem_solving": "Ask about challenging problems they've solved",
            "ownership": "Explore their sense of responsibility and accountability",
            "adaptability": "Ask how they've handled change or learned new skills quickly",
            "strategic_thinking": "Discuss long-term planning and business impact",
            "creativity": "Ask about innovative solutions or novel approaches they've used",
            "teamwork": "Explore collaboration and working with diverse teams",
            "culture_fit": "Assess values alignment and work style preferences"
        }

        for gap in top_gaps:
            if gap in recommendation_templates:
                recommendations.append(f"📌 {gap.replace('_', ' ').title()}: {recommendation_templates[gap]}")

        # Add general recommendations
        if self.questions_asked < 5:
            recommendations.append("⏱️ Still early in interview - continue exploring different areas")

        if self.behavioral_questions < 2:
            recommendations.append("💬 Ask more behavioral questions (STAR format)")

        if self.technical_questions < 2:
            recommendations.append("🔧 Explore technical depth more thoroughly")

        if self.star_attempts > 0 and (self.complete_star_answers / self.star_attempts) < 0.5:
            recommendations.append("⭐ Encourage more complete STAR answers with follow-ups")

        return recommendations

    def _get_coverage_status(self, coverage: float) -> str:
        """
        Get coverage status based on percentage

        Args:
            coverage: Overall coverage percentage

        Returns:
            Status string
        """
        if coverage >= 80:
            return "excellent"
        elif coverage >= 60:
            return "good"
        elif coverage >= 40:
            return "moderate"
        elif coverage >= 20:
            return "limited"
        else:
            return "minimal"

    def get_next_focus_area(self) -> Optional[str]:
        """
        Get the next competency that should be explored

        Returns:
            Competency name or None
        """
        # Find competency with lowest coverage
        sorted_comps = sorted(
            self.competency_coverage.items(),
            key=lambda x: x[1]
        )

        if sorted_comps and sorted_comps[0][1] < 50:
            return sorted_comps[0][0]

        return None

    def reset(self):
        """Reset tracker for a new interview"""
        self.__init__()
        logger.info("🔄 CoverageTracker reset")

    def get_summary(self) -> str:
        """
        Get human-readable coverage summary

        Returns:
            Summary string
        """
        coverage = self.get_coverage()

        summary_parts = [
            f"Overall Coverage: {coverage['overall_coverage']}% ({coverage['status']})",
            f"Questions Asked: {coverage['metrics']['total_questions']}",
            f"Topics Covered: {coverage['topic_count']}",
        ]

        if coverage['gaps']:
            summary_parts.append(f"Gaps: {', '.join(coverage['gaps'][:3])}")

        return " | ".join(summary_parts)
