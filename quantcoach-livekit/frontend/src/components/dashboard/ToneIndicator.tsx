/**
 * ToneIndicator - Visual indicator showing interviewer tone with emoji and color
 */

import { Evaluation } from '@/hooks/useTranscriptStream';
import { Card } from '@/components/ui/card';

interface ToneIndicatorProps {
  evaluations: Evaluation[];
  className?: string;
}

const ToneIndicator = ({ evaluations, className = '' }: ToneIndicatorProps) => {
  // Calculate average tone
  const calculateAverageTone = (): {
    tone: 'harsh' | 'neutral' | 'encouraging';
    score: number;
    confidence: number;
  } => {
    if (evaluations.length === 0) {
      return { tone: 'neutral', score: 50, confidence: 0 };
    }

    const toneValues: Record<string, number> = {
      harsh: 0,
      neutral: 50,
      encouraging: 100,
      unknown: 50,
    };

    // Weight recent evaluations more heavily
    let totalScore = 0;
    let totalWeight = 0;
    let totalConfidence = 0;

    evaluations.forEach((evaluation, index) => {
      const weight = index + 1; // More recent = higher weight
      const tone = evaluation.interviewer_tone.toLowerCase();
      const score = toneValues[tone] ?? 50;

      totalScore += score * weight;
      totalWeight += weight;
      totalConfidence += evaluation.confidence_tone;
    });

    const avgScore = totalWeight > 0 ? totalScore / totalWeight : 50;
    const avgConfidence = evaluations.length > 0 ? totalConfidence / evaluations.length : 0;

    // Determine tone category
    let tone: 'harsh' | 'neutral' | 'encouraging' = 'neutral';
    if (avgScore < 33) {
      tone = 'harsh';
    } else if (avgScore > 66) {
      tone = 'encouraging';
    }

    return { tone, score: avgScore, confidence: avgConfidence };
  };

  const { tone, score, confidence } = calculateAverageTone();

  // Get emoji for tone
  const getEmoji = (tone: string): string => {
    switch (tone) {
      case 'harsh':
        return '😠';
      case 'neutral':
        return '😐';
      case 'encouraging':
        return '😊';
      default:
        return '😐';
    }
  };

  // Get color classes
  const getColorClasses = (tone: string): {
    bg: string;
    border: string;
    text: string;
  } => {
    switch (tone) {
      case 'harsh':
        return {
          bg: 'bg-red-50',
          border: 'border-red-300',
          text: 'text-red-700',
        };
      case 'neutral':
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-300',
          text: 'text-gray-700',
        };
      case 'encouraging':
        return {
          bg: 'bg-green-50',
          border: 'border-green-300',
          text: 'text-green-700',
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-300',
          text: 'text-gray-700',
        };
    }
  };

  const emoji = getEmoji(tone);
  const colors = getColorClasses(tone);

  // Get label
  const getLabel = (tone: string): string => {
    return tone.charAt(0).toUpperCase() + tone.slice(1);
  };

  // Get description
  const getDescription = (tone: string): string => {
    switch (tone) {
      case 'harsh':
        return 'Interviewer tone is direct and challenging';
      case 'neutral':
        return 'Interviewer tone is balanced and professional';
      case 'encouraging':
        return 'Interviewer tone is supportive and positive';
      default:
        return 'Tone analysis in progress';
    }
  };

  return (
    <Card className={`p-4 ${colors.bg} ${colors.border} border-2 ${className}`}>
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">
            Interviewer Tone
          </span>
          {confidence > 0 && (
            <span className="text-xs text-muted-foreground">
              {(confidence * 100).toFixed(0)}% confident
            </span>
          )}
        </div>

        {/* Main indicator */}
        <div className="flex items-center gap-4">
          <div className="text-4xl">{emoji}</div>
          <div className="flex-1">
            <div className={`text-lg font-bold ${colors.text}`}>
              {getLabel(tone)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {getDescription(tone)}
            </p>
          </div>
        </div>

        {/* Tone scale */}
        <div className="relative">
          <div className="h-2 bg-gradient-to-r from-red-200 via-gray-200 to-green-200 rounded-full" />
          <div
            className="absolute top-0 h-2 w-2 rounded-full bg-black shadow-lg transition-all duration-500"
            style={{
              left: `calc(${score}% - 4px)`,
            }}
          />
        </div>

        {/* Label row */}
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>Harsh</span>
          <span>Neutral</span>
          <span>Encouraging</span>
        </div>

        {/* Evaluation count */}
        {evaluations.length > 0 && (
          <div className="text-xs text-muted-foreground pt-2 border-t">
            Based on {evaluations.length} evaluation{evaluations.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </Card>
  );
};

export default ToneIndicator;
