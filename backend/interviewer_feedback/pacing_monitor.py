"""
Pacing Monitor - PILLAR 4.1
Tracks interview pacing and provides real-time alerts for timing issues
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PacingMonitor:
    """
    Monitors interview pacing and provides timing feedback

    Features:
    - Questions per minute tracking
    - Silent period detection
    - Interview stage awareness
    - Pacing alerts (too fast, too slow, appropriate)
    """

    # Pacing thresholds (questions per minute)
    QPM_TOO_FAST = 2.5
    QPM_TOO_SLOW = 0.5
    QPM_IDEAL_MIN = 1.0
    QPM_IDEAL_MAX = 2.0

    # Silent period threshold (minutes)
    SILENT_PERIOD_THRESHOLD = 3.0

    # Interview stage durations (minutes)
    OPENING_STAGE_END = 10
    MIDDLE_STAGE_END = 40
    DEEP_DIVE_STAGE_END = 50
    CLOSING_STAGE_END = 60

    def __init__(self):
        """Initialize pacing monitor"""
        self.questions: List[Tuple[datetime, str]] = []  # (timestamp, question)
        self.start_time: Optional[datetime] = None
        self.last_question_time: Optional[datetime] = None

        logger.info("✅ PacingMonitor initialized")

    def track_question(self, question: str, timestamp: Optional[datetime] = None) -> Dict:
        """
        Track a question and analyze current pacing

        Args:
            question: The question text
            timestamp: When the question was asked (default: now)

        Returns:
            Pacing analysis with status, metrics, and recommendations
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Initialize start time on first question
        if self.start_time is None:
            self.start_time = timestamp
            logger.info(f"🎬 Interview started at {timestamp}")

        # Add question to tracking
        self.questions.append((timestamp, question))
        self.last_question_time = timestamp

        # Calculate metrics
        duration_minutes = self._get_duration_minutes(timestamp)
        total_questions = len(self.questions)
        qpm = self._calculate_qpm(timestamp)
        time_since_last = self._time_since_last_question(timestamp)

        # Determine pacing status
        status, recommendation = self._analyze_pacing(
            qpm, time_since_last, duration_minutes, total_questions
        )

        # Get stage-specific guidance
        stage = self._get_interview_stage(duration_minutes)
        stage_guidance = self._get_stage_recommendation(stage, qpm)

        result = {
            "status": status,
            "questions_per_minute": round(qpm, 2),
            "total_questions": total_questions,
            "duration_minutes": round(duration_minutes, 1),
            "time_since_last_question": round(time_since_last, 1),
            "interview_stage": stage,
            "recommendation": recommendation,
            "stage_guidance": stage_guidance,
            "metrics": {
                "is_too_fast": qpm > self.QPM_TOO_FAST,
                "is_too_slow": qpm < self.QPM_TOO_SLOW,
                "is_ideal": self.QPM_IDEAL_MIN <= qpm <= self.QPM_IDEAL_MAX,
                "silent_period": time_since_last > self.SILENT_PERIOD_THRESHOLD
            }
        }

        logger.info(
            f"📊 Pacing: {status} | QPM: {qpm:.1f} | "
            f"Q#{total_questions} | Stage: {stage}"
        )

        return result

    def get_pacing_summary(self) -> Dict:
        """
        Get overall pacing summary for the interview

        Returns:
            Summary statistics and analysis
        """
        if not self.questions:
            return {
                "status": "not_started",
                "message": "No questions tracked yet"
            }

        now = datetime.now()
        duration_minutes = self._get_duration_minutes(now)
        total_questions = len(self.questions)
        overall_qpm = total_questions / max(duration_minutes, 0.1)

        # Calculate question distribution across stages
        stage_distribution = self._calculate_stage_distribution()

        # Calculate pacing consistency
        qpm_variance = self._calculate_qpm_variance()

        return {
            "status": "in_progress" if duration_minutes < 60 else "completed",
            "total_duration_minutes": round(duration_minutes, 1),
            "total_questions": total_questions,
            "average_qpm": round(overall_qpm, 2),
            "stage_distribution": stage_distribution,
            "pacing_consistency": {
                "variance": round(qpm_variance, 2),
                "is_consistent": qpm_variance < 0.5  # Low variance = consistent
            },
            "overall_assessment": self._get_overall_assessment(
                overall_qpm, total_questions, duration_minutes
            )
        }

    def reset(self):
        """Reset the pacing monitor for a new interview"""
        self.questions = []
        self.start_time = None
        self.last_question_time = None
        logger.info("🔄 PacingMonitor reset")

    # Private helper methods

    def _get_duration_minutes(self, current_time: datetime) -> float:
        """Calculate interview duration in minutes"""
        if self.start_time is None:
            return 0.0
        delta = current_time - self.start_time
        return delta.total_seconds() / 60

    def _calculate_qpm(self, current_time: datetime) -> float:
        """Calculate current questions per minute"""
        duration = self._get_duration_minutes(current_time)
        if duration < 0.1:  # Avoid division by zero
            return 0.0
        return len(self.questions) / duration

    def _time_since_last_question(self, current_time: datetime) -> float:
        """Calculate minutes since last question"""
        if len(self.questions) < 2:
            return 0.0

        previous_time = self.questions[-2][0]
        delta = current_time - previous_time
        return delta.total_seconds() / 60

    def _get_interview_stage(self, duration_minutes: float) -> str:
        """Determine current interview stage"""
        if duration_minutes < self.OPENING_STAGE_END:
            return "opening"
        elif duration_minutes < self.MIDDLE_STAGE_END:
            return "middle"
        elif duration_minutes < self.DEEP_DIVE_STAGE_END:
            return "deep_dive"
        elif duration_minutes < self.CLOSING_STAGE_END:
            return "closing"
        else:
            return "overtime"

    def _analyze_pacing(
        self,
        qpm: float,
        time_since_last: float,
        duration: float,
        total_questions: int
    ) -> Tuple[str, str]:
        """
        Analyze pacing and generate status + recommendation

        Returns:
            (status, recommendation) tuple
        """
        # Check for silent period first
        if time_since_last > self.SILENT_PERIOD_THRESHOLD:
            return (
                "silent_period",
                f"No question for {time_since_last:.1f} minutes. "
                "Check if candidate is struggling or if follow-up is needed."
            )

        # Check pacing thresholds
        if qpm > self.QPM_TOO_FAST:
            return (
                "too_fast",
                f"Pacing is fast ({qpm:.1f} qpm). "
                "Consider slowing down to give candidate more time to think."
            )

        if qpm < self.QPM_TOO_SLOW:
            return (
                "too_slow",
                f"Pacing is slow ({qpm:.1f} qpm). "
                "Consider moving forward to cover more ground."
            )

        # Ideal pacing
        if self.QPM_IDEAL_MIN <= qpm <= self.QPM_IDEAL_MAX:
            return (
                "ideal",
                f"Excellent pacing ({qpm:.1f} qpm). Maintain current rhythm."
            )

        # Acceptable but not ideal
        return (
            "appropriate",
            f"Good pacing ({qpm:.1f} qpm). You're doing well."
        )

    def _get_stage_recommendation(self, stage: str, qpm: float) -> str:
        """Get stage-specific pacing guidance"""
        recommendations = {
            "opening": {
                "ideal_qpm_min": 1.0,
                "ideal_qpm_max": 1.5,
                "guidance": "Opening: Take time to build rapport. 1-1.5 qpm is ideal."
            },
            "middle": {
                "ideal_qpm_min": 1.5,
                "ideal_qpm_max": 2.0,
                "guidance": "Middle: Core assessment phase. 1.5-2 qpm is ideal."
            },
            "deep_dive": {
                "ideal_qpm_min": 1.0,
                "ideal_qpm_max": 1.5,
                "guidance": "Deep-dive: Thorough exploration. 1-1.5 qpm is ideal."
            },
            "closing": {
                "ideal_qpm_min": 2.0,
                "ideal_qpm_max": 2.5,
                "guidance": "Closing: Wrap up efficiently. 2-2.5 qpm is ideal."
            },
            "overtime": {
                "ideal_qpm_min": 2.5,
                "ideal_qpm_max": 3.0,
                "guidance": "Overtime: Conclude quickly. Focus on essential questions only."
            }
        }

        stage_info = recommendations.get(stage, recommendations["middle"])

        if qpm < stage_info["ideal_qpm_min"]:
            return f"{stage_info['guidance']} Current pace is slower than ideal."
        elif qpm > stage_info["ideal_qpm_max"]:
            return f"{stage_info['guidance']} Current pace is faster than ideal."
        else:
            return f"{stage_info['guidance']} Your pace is perfect for this stage!"

    def _calculate_stage_distribution(self) -> Dict:
        """Calculate how many questions were asked in each stage"""
        distribution = {
            "opening": 0,
            "middle": 0,
            "deep_dive": 0,
            "closing": 0,
            "overtime": 0
        }

        for timestamp, _ in self.questions:
            duration = self._get_duration_minutes(timestamp)
            stage = self._get_interview_stage(duration)
            distribution[stage] += 1

        return distribution

    def _calculate_qpm_variance(self) -> float:
        """Calculate variance in questions per minute (measures consistency)"""
        if len(self.questions) < 2:
            return 0.0

        # Calculate QPM for each 5-minute window
        window_qpms = []
        window_size = 5.0  # minutes

        for i in range(0, int(self._get_duration_minutes(datetime.now())), 5):
            window_start = i
            window_end = i + window_size

            questions_in_window = [
                q for q in self.questions
                if window_start <= self._get_duration_minutes(q[0]) < window_end
            ]

            if questions_in_window:
                qpm = len(questions_in_window) / window_size
                window_qpms.append(qpm)

        if not window_qpms:
            return 0.0

        # Calculate variance
        mean_qpm = sum(window_qpms) / len(window_qpms)
        variance = sum((x - mean_qpm) ** 2 for x in window_qpms) / len(window_qpms)

        return variance

    def _get_overall_assessment(
        self,
        overall_qpm: float,
        total_questions: int,
        duration: float
    ) -> str:
        """Generate overall pacing assessment"""
        assessments = []

        # QPM assessment
        if self.QPM_IDEAL_MIN <= overall_qpm <= self.QPM_IDEAL_MAX:
            assessments.append("✅ Excellent overall pacing")
        elif overall_qpm > self.QPM_TOO_FAST:
            assessments.append("⚠️ Interview moved too quickly overall")
        elif overall_qpm < self.QPM_TOO_SLOW:
            assessments.append("⚠️ Interview moved too slowly overall")
        else:
            assessments.append("✓ Good overall pacing")

        # Question count assessment (assuming 60-minute interview)
        ideal_questions_min = 45
        ideal_questions_max = 90

        if duration >= 45:  # Only assess if interview is far enough along
            if total_questions < ideal_questions_min:
                assessments.append(f"⚠️ Only {total_questions} questions - consider asking more")
            elif total_questions > ideal_questions_max:
                assessments.append(f"⚠️ {total_questions} questions - may be too many")
            else:
                assessments.append(f"✓ Good question count ({total_questions})")

        return " | ".join(assessments)
