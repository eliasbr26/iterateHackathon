/**
 * DifficultyBar - Horizontal slider showing interview difficulty
 * Color gradient: Blue (cold/easy) → Yellow (medium) → Red (hot/hard)
 */

import { Evaluation } from '@/hooks/useTranscriptStream';

interface DifficultyBarProps {
  evaluations: Evaluation[];
  className?: string;
}

const DifficultyBar = ({ evaluations, className = '' }: DifficultyBarProps) => {
  // Calculate weighted difficulty score
  const calculateDifficultyScore = (): number => {
    if (evaluations.length === 0) return 50; // Default to medium

    const difficultyValues: Record<string, number> = {
      easy: 0,
      medium: 50,
      hard: 100,
      unknown: 50,
    };

    // Weight recent evaluations more heavily
    let totalScore = 0;
    let totalWeight = 0;

    evaluations.forEach((evaluation, index) => {
      const weight = index + 1; // More recent = higher weight
      const difficulty = evaluation.question_difficulty.toLowerCase();
      const score = difficultyValues[difficulty] ?? 50;

      totalScore += score * weight;
      totalWeight += weight;
    });

    return totalWeight > 0 ? totalScore / totalWeight : 50;
  };

  const score = calculateDifficultyScore();

  // Determine color based on score
  const getColorClasses = (score: number): string => {
    if (score < 33) return 'from-blue-400 to-blue-500'; // Cold/Easy
    if (score < 66) return 'from-yellow-400 to-yellow-500'; // Medium
    return 'from-orange-400 to-red-500'; // Hot/Hard
  };

  // Determine label
  const getLabel = (score: number): string => {
    if (score < 33) return 'Cold (Easy)';
    if (score < 66) return 'Warm (Medium)';
    return 'Hot (Hard)';
  };

  // Determine emoji
  const getEmoji = (score: number): string => {
    if (score < 33) return '🧊';
    if (score < 66) return '🌡️';
    return '🔥';
  };

  const colorClasses = getColorClasses(score);
  const label = getLabel(score);
  const emoji = getEmoji(score);

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Difficulty Level</span>
        <span className="font-medium flex items-center gap-1">
          {emoji} {label}
        </span>
      </div>

      {/* Difficulty Bar */}
      <div className="relative h-8 bg-gradient-to-r from-blue-200 via-yellow-200 to-red-200 rounded-lg overflow-hidden shadow-inner">
        {/* Indicator */}
        <div
          className="absolute top-0 bottom-0 w-2 transition-all duration-500 ease-out"
          style={{
            left: `calc(${score}% - 4px)`,
          }}
        >
          <div className={`h-full w-full bg-gradient-to-b ${colorClasses} rounded-full shadow-lg`} />
        </div>

        {/* Labels */}
        <div className="absolute inset-0 flex items-center justify-between px-3 text-xs font-medium text-gray-700">
          <span>🧊 Easy</span>
          <span>🌡️ Medium</span>
          <span>🔥 Hard</span>
        </div>
      </div>

      {/* Confidence indicator (if recent evaluations exist) */}
      {evaluations.length > 0 && (
        <div className="text-xs text-muted-foreground">
          Based on {evaluations.length} evaluation{evaluations.length !== 1 ? 's' : ''}
          {evaluations[evaluations.length - 1]?.confidence_difficulty && (
            <span className="ml-2">
              (Confidence: {(evaluations[evaluations.length - 1].confidence_difficulty * 100).toFixed(0)}%)
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default DifficultyBar;
