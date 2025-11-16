/**
 * ConfidenceMeters - Circular progress indicators showing AI confidence
 * in subject relevance, difficulty, and tone assessments
 */

import { Evaluation } from '@/hooks/useTranscriptStream';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle } from 'lucide-react';

interface ConfidenceMetersProps {
  evaluations: Evaluation[];
  className?: string;
}

const ConfidenceMeters = ({ evaluations, className = '' }: ConfidenceMetersProps) => {
  // Calculate average confidence scores
  const calculateAverageConfidence = (): {
    subject: number;
    difficulty: number;
    tone: number;
  } => {
    if (evaluations.length === 0) {
      return { subject: 0, difficulty: 0, tone: 0 };
    }

    const totals = evaluations.reduce(
      (acc, evaluation) => ({
        subject: acc.subject + evaluation.confidence_subject,
        difficulty: acc.difficulty + evaluation.confidence_difficulty,
        tone: acc.tone + evaluation.confidence_tone,
      }),
      { subject: 0, difficulty: 0, tone: 0 }
    );

    return {
      subject: totals.subject / evaluations.length,
      difficulty: totals.difficulty / evaluations.length,
      tone: totals.tone / evaluations.length,
    };
  };

  const confidence = calculateAverageConfidence();

  // Confidence threshold for warnings
  const LOW_CONFIDENCE_THRESHOLD = 0.7;

  // Meter configuration
  const meters = [
    {
      label: 'Subject Relevance',
      value: confidence.subject,
      color: 'bg-purple-500',
      emoji: '📊',
    },
    {
      label: 'Question Difficulty',
      value: confidence.difficulty,
      color: 'bg-blue-500',
      emoji: '🎯',
    },
    {
      label: 'Interviewer Tone',
      value: confidence.tone,
      color: 'bg-orange-500',
      emoji: '💬',
    },
  ];

  // Get color class based on confidence value
  const getColorClass = (value: number): string => {
    if (value < LOW_CONFIDENCE_THRESHOLD) return 'text-yellow-600';
    return 'text-green-600';
  };

  // Get progress bar color
  const getProgressColor = (value: number, baseColor: string): string => {
    if (value < LOW_CONFIDENCE_THRESHOLD) return 'bg-yellow-500';
    return baseColor;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">AI Confidence</h3>
        {evaluations.length === 0 && (
          <span className="text-xs text-muted-foreground">
            Awaiting evaluations...
          </span>
        )}
      </div>

      <div className="space-y-4">
        {meters.map((meter) => (
          <div key={meter.label} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm">{meter.emoji}</span>
                <span className="text-xs font-medium text-muted-foreground">
                  {meter.label}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {meter.value > 0 && meter.value < LOW_CONFIDENCE_THRESHOLD && (
                  <AlertTriangle className="h-3 w-3 text-yellow-600" />
                )}
                <span className={`text-sm font-bold ${getColorClass(meter.value)}`}>
                  {meter.value > 0 ? `${(meter.value * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
            </div>

            <div className="relative">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressColor(meter.value, meter.color)} transition-all duration-500`}
                  style={{ width: `${meter.value * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Overall assessment */}
      {evaluations.length > 0 && (
        <div className="pt-4 border-t space-y-2">
          <div className="text-xs font-medium text-muted-foreground">
            Overall AI Reliability
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Progress
                value={
                  ((confidence.subject + confidence.difficulty + confidence.tone) / 3) * 100
                }
                className="h-2"
              />
            </div>
            <div className="text-sm font-bold">
              {(
                ((confidence.subject + confidence.difficulty + confidence.tone) / 3) *
                100
              ).toFixed(0)}
              %
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            {evaluations.length} evaluation{evaluations.length !== 1 ? 's' : ''} analyzed
          </p>
        </div>
      )}

      {/* Info box */}
      <div className="text-xs text-muted-foreground bg-muted/30 p-3 rounded-lg">
        <p className="font-medium mb-1">About Confidence Scores</p>
        <p>
          These metrics show how confident the AI is in its assessments. Lower confidence (&lt;70%)
          may indicate ambiguous content or complex discussions.
        </p>
      </div>
    </div>
  );
};

export default ConfidenceMeters;
