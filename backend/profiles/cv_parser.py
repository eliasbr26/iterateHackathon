"""
CV Parser - PILLAR 6.1

Parses candidate CVs/resumes and extracts structured information:
- Personal information
- Career summary
- Work experience (roles, companies, dates, achievements)
- Education
- Skills (technical, soft skills)
- Projects
- Certifications
- Languages
- Publications/Patents

Generates:
- Skill graph (skill -> proficiency level)
- Experience matrix (role x skill)
- Seniority assessment
- Career trajectory analysis
- Risk flags (gaps, short tenures, etc.)
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class CVParser:
    """
    Parses CV/resume text and extracts structured information
    Uses Claude to intelligently parse and analyze CVs
    """

    CV_PARSING_PROMPT = """You are an expert CV/resume parser. Extract ALL relevant information from this CV in a structured format.

<cv_text>
{cv_text}
</cv_text>

Extract and structure the following information:

1. **Personal Information**
   - Name, email, phone, location (if available)

2. **Professional Summary**
   - Brief career summary (2-3 sentences)
   - Years of experience
   - Current/most recent role and seniority level

3. **Work Experience**
   For each role, extract:
   - Company name
   - Job title
   - Start date, end date (or "Present")
   - Duration in months
   - Key responsibilities (bullet points)
   - Achievements (quantified when possible)
   - Technologies/skills used

4. **Education**
   - Degree, field of study
   - Institution
   - Graduation year
   - GPA (if mentioned)

5. **Skills**
   - Technical skills (with proficiency level: beginner/intermediate/advanced/expert if inferable)
   - Soft skills
   - Tools & technologies

6. **Projects** (if mentioned)
   - Project name
   - Description
   - Technologies used
   - Impact/results

7. **Certifications** (if any)

8. **Languages** (if mentioned)

9. **Publications/Patents** (if any)

10. **Analysis & Insights**
    - Seniority level: junior/mid/senior/staff/principal/executive
    - Career trajectory: ascending/stable/descending/mixed
    - Industry focus areas
    - Strengths (top 3)
    - Potential concerns/red flags:
      - Employment gaps > 6 months
      - Short tenures (< 1 year)
      - Frequent job changes
      - Lack of progression
      - Vague achievements

Respond ONLY with valid JSON in this exact format:
{{
    "personal_info": {{
        "name": "...",
        "email": "...",
        "phone": "...",
        "location": "..."
    }},
    "professional_summary": {{
        "summary": "...",
        "total_years_experience": 0,
        "current_role": "...",
        "seniority_level": "junior|mid|senior|staff|principal|executive"
    }},
    "work_experience": [
        {{
            "company": "...",
            "title": "...",
            "start_date": "YYYY-MM",
            "end_date": "YYYY-MM or Present",
            "duration_months": 0,
            "responsibilities": ["...", "..."],
            "achievements": ["...", "..."],
            "skills_used": ["...", "..."]
        }}
    ],
    "education": [
        {{
            "degree": "...",
            "field": "...",
            "institution": "...",
            "graduation_year": "YYYY",
            "gpa": "..."
        }}
    ],
    "skills": {{
        "technical": [
            {{
                "skill": "...",
                "proficiency": "beginner|intermediate|advanced|expert"
            }}
        ],
        "soft_skills": ["...", "..."]
    }},
    "projects": [
        {{
            "name": "...",
            "description": "...",
            "technologies": ["...", "..."],
            "impact": "..."
        }}
    ],
    "certifications": ["...", "..."],
    "languages": ["...", "..."],
    "publications_patents": ["...", "..."],
    "analysis": {{
        "seniority_assessment": "...",
        "career_trajectory": "ascending|stable|descending|mixed",
        "industry_focus": ["...", "..."],
        "top_strengths": ["...", "...", "..."],
        "red_flags": ["...", "..."]
    }}
}}"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        """
        Initialize CV parser

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"✅ CVParser initialized with model: {model}")

    async def parse(self, cv_text: str) -> Dict:
        """
        Parse CV text and extract structured information

        Args:
            cv_text: Raw CV text

        Returns:
            Dict with parsed CV data
        """
        logger.info(f"📄 Parsing CV ({len(cv_text)} characters)...")

        try:
            # Build prompt
            prompt = self.CV_PARSING_PROMPT.format(cv_text=cv_text)

            # Call Claude API
            logger.debug("📡 Calling Claude API for CV parsing...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response
            response_text = response.content[0].text.strip()
            logger.debug(f"📝 Claude response: {response_text[:100]}...")

            # Parse JSON
            parsed_data = self._parse_response(response_text)

            # Generate derived data
            parsed_data = self._enhance_parsed_data(parsed_data)

            # Add metadata
            parsed_data["parsed_at"] = datetime.utcnow().isoformat()
            parsed_data["parser_version"] = "1.0"

            logger.info(
                f"✅ CV parsing complete: "
                f"name={parsed_data.get('personal_info', {}).get('name', 'Unknown')}, "
                f"experience={parsed_data.get('professional_summary', {}).get('total_years_experience', 0)} years"
            )

            return parsed_data

        except Exception as e:
            logger.error(f"❌ Error parsing CV: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _enhance_parsed_data(self, data: Dict) -> Dict:
        """
        Enhance parsed data with derived metrics

        Args:
            data: Parsed CV data

        Returns:
            Enhanced data
        """
        # Generate skill graph
        data["skill_graph"] = self._generate_skill_graph(data)

        # Generate experience matrix
        data["experience_matrix"] = self._generate_experience_matrix(data)

        # Calculate career metrics
        data["career_metrics"] = self._calculate_career_metrics(data)

        return data

    def _generate_skill_graph(self, data: Dict) -> Dict[str, str]:
        """
        Generate skill -> proficiency mapping

        Args:
            data: Parsed CV data

        Returns:
            Skill graph dict
        """
        skill_graph = {}

        # Add technical skills
        for skill_entry in data.get("skills", {}).get("technical", []):
            if isinstance(skill_entry, dict):
                skill_graph[skill_entry.get("skill", "")] = skill_entry.get("proficiency", "intermediate")
            elif isinstance(skill_entry, str):
                skill_graph[skill_entry] = "intermediate"  # Default

        return skill_graph

    def _generate_experience_matrix(self, data: Dict) -> Dict[str, List[str]]:
        """
        Generate role -> skills matrix

        Args:
            data: Parsed CV data

        Returns:
            Experience matrix dict
        """
        matrix = {}

        for experience in data.get("work_experience", []):
            role_key = f"{experience.get('title', 'Unknown')} @ {experience.get('company', 'Unknown')}"
            matrix[role_key] = experience.get("skills_used", [])

        return matrix

    def _calculate_career_metrics(self, data: Dict) -> Dict:
        """
        Calculate career progression metrics

        Args:
            data: Parsed CV data

        Returns:
            Career metrics dict
        """
        work_exp = data.get("work_experience", [])

        if not work_exp:
            return {
                "total_companies": 0,
                "average_tenure_months": 0,
                "longest_tenure_months": 0,
                "job_changes": 0,
                "tenure_stability": "unknown"
            }

        total_companies = len(work_exp)
        tenures = [exp.get("duration_months", 0) for exp in work_exp]
        avg_tenure = sum(tenures) / len(tenures) if tenures else 0
        longest_tenure = max(tenures) if tenures else 0

        # Assess tenure stability
        if avg_tenure >= 36:
            stability = "high"
        elif avg_tenure >= 24:
            stability = "medium"
        elif avg_tenure >= 12:
            stability = "low"
        else:
            stability = "very_low"

        return {
            "total_companies": total_companies,
            "average_tenure_months": round(avg_tenure, 1),
            "longest_tenure_months": longest_tenure,
            "job_changes": total_companies - 1,
            "tenure_stability": stability
        }

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Claude's JSON response

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed CV dictionary

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
            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _create_error_result(self, error_msg: str) -> Dict:
        """
        Create an error parsing result

        Args:
            error_msg: Error message

        Returns:
            Error result dict
        """
        return {
            "personal_info": {},
            "professional_summary": {},
            "work_experience": [],
            "education": [],
            "skills": {"technical": [], "soft_skills": []},
            "projects": [],
            "certifications": [],
            "languages": [],
            "publications_patents": [],
            "analysis": {
                "seniority_assessment": "unknown",
                "career_trajectory": "unknown",
                "industry_focus": [],
                "top_strengths": [],
                "red_flags": [f"CV parsing failed: {error_msg}"]
            },
            "skill_graph": {},
            "experience_matrix": {},
            "career_metrics": {},
            "parsed_at": datetime.utcnow().isoformat(),
            "error": True,
            "error_message": error_msg
        }
