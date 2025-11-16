"""
STAR Method Analyzer - PILLAR 2.2

Evaluates behavioral interview answers using the STAR framework:
- Situation: What was the context?
- Task: What needed to be done?
- Action: What did the candidate do?
- Result: What was the outcome?

Provides:
- STAR completion percentage (0-100%)
- Quality rating (shallow/partial/decent/excellent)
- Whether results are quantified
- Extracted STAR components
"""

import logging
import json
from typing import Dict, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class STARAnalyzer:
    """
    Analyzes behavioral interview answers using STAR method
    Identifies and extracts STAR components from candidate responses
    """

    STAR_ANALYSIS_PROMPT = """You are an expert interview evaluator analyzing a behavioral interview answer using the STAR method.

<question>
{question}
</question>

<answer>
{answer}
</answer>

Analyze this Q&A exchange and extract the STAR components:

**STAR Framework:**
- **Situation**: The context, background, or scenario the candidate was in
- **Task**: The challenge, responsibility, or goal they faced
- **Action**: The specific steps THEY took (not the team, but the individual)
- **Result**: The outcome, impact, or consequences of their actions

For each component, determine:
1. **Is it present?** (true/false)
2. **Extract the text** (if present)

Additionally assess:
- **STAR Completion %**: What percentage of the STAR framework is covered? (0-100)
  - 0-25%: Only 1 component present
  - 25-50%: 2 components present
  - 50-75%: 3 components present
  - 75-100%: All 4 components present and detailed

- **Result Quantified**: Does the result include specific numbers, metrics, percentages, or measurable outcomes?

- **Quality Rating**: Overall quality of the STAR answer
  - "shallow": Vague, generic, lacking detail
  - "partial": Some detail but missing key components
  - "decent": All components present but could be more detailed
  - "excellent": All components with rich detail, quantified results, clear impact

Respond ONLY with valid JSON in this exact format:
{{
    "has_situation": true/false,
    "has_task": true/false,
    "has_action": true/false,
    "has_result": true/false,
    "situation_text": "extracted text or null",
    "task_text": "extracted text or null",
    "action_text": "extracted text or null",
    "result_text": "extracted text or null",
    "star_completion_percentage": 0-100,
    "result_quantified": true/false,
    "quality_rating": "shallow" | "partial" | "decent" | "excellent"
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize STAR analyzer

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ STARAnalyzer initialized with model: {model}")

    async def analyze(self, question: str, answer: str) -> Dict:
        """
        Analyze a Q&A pair for STAR components

        Args:
            question: Interview question asked
            answer: Candidate's answer

        Returns:
            Dict with STAR analysis
        """
        logger.info(f"⭐ Analyzing STAR method for question: {question[:50]}...")

        try:
            # Build prompt
            prompt = self.STAR_ANALYSIS_PROMPT.format(
                question=question,
                answer=answer
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API for STAR analysis...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
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
            analysis_data["question"] = question
            analysis_data["answer"] = answer
            analysis_data["analyzed_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"✅ STAR analysis complete: "
                f"completion={analysis_data['star_completion_percentage']}%, "
                f"quality={analysis_data['quality_rating']}"
            )

            return analysis_data

        except Exception as e:
            logger.error(f"❌ Error during STAR analysis: {e}", exc_info=True)
            return self._create_error_result(question, answer, str(e))

    async def analyze_batch(self, qa_pairs: list[Dict[str, str]]) -> list[Dict]:
        """
        Analyze multiple Q&A pairs

        Args:
            qa_pairs: List of dicts with 'question' and 'answer' keys

        Returns:
            List of STAR analyses
        """
        logger.info(f"⭐ Analyzing {len(qa_pairs)} Q&A pairs for STAR method")

        results = []
        for qa in qa_pairs:
            result = await self.analyze(qa["question"], qa["answer"])
            results.append(result)

        return results

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
                "has_situation",
                "has_task",
                "has_action",
                "has_result",
                "star_completion_percentage",
                "result_quantified",
                "quality_rating"
            ]

            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_error_result(self, question: str, answer: str, error_msg: str) -> Dict:
        """
        Create an error analysis result

        Args:
            question: The question that failed analysis
            answer: The answer that failed analysis
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "question": question,
            "answer": answer,
            "has_situation": False,
            "has_task": False,
            "has_action": False,
            "has_result": False,
            "situation_text": None,
            "task_text": None,
            "action_text": None,
            "result_text": None,
            "star_completion_percentage": 0.0,
            "result_quantified": False,
            "quality_rating": "shallow",
            "analyzed_at": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": f"Analysis failed: {error_msg}"
        }

    def calculate_star_score(self, analysis: Dict) -> float:
        """
        Calculate a normalized STAR score (0-100)

        Args:
            analysis: STAR analysis result

        Returns:
            Score from 0-100
        """
        # Weight the components
        completion = analysis.get("star_completion_percentage", 0)
        quantified_bonus = 10 if analysis.get("result_quantified") else 0

        # Quality multiplier
        quality_multipliers = {
            "shallow": 0.5,
            "partial": 0.75,
            "decent": 1.0,
            "excellent": 1.25
        }
        quality = analysis.get("quality_rating", "shallow")
        multiplier = quality_multipliers.get(quality, 0.5)

        # Calculate score
        base_score = completion * multiplier
        final_score = min(100, base_score + quantified_bonus)

        return round(final_score, 1)
