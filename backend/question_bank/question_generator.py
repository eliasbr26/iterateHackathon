"""
Question Generator - PILLAR 3.1

Generates tailored interview questions using Claude AI based on:
- Target competency
- Difficulty level
- Candidate background
- Interview context

Produces high-quality behavioral, technical, and situational questions.
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Generates intelligent, context-aware interview questions
    Uses Claude to create tailored questions based on competency and candidate profile
    """

    GENERATION_PROMPT = """You are an expert interview coach helping generate high-quality interview questions.

<context>
Target Competency: {competency}
Difficulty Level: {difficulty}
Question Type: {question_type}
Count Requested: {count}
</context>

<candidate_background>
{candidate_info}
</candidate_background>

Generate {count} high-quality interview questions that:

1. **Target the competency**: Focus specifically on {competency}
2. **Match difficulty**: {difficulty} level questions appropriate for the candidate's background
3. **Follow best practices**:
   - Behavioral questions MUST use STAR format (Situation, Task, Action, Result)
   - Technical questions should probe depth and understanding
   - Situational questions should be realistic and job-relevant
4. **Be specific and actionable**: Avoid generic questions
5. **Encourage detailed responses**: Questions should elicit comprehensive answers

For EACH question, provide:
- The question text
- 2-3 potential follow-up questions
- Evaluation criteria (what to look for in a good answer)
- Expected STAR components (if behavioral)

Respond ONLY with valid JSON in this exact format:
{{
    "questions": [
        {{
            "question": "the interview question text",
            "competency": "{competency}",
            "difficulty": "{difficulty}",
            "type": "{question_type}",
            "follow_ups": ["follow-up question 1", "follow-up question 2"],
            "evaluation_criteria": ["criterion 1", "criterion 2", "criterion 3"],
            "expected_star_components": ["Situation", "Task", "Action", "Result"],
            "reasoning": "why this question is effective for this competency/candidate"
        }}
    ]
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize question generator

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ QuestionGenerator initialized with model: {model}")

    async def generate_questions(
        self,
        competency: str,
        difficulty: str = "medium",
        question_type: str = "behavioral",
        candidate_background: Optional[Dict] = None,
        count: int = 3
    ) -> List[Dict]:
        """
        Generate interview questions

        Args:
            competency: Target competency (leadership, problem_solving, etc.)
            difficulty: easy, medium, or hard
            question_type: behavioral, technical, or situational
            candidate_background: Candidate CV/profile data
            count: Number of questions to generate

        Returns:
            List of question dictionaries
        """
        logger.info(
            f"🎯 Generating {count} {difficulty} {question_type} questions "
            f"for competency: {competency}"
        )

        try:
            # Format candidate info
            candidate_info = self._format_candidate_background(candidate_background)

            # Build prompt
            prompt = self.GENERATION_PROMPT.format(
                competency=competency,
                difficulty=difficulty,
                question_type=question_type,
                count=count,
                candidate_info=candidate_info
            )

            # Call Claude API
            logger.debug("📡 Calling Claude API for question generation...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
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
            for question in result.get("questions", []):
                question["generated_at"] = datetime.utcnow().isoformat()
                question["model_used"] = self.model

            logger.info(f"✅ Generated {len(result.get('questions', []))} questions")

            return result.get("questions", [])

        except Exception as e:
            logger.error(f"❌ Error generating questions: {e}", exc_info=True)
            return self._create_fallback_questions(competency, difficulty, question_type, count)

    def _format_candidate_background(self, background: Optional[Dict]) -> str:
        """Format candidate background into readable text"""
        if not background:
            return "No candidate background provided - generate general questions"

        parts = []

        if "personal_info" in background:
            info = background["personal_info"]
            if info.get("name"):
                parts.append(f"Name: {info['name']}")

        if "experience" in background:
            exp = background["experience"]
            if exp.get("years_of_experience"):
                parts.append(f"Experience: {exp['years_of_experience']} years")
            if exp.get("current_role"):
                parts.append(f"Current Role: {exp['current_role']}")
            if exp.get("companies"):
                companies = ", ".join(exp["companies"][:3])
                parts.append(f"Companies: {companies}")

        if "skills" in background:
            skills = background["skills"]
            if skills.get("technical_skills"):
                tech = ", ".join(skills["technical_skills"][:5])
                parts.append(f"Technical Skills: {tech}")

        if "education" in background:
            edu = background["education"]
            if edu.get("degrees"):
                degree = edu["degrees"][0] if edu["degrees"] else None
                if degree:
                    parts.append(f"Education: {degree.get('degree', 'N/A')} in {degree.get('field', 'N/A')}")

        return "\n".join(parts) if parts else "General candidate profile"

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed question data

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
            if "questions" not in data:
                raise ValueError("Missing 'questions' field")

            for q in data["questions"]:
                required = ["question", "competency", "difficulty", "type"]
                for field in required:
                    if field not in q:
                        raise ValueError(f"Question missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_fallback_questions(
        self,
        competency: str,
        difficulty: str,
        question_type: str,
        count: int
    ) -> List[Dict]:
        """
        Create fallback questions if AI generation fails

        Args:
            competency: Target competency
            difficulty: Difficulty level
            question_type: Type of question
            count: Number of questions needed

        Returns:
            List of fallback question dictionaries
        """
        logger.warning(f"⚠️ Using fallback questions for {competency}")

        # Fallback question templates
        fallback_templates = {
            "leadership": {
                "behavioral": [
                    "Tell me about a time when you led a team through a challenging project.",
                    "Describe a situation where you had to make an unpopular decision as a leader.",
                    "Give me an example of how you motivated a team member who was struggling."
                ],
                "technical": [
                    "How do you approach mentoring junior team members?",
                    "What's your leadership philosophy when it comes to code reviews?",
                    "Describe your approach to technical decision-making in a team setting."
                ]
            },
            "problem_solving": {
                "behavioral": [
                    "Tell me about the most complex problem you've solved in your career.",
                    "Describe a time when you had to debug a critical production issue.",
                    "Give me an example of how you approached a problem with incomplete information."
                ],
                "technical": [
                    "Walk me through how you would debug a performance bottleneck.",
                    "How do you approach system design for scalability?",
                    "Explain your problem-solving process for a complex algorithm."
                ]
            },
            "communication": {
                "behavioral": [
                    "Tell me about a time when you had to explain a complex technical concept to a non-technical stakeholder.",
                    "Describe a situation where miscommunication caused a problem and how you resolved it.",
                    "Give me an example of how you've handled a difficult conversation with a colleague."
                ]
            },
            "teamwork": {
                "behavioral": [
                    "Tell me about a time when you collaborated with a difficult team member.",
                    "Describe your most successful team project and your role in it.",
                    "Give me an example of how you've contributed to improving team dynamics."
                ]
            }
        }

        # Get templates for this competency, or use generic
        comp_questions = fallback_templates.get(competency, {
            "behavioral": [
                f"Tell me about a time when you demonstrated {competency}.",
                f"Describe a situation where {competency} was particularly important.",
                f"Give me an example of how you've developed your {competency} skills."
            ]
        })

        type_questions = comp_questions.get(question_type, comp_questions.get("behavioral", []))

        # Create question objects
        questions = []
        for i in range(min(count, len(type_questions))):
            questions.append({
                "question": type_questions[i],
                "competency": competency,
                "difficulty": difficulty,
                "type": question_type,
                "follow_ups": [
                    "Can you provide more specific details about the situation?",
                    "What was the outcome and impact?",
                    "What would you do differently if you faced this situation again?"
                ],
                "evaluation_criteria": [
                    "Specificity and detail",
                    "Clear demonstration of competency",
                    "Measurable outcomes"
                ],
                "expected_star_components": ["Situation", "Task", "Action", "Result"] if question_type == "behavioral" else [],
                "reasoning": "Fallback question template",
                "generated_at": datetime.utcnow().isoformat(),
                "model_used": "fallback",
                "is_fallback": True
            })

        return questions

    def batch_generate(
        self,
        competencies: List[str],
        difficulty: str = "medium",
        question_type: str = "behavioral",
        questions_per_competency: int = 3
    ) -> Dict[str, List[Dict]]:
        """
        Generate questions for multiple competencies in batch

        Args:
            competencies: List of competencies
            difficulty: Difficulty level
            question_type: Type of questions
            questions_per_competency: How many per competency

        Returns:
            Dict mapping competency -> list of questions
        """
        logger.info(f"📦 Batch generating questions for {len(competencies)} competencies")

        results = {}
        for competency in competencies:
            try:
                questions = self.generate_questions(
                    competency=competency,
                    difficulty=difficulty,
                    question_type=question_type,
                    count=questions_per_competency
                )
                results[competency] = questions
            except Exception as e:
                logger.error(f"Failed to generate questions for {competency}: {e}")
                results[competency] = []

        logger.info(f"✅ Batch generation complete: {sum(len(q) for q in results.values())} total questions")

        return results
