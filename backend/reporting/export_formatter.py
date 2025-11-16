"""
Export Formatter - PILLAR 5.3
Exports reports to various formats (JSON, HTML, Markdown)
"""

import json
import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ExportFormatter:
    """
    Exports reports to various formats

    Supported Formats:
    - JSON: Raw structured data
    - HTML: Styled report
    - Markdown: Human-readable documentation
    """

    def __init__(self):
        """Initialize export formatter"""
        logger.info("✅ ExportFormatter initialized")

    def export_to_json(self, report: Dict, pretty: bool = True) -> str:
        """
        Export to JSON string

        Args:
            report: Report data
            pretty: Pretty-print with indentation

        Returns:
            JSON string
        """
        logger.info("📤 Exporting to JSON")

        if pretty:
            return json.dumps(report, indent=2, default=str)
        return json.dumps(report, default=str)

    def export_to_html(self, report: Dict, template: str = "default") -> str:
        """
        Export to styled HTML

        Args:
            report: Report data
            template: Template style ("default", "minimal", "professional")

        Returns:
            HTML string
        """
        logger.info(f"📤 Exporting to HTML (template: {template})")

        report_type = report.get("report_type", "unknown")

        if report_type == "ats":
            return self._ats_to_html(report)
        elif report_type == "hiring_manager":
            return self._hiring_manager_to_html(report)
        elif report_type == "recruiter":
            return self._recruiter_to_html(report)
        else:
            return self._full_to_html(report)

    def export_to_markdown(self, report: Dict) -> str:
        """
        Export to Markdown

        Args:
            report: Report data

        Returns:
            Markdown string
        """
        logger.info("📤 Exporting to Markdown")

        report_type = report.get("report_type", "unknown")

        if report_type == "hiring_manager":
            return self._hiring_manager_to_markdown(report)
        else:
            return self._generic_to_markdown(report)

    # HTML Export Methods

    def _ats_to_html(self, report: Dict) -> str:
        """Convert ATS summary to HTML"""
        candidate = report.get("candidate", {})
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Interview Summary - {candidate.get('name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; margin-bottom: 20px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
        .section {{ margin: 20px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f9f9f9; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Interview Summary</h1>
        <p><span class="label">Candidate:</span> {candidate.get('name')}</p>
        <p><span class="label">Position:</span> {report.get('position')}</p>
        <p><span class="label">Date:</span> {report.get('interview_date')}</p>
        <p class="score">Overall Score: {report.get('overall_score')}/100</p>
    </div>

    <div class="section">
        <h2>Recommendation</h2>
        <p><strong>{report.get('recommendation', '').upper()}</strong> (Confidence: {report.get('recommendation_confidence', 0)*100:.0f}%)</p>
    </div>

    <div class="section">
        <h2>Competency Scores</h2>
        <table>
            <tr>
                <th>Competency</th>
                <th>Score</th>
            </tr>
            {''.join(f"<tr><td>{comp}</td><td>{score}/100</td></tr>" for comp, score in report.get('competency_scores', {}).items())}
        </table>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <p>{report.get('summary', '')}</p>
    </div>
</body>
</html>
"""

    def _hiring_manager_to_html(self, report: Dict) -> str:
        """Convert hiring manager report to HTML"""
        candidate = report.get("candidate_overview", {})
        recommendation = report.get("hiring_recommendation", {})

        strengths_html = "".join(
            f"<li><strong>{s.get('area')}:</strong> {s.get('evidence', '')}</li>"
            for s in report.get("detailed_assessment", {}).get("strengths", [])
        )

        weaknesses_html = "".join(
            f"<li><strong>{w.get('area')}:</strong> {w.get('evidence', '')}</li>"
            for w in report.get("detailed_assessment", {}).get("weaknesses", [])
        )

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Hiring Manager Report - {candidate.get('name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; margin-bottom: 30px; border-radius: 8px; }}
        .score-badge {{ display: inline-block; background: white; color: #667eea; padding: 10px 20px; border-radius: 20px; font-size: 20px; font-weight: bold; }}
        .section {{ margin: 30px 0; }}
        h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .recommendation {{ background: #f0fdf4; border-left: 4px solid #10b981; padding: 20px; margin: 20px 0; }}
        .concerns {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; }}
        ul {{ list-style-position: inside; }}
        li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Hiring Manager Report</h1>
        <p><strong>Candidate:</strong> {candidate.get('name')}</p>
        <p><strong>Position:</strong> {candidate.get('position_applied')}</p>
        <p><strong>Interview Date:</strong> {candidate.get('interview_date')}</p>
        <div class="score-badge">Score: {candidate.get('overall_score', 0):.1f}/100</div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>{report.get('executive_summary', '')}</p>
    </div>

    <div class="section">
        <h2>Key Highlights</h2>
        <ul>
            {''.join(f"<li>{h}</li>" for h in report.get('key_highlights', []))}
        </ul>
    </div>

    <div class="section">
        <h2>Strengths</h2>
        <ul>
            {strengths_html}
        </ul>
    </div>

    <div class="section">
        <h2>Areas for Development</h2>
        <ul>
            {weaknesses_html}
        </ul>
    </div>

    <div class="recommendation">
        <h2>Hiring Recommendation</h2>
        <p><strong>Decision:</strong> {recommendation.get('decision', '').upper()}</p>
        <p><strong>Confidence:</strong> {recommendation.get('confidence', 0)*100:.0f}%</p>
        <p>{recommendation.get('reasoning', '')}</p>
    </div>

    <div class="section">
        <h2>Next Steps</h2>
        <ul>
            {''.join(f"<li>{step}</li>" for step in report.get('next_steps', []))}
        </ul>
    </div>

    <p style="text-align: center; color: #888; margin-top: 50px;">
        Generated by QuantCoach AI on {report.get('generated_at', '')}
    </p>
</body>
</html>
"""

    def _recruiter_to_html(self, report: Dict) -> str:
        """Convert recruiter brief to HTML"""
        candidate = report.get("candidate", {})
        assessment = report.get("quick_assessment", {})

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Recruiter Brief - {candidate.get('name', 'Unknown')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; }}
        .header {{ text-align: center; padding: 20px; background: #f9fafb; border-radius: 8px; }}
        .score-circle {{ display: inline-block; width: 80px; height: 80px; border-radius: 50%; background: #3b82f6; color: white; line-height: 80px; text-align: center; font-size: 24px; font-weight: bold; }}
        .recommendation {{ font-size: 18px; font-weight: bold; margin: 10px 0; }}
        .section {{ margin: 20px 0; }}
        .badge {{ display: inline-block; padding: 5px 10px; background: #e0e7ff; color: #3730a3; border-radius: 4px; margin: 2px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{candidate.get('name')}</h1>
        <p>{report.get('position')}</p>
        <div class="score-circle">{assessment.get('overall_score', 0):.0f}</div>
        <p class="recommendation">{assessment.get('recommendation', '').upper()}</p>
        <p>Confidence: {assessment.get('confidence', 0)*100:.0f}%</p>
    </div>

    <div class="section">
        <h2>Key Takeaways</h2>
        <ul>
            {''.join(f"<li>{t}</li>" for t in report.get('key_takeaways', []))}
        </ul>
    </div>

    <div class="section">
        <h2>Top Strengths</h2>
        {''.join(f'<span class="badge">{s}</span>' for s in report.get('top_strengths', []))}
    </div>

    <div class="section">
        <h2>Main Concerns</h2>
        <ul>
            {''.join(f"<li>{c}</li>" for c in report.get('main_concerns', []))}
        </ul>
    </div>

    <div class="section">
        <h2>Next Steps</h2>
        <ul>
            {''.join(f"<li>{step}</li>" for step in report.get('next_steps', []))}
        </ul>
    </div>
</body>
</html>
"""

    def _full_to_html(self, report: Dict) -> str:
        """Convert full report to HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Full Interview Report</title>
    <style>
        body {{ font-family: monospace; margin: 20px; white-space: pre-wrap; }}
    </style>
</head>
<body>
{json.dumps(report, indent=2, default=str)}
</body>
</html>
"""

    # Markdown Export Methods

    def _hiring_manager_to_markdown(self, report: Dict) -> str:
        """Convert hiring manager report to Markdown"""
        candidate = report.get("candidate_overview", {})
        recommendation = report.get("hiring_recommendation", {})

        strengths_md = "\n".join(
            f"- **{s.get('area')}**: {s.get('evidence', '')}"
            for s in report.get("detailed_assessment", {}).get("strengths", [])
        )

        weaknesses_md = "\n".join(
            f"- **{w.get('area')}**: {w.get('evidence', '')}"
            for w in report.get("detailed_assessment", {}).get("weaknesses", [])
        )

        return f"""# Hiring Manager Report

## Candidate Information

- **Name**: {candidate.get('name')}
- **Position**: {candidate.get('position_applied')}
- **Interview Date**: {candidate.get('interview_date')}
- **Overall Score**: {candidate.get('overall_score', 0):.1f}/100

## Executive Summary

{report.get('executive_summary', '')}

## Key Highlights

{chr(10).join(f"- {h}" for h in report.get('key_highlights', []))}

## Strengths

{strengths_md}

## Areas for Development

{weaknesses_md}

## Hiring Recommendation

- **Decision**: {recommendation.get('decision', '').upper()}
- **Confidence**: {recommendation.get('confidence', 0)*100:.0f}%

{recommendation.get('reasoning', '')}

## Next Steps

{chr(10).join(f"- {step}" for step in report.get('next_steps', []))}

---

*Generated by QuantCoach AI on {report.get('generated_at', '')}*
"""

    def _generic_to_markdown(self, report: Dict) -> str:
        """Convert generic report to Markdown"""
        return f"""# Interview Report

**Report Type**: {report.get('report_type', 'Unknown')}
**Generated**: {report.get('generated_at', '')}

## Report Data

```json
{json.dumps(report, indent=2, default=str)}
```
"""
