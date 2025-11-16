"""
Interview Quality Scorer - PILLAR 1.3

Provides real-time quality assessment of ongoing interviews.

Scores:
- Overall interview quality (0-100)
- Question quality
- Candidate engagement
- Interviewer effectiveness
- Time management
- Coverage breadth

Helps interviewers understand how well the interview is going.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Calculates real-time interview quality metrics
    Combines multiple factors to assess interview effectiveness
    """

    def __init__(self):
        """Initialize quality scorer"""
        self.scores_history: List[Dict] = []
        logger.info("✅ QualityScorer initialized")

    def calculate(
        self,
        duration_minutes: float,
        questions_asked: int,
        coverage_percentage: float,
        star_completion_rate: float,
        avg_question_difficulty: Optional[str] = None,
        avg_interviewer_tone: Optional[str] = None,
        red_flag_count: int = 0,
        topics_covered_count: int = 0
    ) -> Dict:
        """
        Calculate interview quality score

        Args:
            duration_minutes: Interview duration so far
            questions_asked: Number of questions asked
            coverage_percentage: Competency coverage (0-100)
            star_completion_rate: STAR completion rate (0-100)
            avg_question_difficulty: Average difficulty level
            avg_interviewer_tone: Average interviewer tone
            red_flag_count: Number of red flags detected
            topics_covered_count: Number of topics discussed

        Returns:
            Dict with quality metrics and overall score
        """
        logger.info(f"📊 Calculating interview quality score...")

        # Individual metrics (0-100 scale)
        metrics = {}

        # 1. Question Quality (based on difficulty and variety)
        metrics["question_quality"] = self._score_question_quality(
            questions_asked,
            avg_question_difficulty,
            topics_covered_count
        )

        # 2. Candidate Engagement (based on STAR completion and response depth)
        metrics["candidate_engagement"] = self._score_candidate_engagement(
            star_completion_rate,
            red_flag_count
        )

        # 3. Interviewer Effectiveness (based on tone and coverage)
        metrics["interviewer_effectiveness"] = self._score_interviewer_effectiveness(
            avg_interviewer_tone,
            coverage_percentage
        )

        # 4. Time Management
        metrics["time_management"] = self._score_time_management(
            duration_minutes,
            questions_asked,
            coverage_percentage
        )

        # 5. Coverage Breadth
        metrics["coverage_breadth"] = coverage_percentage

        # Calculate overall quality (weighted average)
        overall_quality = self._calculate_weighted_score(metrics)

        # Generate recommendations
        recommendations = self._generate_quality_recommendations(
            metrics,
            overall_quality
        )

        # Get quality rating
        rating = self._get_quality_rating(overall_quality)

        result = {
            "overall_quality": round(overall_quality, 1),
            "rating": rating,
            "metrics": {k: round(v, 1) for k, v in metrics.items()},
            "recommendations": recommendations,
            "calculated_at": datetime.utcnow().isoformat(),
            "interview_stage": self._get_interview_stage(duration_minutes)
        }

        # Store in history
        self.scores_history.append(result)

        logger.info(
            f"✅ Quality score calculated: {overall_quality:.1f}/100 ({rating})"
        )

        return result

    def _score_question_quality(
        self,
        questions_asked: int,
        avg_difficulty: Optional[str],
        topics_count: int
    ) -> float:
        """Score question quality (0-100)"""
        score = 50  # Base score

        # More questions generally better (up to a point)
        if questions_asked >= 5:
            score += 20
        elif questions_asked >= 3:
            score += 10

        # Difficulty level matters
        if avg_difficulty == "hard":
            score += 15
        elif avg_difficulty == "medium":
            score += 10
        elif avg_difficulty == "easy":
            score += 5

        # Topic variety is good
        if topics_count >= 5:
            score += 15
        elif topics_count >= 3:
            score += 10

        return min(100, score)

    def _score_candidate_engagement(
        self,
        star_completion_rate: float,
        red_flag_count: int
    ) -> float:
        """Score candidate engagement (0-100)"""
        # Start with STAR completion rate as base
        score = star_completion_rate

        # Penalty for red flags
        score -= (red_flag_count * 10)

        return max(0, min(100, score))

    def _score_interviewer_effectiveness(
        self,
        avg_tone: Optional[str],
        coverage: float
    ) -> float:
        """Score interviewer effectiveness (0-100)"""
        score = 50  # Base score

        # Good tone is important
        if avg_tone == "encouraging":
            score += 25
        elif avg_tone == "neutral":
            score += 15
        elif avg_tone == "harsh":
            score -= 20

        # Coverage indicates good questioning
        score += (coverage * 0.25)  # Up to 25 points from coverage

        return max(0, min(100, score))

    def _score_time_management(
        self,
        duration_minutes: float,
        questions_asked: int,
        coverage: float
    ) -> float:
        """Score time management (0-100)"""
        if duration_minutes == 0:
            return 50

        # Target: ~1 question per 5-8 minutes
        questions_per_minute = questions_asked / duration_minutes

        score = 50  # Base score

        # Optimal pace: 0.125 - 0.2 questions/minute (5-8 min per question)
        if 0.125 <= questions_per_minute <= 0.2:
            score += 30
        elif 0.1 <= questions_per_minute <= 0.25:
            score += 15

        # Good coverage in reasonable time
        if duration_minutes <= 45 and coverage >= 60:
            score += 20
        elif duration_minutes <= 60 and coverage >= 50:
            score += 10

        return min(100, score)

    def _calculate_weighted_score(self, metrics: Dict[str, float]) -> float:
        """Calculate weighted average of metrics"""
        weights = {
            "question_quality": 0.25,
            "candidate_engagement": 0.20,
            "interviewer_effectiveness": 0.20,
            "time_management": 0.15,
            "coverage_breadth": 0.20
        }

        weighted_sum = sum(
            metrics.get(metric, 50) * weight
            for metric, weight in weights.items()
        )

        return weighted_sum

    def _generate_quality_recommendations(
        self,
        metrics: Dict[str, float],
        overall: float
    ) -> List[str]:
        """Generate recommendations to improve quality"""
        recommendations = []

        # Check each metric
        if metrics.get("question_quality", 0) < 60:
            recommendations.append(
                "💡 Improve question quality: Ask more varied or challenging questions"
            )

        if metrics.get("candidate_engagement", 0) < 60:
            recommendations.append(
                "💡 Boost engagement: Encourage complete STAR answers with follow-ups"
            )

        if metrics.get("interviewer_effectiveness", 0) < 60:
            recommendations.append(
                "💡 Enhance effectiveness: Maintain encouraging tone and improve coverage"
            )

        if metrics.get("time_management", 0) < 60:
            recommendations.append(
                "💡 Improve pacing: Adjust time spent per question"
            )

        if metrics.get("coverage_breadth", 0) < 60:
            recommendations.append(
                "💡 Broaden coverage: Explore more competencies and topics"
            )

        # Overall feedback
        if overall >= 80:
            recommendations.insert(0, "✅ Excellent interview! Keep up the good work")
        elif overall >= 60:
            recommendations.insert(0, "👍 Good interview overall, minor improvements possible")
        elif overall < 50:
            recommendations.insert(0, "⚠️ Interview quality needs improvement - focus on key metrics")

        return recommendations[:5]  # Return top 5 recommendations

    def _get_quality_rating(self, score: float) -> str:
        """Get quality rating from score"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "very_poor"

    def _get_interview_stage(self, duration: float) -> str:
        """Determine interview stage based on duration"""
        if duration < 10:
            return "opening"
        elif duration < 30:
            return "middle"
        elif duration < 45:
            return "late"
        else:
            return "closing"

    def get_trend(self) -> Optional[str]:
        """
        Get quality trend from history

        Returns:
            "improving", "declining", "stable", or None
        """
        if len(self.scores_history) < 3:
            return None

        recent = [s["overall_quality"] for s in self.scores_history[-3:]]

        if recent[-1] > recent[0] + 5:
            return "improving"
        elif recent[-1] < recent[0] - 5:
            return "declining"
        else:
            return "stable"

    def reset(self):
        """Reset scorer for new interview"""
        self.scores_history = []
        logger.info("🔄 QualityScorer reset")
