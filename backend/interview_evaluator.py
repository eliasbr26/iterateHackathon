"""
LLM-powered interview evaluation system

Uses Anthropic Claude to analyze interview transcripts in real-time

Based on Hugo's comprehensive Quant Finance topic taxonomy
"""

import logging
import json
from datetime import datetime
from anthropic import Anthropic

from audio_pipeline.models import (
    BufferedWindow,
    EvaluationResult,
    QuestionDifficulty,
    InterviewerTone,
    SubjectRelevance
)

logger = logging.getLogger(__name__)


# Hugo's Quant Finance Interview Topics
QUANT_THEMES = {
    "[CV_TECHNIQUES]": "Cross-validation, K-Fold, Walk-Forward, backtesting, out-of-sample robustness.",
    "[REGULARIZATION]": "L1/L2 regularization, Lasso, Ridge, preventing overfitting via coefficient penalty.",
    "[FEATURE_SELECTION]": "Variable selection, feature engineering, SHAP, LIME, PCA, feature importance.",
    "[STATIONARITY]": "Stationarity, non-stationarity, unit root tests (ADF, KPSS), co-integration.",
    "[TIME_SERIES_MODELS]": "Specific time series models (ARIMA, GARCH, VAR), volatility modeling.",
    "[OPTIMIZATION_PYTHON]": "Python code performance, vectorization, NumPy, Pandas, Numba, Cython.",
    "[LOOKAHEAD_BIAS]": "Look-ahead bias, future data leakage, common backtesting errors.",
    "[DATA_PIPELINE]": "Data cleaning, ingestion, ETL pipelines, market data management.",
    "[BEHAVIORAL_PRESSURE]": "Handling stress, tight deadlines, crisis situations.",
    "[BEHAVIORAL_TEAMWORK]": "Collaboration, conflict management, communication with PMs or traders.",
    "[EXTRA]": "Off-topic questions, greetings, transitions, questions about the job."
}


class InterviewEvaluator:
    """
    Evaluates interview quality using Claude LLM

    Analyzes:
    - Subject relevance (is content on-topic?)
    - Question difficulty (easy/medium/hard)
    - Interviewer tone (harsh/neutral/encouraging)
    - Key topics and flags
    """

    # Evaluation prompt template with Hugo's Quant Finance themes
    EVALUATION_PROMPT = """You are an expert Quant Finance interview evaluator analyzing a live interview conversation.

<themes_to_track>
Here are the Quant Finance topics we track (read descriptions carefully):
{themes_list}
</themes_to_track>

<conversation>
{conversation}
</conversation>

Analyze this interview excerpt and provide structured evaluation:

1. QUANT THEMES: Identify ALL themes from the list above that were discussed (by recruiter OR candidate)
   - Respond with a Python-style list of theme tags, e.g., ["[CV_TECHNIQUES]", "[REGULARIZATION]"]
   - If discussing off-topic/casual content, include ["[EXTRA]"]
   - If NO themes match, return []

2. SUBJECT RELEVANCE: Overall relevance to Quant Finance interview
   - on_topic: Discussing technical Quant Finance topics (any theme except [EXTRA])
   - partially_relevant: Mix of relevant and off-topic ([EXTRA] + technical themes)
   - off_topic: Mostly casual chat, greetings, transitions (only [EXTRA])

3. QUESTION DIFFICULTY: Technical depth of questions asked
   - easy: Basic definitions, simple explanations (e.g., "What is cross-validation?")
   - medium: Moderate depth, practical applications (e.g., "How would you validate a trading model?")
   - hard: Advanced problems, edge cases (e.g., "Explain look-ahead bias in walk-forward validation")
   - unknown: No clear technical questions asked

4. INTERVIEWER TONE: Demeanor and communication style
   - harsh: Aggressive, dismissive, overly critical, interrupting
   - neutral: Professional, balanced, objective
   - encouraging: Supportive, friendly, helpful, positive feedback
   - unknown: Insufficient data

5. SUMMARY: 1-2 sentence summary of what was discussed

6. FLAGS: Note concerns (e.g., "Harsh tone detected", "Off-topic discussion", "Look-ahead bias mentioned but not explained")

7. CONFIDENCE: Rate confidence in each assessment (0.0-1.0)

Respond ONLY with valid JSON in this exact format:
{{
    "quant_themes": ["[THEME1]", "[THEME2]", ...] or [],
    "subject_relevance": "on_topic" | "partially_relevant" | "off_topic" | "unknown",
    "question_difficulty": "easy" | "medium" | "hard" | "unknown",
    "interviewer_tone": "harsh" | "neutral" | "encouraging" | "unknown",
    "summary": "brief summary here",
    "flags": ["flag1", "flag2", ...] or [],
    "confidence_subject": 0.0-1.0,
    "confidence_difficulty": 0.0-1.0,
    "confidence_tone": 0.0-1.0
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize evaluator

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

        logger.info(f"✅ InterviewEvaluator initialized with model: {model}")

    async def evaluate(self, window: BufferedWindow) -> EvaluationResult:
        """
        Evaluate a window of transcripts

        Args:
            window: BufferedWindow containing transcripts to evaluate

        Returns:
            EvaluationResult with LLM assessment
        """
        logger.info(
            f"🤖 Evaluating window: {len(window)} transcripts, "
            f"{window.duration_seconds():.1f}s duration"
        )

        try:
            # Format conversation for LLM
            conversation_text = window.get_text(include_speakers=True)

            # Format themes list
            themes_list = "\n".join([f"{tag}: {desc}" for tag, desc in QUANT_THEMES.items()])

            # Build prompt
            prompt = self.EVALUATION_PROMPT.format(
                themes_list=themes_list,
                conversation=conversation_text
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response text
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON response
            evaluation_data = self._parse_response(response_text)

            # Extract quant themes (Hugo's format)
            quant_themes = evaluation_data.get("quant_themes", [])

            # Use quant themes as key_topics, clean up the brackets
            key_topics = [theme.strip("[]") for theme in quant_themes if theme != "[EXTRA]"]

            # Add [EXTRA] to flags if present
            flags = evaluation_data.get("flags", [])
            if "[EXTRA]" in quant_themes:
                flags.append("Off-topic/casual discussion detected ([EXTRA])")

            # Create EvaluationResult
            result = EvaluationResult(
                timestamp=datetime.now(),
                window_start=window.window_start,
                window_end=window.window_end,
                transcripts_evaluated=len(window),
                subject_relevance=SubjectRelevance(evaluation_data["subject_relevance"]),
                question_difficulty=QuestionDifficulty(evaluation_data["question_difficulty"]),
                interviewer_tone=InterviewerTone(evaluation_data["interviewer_tone"]),
                summary=evaluation_data["summary"],
                key_topics=key_topics,  # Quant themes without brackets
                flags=flags,
                confidence_subject=evaluation_data["confidence_subject"],
                confidence_difficulty=evaluation_data["confidence_difficulty"],
                confidence_tone=evaluation_data["confidence_tone"],
                raw_llm_response=response_text
            )

            logger.info(
                f"✅ Evaluation complete: "
                f"relevance={result.subject_relevance.value}, "
                f"difficulty={result.question_difficulty.value}, "
                f"tone={result.interviewer_tone.value}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error during evaluation: {e}", exc_info=True)
            # Return unknown/error result
            return self._create_error_result(window, str(e))

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
        # Try to extract JSON from response
        # Claude sometimes adds markdown formatting
        response_text = response_text.strip()

        # Remove markdown code blocks if present
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
                "quant_themes",
                "subject_relevance",
                "question_difficulty",
                "interviewer_tone",
                "summary",
                "confidence_subject",
                "confidence_difficulty",
                "confidence_tone"
            ]

            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_error_result(self, window: BufferedWindow, error_msg: str) -> EvaluationResult:
        """
        Create an error evaluation result

        Args:
            window: The window that failed evaluation
            error_msg: Error message

        Returns:
            EvaluationResult with unknown values and error flag
        """
        return EvaluationResult(
            timestamp=datetime.now(),
            window_start=window.window_start,
            window_end=window.window_end,
            transcripts_evaluated=len(window),
            subject_relevance=SubjectRelevance.UNKNOWN,
            question_difficulty=QuestionDifficulty.UNKNOWN,
            interviewer_tone=InterviewerTone.UNKNOWN,
            summary=f"Evaluation failed: {error_msg}",
            key_topics=[],
            flags=[f"EVALUATION_ERROR: {error_msg}"],
            confidence_subject=0.0,
            confidence_difficulty=0.0,
            confidence_tone=0.0,
            raw_llm_response=None
        )
