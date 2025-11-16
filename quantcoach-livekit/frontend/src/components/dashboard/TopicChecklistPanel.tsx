/**
 * TopicChecklistPanel - Checklist view of topic coverage with checkboxes
 * Replaces the radar chart with a simple, clean checkbox list
 */

import { Evaluation } from '@/hooks/useTranscriptStream';
import { CheckCircle2, Circle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TopicChecklistPanelProps {
  evaluations: Evaluation[];
  className?: string;
}

// Coverage threshold to mark a topic as "covered"
const COVERAGE_THRESHOLD = 50; // percentage

const TopicChecklistPanel = ({ evaluations, className = '' }: TopicChecklistPanelProps) => {
  // Topic definitions with friendly names
  const topicDefinitions: Record<string, string> = {
    CV_TECHNIQUES: 'Cross-Validation',
    REGULARIZATION: 'Regularization',
    FEATURE_SELECTION: 'Feature Selection',
    STATIONARITY: 'Stationarity',
    TIME_SERIES_MODELS: 'Time Series',
    OPTIMIZATION_PYTHON: 'Python Optimization',
    LOOKAHEAD_BIAS: 'Lookahead Bias',
    DATA_PIPELINE: 'Data Pipeline',
    BEHAVIORAL_PRESSURE: 'Pressure Handling',
    BEHAVIORAL_TEAMWORK: 'Teamwork',
    EXTRA: 'Other Topics',
  };

  // Calculate topic coverage
  const calculateCoverage = () => {
    const topicCounts: Record<string, number> = {};
    const totalEvaluations = evaluations.length || 1; // Avoid division by zero

    // Count mentions of each topic
    evaluations.forEach((evaluation) => {
      evaluation.key_topics.forEach((topic) => {
        topicCounts[topic] = (topicCounts[topic] || 0) + 1;
      });
    });

    // Convert to checklist data with coverage percentage
    return Object.entries(topicDefinitions).map(([key, name]) => {
      const count = topicCounts[key] || 0;
      const percentage = Math.min(100, Math.round((count / totalEvaluations) * 100));

      return {
        key,
        name,
        count,
        percentage,
        isCovered: percentage >= COVERAGE_THRESHOLD || count > 0, // Mark as covered if threshold met or mentioned at least once
      };
    });
  };

  const topics = calculateCoverage();
  const coveredCount = topics.filter((t) => t.isCovered).length;
  const totalCount = topics.length;
  const overallPercentage = Math.round((coveredCount / totalCount) * 100);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Topic Coverage</CardTitle>
          <Badge variant={overallPercentage >= 70 ? 'default' : overallPercentage >= 40 ? 'secondary' : 'outline'}>
            {coveredCount}/{totalCount}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {overallPercentage}% of topics covered
        </p>
      </CardHeader>
      <CardContent className="space-y-1">
        {topics.map((topic) => (
          <div
            key={topic.key}
            className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
              topic.isCovered
                ? 'bg-primary/5 hover:bg-primary/10'
                : 'bg-muted/30 hover:bg-muted/50'
            }`}
          >
            {/* Checkbox icon */}
            {topic.isCovered ? (
              <CheckCircle2 className="h-4 w-4 text-primary shrink-0" />
            ) : (
              <Circle className="h-4 w-4 text-muted-foreground shrink-0" />
            )}

            {/* Topic name */}
            <span
              className={`text-sm flex-1 ${
                topic.isCovered ? 'font-medium text-foreground' : 'text-muted-foreground'
              }`}
            >
              {topic.name}
            </span>

            {/* Score display */}
            {topic.count > 0 && (
              <span className="text-xs font-medium text-primary">
                {topic.percentage}%
              </span>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default TopicChecklistPanel;
