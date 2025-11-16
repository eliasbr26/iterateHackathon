"""
Competency Scoring Evaluator - PILLAR 2.1

Evaluates candidates across multiple competency dimensions:
- Leadership
- Communication
- Technical Depth
- Problem Solving
- Ownership
- Adaptability
- Strategic Thinking
- Creativity
- Teamwork
- Culture Fit

Each competency is scored on multiple dimensions:
- Overall Score (0-100)
- Depth Score (0-100)
- Clarity Score (0-100)
- Relevance Score (0-100)
- Evidence Score (0-100) - how well they prove it
"""

import logging
import json
from typing import List, Dict, Optional
from datetime import datetime
from anthropic import Anthropic

from database.models import CompetencyType

logger = logging.getLogger(__name__)


class CompetencyEvaluator:
    """
    Evaluates interview answers for specific competencies
    Uses Claude to deeply analyze candidate responses
    """

    # Competency definitions
    COMPETENCY_DEFINITIONS = {
        CompetencyType.LEADERSHIP: "Ability to inspire, guide teams, make decisions, delegate, and take ownership of outcomes",
        CompetencyType.COMMUNICATION: "Clarity of expression, active listening, ability to explain complex concepts, presentation skills",
        CompetencyType.TECHNICAL_DEPTH: "Deep understanding of technical concepts, problem-solving approach, coding ability, system design",
        CompetencyType.PROBLEM_SOLVING: "Analytical thinking, creativity in solutions, systematic approach, handling ambiguity",
        CompetencyType.OWNERSHIP: "Taking responsibility, following through, accountability, proactive initiative",
        CompetencyType.ADAPTABILITY: "Handling change, learning quickly, flexibility, resilience in face of setbacks",
        CompetencyType.STRATEGIC_THINKING: "Long-term vision, understanding business impact, prioritization, trade-off analysis",
        CompetencyType.CREATIVITY: "Innovative thinking, novel approaches, challenging assumptions, thinking outside the box",
        CompetencyType.TEAMWORK: "Collaboration, conflict resolution, supporting others, building consensus",
        CompetencyType.CULTURE_FIT: "Alignment with company values, work style compatibility, mindset match",
    }

    EVALUATION_PROMPT = """You are an expert interview evaluator assessing a candidate's competency in: {competency_name}

<competency_definition>
{competency_definition}
</competency_definition>

<conversation>
{conversation}
</conversation>

Analyze this conversation and evaluate the candidate's demonstration of {competency_name}.

Provide detailed scoring across 5 dimensions:

1. **Overall Score** (0-100): Holistic assessment of this competency
2. **Depth Score** (0-100): How deeply they demonstrated this competency
3. **Clarity Score** (0-100): How clearly they communicated about it
4. **Relevance Score** (0-100): How relevant their examples/discussion was
5. **Evidence Score** (0-100): How well they PROVED they have this competency (concrete examples, metrics, outcomes)

Also provide:
- **Evidence Quotes**: 2-3 specific quotes from the conversation that demonstrate this competency
- **Reasoning**: 2-3 sentences explaining your scoring

Scoring Guidelines:
- 0-20: No evidence or very weak
- 21-40: Minimal evidence, vague claims
- 41-60: Moderate evidence, some concrete examples
- 61-80: Strong evidence, clear examples with outcomes
- 81-100: Exceptional evidence, multiple detailed examples with quantified results

Respond ONLY with valid JSON in this exact format:
{{
    "overall_score": 0-100,
    "depth_score": 0-100,
    "clarity_score": 0-100,
    "relevance_score": 0-100,
    "evidence_score": 0-100,
    "evidence_quotes": ["quote1", "quote2", "quote3"],
    "reasoning": "brief explanation of scores"
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize competency evaluator

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ CompetencyEvaluator initialized with model: {model}")

    async def evaluate_competency(
        self,
        competency: CompetencyType,
        conversation: str,
    ) -> Dict:
        """
        Evaluate a specific competency based on conversation

        Args:
            competency: Competency type to evaluate
            conversation: Conversation transcript

        Returns:
            Dict with scoring details
        """
        competency_name = competency.value.replace("_", " ").title()
        competency_def = self.COMPETENCY_DEFINITIONS.get(
            competency,
            "General competency assessment"
        )

        logger.info(f"🎯 Evaluating competency: {competency_name}")

        try:
            # Build prompt
            prompt = self.EVALUATION_PROMPT.format(
                competency_name=competency_name,
                competency_definition=competency_def,
                conversation=conversation
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API for competency evaluation...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON
            evaluation_data = self._parse_response(response_text)

            # Add metadata
            evaluation_data["competency"] = competency
            evaluation_data["evaluated_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"✅ Competency evaluation complete: {competency_name} "
                f"(overall={evaluation_data['overall_score']}, "
                f"evidence={evaluation_data['evidence_score']})"
            )

            return evaluation_data

        except Exception as e:
            logger.error(f"❌ Error evaluating competency {competency_name}: {e}", exc_info=True)
            return self._create_error_result(competency, str(e))

    async def evaluate_all_competencies(
        self,
        conversation: str,
        target_competencies: Optional[List[CompetencyType]] = None,
    ) -> List[Dict]:
        """
        Evaluate multiple competencies from a conversation

        Args:
            conversation: Conversation transcript
            target_competencies: List of competencies to evaluate (None = all)

        Returns:
            List of competency evaluations
        """
        if target_competencies is None:
            target_competencies = list(CompetencyType)

        logger.info(f"🎯 Evaluating {len(target_competencies)} competencies")

        results = []
        for competency in target_competencies:
            result = await self.evaluate_competency(competency, conversation)
            results.append(result)

        return results

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed evaluation dictionary

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
                "overall_score",
                "depth_score",
                "clarity_score",
                "relevance_score",
                "evidence_score",
                "reasoning"
            ]

            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_error_result(self, competency: CompetencyType, error_msg: str) -> Dict:
        """
        Create an error evaluation result

        Args:
            competency: The competency that failed evaluation
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "competency": competency,
            "overall_score": 0.0,
            "depth_score": 0.0,
            "clarity_score": 0.0,
            "relevance_score": 0.0,
            "evidence_score": 0.0,
            "evidence_quotes": [],
            "reasoning": f"Evaluation failed: {error_msg}",
            "evaluated_at": datetime.utcnow().isoformat(),
            "error": True
        }
