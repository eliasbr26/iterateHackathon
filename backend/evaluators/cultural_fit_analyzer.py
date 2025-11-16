"""
Cultural Fit Analyzer - PILLAR 2.4

Analyzes candidate's cultural fit based on:
- Mindset & values alignment
- Communication style
- Teamwork approach
- Humility vs ego
- Attitude towards conflict
- Ownership vs delegation tendencies
- Work style preferences
- Growth mindset indicators

Provides detailed cultural fit assessment and compatibility score
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class CulturalFitAnalyzer:
    """
    Analyzes candidate's cultural fit with company values and culture
    Uses Claude to assess alignment on multiple cultural dimensions
    """

    DEFAULT_COMPANY_VALUES = [
        "Ownership & Accountability",
        "Customer Obsession",
        "Innovation & Creativity",
        "Collaboration & Teamwork",
        "Continuous Learning",
        "Integrity & Transparency",
        "Bias for Action",
        "Frugality & Resourcefulness"
    ]

    CULTURAL_FIT_PROMPT = """You are an expert cultural fit analyst evaluating a candidate's alignment with company culture.

<company_values>
{company_values}
</company_values>

<conversation>
{conversation}
</conversation>

Analyze this conversation for cultural fit indicators. Assess the candidate on:

**Cultural Dimensions:**

1. **Mindset**
   - Growth mindset vs fixed mindset
   - Proactive vs reactive
   - Long-term vs short-term thinking

2. **Communication Style**
   - Direct vs indirect
   - Data-driven vs intuition-driven
   - Collaborative vs individual

3. **Teamwork Approach**
   - Team player vs lone wolf
   - Supportive vs competitive
   - Consensus-seeking vs decisive

4. **Humility vs Ego**
   - Gives credit to others
   - Acknowledges mistakes
   - Open to feedback
   - Celebrates team success

5. **Attitude Towards Conflict**
   - Confronts issues directly
   - Avoids conflict
   - Seeks win-win solutions

6. **Ownership Tendencies**
   - Takes initiative
   - Sees projects through
   - Delegates appropriately
   - Accountable for outcomes

7. **Work Style**
   - Structured vs flexible
   - Autonomous vs guided
   - Fast-paced vs methodical

8. **Learning & Growth**
   - Seeks feedback
   - Embraces challenges
   - Learns from failures
   - Pursues development

For each company value, assess:
- **Alignment Score** (0-100): How well does candidate align?
- **Evidence**: Specific examples demonstrating alignment/misalignment

Provide:
- **Overall Cultural Fit Score** (0-100)
- **Top Strengths**: 3 strongest cultural alignment areas
- **Potential Concerns**: 3 areas of misalignment or concern
- **Recommendation**: strong_fit | good_fit | moderate_fit | poor_fit

Respond ONLY with valid JSON in this exact format:
{{
    "overall_fit_score": 0-100,
    "recommendation": "strong_fit" | "good_fit" | "moderate_fit" | "poor_fit",
    "value_alignment": [
        {{
            "value": "value name",
            "alignment_score": 0-100,
            "evidence": ["evidence1", "evidence2"]
        }}
    ],
    "cultural_dimensions": {{
        "mindset": "growth" | "fixed" | "mixed",
        "communication_style": "direct" | "indirect" | "balanced",
        "teamwork_approach": "collaborative" | "independent" | "balanced",
        "humility_level": "high" | "medium" | "low",
        "conflict_style": "confrontational" | "avoidant" | "constructive",
        "ownership_tendency": "high" | "medium" | "low",
        "work_style": "structured" | "flexible" | "adaptive",
        "learning_orientation": "high" | "medium" | "low"
    }},
    "top_strengths": ["strength1", "strength2", "strength3"],
    "potential_concerns": ["concern1", "concern2", "concern3"],
    "cultural_fit_summary": "brief narrative summary"
}}"""

    def __init__(
        self,
        api_key: str,
        company_values: Optional[List[str]] = None,
        model: str = "claude-sonnet-4-5"
    ):
        """
        Initialize cultural fit analyzer

        Args:
            api_key: Anthropic API key
            company_values: List of company values (uses defaults if None)
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.company_values = company_values or self.DEFAULT_COMPANY_VALUES

        logger.info(
            f"✅ CulturalFitAnalyzer initialized with model: {model}, "
            f"{len(self.company_values)} values"
        )

    async def analyze(
        self,
        conversation: str,
        custom_values: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze cultural fit from conversation

        Args:
            conversation: Full conversation transcript
            custom_values: Override company values for this analysis

        Returns:
            Dict with cultural fit analysis
        """
        values = custom_values or self.company_values
        logger.info(f"🎭 Analyzing cultural fit against {len(values)} company values...")

        try:
            # Format company values
            values_text = "\n".join([f"- {v}" for v in values])

            # Build prompt
            prompt = self.CULTURAL_FIT_PROMPT.format(
                company_values=values_text,
                conversation=conversation
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API for cultural fit analysis...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON
            analysis_data = self._parse_response(response_text)

            # Add metadata
            analysis_data["analyzed_at"] = datetime.utcnow().isoformat()
            analysis_data["company_values_used"] = values

            logger.info(
                f"✅ Cultural fit analysis complete: "
                f"score={analysis_data['overall_fit_score']}, "
                f"recommendation={analysis_data['recommendation']}"
            )

            return analysis_data

        except Exception as e:
            logger.error(f"❌ Error during cultural fit analysis: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed analysis dictionary

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
            required = [
                "overall_fit_score",
                "recommendation",
                "cultural_dimensions"
            ]

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
        Create an error analysis result

        Args:
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "overall_fit_score": 50,  # Neutral score
            "recommendation": "moderate_fit",
            "value_alignment": [],
            "cultural_dimensions": {
                "mindset": "mixed",
                "communication_style": "balanced",
                "teamwork_approach": "balanced",
                "humility_level": "medium",
                "conflict_style": "constructive",
                "ownership_tendency": "medium",
                "work_style": "adaptive",
                "learning_orientation": "medium"
            },
            "top_strengths": [],
            "potential_concerns": [f"Analysis failed: {error_msg}"],
            "cultural_fit_summary": f"Unable to assess cultural fit: {error_msg}",
            "analyzed_at": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": error_msg
        }

    def interpret_fit_score(self, score: float) -> str:
        """
        Interpret cultural fit score into human-readable category

        Args:
            score: Cultural fit score (0-100)

        Returns:
            Interpretation string
        """
        if score >= 80:
            return "Excellent cultural fit"
        elif score >= 65:
            return "Good cultural fit"
        elif score >= 50:
            return "Moderate cultural fit"
        elif score >= 35:
            return "Some cultural alignment concerns"
        else:
            return "Significant cultural fit concerns"
