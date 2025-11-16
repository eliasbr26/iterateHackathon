"""
Question Quality Checker - PILLAR 4.3
Evaluates the quality of interviewer questions in real-time
"""

import json
import logging
from typing import Dict, List, Optional
from collections import Counter

import anthropic

logger = logging.getLogger(__name__)


class QuestionQualityChecker:
    """
    Evaluates question quality using Claude AI

    Features:
    - Detects leading questions
    - Identifies yes/no questions (low quality for behavioral)
    - Flags unclear/compound questions
    - Suggests improvements
    - Quality score (0-100)
    """

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 700
    TEMPERATURE = 0.3

    # Quality thresholds
    EXCELLENT_THRESHOLD = 90
    GOOD_THRESHOLD = 70
    FAIR_THRESHOLD = 50

    QUALITY_CHECK_PROMPT = """Evaluate the quality of this interview question.

Question: "{question}"
Interview Type: {interview_type}
Expected Answer Type: {expected_type}

Check for these quality issues:
1. Leading question (suggests desired answer or contains bias)
2. Yes/No question (for behavioral interviews, these limit detailed responses)
3. Compound question (asks multiple things at once, confusing)
4. Unclear/ambiguous phrasing
5. Too broad/vague (candidate won't know what you want)
6. Too narrow/specific (limits valuable discussion)

Respond in valid JSON format only (no markdown, no code blocks):
{{
    "quality_score": 0-100,
    "quality_rating": "poor" | "fair" | "good" | "excellent",
    "issues": [
        {{
            "type": "leading" | "yes_no" | "compound" | "unclear" | "too_broad" | "too_narrow",
            "severity": "low" | "medium" | "high",
            "explanation": "Why this is an issue"
        }}
    ],
    "improved_version": "Suggested rewrite (empty string if no issues)",
    "strengths": ["Positive aspects of the question"]
}}

Quality scoring guide:
- 90-100 (excellent): Open-ended, clear, STAR-friendly, encourages detailed responses
- 70-89 (good): Minor issues but mostly effective
- 50-69 (fair): Some significant issues, needs improvement
- 0-49 (poor): Major issues, ineffective question"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize question quality checker

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Track quality scores for statistics
        self.quality_scores: List[int] = []
        self.issue_counts: Counter = Counter()

        logger.info(f"✅ QuestionQualityChecker initialized with model: {model}")

    async def check(
        self,
        question: str,
        interview_type: str = "behavioral",
        expected_type: str = "detailed behavioral response"
    ) -> Dict:
        """
        Check the quality of an interview question

        Args:
            question: The question text
            interview_type: Type of interview (behavioral, technical, etc.)
            expected_type: What kind of answer is expected

        Returns:
            Quality analysis with score, issues, and suggestions
        """
        try:
            # Prepare prompt
            prompt = self.QUALITY_CHECK_PROMPT.format(
                question=question,
                interview_type=interview_type,
                expected_type=expected_type
            )

            logger.info(f"🔍 Checking quality for: {question[:50]}...")

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

            result = json.loads(response_text)

            # Validate and normalize
            quality_score = max(0, min(100, result.get("quality_score", 50)))
            quality_rating = result.get("quality_rating", "fair")

            # Track statistics
            self.quality_scores.append(quality_score)
            for issue in result.get("issues", []):
                self.issue_counts[issue["type"]] += 1

            # Generate alert if needed
            alert = self._generate_alert(quality_score, result.get("issues", []))

            # Build final result
            analysis = {
                "quality_score": quality_score,
                "quality_rating": quality_rating,
                "issues": result.get("issues", []),
                "improved_version": result.get("improved_version", ""),
                "strengths": result.get("strengths", []),
                "alert": alert,
                "average_quality": self.get_average_quality()
            }

            logger.info(
                f"✅ Quality: {quality_score}/100 ({quality_rating}) | "
                f"Issues: {len(result.get('issues', []))}"
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse quality check JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return self._fallback_check(question, interview_type)

        except Exception as e:
            logger.error(f"❌ Quality check failed: {e}", exc_info=True)
            return self._fallback_check(question, interview_type)

    def get_quality_summary(self) -> Dict:
        """
        Get summary of question quality across interview

        Returns:
            Summary statistics and recommendations
        """
        if not self.quality_scores:
            return {
                "status": "no_data",
                "message": "No questions analyzed yet"
            }

        avg_quality = sum(self.quality_scores) / len(self.quality_scores)

        # Count by rating
        rating_counts = {
            "excellent": sum(1 for s in self.quality_scores if s >= self.EXCELLENT_THRESHOLD),
            "good": sum(1 for s in self.quality_scores
                       if self.GOOD_THRESHOLD <= s < self.EXCELLENT_THRESHOLD),
            "fair": sum(1 for s in self.quality_scores
                       if self.FAIR_THRESHOLD <= s < self.GOOD_THRESHOLD),
            "poor": sum(1 for s in self.quality_scores if s < self.FAIR_THRESHOLD)
        }

        # Determine overall quality
        if avg_quality >= self.EXCELLENT_THRESHOLD:
            overall = "excellent"
        elif avg_quality >= self.GOOD_THRESHOLD:
            overall = "good"
        elif avg_quality >= self.FAIR_THRESHOLD:
            overall = "fair"
        else:
            overall = "poor"

        # Get top issues
        top_issues = self.issue_counts.most_common(3)

        # Generate recommendation
        recommendation = self._get_quality_recommendation(avg_quality, top_issues)

        return {
            "total_questions_analyzed": len(self.quality_scores),
            "average_quality": round(avg_quality, 1),
            "overall_rating": overall,
            "rating_distribution": rating_counts,
            "top_issues": [
                {"type": issue, "count": count}
                for issue, count in top_issues
            ],
            "recommendation": recommendation
        }

    def get_average_quality(self) -> float:
        """Get current average quality score"""
        if not self.quality_scores:
            return 0.0
        return round(sum(self.quality_scores) / len(self.quality_scores), 1)

    def reset(self):
        """Reset quality tracking for a new interview"""
        self.quality_scores.clear()
        self.issue_counts.clear()
        logger.info("🔄 QuestionQualityChecker reset")

    # Private helper methods

    def _generate_alert(self, quality_score: int, issues: List[Dict]) -> Optional[Dict]:
        """
        Generate alert if quality needs attention

        Args:
            quality_score: The quality score (0-100)
            issues: List of identified issues

        Returns:
            Alert dict or None
        """
        # High severity alert for poor quality
        if quality_score < self.FAIR_THRESHOLD:
            high_severity_issues = [
                i for i in issues if i.get("severity") == "high"
            ]
            if high_severity_issues:
                return {
                    "severity": "high",
                    "message": f"Low quality question (score: {quality_score}/100). "
                               f"Major issues detected: {', '.join(i['type'] for i in high_severity_issues)}",
                    "action": "revise_question"
                }

        # Medium severity for fair quality
        if quality_score < self.GOOD_THRESHOLD and issues:
            return {
                "severity": "medium",
                "message": f"Question quality could be improved (score: {quality_score}/100). "
                           f"Consider addressing: {issues[0]['type']}",
                "action": "review_question"
            }

        # Low severity for repeated issues
        if len(self.quality_scores) >= 5:
            recent_scores = self.quality_scores[-5:]
            if sum(s < self.GOOD_THRESHOLD for s in recent_scores) >= 3:
                return {
                    "severity": "low",
                    "message": "3 of last 5 questions were below 'good' quality. "
                               "Consider taking more time to craft questions.",
                    "action": "slow_down"
                }

        return None

    def _get_quality_recommendation(
        self,
        avg_quality: float,
        top_issues: List[tuple]
    ) -> str:
        """Generate overall quality recommendation"""
        if avg_quality >= self.EXCELLENT_THRESHOLD:
            return (
                "Excellent question quality! Your questions are well-crafted, "
                "open-ended, and effective at drawing out detailed responses."
            )

        if avg_quality >= self.GOOD_THRESHOLD:
            if top_issues:
                top_issue = top_issues[0][0]
                return (
                    f"Good overall quality. Your most common issue is '{top_issue}'. "
                    f"Focus on addressing this to reach excellent quality."
                )
            return "Good question quality overall. Keep up the strong work!"

        if avg_quality >= self.FAIR_THRESHOLD:
            issue_str = ", ".join(issue for issue, _ in top_issues)
            return (
                f"Fair quality overall. Common issues: {issue_str}. "
                "Take more time to craft open-ended, clear questions."
            )

        # Poor quality
        return (
            "⚠️ Question quality needs significant improvement. "
            "Focus on asking open-ended questions that encourage detailed responses. "
            "Avoid yes/no questions and leading phrasing."
        )

    def _fallback_check(self, question: str, interview_type: str) -> Dict:
        """
        Fallback quality check using simple heuristics

        Args:
            question: The question text
            interview_type: Type of interview

        Returns:
            Basic quality analysis
        """
        question_lower = question.lower().strip()
        issues = []
        strengths = []
        score = 70  # Start at fair-good quality

        # Check for yes/no question (starts with do/does/did/is/are/can/could/would/will)
        yes_no_starters = [
            "do ", "does ", "did ", "is ", "are ", "was ", "were ",
            "can ", "could ", "would ", "will ", "shall ", "should ",
            "have ", "has ", "had "
        ]
        if any(question_lower.startswith(s) for s in yes_no_starters):
            issues.append({
                "type": "yes_no",
                "severity": "high" if interview_type == "behavioral" else "medium",
                "explanation": "Question appears to be yes/no, which limits detailed responses"
            })
            score -= 25

        # Check for leading question
        leading_indicators = [
            "don't you think", "wouldn't you say", "isn't it true",
            "you agree that", "clearly", "obviously"
        ]
        if any(ind in question_lower for ind in leading_indicators):
            issues.append({
                "type": "leading",
                "severity": "high",
                "explanation": "Question contains leading language that suggests a desired answer"
            })
            score -= 30

        # Check for compound question (multiple question marks or "and" + question words)
        if question.count("?") > 1:
            issues.append({
                "type": "compound",
                "severity": "medium",
                "explanation": "Multiple questions asked at once can confuse the candidate"
            })
            score -= 15

        # Check for open-ended questions (positive indicator)
        open_ended_starters = [
            "tell me about", "describe", "explain", "walk me through",
            "what ", "how ", "why ", "when "
        ]
        if any(question_lower.startswith(s) for s in open_ended_starters):
            strengths.append("Open-ended question structure")
            score += 10

        # Check for STAR-friendly phrasing (behavioral interviews)
        star_keywords = [
            "time when", "situation", "example", "experience",
            "tell me about a", "describe a"
        ]
        if interview_type == "behavioral" and any(kw in question_lower for kw in star_keywords):
            strengths.append("STAR-friendly phrasing")
            score += 15

        # Ensure score is in valid range
        score = max(0, min(100, score))

        # Determine rating
        if score >= self.EXCELLENT_THRESHOLD:
            rating = "excellent"
        elif score >= self.GOOD_THRESHOLD:
            rating = "good"
        elif score >= self.FAIR_THRESHOLD:
            rating = "fair"
        else:
            rating = "poor"

        # Track statistics
        self.quality_scores.append(score)
        for issue in issues:
            self.issue_counts[issue["type"]] += 1

        # Generate improved version if there are issues
        improved = ""
        if issues:
            if any(i["type"] == "yes_no" for i in issues):
                improved = f"Tell me about {question[3:] if question_lower.startswith(('do ', 'is ')) else question}"
            elif any(i["type"] == "leading" for i in issues):
                improved = "Consider rephrasing without suggesting the desired answer"

        return {
            "quality_score": score,
            "quality_rating": rating,
            "issues": issues,
            "improved_version": improved,
            "strengths": strengths if strengths else ["Question is understandable"],
            "alert": self._generate_alert(score, issues),
            "average_quality": self.get_average_quality(),
            "fallback": True
        }
