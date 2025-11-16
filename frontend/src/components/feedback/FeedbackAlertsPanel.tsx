import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  Clock,
  MessageSquare,
  ThumbsUp,
  Shield,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface FeedbackAlertsPanelProps {
  interviewId: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface PacingAnalysis {
  status: 'too_fast' | 'too_slow' | 'ideal';
  qpm: number;
  recommendation: string;
  silent_periods_detected: boolean;
}

interface ToneAnalysis {
  tone: 'harsh' | 'neutral' | 'encouraging';
  confidence: number;
  trend: 'improving' | 'declining' | 'stable';
  specific_concerns: string[];
  suggestion: string;
}

interface QualityCheck {
  quality_score: number;
  quality_rating: 'excellent' | 'good' | 'needs_improvement' | 'poor';
  issues: string[];
  strengths: string[];
  improved_version?: string;
}

interface BiasDetection {
  has_bias: boolean;
  bias_score: number;
  severity: 'low' | 'medium' | 'high';
  bias_types: string[];
  bias_free_version?: string;
  legal_risk: boolean;
}

interface FeedbackData {
  pacing: PacingAnalysis;
  tone: ToneAnalysis;
  quality: QualityCheck;
  bias: BiasDetection;
  overall_feedback: string;
}

export const FeedbackAlertsPanel = ({
  interviewId,
  autoRefresh = false,
  refreshInterval = 30000
}: FeedbackAlertsPanelProps) => {
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchFeedback = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getCurrentFeedback(interviewId);
      setFeedback(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch feedback';
      setError(message);
      console.error('Feedback fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeedback();

    if (autoRefresh) {
      const interval = setInterval(fetchFeedback, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [interviewId, autoRefresh, refreshInterval]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const getPacingStatusIcon = (status: string) => {
    switch (status) {
      case 'ideal':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'too_fast':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'too_slow':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getToneIcon = (tone: string) => {
    switch (tone) {
      case 'encouraging':
        return <ThumbsUp className="h-4 w-4 text-green-500" />;
      case 'harsh':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <MessageSquare className="h-4 w-4 text-blue-500" />;
    }
  };

  if (error) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Real-Time Feedback
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={fetchFeedback} variant="outline" size="sm" className="mt-4">
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
            <Shield className="h-5 w-5 text-primary" />
            <CardTitle>Real-Time Feedback</CardTitle>
          </div>
          <Button
            onClick={fetchFeedback}
            variant="ghost"
            size="sm"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <CardDescription>
          AI-powered analysis of your interviewing technique
        </CardDescription>
      </CardHeader>

      <CardContent>
        {loading && !feedback ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : feedback && feedback.pacing && feedback.tone && feedback.quality && feedback.bias ? (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="pacing">
                <Clock className="h-4 w-4 mr-1" />
                Pacing
              </TabsTrigger>
              <TabsTrigger value="tone">
                <MessageSquare className="h-4 w-4 mr-1" />
                Tone
              </TabsTrigger>
              <TabsTrigger value="quality">
                <TrendingUp className="h-4 w-4 mr-1" />
                Quality
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4 mt-4">
              {/* Overall Feedback */}
              {feedback.overall_feedback && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{feedback.overall_feedback}</AlertDescription>
                </Alert>
              )}

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border p-3">
                  <div className="flex items-center gap-2 mb-1">
                    {getPacingStatusIcon(feedback.pacing.status)}
                    <span className="text-sm font-medium">Pacing</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {feedback.pacing.qpm.toFixed(1)} questions/min
                  </p>
                </div>

                <div className="rounded-lg border p-3">
                  <div className="flex items-center gap-2 mb-1">
                    {getToneIcon(feedback.tone.tone)}
                    <span className="text-sm font-medium">Tone</span>
                  </div>
                  <p className="text-xs text-muted-foreground capitalize">
                    {feedback.tone.tone} ({Math.round(feedback.tone.confidence * 100)}%)
                  </p>
                </div>

                <div className="rounded-lg border p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">Quality</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {feedback.quality.quality_score}/100 ({feedback.quality.quality_rating})
                  </p>
                </div>

                <div className="rounded-lg border p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <Shield className={`h-4 w-4 ${feedback.bias.has_bias ? 'text-red-500' : 'text-green-500'}`} />
                    <span className="text-sm font-medium">Bias Check</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {feedback.bias.has_bias ? `${feedback.bias.severity} risk` : 'No bias detected'}
                  </p>
                </div>
              </div>

              {/* Active Alerts */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Active Alerts</h4>
                <ScrollArea className="h-[200px]">
                  <div className="space-y-2">
                    {feedback.bias.has_bias && (
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Bias Detected:</strong> {feedback.bias.bias_types.join(', ')}
                          {feedback.bias.legal_risk && ' (Legal Risk)'}
                        </AlertDescription>
                      </Alert>
                    )}

                    {feedback.quality.quality_rating === 'poor' && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Question Quality:</strong> {feedback.quality.issues.join(', ')}
                        </AlertDescription>
                      </Alert>
                    )}

                    {feedback.tone.tone === 'harsh' && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Tone Alert:</strong> {feedback.tone.suggestion}
                        </AlertDescription>
                      </Alert>
                    )}

                    {feedback.pacing.status !== 'ideal' && (
                      <Alert>
                        <Clock className="h-4 w-4" />
                        <AlertDescription>
                          <strong>Pacing:</strong> {feedback.pacing.recommendation}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </ScrollArea>
              </div>
            </TabsContent>

            <TabsContent value="pacing" className="space-y-4 mt-4">
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getPacingStatusIcon(feedback.pacing.status)}
                    <h4 className="font-semibold capitalize">{feedback.pacing.status.replace('_', ' ')}</h4>
                  </div>
                  <Badge variant="outline">{feedback.pacing.qpm.toFixed(2)} QPM</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  {feedback.pacing.recommendation}
                </p>
                {feedback.pacing.silent_periods_detected && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      Silent periods detected. Consider asking follow-up questions.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </TabsContent>

            <TabsContent value="tone" className="space-y-4 mt-4">
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getToneIcon(feedback.tone.tone)}
                    <h4 className="font-semibold capitalize">{feedback.tone.tone}</h4>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{Math.round(feedback.tone.confidence * 100)}% confidence</Badge>
                    <Badge variant="secondary">{feedback.tone.trend}</Badge>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  {feedback.tone.suggestion}
                </p>
                {feedback.tone.specific_concerns.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold">Specific Concerns:</p>
                    <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                      {feedback.tone.specific_concerns.map((concern, idx) => (
                        <li key={idx}>{concern}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="quality" className="space-y-4 mt-4">
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold">Quality Score: {feedback.quality.quality_score}/100</h4>
                  <Badge>{feedback.quality.quality_rating}</Badge>
                </div>

                {feedback.quality.issues.length > 0 && (
                  <div className="space-y-2 mb-3">
                    <p className="text-xs font-semibold text-destructive">Issues:</p>
                    <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                      {feedback.quality.issues.map((issue, idx) => (
                        <li key={idx}>{issue.replace('_', ' ')}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {feedback.quality.strengths.length > 0 && (
                  <div className="space-y-2 mb-3">
                    <p className="text-xs font-semibold text-green-600">Strengths:</p>
                    <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                      {feedback.quality.strengths.map((strength, idx) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {feedback.quality.improved_version && (
                  <div className="rounded-lg bg-primary/5 p-3 mt-3">
                    <p className="text-xs font-semibold mb-1">Suggested Improvement:</p>
                    <p className="text-sm">{feedback.quality.improved_version}</p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Shield className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No feedback available yet</p>
            <p className="text-xs mt-1">Ask a question to get real-time analysis</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
