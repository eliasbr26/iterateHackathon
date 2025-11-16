"""
Tone Analyzer - PILLAR 4.2
Monitors interviewer tone to ensure professional, encouraging atmosphere
"""

import json
import logging
from typing import Dict, List, Optional
from collections import deque

import anthropic

logger = logging.getLogger(__name__)


class ToneAnalyzer:
    """
    Analyzes interviewer tone using Claude AI

    Features:
    - Real-time tone classification (harsh, neutral, encouraging)
    - Trend analysis (improving/declining over time)
    - Alerts for consistently harsh tone
    - Suggestions for improvement
    """

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 500
    TEMPERATURE = 0.3  # Lower for more consistent analysis

    # Tone history for trend analysis
    HISTORY_SIZE = 5  # Track last 5 questions

    TONE_ANALYSIS_PROMPT = """Analyze the tone of this interviewer's question in a job interview context.

Question: "{question}"
Context: This is question #{question_num} in a {duration_minutes:.0f}-minute interview.

Classify the tone as one of:
- harsh: Critical, dismissive, aggressive, condescending, or overly challenging
- neutral: Professional, matter-of-fact, straightforward, businesslike
- encouraging: Supportive, warm, positive, collaborative, empathetic

Consider:
- Word choice and phrasing
- Implied judgment or assumptions
- Openness vs. closed framing
- Respectful vs. challenging language

Respond in valid JSON format only (no markdown, no code blocks):
{{
    "tone": "harsh" | "neutral" | "encouraging",
    "confidence": 0.0-1.0,
    "indicators": ["specific words/phrases that indicate this tone"],
    "suggestion": "How to make this more encouraging (empty string if already encouraging)"
}}"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize tone analyzer

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Track tone history for trend analysis
        self.tone_history: deque = deque(maxlen=self.HISTORY_SIZE)

        logger.info(f"✅ ToneAnalyzer initialized with model: {model}")

    async def analyze(
        self,
        question: str,
        question_num: int = 1,
        duration_minutes: float = 0.0
    ) -> Dict:
        """
        Analyze the tone of an interviewer question

        Args:
            question: The question text
            question_num: Question number in the interview
            duration_minutes: How long interview has been running

        Returns:
            Tone analysis with classification, confidence, and suggestions
        """
        try:
            # Prepare prompt
            prompt = self.TONE_ANALYSIS_PROMPT.format(
                question=question,
                question_num=question_num,
                duration_minutes=duration_minutes
            )

            logger.info(f"🎭 Analyzing tone for question #{question_num}")

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

            # Validate tone value
            valid_tones = ["harsh", "neutral", "encouraging"]
            if result["tone"] not in valid_tones:
                logger.warning(f"Invalid tone: {result['tone']}, defaulting to neutral")
                result["tone"] = "neutral"

            # Add to history
            self.tone_history.append(result["tone"])

            # Calculate trend
            trend = self._calculate_trend()

            # Generate alert if needed
            alert = self._generate_alert(result["tone"], trend)

            # Build final result
            analysis = {
                "tone": result["tone"],
                "confidence": result.get("confidence", 0.8),
                "indicators": result.get("indicators", []),
                "suggestion": result.get("suggestion", ""),
                "trend": trend,
                "alert": alert,
                "history_count": len(self.tone_history)
            }

            logger.info(
                f"✅ Tone analysis: {result['tone']} "
                f"(confidence: {result.get('confidence', 0.8):.2f}) | "
                f"Trend: {trend}"
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse tone analysis JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return self._fallback_analysis(question)

        except Exception as e:
            logger.error(f"❌ Tone analysis failed: {e}", exc_info=True)
            return self._fallback_analysis(question)

    def get_tone_summary(self) -> Dict:
        """
        Get summary of tone across all analyzed questions

        Returns:
            Summary statistics and overall tone assessment
        """
        if not self.tone_history:
            return {
                "status": "no_data",
                "message": "No questions analyzed yet"
            }

        # Count tones
        tone_counts = {
            "harsh": 0,
            "neutral": 0,
            "encouraging": 0
        }

        for tone in self.tone_history:
            tone_counts[tone] += 1

        total = len(self.tone_history)

        # Calculate percentages
        tone_percentages = {
            tone: (count / total * 100)
            for tone, count in tone_counts.items()
        }

        # Determine overall tone
        if tone_percentages["encouraging"] >= 60:
            overall = "excellent"
        elif tone_percentages["encouraging"] >= 40:
            overall = "good"
        elif tone_percentages["harsh"] <= 20:
            overall = "fair"
        else:
            overall = "needs_improvement"

        # Generate recommendation
        recommendation = self._get_overall_recommendation(
            tone_percentages, overall
        )

        return {
            "total_questions_analyzed": total,
            "tone_distribution": tone_counts,
            "tone_percentages": {
                tone: round(pct, 1)
                for tone, pct in tone_percentages.items()
            },
            "overall_tone": overall,
            "trend": self._calculate_trend(),
            "recommendation": recommendation
        }

    def reset(self):
        """Reset tone history for a new interview"""
        self.tone_history.clear()
        logger.info("🔄 ToneAnalyzer reset")

    # Private helper methods

    def _calculate_trend(self) -> str:
        """
        Calculate tone trend based on recent history

        Returns:
            "improving", "declining", "stable", or "insufficient_data"
        """
        if len(self.tone_history) < 3:
            return "insufficient_data"

        # Convert tones to numeric scores
        tone_scores = {
            "harsh": 0,
            "neutral": 1,
            "encouraging": 2
        }

        # Get scores for first half and second half
        mid = len(self.tone_history) // 2
        first_half = [tone_scores[t] for t in list(self.tone_history)[:mid]]
        second_half = [tone_scores[t] for t in list(self.tone_history)[mid:]]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        # Determine trend
        diff = second_avg - first_avg

        if diff > 0.3:
            return "improving"
        elif diff < -0.3:
            return "declining"
        else:
            return "stable"

    def _generate_alert(self, current_tone: str, trend: str) -> Optional[Dict]:
        """
        Generate alert if tone needs attention

        Args:
            current_tone: Current tone classification
            trend: Tone trend

        Returns:
            Alert dict or None
        """
        # Alert for harsh tone
        if current_tone == "harsh":
            return {
                "severity": "high",
                "message": "Harsh tone detected. Consider rephrasing to be more encouraging.",
                "action": "review_question"
            }

        # Alert for declining trend
        if trend == "declining" and len(self.tone_history) >= 4:
            harsh_count = sum(1 for t in self.tone_history if t == "harsh")
            if harsh_count >= 2:
                return {
                    "severity": "medium",
                    "message": f"Tone has become less encouraging recently. "
                               f"{harsh_count} harsh questions in last {len(self.tone_history)}.",
                    "action": "improve_tone"
                }

        # Alert for consistently neutral (not necessarily bad, but could be better)
        if len(self.tone_history) >= 5:
            neutral_count = sum(1 for t in self.tone_history if t == "neutral")
            if neutral_count == len(self.tone_history):
                return {
                    "severity": "low",
                    "message": "All questions have been neutral. "
                               "Consider adding more encouraging language to build rapport.",
                    "action": "add_warmth"
                }

        return None

    def _get_overall_recommendation(
        self,
        tone_percentages: Dict[str, float],
        overall: str
    ) -> str:
        """Generate overall tone recommendation"""
        if overall == "excellent":
            return (
                "Outstanding! Your encouraging tone creates a positive interview environment. "
                "Candidates are likely to perform their best."
            )

        if overall == "good":
            return (
                "Good tone overall. Consider adding more encouraging language "
                "to create an even more welcoming atmosphere."
            )

        if overall == "fair":
            harsh_pct = tone_percentages.get("harsh", 0)
            if harsh_pct > 0:
                return (
                    f"Tone is mostly professional, but {harsh_pct:.0f}% of questions were harsh. "
                    "Try to frame questions more positively."
                )
            else:
                return (
                    "Tone is professional but neutral. Adding warmth and encouragement "
                    "can help candidates feel more comfortable."
                )

        # needs_improvement
        harsh_pct = tone_percentages.get("harsh", 0)
        return (
            f"⚠️ {harsh_pct:.0f}% of questions have harsh tone. "
            "Focus on being more encouraging and supportive. "
            "This will help candidates perform better and improve interview outcomes."
        )

    def _fallback_analysis(self, question: str) -> Dict:
        """
        Fallback analysis when AI fails

        Uses simple heuristics based on keywords
        """
        question_lower = question.lower()

        # Keywords for harsh tone
        harsh_keywords = [
            "really?", "seriously?", "obviously", "clearly you",
            "don't you know", "you should", "why didn't you",
            "that's wrong", "incorrect"
        ]

        # Keywords for encouraging tone
        encouraging_keywords = [
            "great", "excellent", "interesting", "i'd love to hear",
            "could you share", "tell me more", "that's helpful",
            "thanks for", "appreciate"
        ]

        # Check for harsh indicators
        harsh_found = [kw for kw in harsh_keywords if kw in question_lower]
        if harsh_found:
            return {
                "tone": "harsh",
                "confidence": 0.6,
                "indicators": harsh_found,
                "suggestion": "Consider rephrasing to be more open and supportive",
                "trend": self._calculate_trend(),
                "alert": {
                    "severity": "medium",
                    "message": "Potentially harsh phrasing detected (fallback analysis)",
                    "action": "review_question"
                },
                "history_count": len(self.tone_history),
                "fallback": True
            }

        # Check for encouraging indicators
        encouraging_found = [kw for kw in encouraging_keywords if kw in question_lower]
        if encouraging_found:
            self.tone_history.append("encouraging")
            return {
                "tone": "encouraging",
                "confidence": 0.6,
                "indicators": encouraging_found,
                "suggestion": "",
                "trend": self._calculate_trend(),
                "alert": None,
                "history_count": len(self.tone_history),
                "fallback": True
            }

        # Default to neutral
        self.tone_history.append("neutral")
        return {
            "tone": "neutral",
            "confidence": 0.5,
            "indicators": ["No strong tone indicators found"],
            "suggestion": "Consider adding more encouraging language",
            "trend": self._calculate_trend(),
            "alert": None,
            "history_count": len(self.tone_history),
            "fallback": True
        }
