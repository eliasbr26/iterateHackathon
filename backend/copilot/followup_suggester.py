"""
Follow-Up Question Suggester - PILLAR 1.1

Generates intelligent follow-up questions in real-time based on candidate responses.

Analyzes:
- Response depth and completeness
- Missing STAR components
- Vague or unclear answers
- Technical depth opportunities
- Behavioral exploration needs

Provides smart, contextual suggestions to help interviewers dig deeper.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class FollowUpSuggester:
    """
    Generates intelligent follow-up questions for interviewers in real-time
    Uses Claude to analyze answers and suggest probing questions
    """

    SUGGESTION_PROMPT = """You are an expert interview coach helping an interviewer conduct better interviews.

<question>
{question}
</question>

<candidate_answer>
{answer}
</candidate_answer>

<context>
{context}
</context>

Analyze this Q&A exchange and generate 2-3 intelligent follow-up questions that would help the interviewer:

1. **Probe for depth** - Get more specific details, examples, or metrics
2. **Complete STAR** - Fill in missing Situation/Task/Action/Result components
3. **Clarify vagueness** - Ask for concrete examples when answers are generic
4. **Explore competencies** - Dig into leadership, problem-solving, teamwork, etc.
5. **Challenge assumptions** - Gently probe claims that lack evidence

For each suggestion:
- Make it specific and actionable
- Explain WHY this follow-up would be valuable
- Prioritize (high/medium/low) based on importance
- Categorize the type of follow-up

Respond ONLY with valid JSON in this exact format:
{{
    "suggestions": [
        {{
            "question": "exact question to ask",
            "reason": "why this follow-up matters",
            "priority": "high" | "medium" | "low",
            "category": "clarification" | "star_completion" | "depth" | "competency" | "evidence",
            "expected_insight": "what we hope to learn"
        }}
    ],
    "overall_assessment": "brief assessment of answer quality",
    "needs_followup": true | false
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize follow-up suggester

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ FollowUpSuggester initialized with model: {model}")

    async def generate(
        self,
        question: str,
        answer: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate follow-up question suggestions

        Args:
            question: The question that was asked
            answer: The candidate's answer
            context: Optional context (evaluation results, topics covered, etc.)

        Returns:
            Dict with suggestions and metadata
        """
        logger.info(f"🎯 Generating follow-up suggestions for Q&A...")

        try:
            # Format context
            context_text = self._format_context(context) if context else "First question in interview"

            # Build prompt
            prompt = self.SUGGESTION_PROMPT.format(
                question=question,
                answer=answer,
                context=context_text
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API for follow-up suggestions...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            result = self._parse_response(response_text)

            # Add metadata
            result["generated_at"] = datetime.utcnow().isoformat()
            result["question_asked"] = question
            result["model_used"] = self.model

            logger.info(
                f"✅ Generated {len(result.get('suggestions', []))} follow-up suggestions, "
                f"needs_followup={result.get('needs_followup', False)}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error generating follow-up suggestions: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _format_context(self, context: Dict) -> str:
        """Format context dictionary into readable text"""
        parts = []

        if "topics_covered" in context:
            parts.append(f"Topics covered: {', '.join(context['topics_covered'])}")

        if "competencies_discussed" in context:
            parts.append(f"Competencies discussed: {', '.join(context['competencies_discussed'])}")

        if "interview_duration" in context:
            parts.append(f"Interview duration: {context['interview_duration']} minutes")

        if "difficulty_level" in context:
            parts.append(f"Current difficulty level: {context['difficulty_level']}")

        return "\n".join(parts) if parts else "No additional context"

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed suggestion dictionary

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
            required = ["suggestions", "needs_followup"]
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
        Create an error result

        Args:
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "suggestions": [],
            "overall_assessment": f"Error generating suggestions: {error_msg}",
            "needs_followup": False,
            "generated_at": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": error_msg
        }

    def filter_by_priority(
        self,
        result: Dict,
        min_priority: str = "medium"
    ) -> List[Dict]:
        """
        Filter suggestions by priority

        Args:
            result: Result from generate()
            min_priority: Minimum priority (high/medium/low)

        Returns:
            Filtered list of suggestions
        """
        priority_order = {"high": 3, "medium": 2, "low": 1}
        min_level = priority_order.get(min_priority, 2)

        suggestions = result.get("suggestions", [])
        return [
            s for s in suggestions
            if priority_order.get(s.get("priority", "low"), 1) >= min_level
        ]

    def get_top_suggestion(self, result: Dict) -> Optional[Dict]:
        """
        Get the highest priority suggestion

        Args:
            result: Result from generate()

        Returns:
            Top suggestion or None
        """
        suggestions = result.get("suggestions", [])
        if not suggestions:
            return None

        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_suggestions = sorted(
            suggestions,
            key=lambda s: priority_order.get(s.get("priority", "low"), 1),
            reverse=True
        )

        return sorted_suggestions[0]
