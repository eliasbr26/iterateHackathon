"""
Question Selector - PILLAR 3.3

Intelligently selects the best question from available options based on:
- Coverage gaps (missing competencies)
- Difficulty level (from calibrator)
- Interview balance (behavioral vs technical)
- Candidate background relevance
- Already-asked questions (avoid repetition)

Selection Strategy:
1. Identify coverage gaps (competencies < 30%)
2. Match target difficulty level
3. Balance question types
4. Prioritize candidate-relevant questions
5. Avoid repetition
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class QuestionSelector:
    """
    Intelligently selects interview questions based on context
    Optimizes for coverage, difficulty, and candidate fit
    """

    # Coverage thresholds
    URGENT_COVERAGE_THRESHOLD = 0.20  # < 20% coverage
    HIGH_PRIORITY_THRESHOLD = 0.50    # < 50% coverage
    MEDIUM_PRIORITY_THRESHOLD = 0.80  # < 80% coverage

    # Balance targets
    BEHAVIORAL_TARGET = 0.60  # 60% behavioral questions
    TECHNICAL_TARGET = 0.30   # 30% technical questions
    SITUATIONAL_TARGET = 0.10  # 10% situational questions

    def __init__(self):
        """Initialize question selector"""
        self.asked_questions: Set[str] = set()  # Track asked question IDs/text
        self.question_history: List[Dict] = []
        self.type_counts = {"behavioral": 0, "technical": 0, "situational": 0}

        logger.info("✅ QuestionSelector initialized")

    async def select_question(
        self,
        question_bank: List[Dict],
        coverage: Dict,
        target_difficulty: str,
        candidate_profile: Optional[Dict] = None,
        interview_duration_minutes: float = 0
    ) -> Optional[Dict]:
        """
        Select best question from available options

        Args:
            question_bank: List of available questions
            coverage: Coverage data from CoverageTracker
            target_difficulty: Desired difficulty (from DifficultyCalibrator)
            candidate_profile: Candidate background data
            interview_duration_minutes: How long interview has been going

        Returns:
            Selected question dict or None if no suitable question found
        """
        logger.info(
            f"🎯 Selecting question (difficulty: {target_difficulty}, "
            f"duration: {interview_duration_minutes:.1f}m)"
        )

        if not question_bank:
            logger.warning("❌ Empty question bank provided")
            return None

        # Filter out already-asked questions
        available_questions = [
            q for q in question_bank
            if self._get_question_id(q) not in self.asked_questions
        ]

        if not available_questions:
            logger.warning("⚠️ All questions have been asked, allowing repeats")
            available_questions = question_bank

        # Score each question
        scored_questions = []
        for question in available_questions:
            score = self._score_question(
                question=question,
                coverage=coverage,
                target_difficulty=target_difficulty,
                candidate_profile=candidate_profile,
                interview_duration_minutes=interview_duration_minutes
            )
            scored_questions.append((score, question))

        # Sort by score (descending)
        scored_questions.sort(key=lambda x: x[0], reverse=True)

        # Log top 3 candidates
        logger.info(f"📊 Top question candidates:")
        for i, (score, q) in enumerate(scored_questions[:3], 1):
            logger.info(
                f"  {i}. [{score:.2f}] {q.get('competency', 'N/A')} - "
                f"{q.get('difficulty', 'N/A')} - {q.get('type', 'N/A')}"
            )

        # Select top question
        if scored_questions:
            best_score, best_question = scored_questions[0]

            # Add selection reasoning
            best_question["selection_reasoning"] = self._explain_selection(
                question=best_question,
                score=best_score,
                coverage=coverage,
                target_difficulty=target_difficulty
            )

            # Mark as used
            self._mark_question_used(best_question)

            logger.info(
                f"✅ Selected question: {best_question.get('competency', 'N/A')} "
                f"({best_question.get('difficulty', 'N/A')}, score: {best_score:.2f})"
            )

            return best_question

        logger.warning("❌ No suitable question found")
        return None

    def _score_question(
        self,
        question: Dict,
        coverage: Dict,
        target_difficulty: str,
        candidate_profile: Optional[Dict],
        interview_duration_minutes: float
    ) -> float:
        """
        Score a question based on multiple factors

        Scoring components:
        - Coverage gap priority (0-40 points)
        - Difficulty match (0-25 points)
        - Type balance (0-15 points)
        - Candidate relevance (0-10 points)
        - Interview stage fit (0-10 points)

        Args:
            question: Question to score
            coverage: Current coverage state
            target_difficulty: Desired difficulty
            candidate_profile: Candidate background
            interview_duration_minutes: Interview duration

        Returns:
            Total score (0-100)
        """
        score = 0.0

        # 1. Coverage Gap Priority (0-40 points)
        competency = question.get("competency", "").lower()
        competency_coverage = coverage.get("competency_coverage", {}).get(competency, 0)

        if competency_coverage < self.URGENT_COVERAGE_THRESHOLD * 100:
            score += 40  # Urgent gap
        elif competency_coverage < self.HIGH_PRIORITY_THRESHOLD * 100:
            score += 30  # High priority
        elif competency_coverage < self.MEDIUM_PRIORITY_THRESHOLD * 100:
            score += 20  # Medium priority
        else:
            score += 10  # Low priority (already well-covered)

        # 2. Difficulty Match (0-25 points)
        question_difficulty = question.get("difficulty", "medium").lower()
        if question_difficulty == target_difficulty.lower():
            score += 25  # Perfect match
        elif abs(
            self._difficulty_index(question_difficulty) -
            self._difficulty_index(target_difficulty)
        ) == 1:
            score += 15  # One level off
        else:
            score += 5  # Two levels off

        # 3. Type Balance (0-15 points)
        question_type = question.get("type", "behavioral").lower()
        type_balance_score = self._calculate_type_balance_score(question_type)
        score += type_balance_score

        # 4. Candidate Relevance (0-10 points)
        if candidate_profile:
            relevance_score = self._calculate_candidate_relevance(
                question, candidate_profile
            )
            score += relevance_score
        else:
            score += 5  # Neutral if no profile

        # 5. Interview Stage Fit (0-10 points)
        stage_score = self._calculate_stage_fit(
            question, interview_duration_minutes
        )
        score += stage_score

        return score

    def _difficulty_index(self, difficulty: str) -> int:
        """Get numeric index for difficulty level"""
        difficulty_map = {"easy": 0, "medium": 1, "hard": 2}
        return difficulty_map.get(difficulty.lower(), 1)

    def _calculate_type_balance_score(self, question_type: str) -> float:
        """
        Calculate score based on question type balance

        Returns:
            Score (0-15) based on how well this type fits target balance
        """
        total_questions = sum(self.type_counts.values()) or 1
        current_ratios = {
            qtype: count / total_questions
            for qtype, count in self.type_counts.items()
        }

        targets = {
            "behavioral": self.BEHAVIORAL_TARGET,
            "technical": self.TECHNICAL_TARGET,
            "situational": self.SITUATIONAL_TARGET
        }

        current_ratio = current_ratios.get(question_type, 0)
        target_ratio = targets.get(question_type, 0.33)

        # Score higher if we're below target ratio
        if current_ratio < target_ratio:
            return 15  # Need more of this type
        elif current_ratio < target_ratio + 0.10:
            return 10  # Close to target
        else:
            return 5  # Over target

    def _calculate_candidate_relevance(
        self,
        question: Dict,
        candidate_profile: Dict
    ) -> float:
        """
        Calculate how relevant question is to candidate background

        Args:
            question: Question to evaluate
            candidate_profile: Candidate data

        Returns:
            Relevance score (0-10)
        """
        score = 5.0  # Base score

        # Check if question topics match candidate's experience
        question_topics = set(question.get("topics", []))
        if not question_topics:
            return score

        # Extract candidate skills/experience
        candidate_skills = set()
        if "skills" in candidate_profile:
            skills = candidate_profile["skills"]
            candidate_skills.update(skills.get("technical_skills", []))
            candidate_skills.update(skills.get("soft_skills", []))

        if "experience" in candidate_profile:
            exp = candidate_profile["experience"]
            candidate_skills.update(exp.get("domains", []))
            candidate_skills.update(exp.get("technologies", []))

        # Calculate overlap
        overlap = question_topics.intersection(
            {s.lower() for s in candidate_skills}
        )

        if overlap:
            # More overlap = more relevant
            overlap_ratio = len(overlap) / len(question_topics)
            score += 5 * overlap_ratio  # Up to +5 points

        return min(score, 10)

    def _calculate_stage_fit(
        self,
        question: Dict,
        interview_duration_minutes: float
    ) -> float:
        """
        Calculate how well question fits current interview stage

        Stages:
        - Opening (0-10m): Easy, warm-up questions
        - Middle (10-30m): Core questions, balanced difficulty
        - Deep Dive (30-45m): Hard questions, probe depth
        - Closing (45m+): Wrap-up, candidate questions

        Args:
            question: Question to evaluate
            interview_duration_minutes: Current duration

        Returns:
            Stage fit score (0-10)
        """
        difficulty = question.get("difficulty", "medium").lower()

        if interview_duration_minutes < 10:
            # Opening: prefer easy questions
            if difficulty == "easy":
                return 10
            elif difficulty == "medium":
                return 5
            else:
                return 2

        elif interview_duration_minutes < 30:
            # Middle: any difficulty works
            return 8

        elif interview_duration_minutes < 45:
            # Deep dive: prefer medium/hard
            if difficulty == "hard":
                return 10
            elif difficulty == "medium":
                return 7
            else:
                return 4

        else:
            # Closing: prefer easier, wrap-up questions
            if difficulty == "easy" or difficulty == "medium":
                return 10
            else:
                return 6

    def _explain_selection(
        self,
        question: Dict,
        score: float,
        coverage: Dict,
        target_difficulty: str
    ) -> str:
        """
        Generate human-readable explanation for why this question was selected

        Args:
            question: Selected question
            score: Question score
            coverage: Coverage data
            target_difficulty: Target difficulty

        Returns:
            Explanation string
        """
        reasons = []

        # Coverage reason
        competency = question.get("competency", "unknown")
        competency_coverage = coverage.get("competency_coverage", {}).get(competency, 0)

        if competency_coverage < 20:
            reasons.append(f"URGENT: {competency} competency has only {competency_coverage:.0f}% coverage")
        elif competency_coverage < 50:
            reasons.append(f"Targeting {competency} competency (current coverage: {competency_coverage:.0f}%)")
        else:
            reasons.append(f"Deepening {competency} assessment (coverage: {competency_coverage:.0f}%)")

        # Difficulty reason
        question_difficulty = question.get("difficulty", "medium")
        if question_difficulty == target_difficulty:
            reasons.append(f"Matches target difficulty: {target_difficulty}")
        else:
            reasons.append(f"Difficulty: {question_difficulty} (target: {target_difficulty})")

        # Type balance reason
        question_type = question.get("type", "behavioral")
        total_questions = sum(self.type_counts.values()) or 1
        type_ratio = self.type_counts.get(question_type, 0) / total_questions
        target_ratio = {
            "behavioral": 0.60,
            "technical": 0.30,
            "situational": 0.10
        }.get(question_type, 0.33)

        if type_ratio < target_ratio:
            reasons.append(f"Balancing question types ({question_type}: {type_ratio:.0%} of {target_ratio:.0%} target)")

        return " | ".join(reasons)

    def _get_question_id(self, question: Dict) -> str:
        """Get unique identifier for a question"""
        # Use question ID if available, otherwise hash of question text
        if "id" in question:
            return str(question["id"])
        return question.get("question", "")[:100]  # First 100 chars

    def _mark_question_used(self, question: Dict):
        """Mark a question as used"""
        question_id = self._get_question_id(question)
        self.asked_questions.add(question_id)

        # Update type counts
        question_type = question.get("type", "behavioral").lower()
        self.type_counts[question_type] = self.type_counts.get(question_type, 0) + 1

        # Add to history
        self.question_history.append({
            "question_id": question_id,
            "competency": question.get("competency"),
            "difficulty": question.get("difficulty"),
            "type": question.get("type"),
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"📝 Marked question as used: {question_id}")

    def get_selection_stats(self) -> Dict:
        """
        Get statistics about question selection

        Returns:
            Dict with selection metrics
        """
        total_questions = len(self.question_history)

        if total_questions == 0:
            return {
                "total_questions_asked": 0,
                "type_distribution": {},
                "competency_distribution": {},
                "difficulty_distribution": {}
            }

        # Type distribution
        type_dist = {}
        for qtype, count in self.type_counts.items():
            type_dist[qtype] = {
                "count": count,
                "percentage": round((count / total_questions) * 100, 1)
            }

        # Competency distribution
        comp_counts = {}
        for entry in self.question_history:
            comp = entry.get("competency", "unknown")
            comp_counts[comp] = comp_counts.get(comp, 0) + 1

        comp_dist = {
            comp: {
                "count": count,
                "percentage": round((count / total_questions) * 100, 1)
            }
            for comp, count in comp_counts.items()
        }

        # Difficulty distribution
        diff_counts = {}
        for entry in self.question_history:
            diff = entry.get("difficulty", "unknown")
            diff_counts[diff] = diff_counts.get(diff, 0) + 1

        diff_dist = {
            diff: {
                "count": count,
                "percentage": round((count / total_questions) * 100, 1)
            }
            for diff, count in diff_counts.items()
        }

        return {
            "total_questions_asked": total_questions,
            "type_distribution": type_dist,
            "competency_distribution": comp_dist,
            "difficulty_distribution": diff_dist
        }

    def reset(self):
        """Reset selector for new interview"""
        self.asked_questions.clear()
        self.question_history = []
        self.type_counts = {"behavioral": 0, "technical": 0, "situational": 0}
        logger.info("🔄 QuestionSelector reset")

    def get_next_recommended_competency(self, coverage: Dict) -> Optional[str]:
        """
        Get the competency that should be targeted next

        Args:
            coverage: Coverage data from CoverageTracker

        Returns:
            Competency name or None
        """
        competency_coverage = coverage.get("competency_coverage", {})

        if not competency_coverage:
            return None

        # Find competency with lowest coverage
        sorted_comps = sorted(
            competency_coverage.items(),
            key=lambda x: x[1]
        )

        if sorted_comps and sorted_comps[0][1] < 80:  # If lowest is still < 80%
            return sorted_comps[0][0]

        return None
