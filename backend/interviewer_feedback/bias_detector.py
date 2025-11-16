"""
Bias Detector - PILLAR 4.4
Identifies potential bias in interviewer questions
"""

import json
import logging
from typing import Dict, List, Optional
from collections import Counter

import anthropic

logger = logging.getLogger(__name__)


class BiasDetector:
    """
    Detects bias in interviewer questions using Claude AI

    Features:
    - Detects demographic bias (age, gender, race, etc.)
    - Identifies assumption-based questions
    - Flags culturally insensitive phrasing
    - Provides bias-free alternatives
    - Tracks bias patterns over time
    """

    # Model configuration
    DEFAULT_MODEL = "claude-sonnet-4-5"
    MAX_TOKENS = 800
    TEMPERATURE = 0.2  # Lower temperature for more consistent bias detection

    # Bias score thresholds
    HIGH_BIAS_THRESHOLD = 0.7
    MEDIUM_BIAS_THRESHOLD = 0.4
    LOW_BIAS_THRESHOLD = 0.2

    BIAS_DETECTION_PROMPT = """Analyze this interview question for potential bias that could disadvantage or unfairly favor certain candidates.

Question: "{question}"

Check for these bias types:
1. Age bias - Assumptions about generation, tech familiarity, energy levels, career stage
2. Gender bias - Assumptions about roles, capabilities, family responsibilities, interests
3. Cultural bias - Assumptions about background, customs, holidays, language, or nationality
4. Ability bias - Assumptions about physical/mental capabilities, health, or disabilities
5. Socioeconomic bias - Assumptions about education, resources, lifestyle, or privilege
6. Implicit assumptions - Any unstated assumptions about the candidate's personal life, background, or circumstances

Legal considerations:
- Questions about protected characteristics are typically illegal (age, gender, race, religion, nationality, disability, marital status, parental status)
- Focus on job-related qualifications only

Respond in valid JSON format only (no markdown, no code blocks):
{{
    "has_bias": true/false,
    "bias_score": 0.0-1.0,
    "bias_types": [
        {{
            "type": "age" | "gender" | "cultural" | "ability" | "socioeconomic" | "implicit",
            "severity": "low" | "medium" | "high",
            "explanation": "Specific bias detected and why it's problematic",
            "problematic_phrase": "The exact phrase that's biased",
            "legal_risk": true/false
        }}
    ],
    "bias_free_version": "Rewritten question without bias (empty string if no bias)",
    "recommendation": "How to avoid this bias in future questions"
}}

Bias score guide:
- 0.0-0.2: No significant bias
- 0.2-0.4: Low bias, minor issues
- 0.4-0.7: Medium bias, needs correction
- 0.7-1.0: High bias, serious issue, possible legal risk"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize bias detector

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Track bias incidents
        self.bias_incidents: List[Dict] = []
        self.bias_type_counts: Counter = Counter()

        logger.info(f"✅ BiasDetector initialized with model: {model}")

    async def detect(self, question: str) -> Dict:
        """
        Detect bias in an interview question

        Args:
            question: The question text

        Returns:
            Bias analysis with types, severity, and alternatives
        """
        try:
            # Prepare prompt
            prompt = self.BIAS_DETECTION_PROMPT.format(question=question)

            logger.info(f"🔎 Detecting bias for: {question[:50]}...")

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

            # Validate bias score
            bias_score = max(0.0, min(1.0, result.get("bias_score", 0.0)))
            has_bias = result.get("has_bias", False)

            # Track bias incidents
            if has_bias and result.get("bias_types"):
                self.bias_incidents.append({
                    "question": question,
                    "bias_score": bias_score,
                    "types": result.get("bias_types", [])
                })

                for bias_type in result.get("bias_types", []):
                    self.bias_type_counts[bias_type["type"]] += 1

            # Determine severity level
            severity = self._determine_severity(bias_score, result.get("bias_types", []))

            # Generate alert
            alert = self._generate_alert(
                has_bias,
                bias_score,
                severity,
                result.get("bias_types", [])
            )

            # Build final result
            analysis = {
                "has_bias": has_bias,
                "bias_score": bias_score,
                "severity": severity,
                "bias_types": result.get("bias_types", []),
                "bias_free_version": result.get("bias_free_version", ""),
                "recommendation": result.get("recommendation", ""),
                "alert": alert,
                "total_bias_incidents": len(self.bias_incidents)
            }

            if has_bias:
                logger.warning(
                    f"⚠️ Bias detected: score={bias_score:.2f}, "
                    f"severity={severity}, types={len(result.get('bias_types', []))}"
                )
            else:
                logger.info("✅ No bias detected")

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse bias detection JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return self._fallback_detection(question)

        except Exception as e:
            logger.error(f"❌ Bias detection failed: {e}", exc_info=True)
            return self._fallback_detection(question)

    def get_bias_summary(self) -> Dict:
        """
        Get summary of bias incidents across interview

        Returns:
            Summary statistics and patterns
        """
        if not self.bias_incidents:
            return {
                "status": "no_bias_detected",
                "total_incidents": 0,
                "message": "No bias detected in analyzed questions"
            }

        # Calculate average bias score
        avg_bias_score = sum(
            incident["bias_score"] for incident in self.bias_incidents
        ) / len(self.bias_incidents)

        # Count severity levels
        severity_counts = {
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for incident in self.bias_incidents:
            for bias_type in incident["types"]:
                severity = bias_type.get("severity", "low")
                severity_counts[severity] += 1

        # Get top bias types
        top_bias_types = self.bias_type_counts.most_common(3)

        # Determine overall assessment
        if severity_counts["high"] > 0:
            overall = "critical"
        elif severity_counts["medium"] > 2:
            overall = "concerning"
        elif avg_bias_score > self.MEDIUM_BIAS_THRESHOLD:
            overall = "needs_improvement"
        else:
            overall = "acceptable"

        # Generate recommendation
        recommendation = self._get_overall_recommendation(
            overall,
            severity_counts,
            top_bias_types
        )

        return {
            "total_incidents": len(self.bias_incidents),
            "average_bias_score": round(avg_bias_score, 2),
            "overall_assessment": overall,
            "severity_distribution": severity_counts,
            "top_bias_types": [
                {"type": bias_type, "count": count}
                for bias_type, count in top_bias_types
            ],
            "recommendation": recommendation,
            "legal_risk_questions": sum(
                1 for incident in self.bias_incidents
                if any(bt.get("legal_risk", False) for bt in incident["types"])
            )
        }

    def reset(self):
        """Reset bias tracking for a new interview"""
        self.bias_incidents.clear()
        self.bias_type_counts.clear()
        logger.info("🔄 BiasDetector reset")

    # Private helper methods

    def _determine_severity(
        self,
        bias_score: float,
        bias_types: List[Dict]
    ) -> str:
        """Determine overall severity level"""
        # Check for legal risk
        if any(bt.get("legal_risk", False) for bt in bias_types):
            return "high"

        # Check for high severity types
        if any(bt.get("severity") == "high" for bt in bias_types):
            return "high"

        # Use bias score thresholds
        if bias_score >= self.HIGH_BIAS_THRESHOLD:
            return "high"
        elif bias_score >= self.MEDIUM_BIAS_THRESHOLD:
            return "medium"
        elif bias_score >= self.LOW_BIAS_THRESHOLD:
            return "low"
        else:
            return "none"

    def _generate_alert(
        self,
        has_bias: bool,
        bias_score: float,
        severity: str,
        bias_types: List[Dict]
    ) -> Optional[Dict]:
        """Generate alert for bias detection"""
        if not has_bias or severity == "none":
            return None

        # High severity alert
        if severity == "high":
            legal_risk = any(bt.get("legal_risk", False) for bt in bias_types)
            bias_type_names = ", ".join(bt["type"] for bt in bias_types)

            message = (
                f"🚨 HIGH SEVERITY: Bias detected in question (score: {bias_score:.2f}). "
                f"Types: {bias_type_names}."
            )

            if legal_risk:
                message += " ⚖️ LEGAL RISK: This question may violate employment law."

            return {
                "severity": "high",
                "message": message,
                "action": "do_not_ask",
                "legal_risk": legal_risk
            }

        # Medium severity alert
        if severity == "medium":
            return {
                "severity": "medium",
                "message": f"⚠️ Potential bias detected (score: {bias_score:.2f}). "
                           f"Consider using the bias-free alternative.",
                "action": "revise_question",
                "legal_risk": False
            }

        # Low severity alert
        return {
            "severity": "low",
            "message": f"Minor bias detected (score: {bias_score:.2f}). "
                       "Consider rephrasing for neutrality.",
            "action": "review_question",
            "legal_risk": False
        }

    def _get_overall_recommendation(
        self,
        overall: str,
        severity_counts: Dict[str, int],
        top_bias_types: List[tuple]
    ) -> str:
        """Generate overall bias recommendation"""
        if overall == "critical":
            return (
                "🚨 CRITICAL: Multiple high-severity bias incidents detected. "
                "This interview has serious legal risk. Immediate training required. "
                "Focus on job-related questions only."
            )

        if overall == "concerning":
            top_types = ", ".join(bt for bt, _ in top_bias_types)
            return (
                f"⚠️ CONCERNING: {severity_counts['medium']} medium-severity bias incidents. "
                f"Common types: {top_types}. "
                "Review bias training and focus on competency-based questions."
            )

        if overall == "needs_improvement":
            return (
                "Minor bias patterns detected. Be more mindful of assumptions "
                "about candidates' backgrounds and circumstances. "
                "Stick to job-related questions."
            )

        # acceptable
        return (
            "Good job maintaining bias-free questions. "
            "Continue focusing on competencies and job-related skills."
        )

    def _fallback_detection(self, question: str) -> Dict:
        """
        Fallback bias detection using keyword matching

        Args:
            question: The question text

        Returns:
            Basic bias analysis
        """
        question_lower = question.lower()
        bias_types = []
        bias_score = 0.0

        # Age bias keywords
        age_keywords = [
            "young", "old", "recent grad", "years of experience",
            "generation", "millenni", "boomer", "digital native",
            "energy level", "retire"
        ]
        age_matches = [kw for kw in age_keywords if kw in question_lower]
        if age_matches:
            bias_types.append({
                "type": "age",
                "severity": "medium",
                "explanation": f"Question contains age-related terms: {', '.join(age_matches)}",
                "problematic_phrase": age_matches[0],
                "legal_risk": True
            })
            bias_score += 0.5

        # Gender bias keywords
        gender_keywords = [
            "he ", "she ", "his ", "her ", "him ",
            "husband", "wife", "girlfriend", "boyfriend",
            "mr.", "mrs.", "miss", "ma'am", "sir"
        ]
        gender_matches = [kw for kw in gender_keywords if kw in question_lower]
        if gender_matches:
            bias_types.append({
                "type": "gender",
                "severity": "medium",
                "explanation": f"Question uses gendered language: {', '.join(gender_matches)}",
                "problematic_phrase": gender_matches[0],
                "legal_risk": True
            })
            bias_score += 0.5

        # Family/marital status keywords (protected in many jurisdictions)
        family_keywords = [
            "married", "single", "children", "kids", "family",
            "pregnant", "maternity", "paternity"
        ]
        family_matches = [kw for kw in family_keywords if kw in question_lower]
        if family_matches:
            bias_types.append({
                "type": "implicit",
                "severity": "high",
                "explanation": f"Question asks about protected characteristics: {', '.join(family_matches)}",
                "problematic_phrase": family_matches[0],
                "legal_risk": True
            })
            bias_score += 0.7

        # Cultural bias keywords
        cultural_keywords = [
            "native", "accent", "where are you from",
            "english is your", "holiday", "christmas",
            "religion", "church", "mosque", "temple"
        ]
        cultural_matches = [kw for kw in cultural_keywords if kw in question_lower]
        if cultural_matches:
            bias_types.append({
                "type": "cultural",
                "severity": "medium",
                "explanation": f"Question may contain cultural bias: {', '.join(cultural_matches)}",
                "problematic_phrase": cultural_matches[0],
                "legal_risk": True
            })
            bias_score += 0.6

        # Socioeconomic bias keywords
        socioeconomic_keywords = [
            "elite university", "ivy league", "private school",
            "country club", "summer home", "travels"
        ]
        socioeconomic_matches = [kw for kw in socioeconomic_keywords if kw in question_lower]
        if socioeconomic_matches:
            bias_types.append({
                "type": "socioeconomic",
                "severity": "low",
                "explanation": f"Question may assume privileged background: {', '.join(socioeconomic_matches)}",
                "problematic_phrase": socioeconomic_matches[0],
                "legal_risk": False
            })
            bias_score += 0.3

        # Cap bias score at 1.0
        bias_score = min(1.0, bias_score)
        has_bias = len(bias_types) > 0

        # Track incidents
        if has_bias:
            self.bias_incidents.append({
                "question": question,
                "bias_score": bias_score,
                "types": bias_types
            })
            for bt in bias_types:
                self.bias_type_counts[bt["type"]] += 1

        # Determine severity
        severity = self._determine_severity(bias_score, bias_types)

        # Generate bias-free version if needed
        bias_free = ""
        if has_bias:
            bias_free = "Focus on job-related competencies and skills rather than personal characteristics."

        return {
            "has_bias": has_bias,
            "bias_score": bias_score,
            "severity": severity,
            "bias_types": bias_types,
            "bias_free_version": bias_free,
            "recommendation": "Review employment law guidelines for interview questions. "
                            "Focus on job-related qualifications only.",
            "alert": self._generate_alert(has_bias, bias_score, severity, bias_types),
            "total_bias_incidents": len(self.bias_incidents),
            "fallback": True
        }
