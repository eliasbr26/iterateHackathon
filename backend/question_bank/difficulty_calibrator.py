"""
Difficulty Calibrator - PILLAR 3.2

Dynamically adjusts question difficulty based on candidate performance.

Progression Logic:
- Start with easy questions to build confidence
- Increase difficulty as candidate succeeds
- Decrease difficulty if candidate struggles
- Maintain optimal challenge level

Performance Metrics:
- STAR completion percentage
- Competency scores
- Response quality ratings
- Interviewer assessments
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class DifficultyCalibrator:
    """
    Tracks candidate performance and recommends difficulty adjustments
    Ensures optimal interview challenge level
    """

    # Difficulty levels
    DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

    # Performance thresholds
    EXCELLENT_THRESHOLD = 0.80  # 80%+ performance
    GOOD_THRESHOLD = 0.65       # 65%+ performance
    POOR_THRESHOLD = 0.45       # Below 45% is struggling

    # Progression rules
    QUESTIONS_BEFORE_INCREASE = 2  # Need 2 good answers before increasing
    QUESTIONS_BEFORE_DECREASE = 2  # Need 2 poor answers before decreasing

    def __init__(self, starting_difficulty: str = "easy"):
        """
        Initialize difficulty calibrator

        Args:
            starting_difficulty: Initial difficulty level (easy/medium/hard)
        """
        if starting_difficulty not in self.DIFFICULTY_LEVELS:
            logger.warning(f"Invalid starting difficulty: {starting_difficulty}, using 'easy'")
            starting_difficulty = "easy"

        self.current_difficulty = starting_difficulty
        self.performance_history: List[Dict] = []
        self.recent_performance = deque(maxlen=5)  # Track last 5 questions

        logger.info(f"✅ DifficultyCalibrator initialized (starting: {starting_difficulty})")

    def update_performance(
        self,
        question_difficulty: str,
        star_completion: Optional[float] = None,
        competency_score: Optional[float] = None,
        response_quality: Optional[str] = None,
        interviewer_rating: Optional[int] = None
    ) -> Dict:
        """
        Update performance tracking with latest question results

        Args:
            question_difficulty: Difficulty of the question asked
            star_completion: STAR completion percentage (0-100)
            competency_score: Competency score (0-100)
            response_quality: Quality rating (poor/fair/good/excellent)
            interviewer_rating: Interviewer's rating (1-5)

        Returns:
            Dict with updated performance summary
        """
        # Calculate normalized performance score (0-1)
        performance_score = self._calculate_performance_score(
            star_completion=star_completion,
            competency_score=competency_score,
            response_quality=response_quality,
            interviewer_rating=interviewer_rating
        )

        # Record performance
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question_difficulty": question_difficulty,
            "star_completion": star_completion,
            "competency_score": competency_score,
            "response_quality": response_quality,
            "interviewer_rating": interviewer_rating,
            "performance_score": performance_score,
            "difficulty_at_time": self.current_difficulty
        }

        self.performance_history.append(entry)
        self.recent_performance.append(performance_score)

        logger.info(
            f"📊 Performance updated: score={performance_score:.2f}, "
            f"difficulty={question_difficulty}"
        )

        return self.get_performance_summary()

    def get_next_difficulty(self) -> str:
        """
        Recommend difficulty level for next question

        Returns:
            Recommended difficulty (easy/medium/hard)
        """
        # Not enough data yet - stick with current
        if len(self.recent_performance) < 2:
            logger.info(f"💡 Insufficient data, maintaining {self.current_difficulty}")
            return self.current_difficulty

        # Calculate recent average performance
        recent_avg = sum(self.recent_performance) / len(self.recent_performance)

        # Get current difficulty index
        current_idx = self.DIFFICULTY_LEVELS.index(self.current_difficulty)

        # Determine if should increase, decrease, or maintain
        if recent_avg >= self.EXCELLENT_THRESHOLD and len(self.recent_performance) >= self.QUESTIONS_BEFORE_INCREASE:
            # Performing excellently - increase difficulty
            if current_idx < len(self.DIFFICULTY_LEVELS) - 1:
                new_difficulty = self.DIFFICULTY_LEVELS[current_idx + 1]
                logger.info(
                    f"📈 Strong performance ({recent_avg:.2f}) → "
                    f"increasing difficulty: {self.current_difficulty} → {new_difficulty}"
                )
                self.current_difficulty = new_difficulty
            else:
                logger.info(f"💪 Excellent performance at max difficulty: {self.current_difficulty}")

        elif recent_avg < self.POOR_THRESHOLD and len(self.recent_performance) >= self.QUESTIONS_BEFORE_DECREASE:
            # Struggling - decrease difficulty
            if current_idx > 0:
                new_difficulty = self.DIFFICULTY_LEVELS[current_idx - 1]
                logger.info(
                    f"📉 Struggling ({recent_avg:.2f}) → "
                    f"decreasing difficulty: {self.current_difficulty} → {new_difficulty}"
                )
                self.current_difficulty = new_difficulty
                # Clear recent history to give fresh start at new difficulty
                self.recent_performance.clear()
            else:
                logger.info(f"⚠️ Struggling at easiest difficulty: {self.current_difficulty}")

        else:
            # Performance is acceptable - maintain current level
            logger.info(
                f"✅ Maintaining {self.current_difficulty} difficulty "
                f"(performance: {recent_avg:.2f})"
            )

        return self.current_difficulty

    def _calculate_performance_score(
        self,
        star_completion: Optional[float],
        competency_score: Optional[float],
        response_quality: Optional[str],
        interviewer_rating: Optional[int]
    ) -> float:
        """
        Calculate normalized performance score (0-1) from multiple metrics

        Weighting:
        - STAR completion: 30%
        - Competency score: 30%
        - Response quality: 20%
        - Interviewer rating: 20%

        Args:
            star_completion: STAR completion (0-100)
            competency_score: Competency score (0-100)
            response_quality: Quality string (poor/fair/good/excellent)
            interviewer_rating: Rating (1-5)

        Returns:
            Normalized score (0-1)
        """
        scores = []
        weights = []

        # STAR completion (0-100 → 0-1)
        if star_completion is not None:
            scores.append(star_completion / 100.0)
            weights.append(0.30)

        # Competency score (0-100 → 0-1)
        if competency_score is not None:
            scores.append(competency_score / 100.0)
            weights.append(0.30)

        # Response quality (poor/fair/good/excellent → 0-1)
        if response_quality is not None:
            quality_map = {
                "poor": 0.25,
                "fair": 0.50,
                "good": 0.75,
                "excellent": 1.0
            }
            scores.append(quality_map.get(response_quality.lower(), 0.50))
            weights.append(0.20)

        # Interviewer rating (1-5 → 0-1)
        if interviewer_rating is not None:
            scores.append((interviewer_rating - 1) / 4.0)  # 1→0, 5→1
            weights.append(0.20)

        # If no metrics provided, return neutral score
        if not scores:
            logger.warning("No performance metrics provided, using neutral score")
            return 0.65  # Assume good performance

        # Calculate weighted average
        total_weight = sum(weights)
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        normalized_score = weighted_sum / total_weight if total_weight > 0 else 0.65

        return normalized_score

    def get_performance_summary(self) -> Dict:
        """
        Get comprehensive performance summary

        Returns:
            Dict with performance metrics and recommendations
        """
        if not self.performance_history:
            return {
                "total_questions": 0,
                "current_difficulty": self.current_difficulty,
                "average_performance": None,
                "recent_performance": None,
                "trend": "insufficient_data",
                "recommendation": self.current_difficulty
            }

        # Calculate averages
        all_scores = [entry["performance_score"] for entry in self.performance_history]
        average_performance = sum(all_scores) / len(all_scores)

        recent_avg = (
            sum(self.recent_performance) / len(self.recent_performance)
            if self.recent_performance else None
        )

        # Determine trend
        trend = self._calculate_trend()

        # Get next difficulty recommendation
        next_difficulty = self.get_next_difficulty()

        return {
            "total_questions": len(self.performance_history),
            "current_difficulty": self.current_difficulty,
            "average_performance": round(average_performance, 2),
            "recent_performance": round(recent_avg, 2) if recent_avg is not None else None,
            "recent_questions_tracked": len(self.recent_performance),
            "trend": trend,
            "recommendation": next_difficulty,
            "performance_level": self._get_performance_level(recent_avg or average_performance)
        }

    def _calculate_trend(self) -> str:
        """
        Calculate performance trend

        Returns:
            "improving", "declining", "stable", or "insufficient_data"
        """
        if len(self.performance_history) < 4:
            return "insufficient_data"

        # Compare first half vs second half
        scores = [entry["performance_score"] for entry in self.performance_history]
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

        diff = second_half_avg - first_half_avg

        if diff > 0.10:
            return "improving"
        elif diff < -0.10:
            return "declining"
        else:
            return "stable"

    def _get_performance_level(self, score: float) -> str:
        """
        Get performance level label

        Args:
            score: Performance score (0-1)

        Returns:
            Performance level string
        """
        if score >= self.EXCELLENT_THRESHOLD:
            return "excellent"
        elif score >= self.GOOD_THRESHOLD:
            return "good"
        elif score >= self.POOR_THRESHOLD:
            return "fair"
        else:
            return "struggling"

    def reset(self):
        """Reset calibrator for new interview"""
        self.current_difficulty = "easy"
        self.performance_history = []
        self.recent_performance.clear()
        logger.info("🔄 DifficultyCalibrator reset")

    def get_difficulty_breakdown(self) -> Dict:
        """
        Get breakdown of performance by difficulty level

        Returns:
            Dict mapping difficulty -> average performance
        """
        breakdown = {level: [] for level in self.DIFFICULTY_LEVELS}

        for entry in self.performance_history:
            difficulty = entry["question_difficulty"]
            if difficulty in breakdown:
                breakdown[difficulty].append(entry["performance_score"])

        # Calculate averages
        result = {}
        for difficulty, scores in breakdown.items():
            if scores:
                result[difficulty] = {
                    "count": len(scores),
                    "average": round(sum(scores) / len(scores), 2),
                    "min": round(min(scores), 2),
                    "max": round(max(scores), 2)
                }
            else:
                result[difficulty] = {
                    "count": 0,
                    "average": None,
                    "min": None,
                    "max": None
                }

        return result

    def should_increase_difficulty(self) -> bool:
        """
        Check if difficulty should be increased

        Returns:
            True if should increase, False otherwise
        """
        if len(self.recent_performance) < self.QUESTIONS_BEFORE_INCREASE:
            return False

        recent_avg = sum(self.recent_performance) / len(self.recent_performance)
        current_idx = self.DIFFICULTY_LEVELS.index(self.current_difficulty)

        return (
            recent_avg >= self.EXCELLENT_THRESHOLD and
            current_idx < len(self.DIFFICULTY_LEVELS) - 1
        )

    def should_decrease_difficulty(self) -> bool:
        """
        Check if difficulty should be decreased

        Returns:
            True if should decrease, False otherwise
        """
        if len(self.recent_performance) < self.QUESTIONS_BEFORE_DECREASE:
            return False

        recent_avg = sum(self.recent_performance) / len(self.recent_performance)
        current_idx = self.DIFFICULTY_LEVELS.index(self.current_difficulty)

        return (
            recent_avg < self.POOR_THRESHOLD and
            current_idx > 0
        )
