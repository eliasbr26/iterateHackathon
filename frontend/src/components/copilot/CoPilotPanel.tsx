import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Lightbulb,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  MessageSquare,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface CoPilotPanelProps {
  interviewId: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
}

interface FollowUpSuggestion {
  question: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  competency: string;
}

interface CoverageData {
  competency: string;
  current_score: number;
  target_score: number;
  coverage_percentage: number;
  status: 'not_started' | 'in_progress' | 'well_covered' | 'needs_attention';
  suggested_questions_count: number;
}

interface CoPilotData {
  follow_up_suggestions: FollowUpSuggestion[];
  coverage_status: CoverageData[];
  overall_progress: number;
  recommended_next_step: string;
  interview_phase: string;
  time_remaining_minutes: number;
}

export const CoPilotPanel = ({
  interviewId,
  autoRefresh = false,
  refreshInterval = 30000
}: CoPilotPanelProps) => {
  const [data, setData] = useState<CoPilotData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getCoPilotSuggestions(interviewId);
      setData(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch co-pilot suggestions';
      setError(message);
      console.error('Co-pilot fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();

    if (autoRefresh) {
      const interval = setInterval(fetchSuggestions, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [interviewId, autoRefresh, refreshInterval]);

  const getCoverageStatusColor = (status: string) => {
    switch (status) {
      case 'well_covered':
        return 'bg-green-500/10 text-green-700 border-green-500/20';
      case 'in_progress':
        return 'bg-blue-500/10 text-blue-700 border-blue-500/20';
      case 'needs_attention':
        return 'bg-yellow-500/10 text-yellow-700 border-yellow-500/20';
      default:
        return 'bg-gray-500/10 text-gray-700 border-gray-500/20';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const handleCopyQuestion = (question: string) => {
    navigator.clipboard.writeText(question);
    toast({
      title: 'Copied!',
      description: 'Question copied to clipboard',
    });
  };

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            AI Co-Pilot
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <p className="text-sm">{error}</p>
          </div>
          <Button onClick={fetchSuggestions} variant="outline" size="sm" className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle>AI Co-Pilot</CardTitle>
          </div>
          <Button
            onClick={fetchSuggestions}
            variant="ghost"
            size="sm"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <CardDescription>
          Real-time interview guidance and suggestions
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {loading && !data ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : data ? (
          <>
            {/* Overall Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Overall Coverage</span>
                <span className="text-muted-foreground">{Math.round(data.overall_progress)}%</span>
              </div>
              <Progress value={data.overall_progress} className="h-2" />
              {data.interview_phase && (
                <p className="text-xs text-muted-foreground">
                  Phase: {data.interview_phase}
                  {data.time_remaining_minutes > 0 &&
                    ` • ${data.time_remaining_minutes} min remaining`
                  }
                </p>
              )}
            </div>

            <Separator />

            {/* Recommended Next Step */}
            {data.recommended_next_step && (
              <div className="rounded-lg border bg-primary/5 p-4">
                <div className="flex items-start gap-3">
                  <Lightbulb className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium mb-1">Recommended Next Step</p>
                    <p className="text-sm text-muted-foreground">
                      {data.recommended_next_step}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Follow-up Suggestions */}
            {data.follow_up_suggestions && data.follow_up_suggestions.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold">Suggested Follow-ups</h3>
                </div>
                <ScrollArea className="h-[300px] pr-4">
                  <div className="space-y-3">
                    {data.follow_up_suggestions.map((suggestion, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg border p-3 hover:bg-accent/50 transition-colors cursor-pointer group"
                        onClick={() => handleCopyQuestion(suggestion.question)}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <Badge
                            variant={getPriorityColor(suggestion.priority) as any}
                            className="text-xs"
                          >
                            {suggestion.priority}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {suggestion.competency}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium mb-1 group-hover:text-primary transition-colors">
                          {suggestion.question}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {suggestion.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            {/* Coverage Status */}
            {data.coverage_status && data.coverage_status.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold">Competency Coverage</h3>
                </div>
                <div className="space-y-2">
                  {data.coverage_status.map((coverage, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium">{coverage.competency}</span>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={`text-xs ${getCoverageStatusColor(coverage.status)}`}
                          >
                            {coverage.status.replace('_', ' ')}
                          </Badge>
                          <span className="text-muted-foreground">
                            {Math.round(coverage.coverage_percentage)}%
                          </span>
                        </div>
                      </div>
                      <Progress value={coverage.coverage_percentage} className="h-1" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">No suggestions available yet</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
