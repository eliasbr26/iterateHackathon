"""
LLM-powered interview evaluation system

Uses Anthropic Claude to analyze interview transcripts in real-time

Based on Hugo's comprehensive Quant Finance topic taxonomy
"""

import logging
import json
from datetime import datetime
from typing import List
from anthropic import Anthropic

from audio_pipeline.models import (
    BufferedWindow,
    EvaluationResult,
    QuestionDifficulty,
    InterviewerTone,
    SubjectRelevance,
    CoachingFlag,
    CoachingFlagType,
    InterviewerTechniqueAssessment,
    InterviewerTechniqueQuality,
    CoachingPoint,
    InterviewerPerformanceReport
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

    # Enhanced evaluation prompt with interviewer coaching
    COACHING_EVALUATION_PROMPT = """You are an expert Quant Finance interview coach analyzing a live interview to provide feedback to the INTERVIEWER.

Your goal is to help the interviewer improve their questioning techniques and interview skills.

<themes_to_track>
Here are the Quant Finance topics we track:
{themes_list}
</themes_to_track>

<conversation>
{conversation}
</conversation>

Analyze this interview excerpt focusing on the INTERVIEWER's performance:

1. QUANT THEMES: Identify ALL themes discussed
   - Respond with list: ["[CV_TECHNIQUES]", "[REGULARIZATION]", ...] or []

2. SUBJECT RELEVANCE: Overall relevance
   - on_topic / partially_relevant / off_topic / unknown

3. QUESTION DIFFICULTY: Technical depth
   - easy / medium / hard / unknown

4. INTERVIEWER TONE: Communication style
   - harsh / neutral / encouraging / unknown

5. INTERVIEWER TECHNIQUE: Assess questioning skills
   - open_ended_ratio: Estimate % of open-ended questions (0.0-1.0)
     * Open-ended: "How...", "Why...", "Tell me about...", "Explain..."
     * Closed: Yes/no, single-word answers, "Did you...", "Is it..."
   - question_quality: poor / fair / good / excellent
     * Poor: Only closed/leading questions
     * Fair: Mix with some open questions
     * Good: Mostly open, few leading
     * Excellent: All open, probing, no leading
   - follow_up_effectiveness: poor / fair / good / excellent
     * Assess if interviewer probes deeper when candidate mentions interesting concepts

6. COACHING FLAGS: Specific, actionable feedback for the interviewer
   Identify issues and provide suggestions. Each flag should have:
   - type: leading_question / missed_followup / closed_question / positive / speaking_too_much / unclear_question / great_probing
   - severity: info / warning / critical
   - message: Clear description of the issue or positive moment
   - suggestion: Actionable advice (for issues)
   - example_good: How to rephrase (for questions)
   - context_quote: Relevant quote from conversation

   Examples:
   * Leading question: {{"type": "leading_question", "severity": "warning", "message": "Question suggested the answer", "suggestion": "Ask: 'How would you validate?' instead of 'Would you use cross-validation?'", "example_good": "How would you approach model validation?", "context_quote": "Would you use cross-validation?"}}
   * Missed follow-up: {{"type": "missed_followup", "severity": "info", "message": "Candidate mentioned 'co-integration' but wasn't asked to elaborate", "suggestion": "Try: 'Tell me more about how you test for co-integration'", "context_quote": "...mentioned co-integration..."}}
   * Positive: {{"type": "positive", "severity": "info", "message": "Excellent open-ended question", "context_quote": "How did you handle non-stationarity?"}}

7. SUMMARY: 1-2 sentences on what was discussed

8. CONFIDENCE: Rate confidence (0.0-1.0) for each assessment

Respond ONLY with valid JSON:
{{
    "quant_themes": ["[THEME1]", ...],
    "subject_relevance": "on_topic|partially_relevant|off_topic|unknown",
    "question_difficulty": "easy|medium|hard|unknown",
    "interviewer_tone": "harsh|neutral|encouraging|unknown",
    "interviewer_technique": {{
        "open_ended_ratio": 0.0-1.0,
        "question_quality": "poor|fair|good|excellent",
        "follow_up_effectiveness": "poor|fair|good|excellent",
        "confidence": 0.0-1.0
    }},
    "coaching_flags": [
        {{
            "type": "leading_question|missed_followup|closed_question|positive|speaking_too_much|unclear_question|great_probing",
            "severity": "info|warning|critical",
            "message": "description",
            "suggestion": "actionable advice or null",
            "example_good": "better phrasing or null",
            "context_quote": "relevant quote or null"
        }}
    ],
    "summary": "brief summary",
    "confidence_subject": 0.0-1.0,
    "confidence_difficulty": 0.0-1.0,
    "confidence_tone": 0.0-1.0
}}"""

    # Evaluation prompt template with Hugo's Quant Finance themes (legacy)
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

            # Build prompt (use coaching-focused prompt)
            prompt = self.COACHING_EVALUATION_PROMPT.format(
                themes_list=themes_list,
                conversation=conversation_text
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1536,  # Increased for coaching flags
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response text
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON response
            evaluation_data = self._parse_coaching_response(response_text)

            # Extract quant themes (Hugo's format)
            quant_themes = evaluation_data.get("quant_themes", [])

            # Use quant themes as key_topics, clean up the brackets
            key_topics = [theme.strip("[]") for theme in quant_themes if theme != "[EXTRA]"]

            # Add [EXTRA] to flags if present
            flags = evaluation_data.get("flags", [])
            if "[EXTRA]" in quant_themes:
                flags.append("Off-topic/casual discussion detected ([EXTRA])")

            # Parse interviewer technique
            interviewer_technique = None
            if "interviewer_technique" in evaluation_data:
                tech_data = evaluation_data["interviewer_technique"]
                interviewer_technique = InterviewerTechniqueAssessment(
                    open_ended_ratio=tech_data.get("open_ended_ratio", 0.5),
                    question_quality=InterviewerTechniqueQuality(tech_data.get("question_quality", "unknown")),
                    follow_up_effectiveness=InterviewerTechniqueQuality(tech_data.get("follow_up_effectiveness", "unknown")),
                    confidence=tech_data.get("confidence", 0.0)
                )

            # Parse coaching flags
            coaching_flags = []
            if "coaching_flags" in evaluation_data:
                for flag_data in evaluation_data["coaching_flags"]:
                    try:
                        coaching_flag = CoachingFlag(
                            type=CoachingFlagType(flag_data["type"]),
                            severity=flag_data["severity"],
                            message=flag_data["message"],
                            suggestion=flag_data.get("suggestion"),
                            example_good=flag_data.get("example_good"),
                            example_bad=flag_data.get("example_bad"),
                            context_quote=flag_data.get("context_quote")
                        )
                        coaching_flags.append(coaching_flag)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse coaching flag: {e}")
                        continue

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
                coaching_flags=coaching_flags,
                interviewer_technique=interviewer_technique,
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

    def _parse_coaching_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response for coaching evaluation

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed evaluation dictionary

        Raises:
            ValueError: If response cannot be parsed
        """
        # Clean JSON response
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

            # Optional fields with defaults
            if "interviewer_technique" not in data:
                data["interviewer_technique"] = {
                    "open_ended_ratio": 0.5,
                    "question_quality": "unknown",
                    "follow_up_effectiveness": "unknown",
                    "confidence": 0.0
                }

            if "coaching_flags" not in data:
                data["coaching_flags"] = []

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response (legacy method for backward compatibility)

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

    async def evaluate_interviewer_performance(
        self,
        all_transcripts: List,
        evaluation_history: List[EvaluationResult]
    ) -> InterviewerPerformanceReport:
        """
        Generate comprehensive performance report for interviewer across entire session

        This method analyzes all transcripts and evaluation history to provide:
        - Overall performance score
        - Key strengths
        - Areas for improvement
        - Detailed metrics and breakdowns

        Args:
            all_transcripts: Complete list of transcripts from the session
            evaluation_history: All evaluations performed during the session

        Returns:
            InterviewerPerformanceReport with comprehensive assessment
        """
        logger.info(f"📊 Generating interviewer performance report: {len(all_transcripts)} transcripts, {len(evaluation_history)} evaluations")

        # Calculate session duration
        if all_transcripts and len(all_transcripts) > 0:
            session_start = all_transcripts[0].timestamp
            session_end = all_transcripts[-1].timestamp
            session_duration = (session_end - session_start).total_seconds()
        else:
            session_duration = 0.0

        # Count questions (approximate by counting interviewer transcripts ending with '?')
        interviewer_transcripts = [t for t in all_transcripts if t.speaker == "recruiter"]
        total_questions = sum(1 for t in interviewer_transcripts if '?' in t.text)

        # Aggregate metrics from evaluation history
        metrics = self._calculate_aggregated_metrics(evaluation_history, all_transcripts)

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)

        # Extract strengths
        strengths = self._extract_strengths(evaluation_history, metrics)

        # Extract improvements
        improvements = self._extract_improvements(evaluation_history, metrics)

        # Detailed breakdowns
        question_quality_breakdown = self._analyze_question_quality(evaluation_history)
        topic_coverage = self._analyze_topic_coverage(evaluation_history)
        tone_analysis = self._analyze_tone(evaluation_history)

        report = InterviewerPerformanceReport(
            overall_score=overall_score,
            session_duration_seconds=session_duration,
            total_questions_asked=total_questions,
            strengths=strengths,
            improvements=improvements,
            metrics=metrics,
            question_quality_breakdown=question_quality_breakdown,
            topic_coverage=topic_coverage,
            tone_analysis=tone_analysis
        )

        logger.info(f"✅ Performance report generated: overall_score={overall_score:.1f}/10")
        return report

    def _calculate_aggregated_metrics(self, evaluations: List[EvaluationResult], transcripts: List) -> dict:
        """Calculate aggregated metrics from evaluation history"""
        if not evaluations:
            return {
                "open_ended_ratio": 0.0,
                "follow_up_rate": 0.0,
                "speaking_time_ratio": 0.0,
                "avg_difficulty": "unknown",
                "tone_consistency": "unknown"
            }

        # Open-ended ratio (from interviewer_technique)
        open_ended_ratios = [
            e.interviewer_technique.open_ended_ratio
            for e in evaluations
            if e.interviewer_technique and e.interviewer_technique.open_ended_ratio > 0
        ]
        avg_open_ended_ratio = sum(open_ended_ratios) / len(open_ended_ratios) if open_ended_ratios else 0.0

        # Follow-up effectiveness (convert quality to numeric)
        quality_map = {"poor": 0.25, "fair": 0.5, "good": 0.75, "excellent": 1.0, "unknown": 0.5}
        follow_up_scores = [
            quality_map.get(e.interviewer_technique.follow_up_effectiveness.value, 0.5)
            for e in evaluations
            if e.interviewer_technique
        ]
        avg_follow_up = sum(follow_up_scores) / len(follow_up_scores) if follow_up_scores else 0.5

        # Speaking time ratio (interviewer vs total)
        if transcripts:
            interviewer_words = sum(len(t.text.split()) for t in transcripts if t.speaker == "recruiter")
            total_words = sum(len(t.text.split()) for t in transcripts)
            speaking_ratio = interviewer_words / total_words if total_words > 0 else 0.5
        else:
            speaking_ratio = 0.5

        # Average difficulty
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0, "unknown": 0}
        for e in evaluations:
            difficulty_counts[e.question_difficulty.value] += 1
        max_difficulty = max(difficulty_counts, key=difficulty_counts.get)

        # Tone consistency
        tones = [e.interviewer_tone.value for e in evaluations if e.interviewer_tone.value != "unknown"]
        if tones:
            most_common_tone = max(set(tones), key=tones.count)
            consistency_ratio = tones.count(most_common_tone) / len(tones)
            if consistency_ratio > 0.8:
                tone_consistency = "high"
            elif consistency_ratio > 0.5:
                tone_consistency = "medium"
            else:
                tone_consistency = "low"
        else:
            tone_consistency = "unknown"

        return {
            "open_ended_ratio": round(avg_open_ended_ratio, 2),
            "follow_up_rate": round(avg_follow_up, 2),
            "speaking_time_ratio": round(speaking_ratio, 2),
            "avg_difficulty": max_difficulty,
            "tone_consistency": tone_consistency
        }

    def _calculate_overall_score(self, metrics: dict) -> float:
        """Calculate overall interviewer performance score (0-10)"""
        # Weight different factors
        score = 0.0

        # Open-ended ratio (0-3 points): Higher is better
        score += metrics["open_ended_ratio"] * 3

        # Follow-up rate (0-2 points): Higher is better
        score += metrics["follow_up_rate"] * 2

        # Speaking time ratio (0-2 points): Ideal is 30-40%, penalize extremes
        speaking_ratio = metrics["speaking_time_ratio"]
        if 0.3 <= speaking_ratio <= 0.4:
            score += 2.0  # Ideal range
        elif 0.2 <= speaking_ratio < 0.3 or 0.4 < speaking_ratio <= 0.5:
            score += 1.5  # Acceptable
        elif speaking_ratio < 0.2 or speaking_ratio > 0.5:
            score += 0.5  # Poor

        # Difficulty progression (0-2 points)
        if metrics["avg_difficulty"] == "hard":
            score += 2.0
        elif metrics["avg_difficulty"] == "medium":
            score += 1.5
        elif metrics["avg_difficulty"] == "easy":
            score += 1.0

        # Tone consistency (0-1 point)
        if metrics["tone_consistency"] == "high":
            score += 1.0
        elif metrics["tone_consistency"] == "medium":
            score += 0.5

        return round(score, 1)

    def _extract_strengths(self, evaluations: List[EvaluationResult], metrics: dict) -> List[CoachingPoint]:
        """Extract interviewer strengths from evaluations"""
        strengths = []

        # Positive coaching flags
        positive_flags = []
        for eval in evaluations:
            positive_flags.extend([
                cf for cf in eval.coaching_flags
                if cf.type == CoachingFlagType.POSITIVE or cf.type == CoachingFlagType.GREAT_PROBING
            ])

        if positive_flags:
            # Group by message similarity (simple: just take unique messages)
            unique_positives = {cf.message: cf for cf in positive_flags}.values()
            for cf in list(unique_positives)[:3]:  # Top 3
                strengths.append(CoachingPoint(
                    category="question_quality",
                    title="Excellent Questioning Technique",
                    description=cf.message,
                    examples=[cf.context_quote] if cf.context_quote else [],
                    score=9.0
                ))

        # High open-ended ratio
        if metrics["open_ended_ratio"] > 0.7:
            strengths.append(CoachingPoint(
                category="question_quality",
                title="Strong Use of Open-Ended Questions",
                description=f"Maintained {metrics['open_ended_ratio']:.0%} open-ended questions throughout the interview",
                examples=["Examples of effective open questions were used consistently"],
                score=8.5
            ))

        # Good follow-up rate
        if metrics["follow_up_rate"] > 0.7:
            strengths.append(CoachingPoint(
                category="follow_up",
                title="Effective Follow-Up Questions",
                description="Consistently probed deeper when candidates mentioned interesting concepts",
                score=8.0
            ))

        # Ideal speaking balance
        if 0.3 <= metrics["speaking_time_ratio"] <= 0.4:
            strengths.append(CoachingPoint(
                category="speaking_balance",
                title="Optimal Speaking Balance",
                description=f"Maintained ideal interviewer-candidate balance ({metrics['speaking_time_ratio']:.0%} interviewer speaking time)",
                score=9.0
            ))

        return strengths[:5]  # Top 5 strengths

    def _extract_improvements(self, evaluations: List[EvaluationResult], metrics: dict) -> List[CoachingPoint]:
        """Extract improvement areas for the interviewer"""
        improvements = []

        # Analyze coaching flags for issues
        issue_flags = []
        for eval in evaluations:
            issue_flags.extend([
                cf for cf in eval.coaching_flags
                if cf.type in [CoachingFlagType.LEADING_QUESTION, CoachingFlagType.CLOSED_QUESTION,
                               CoachingFlagType.MISSED_FOLLOWUP, CoachingFlagType.UNCLEAR_QUESTION]
            ])

        # Group by type
        flag_groups = {}
        for cf in issue_flags:
            if cf.type.value not in flag_groups:
                flag_groups[cf.type.value] = []
            flag_groups[cf.type.value].append(cf)

        # Create improvements from most common issues
        for flag_type, flags in sorted(flag_groups.items(), key=lambda x: len(x[1]), reverse=True)[:3]:
            suggestions = list(set([cf.suggestion for cf in flags if cf.suggestion]))[:3]

            improvements.append(CoachingPoint(
                category="question_quality",
                title=self._flag_type_to_title(flag_type),
                description=f"Detected {len(flags)} instances of {flag_type.replace('_', ' ')}",
                examples=[cf.context_quote for cf in flags[:2] if cf.context_quote],
                suggestions=suggestions,
                severity="high" if len(flags) > 5 else "medium"
            ))

        # Low open-ended ratio
        if metrics["open_ended_ratio"] < 0.4:
            improvements.append(CoachingPoint(
                category="question_quality",
                title="Increase Open-Ended Questions",
                description=f"Only {metrics['open_ended_ratio']:.0%} of questions were open-ended",
                suggestions=[
                    "Use 'How...', 'Why...', 'Tell me about...' instead of yes/no questions",
                    "Avoid questions starting with 'Did you...', 'Is it...', 'Have you...'"
                ],
                severity="high"
            ))

        # Poor follow-up rate
        if metrics["follow_up_rate"] < 0.4:
            improvements.append(CoachingPoint(
                category="follow_up",
                title="Missed Follow-Up Opportunities",
                description="Several interesting concepts mentioned by candidate were not explored",
                suggestions=[
                    "When candidate mentions technical concept, ask: 'Can you tell me more about...'",
                    "Listen for keywords and probe deeper: 'How did you implement that?'"
                ],
                severity="medium"
            ))

        # Speaking too much or too little
        if metrics["speaking_time_ratio"] > 0.5:
            improvements.append(CoachingPoint(
                category="speaking_balance",
                title="Speaking Too Much",
                description=f"Interviewer spoke {metrics['speaking_time_ratio']:.0%} of the time (ideal: 30-40%)",
                suggestions=[
                    "Ask question, then let candidate speak",
                    "Avoid lengthy explanations - keep questions concise",
                    "Use silence effectively to encourage candidate elaboration"
                ],
                severity="high"
            ))
        elif metrics["speaking_time_ratio"] < 0.2:
            improvements.append(CoachingPoint(
                category="speaking_balance",
                title="Not Engaging Enough",
                description=f"Interviewer only spoke {metrics['speaking_time_ratio']:.0%} of the time",
                suggestions=[
                    "Ask more probing follow-up questions",
                    "Provide context for questions when needed",
                    "Guide the conversation more actively"
                ],
                severity="medium"
            ))

        return improvements[:5]  # Top 5 improvements

    def _flag_type_to_title(self, flag_type: str) -> str:
        """Convert flag type to human-readable title"""
        titles = {
            "leading_question": "Reduce Leading Questions",
            "closed_question": "Avoid Closed Questions",
            "missed_followup": "Follow Up More Consistently",
            "unclear_question": "Improve Question Clarity"
        }
        return titles.get(flag_type, flag_type.replace("_", " ").title())

    def _analyze_question_quality(self, evaluations: List[EvaluationResult]) -> dict:
        """Analyze question quality distribution"""
        quality_counts = {"poor": 0, "fair": 0, "good": 0, "excellent": 0, "unknown": 0}
        for eval in evaluations:
            if eval.interviewer_technique:
                quality_counts[eval.interviewer_technique.question_quality.value] += 1

        total = sum(quality_counts.values())
        return {
            quality: count / total if total > 0 else 0
            for quality, count in quality_counts.items()
        }

    def _analyze_topic_coverage(self, evaluations: List[EvaluationResult]) -> dict:
        """Analyze which topics were covered"""
        topic_counts = {}
        for eval in evaluations:
            for topic in eval.key_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        return {
            "total_unique_topics": len(topic_counts),
            "topic_counts": topic_counts,
            "coverage_percentage": round(len(topic_counts) / 11 * 100, 1)  # 11 total quant topics
        }

    def _analyze_tone(self, evaluations: List[EvaluationResult]) -> dict:
        """Analyze interviewer tone patterns"""
        tone_counts = {"harsh": 0, "neutral": 0, "encouraging": 0, "unknown": 0}
        for eval in evaluations:
            tone_counts[eval.interviewer_tone.value] += 1

        total = sum(tone_counts.values())
        return {
            "distribution": {
                tone: count / total if total > 0 else 0
                for tone, count in tone_counts.items()
            },
            "predominant_tone": max(tone_counts, key=tone_counts.get)
        }
