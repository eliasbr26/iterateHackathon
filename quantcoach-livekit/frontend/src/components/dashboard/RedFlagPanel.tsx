/**
 * RedFlagPanel - Alert panel for off-topic moments, low confidence, and LLM flags
 */

import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { Evaluation } from '@/hooks/useTranscriptStream';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface RedFlagPanelProps {
  evaluations: Evaluation[];
  className?: string;
}

interface Flag {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  timestamp: string;
  confidence?: number;
}

const RedFlagPanel = ({ evaluations, className = '' }: RedFlagPanelProps) => {
  // Extract all flags from evaluations
  const extractFlags = (): Flag[] => {
    const flags: Flag[] = [];

    evaluations.forEach((evaluation, index) => {
      const evalId = `eval-${index}-${evaluation.timestamp}`;

      // Check suppression flags from backend
      const suppressPartiallyRelevant = evaluation._suppress_partially_relevant_alert === true;
      const suppressLowConfidence = evaluation._suppress_low_confidence_alert === true;

      // Note: Off-topic alerts have been removed per product requirements

      // Warning: Partially relevant (only if not suppressed)
      if (evaluation.subject_relevance === 'partially_relevant' && !suppressPartiallyRelevant) {
        flags.push({
          id: `${evalId}-partial`,
          type: 'warning',
          title: 'Partially Off-Topic',
          description: evaluation.summary || 'Discussion has partially strayed from core topics.',
          timestamp: evaluation.timestamp,
          confidence: evaluation.confidence_subject,
        });
      }

      // Harsh tone alerts - NEVER suppressed (always immediate)
      if (evaluation.interviewer_tone === 'harsh') {
        flags.push({
          id: `${evalId}-harsh-tone`,
          type: 'critical',
          title: 'Harsh Interviewer Tone',
          description: 'Interviewer tone detected as harsh or aggressive.',
          timestamp: evaluation.timestamp,
          confidence: evaluation.confidence_tone,
        });
      }

      // Interviewer dominance alert
      if (evaluation.interviewer_dominance?.is_dominant) {
        flags.push({
          id: `${evalId}-interviewer-dominance`,
          type: 'warning',
          title: 'Interviewer Speaking Too Much',
          description: `Interviewer is speaking ${evaluation.interviewer_dominance.percentage}% of the time in the last minute (threshold: ${evaluation.interviewer_dominance.threshold}%). Consider letting the candidate speak more.`,
          timestamp: evaluation.timestamp,
        });
      }

      // Low confidence warnings (only if not suppressed)
      const lowConfidenceThreshold = 0.7;
      if (!suppressLowConfidence) {
        if (evaluation.confidence_subject < lowConfidenceThreshold) {
          flags.push({
            id: `${evalId}-low-conf-subject`,
            type: 'warning',
            title: 'Low Confidence: Subject Relevance',
            description: `AI is uncertain about topic relevance (${(evaluation.confidence_subject * 100).toFixed(0)}% confidence)`,
            timestamp: evaluation.timestamp,
            confidence: evaluation.confidence_subject,
          });
        }

        if (evaluation.confidence_difficulty < lowConfidenceThreshold) {
          flags.push({
            id: `${evalId}-low-conf-difficulty`,
            type: 'warning',
            title: 'Low Confidence: Question Difficulty',
            description: `AI is uncertain about difficulty level (${(evaluation.confidence_difficulty * 100).toFixed(0)}% confidence)`,
            timestamp: evaluation.timestamp,
            confidence: evaluation.confidence_difficulty,
          });
        }

        if (evaluation.confidence_tone < lowConfidenceThreshold) {
          flags.push({
            id: `${evalId}-low-conf-tone`,
            type: 'warning',
            title: 'Low Confidence: Interviewer Tone',
            description: `AI is uncertain about tone assessment (${(evaluation.confidence_tone * 100).toFixed(0)}% confidence)`,
            timestamp: evaluation.timestamp,
            confidence: evaluation.confidence_tone,
          });
        }
      }

      // LLM-generated flags - harsh tone never suppressed, others follow general rules
      evaluation.flags.forEach((flag, flagIndex) => {
        const isHarshTone = flag.toLowerCase().includes('harsh');

        // Harsh tone always shows, others respect low confidence suppression
        if (isHarshTone || !suppressLowConfidence) {
          flags.push({
            id: `${evalId}-llm-${flagIndex}`,
            type: isHarshTone ? 'critical' : 'info',
            title: isHarshTone ? 'Tone Warning' : 'AI Suggestion',
            description: flag,
            timestamp: evaluation.timestamp,
          });
        }
      });
    });

    // Sort by severity (critical > warning > info) and recency
    return flags.sort((a, b) => {
      const severityOrder = { critical: 0, warning: 1, info: 2 };
      const severityDiff = severityOrder[a.type] - severityOrder[b.type];

      if (severityDiff !== 0) return severityDiff;

      // If same severity, sort by timestamp (newest first)
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
  };

  const flags = extractFlags();
  const criticalCount = flags.filter((f) => f.type === 'critical').length;
  const warningCount = flags.filter((f) => f.type === 'warning').length;

  // Format timestamp
  const formatTime = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  // Get icon for flag type
  const getIcon = (type: Flag['type']) => {
    switch (type) {
      case 'critical':
        return <AlertTriangle className="h-4 w-4" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4" />;
      case 'info':
        return <Info className="h-4 w-4" />;
    }
  };

  // Get variant for alert
  const getVariant = (type: Flag['type']): 'default' | 'destructive' => {
    return type === 'critical' ? 'destructive' : 'default';
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with counts */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Alerts & Flags</h3>
        <div className="flex gap-2">
          {criticalCount > 0 && (
            <Badge variant="destructive" className="text-xs">
              {criticalCount} Critical
            </Badge>
          )}
          {warningCount > 0 && (
            <Badge variant="outline" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-300">
              {warningCount} Warnings
            </Badge>
          )}
        </div>
      </div>

      {/* Flags list */}
      {flags.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No flags yet. All good! 👍</p>
        </div>
      ) : (
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {flags.map((flag) => (
              <Alert
                key={flag.id}
                variant={getVariant(flag.type)}
                className="relative"
              >
                <div className="flex gap-3">
                  <div className="mt-0.5">{getIcon(flag.type)}</div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-sm font-medium leading-none">
                        {flag.title}
                      </h4>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatTime(flag.timestamp)}
                      </span>
                    </div>
                    <AlertDescription className="text-xs">
                      {flag.description}
                    </AlertDescription>
                    {flag.confidence !== undefined && (
                      <div className="text-xs text-muted-foreground mt-1">
                        Confidence: {(flag.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              </Alert>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
};

export default RedFlagPanel;
