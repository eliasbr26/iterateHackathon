"""
Bluffing & Inconsistency Detector - PILLAR 2.3

Detects suspicious patterns in candidate responses:
- Vague explanations
- Evasion of questions
- Contradictions
- Unrealistic descriptions
- Inflated responsibilities
- Non-answers
- Overuse of buzzwords
- Lack of quantification
- Weak evidence

Provides detailed red flags and confidence scores
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class BluffingDetector:
    """
    Detects bluffing, vagueness, and inconsistencies in interview responses
    Uses Claude to identify suspicious patterns
    """

    DETECTION_PROMPT = """You are an expert interview analyst trained to detect bluffing, vagueness, and inconsistencies in candidate responses.

<conversation>
{conversation}
</conversation>

Analyze this conversation for signs of bluffing, evasion, or weak evidence. Look for:

1. **Vague Explanations**: Generic answers without specific details
2. **Evasion**: Not directly answering questions, deflecting
3. **Contradictions**: Statements that conflict with earlier claims
4. **Unrealistic Claims**: Descriptions that seem inflated or impossible
5. **Inflated Responsibility**: Taking credit for team achievements
6. **Non-Answers**: Talking around the question without answering
7. **Buzzword Overuse**: Heavy use of jargon without substance
8. **Lack of Quantification**: No metrics, numbers, or measurable outcomes
9. **Weak Evidence**: Claims without supporting examples
10. **Timeline Inconsistencies**: Dates or sequences that don't add up

For each suspicious pattern found:
- Identify the type
- Extract the problematic text/quote
- Explain why it's suspicious
- Assess severity (low/medium/high)

Also provide:
- **Overall Bluffing Score** (0-100): How suspicious is this candidate overall?
  - 0-20: Highly credible, strong evidence
  - 21-40: Mostly credible, minor concerns
  - 41-60: Mixed signals, some red flags
  - 61-80: Multiple red flags, questionable credibility
  - 81-100: Highly suspicious, likely bluffing

- **Risk Level**: low/medium/high/critical

Respond ONLY with valid JSON in this exact format:
{{
    "bluffing_score": 0-100,
    "risk_level": "low" | "medium" | "high" | "critical",
    "red_flags": [
        {{
            "type": "vague_explanation" | "evasion" | "contradiction" | "unrealistic_claim" | "inflated_responsibility" | "non_answer" | "buzzword_overuse" | "lack_quantification" | "weak_evidence" | "timeline_inconsistency",
            "quote": "extracted text",
            "explanation": "why this is suspicious",
            "severity": "low" | "medium" | "high"
        }}
    ],
    "credibility_assessment": "brief overall assessment",
    "specific_concerns": ["concern1", "concern2", ...]
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize bluffing detector

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ BluffingDetector initialized with model: {model}")

    async def detect(self, conversation: str) -> Dict:
        """
        Detect bluffing and inconsistencies in conversation

        Args:
            conversation: Full conversation transcript

        Returns:
            Dict with detection results
        """
        logger.info(f"🔍 Analyzing conversation for bluffing/inconsistencies...")

        try:
            # Build prompt
            prompt = self.DETECTION_PROMPT.format(conversation=conversation)

            # Call Claude API
            logger.debug("📡 Calling Claude API for bluffing detection...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON
            detection_data = self._parse_response(response_text)

            # Add metadata
            detection_data["analyzed_at"] = datetime.utcnow().isoformat()
            detection_data["red_flag_count"] = len(detection_data.get("red_flags", []))

            logger.info(
                f"✅ Bluffing detection complete: "
                f"score={detection_data['bluffing_score']}, "
                f"risk={detection_data['risk_level']}, "
                f"flags={detection_data['red_flag_count']}"
            )

            return detection_data

        except Exception as e:
            logger.error(f"❌ Error during bluffing detection: {e}", exc_info=True)
            return self._create_error_result(str(e))

    async def check_consistency(
        self,
        current_answer: str,
        previous_answers: List[str],
        cv_text: Optional[str] = None
    ) -> Dict:
        """
        Check consistency between current answer and previous statements/CV

        Args:
            current_answer: Current answer to check
            previous_answers: List of previous answers from same interview
            cv_text: Candidate's CV text (optional)

        Returns:
            Dict with consistency analysis
        """
        logger.info("🔍 Checking answer consistency...")

        # Build comparison text
        comparison_text = f"<current_answer>\n{current_answer}\n</current_answer>\n\n"

        if previous_answers:
            comparison_text += "<previous_answers>\n"
            for i, ans in enumerate(previous_answers, 1):
                comparison_text += f"Answer {i}: {ans}\n\n"
            comparison_text += "</previous_answers>\n\n"

        if cv_text:
            comparison_text += f"<cv>\n{cv_text}\n</cv>"

        prompt = f"""Analyze this answer for consistency with previous statements and/or CV.

{comparison_text}

Look for:
- Contradictions with previous answers
- Contradictions with CV claims
- Timeline inconsistencies
- Conflicting responsibility claims

Respond with JSON:
{{
    "is_consistent": true/false,
    "contradictions": [
        {{
            "statement_1": "text",
            "statement_2": "conflicting text",
            "explanation": "why they contradict"
        }}
    ],
    "consistency_score": 0-100
}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            result = self._parse_response(response.content[0].text.strip())
            result["analyzed_at"] = datetime.utcnow().isoformat()

            logger.info(f"✅ Consistency check complete: score={result.get('consistency_score', 0)}")
            return result

        except Exception as e:
            logger.error(f"❌ Error checking consistency: {e}")
            return {
                "is_consistent": True,  # Assume innocent until proven guilty
                "contradictions": [],
                "consistency_score": 100,
                "error": True,
                "error_message": str(e)
            }

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed detection dictionary

        Raises:
            ValueError: If response cannot be parsed
        """
        # Clean up markdown
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            data = json.loads(response_text)

            # Validate required fields
            required = ["bluffing_score", "risk_level"]

            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_error_result(self, error_msg: str) -> Dict:
        """
        Create an error detection result

        Args:
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "bluffing_score": 0,
            "risk_level": "low",
            "red_flags": [],
            "credibility_assessment": f"Analysis failed: {error_msg}",
            "specific_concerns": [],
            "red_flag_count": 0,
            "analyzed_at": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": error_msg
        }

    def calculate_credibility_score(self, detection: Dict) -> float:
        """
        Calculate overall credibility score (inverse of bluffing score)

        Args:
            detection: Bluffing detection result

        Returns:
            Credibility score from 0-100 (higher is better)
        """
        bluffing_score = detection.get("bluffing_score", 0)
        return 100 - bluffing_score
