/**
 * InterviewTimeline - Horizontal timeline showing conversation flow
 * Color-coded by difficulty and relevance
 */

import { Evaluation } from '@/hooks/useTranscriptStream';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card } from '@/components/ui/card';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface InterviewTimelineProps {
  evaluations: Evaluation[];
  className?: string;
  onSegmentClick?: (evaluation: Evaluation) => void;
}

const InterviewTimeline = ({
  evaluations,
  className = '',
  onSegmentClick,
}: InterviewTimelineProps) => {
  // Get color for segment based on difficulty and relevance
  const getSegmentColor = (
    difficulty: string,
    relevance: string
  ): { bg: string; border: string } => {
    // If off-topic, override with red
    if (relevance === 'off_topic') {
      return { bg: 'bg-red-400', border: 'border-red-600' };
    }

    // If partially relevant, use yellow
    if (relevance === 'partially_relevant') {
      return { bg: 'bg-yellow-300', border: 'border-yellow-500' };
    }

    // On-topic: color by difficulty
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return { bg: 'bg-blue-400', border: 'border-blue-600' };
      case 'medium':
        return { bg: 'bg-yellow-400', border: 'border-yellow-600' };
      case 'hard':
        return { bg: 'bg-red-500', border: 'border-red-700' };
      default:
        return { bg: 'bg-gray-300', border: 'border-gray-500' };
    }
  };

  // Format time
  const formatTime = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  // Get icon for relevance
  const getRelevanceIcon = (relevance: string): string => {
    switch (relevance) {
      case 'on_topic':
        return '✓';
      case 'off_topic':
        return '✗';
      case 'partially_relevant':
        return '~';
      default:
        return '?';
    }
  };

  // Get label for difficulty
  const getDifficultyLabel = (difficulty: string): string => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return '🧊';
      case 'medium':
        return '🌡️';
      case 'hard':
        return '🔥';
      default:
        return '?';
    }
  };

  if (evaluations.length === 0) {
    return (
      <Card className={`p-4 bg-white ${className}`}>
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-900">Interview Timeline</h3>
          <div className="text-center py-8 text-gray-500 text-sm">
            <p>Timeline will appear as interview progresses</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-3 bg-white ${className}`}>
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-medium text-gray-900">Interview Timeline</h3>
          <div className="flex gap-2 text-[10px] text-gray-600">
            <span>🧊 Easy</span>
            <span>🌡️ Medium</span>
            <span>🔥 Hard</span>
          </div>
        </div>

        <ScrollArea className="w-full" orientation="horizontal">
          <div className="relative pb-2">
            {/* Timeline segments - Compact Version */}
            <div className="flex gap-1 relative" style={{ minWidth: 'max-content' }}>
              {/* Timeline line */}
              <div className="absolute left-0 right-0 top-4 h-0.5 bg-gray-200" style={{ width: '100%' }} />
              <TooltipProvider>
                {evaluations.map((evaluation, index) => {
                  const colors = getSegmentColor(
                    evaluation.question_difficulty,
                    evaluation.subject_relevance
                  );

                  return (
                    <Tooltip key={`segment-${index}`}>
                      <TooltipTrigger asChild>
                        <button
                          className={`flex flex-col items-center min-w-[50px] group ${
                            onSegmentClick ? 'cursor-pointer' : ''
                          }`}
                          onClick={() => onSegmentClick?.(evaluation)}
                        >
                          {/* Time label - Compact */}
                          <div className="text-[9px] text-gray-600 mb-0.5">
                            {formatTime(evaluation.timestamp)}
                          </div>

                          {/* Segment - Reduced Height */}
                          <div
                            className={`w-full h-8 ${colors.bg} ${colors.border} border rounded shadow-sm transition-all duration-200 group-hover:shadow-md group-hover:scale-105 flex items-center justify-center`}
                          >
                            <div className="text-center">
                              <div className="text-base">
                                {getDifficultyLabel(evaluation.question_difficulty)}
                              </div>
                            </div>
                          </div>
                        </button>
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <div className="space-y-1">
                          <div className="font-semibold text-xs">
                            {formatTime(evaluation.timestamp)}
                          </div>
                          <div className="text-xs space-y-1">
                            <p>
                              <span className="font-medium">Difficulty:</span>{' '}
                              {evaluation.question_difficulty}
                            </p>
                            <p>
                              <span className="font-medium">Relevance:</span>{' '}
                              {evaluation.subject_relevance.replace('_', ' ')}
                            </p>
                            {evaluation.key_topics.length > 0 && (
                              <p>
                                <span className="font-medium">Topics:</span>{' '}
                                {evaluation.key_topics.slice(0, 2).join(', ')}
                              </p>
                            )}
                          </div>
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
              </TooltipProvider>
            </div>
          </div>
        </ScrollArea>
      </div>
    </Card>
  );
};

export default InterviewTimeline;
