/**
 * TopicCoverageRadar - Radar chart showing coverage of 11 quantitative finance topics
 */

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Evaluation } from '@/hooks/useTranscriptStream';

interface TopicCoverageRadarProps {
  evaluations: Evaluation[];
  className?: string;
}

const TopicCoverageRadar = ({ evaluations, className = '' }: TopicCoverageRadarProps) => {
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

    // Count mentions of each topic
    evaluations.forEach((evaluation) => {
      evaluation.key_topics.forEach((topic) => {
        topicCounts[topic] = (topicCounts[topic] || 0) + 1;
      });
    });

    // Convert to radar chart data
    return Object.entries(topicDefinitions).map(([key, name]) => ({
      topic: name,
      coverage: topicCounts[key] || 0,
      fullMark: Math.max(5, Math.max(...Object.values(topicCounts), 1)), // Dynamic scale
    }));
  };

  const data = calculateCoverage();
  const totalTopicsCovered = data.filter((d) => d.coverage > 0).length;
  const coveragePercentage = ((totalTopicsCovered / data.length) * 100).toFixed(0);

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium">Topic Coverage</h3>
          <p className="text-xs text-muted-foreground mt-1">
            {totalTopicsCovered} of {data.length} topics discussed ({coveragePercentage}%)
          </p>
        </div>
      </div>

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="topic"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              tickLine={false}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 'dataMax']}
              tick={{ fill: '#9ca3af', fontSize: 10 }}
            />
            <Radar
              name="Coverage"
              dataKey="coverage"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.6}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload[0]) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-background border rounded-lg shadow-lg p-3">
                      <p className="font-medium text-sm">{data.topic}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Discussed {data.coverage} time{data.coverage !== 1 ? 's' : ''}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '12px' }}
              iconType="circle"
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Topic list with indicators */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {data.map((item) => (
          <div
            key={item.topic}
            className="flex items-center gap-2 p-2 rounded bg-muted/30"
          >
            <div
              className={`w-2 h-2 rounded-full ${
                item.coverage > 0 ? 'bg-purple-500' : 'bg-gray-300'
              }`}
            />
            <span className={item.coverage > 0 ? 'font-medium' : 'text-muted-foreground'}>
              {item.topic}
            </span>
            {item.coverage > 0 && (
              <span className="ml-auto text-purple-600 font-medium">
                ×{item.coverage}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopicCoverageRadar;
