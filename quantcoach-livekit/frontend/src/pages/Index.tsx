import { useState, useEffect, useMemo, useCallback } from "react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import MetricsPanel from "@/components/dashboard/MetricsPanel";
import TranscriptFeed from "@/components/dashboard/TranscriptFeed";
import { VideoArea } from "@/components/video/VideoArea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2, TrendingUp, User, Briefcase, Globe, Calendar } from "lucide-react";

// New visualization components
import DifficultyBar from "@/components/dashboard/DifficultyBar";
import TopicChecklistPanel from "@/components/dashboard/TopicChecklistPanel";
import RedFlagPanel from "@/components/dashboard/RedFlagPanel";
import ToneIndicator from "@/components/dashboard/ToneIndicator";
import InterviewTimeline from "@/components/dashboard/InterviewTimeline";
import ConfidenceMeters from "@/components/dashboard/ConfidenceMeters";
import LiveTranscriptPanel from "@/components/dashboard/LiveTranscriptPanel";

// Real-time data hook
import { useTranscriptStream } from "@/hooks/useTranscriptStream";

// Demo data (kept for demo mode)
const DEMO_TRANSCRIPTS = [
  {
    id: '1',
    text: "Let's start with a technical question. Can you walk me through the Black-Scholes model and its assumptions?",
    speaker: 'interviewer' as const,
    timestamp: Date.now() - 120000,
    confidence: 0.96
  },
  {
    id: '2',
    text: "Absolutely. The Black-Scholes model is a mathematical framework for pricing European options. The key assumptions include: constant volatility, log-normal distribution of returns, no transaction costs, and the ability to short sell.",
    speaker: 'candidate' as const,
    timestamp: Date.now() - 105000,
    confidence: 0.94
  },
];

const DEMO_EVALUATIONS = [
  {
    timestamp: new Date().toISOString(),
    window_start: new Date(Date.now() - 20000).toISOString(),
    window_end: new Date(Date.now() - 10000).toISOString(),
    transcripts_evaluated: 2,
    subject_relevance: 'on_topic' as const,
    question_difficulty: 'medium' as const,
    interviewer_tone: 'neutral' as const,
    summary: 'Discussion about Black-Scholes model and option pricing fundamentals.',
    key_topics: ['CV_TECHNIQUES', 'TIME_SERIES_MODELS'],
    flags: [],
    confidence_subject: 0.95,
    confidence_difficulty: 0.88,
    confidence_tone: 0.92,
  }
];

const Index = () => {
  const [demoMode, setDemoMode] = useState(false); // Start in demo mode
  const [sessionStatus, setSessionStatus] = useState<'initializing' | 'active' | 'paused' | 'completed'>('active');
  const [duration, setDuration] = useState(0);
  const [activeTab, setActiveTab] = useState("session");
  const [roomName, setRoomName] = useState<string>("test1");

  // Real-time SSE connection
  const {
    transcripts: liveTranscripts,
    evaluations: liveEvaluations,
    isConnected,
    error: sseError
  } = useTranscriptStream({
    roomName: roomName,
    apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    autoConnect: !demoMode, // Only connect if not in demo mode
  });

  // Handle room creation from VideoArea
  const handleRoomCreated = useCallback((newRoomName: string) => {
    console.log('[Index] Room created:', newRoomName);
    // Update room name - the hook will automatically reconnect
    setRoomName(newRoomName);
  }, []);

  // Choose between demo and real data
  const transcripts = demoMode ? DEMO_TRANSCRIPTS : liveTranscripts;
  const evaluations = demoMode ? DEMO_EVALUATIONS : liveEvaluations;

  // Convert transcripts to feed format
  const transcriptFeedData = transcripts.map((t, idx) => ({
    id: `transcript-${idx}`,
    text: t.text,
    speaker: t.speaker as 'interviewer' | 'candidate',
    timestamp: new Date(t.timestamp).getTime(),
    confidence: 0.9,
  }));

  // Calculate metrics from evaluations
  const calculateMetrics = () => {
    if (evaluations.length === 0) {
      return {
        coverageScore: 0,
        scriptAdherence: 0,
        biasAlerts: 0,
        consistency: 'Unknown' as const
      };
    }

    // Calculate coverage score based on topic variety
    const uniqueTopics = new Set(evaluations.flatMap(e => e.key_topics));
    const coverageScore = Math.min(10, (uniqueTopics.size / 11) * 10);

    // Calculate script adherence based on relevance
    const onTopicCount = evaluations.filter(e => e.subject_relevance === 'on_topic').length;
    const scriptAdherence = (onTopicCount / evaluations.length) * 100;

    // Count bias alerts (harsh tone or off-topic)
    const biasAlerts = evaluations.filter(
      e => e.interviewer_tone === 'harsh' || e.subject_relevance === 'off_topic'
    ).length;

    // Determine consistency based on tone variance
    const toneValues = { harsh: 0, neutral: 1, encouraging: 2 };
    const toneScores = evaluations.map(e => toneValues[e.interviewer_tone.toLowerCase() as keyof typeof toneValues] ?? 1);
    const toneVariance = toneScores.reduce((acc, val) => acc + Math.abs(val - 1), 0) / toneScores.length;
    const consistency = toneVariance < 0.3 ? 'High' : toneVariance < 0.6 ? 'Medium' : 'Low';

    return {
      coverageScore,
      scriptAdherence: Math.round(scriptAdherence),
      biasAlerts,
      consistency: consistency as 'High' | 'Medium' | 'Low'
    };
  };

  const metrics = calculateMetrics();

  // Note: Coverage calculation removed per product requirements

  // Update duration timer
  useEffect(() => {
    if (sessionStatus !== 'active') return;

    const timer = setInterval(() => {
      setDuration(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [sessionStatus]);

  const handlePause = () => {
    setSessionStatus(prev => prev === 'active' ? 'paused' : 'active');
  };

  const handleEnd = () => {
    if (confirm('Are you sure you want to end this interview session?')) {
      setSessionStatus('completed');
    }
  };

  const handleToggleDemo = () => {
    setDemoMode(!demoMode);
  };

  const dashboardContent = useMemo(() => {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        {/* Main Content Grid - Takes Full Height */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full grid grid-cols-12 gap-3 p-3">
            {/* Left Column - Fixed Width - Topic Coverage */}
            <div className="col-span-3 h-full overflow-y-auto space-y-2 pr-2">
              <TopicChecklistPanel evaluations={evaluations} />
            </div>

            {/* Center Column - Flexible Width - Main Content */}
            <div className="col-span-6 h-full flex flex-col space-y-2 overflow-y-auto">
              <DifficultyBar evaluations={evaluations} />
              <ToneIndicator evaluations={evaluations} />
              <ConfidenceMeters evaluations={evaluations} />
              <InterviewTimeline evaluations={evaluations} />
            </div>

            {/* Right Column - Fixed Width - Alerts & Metrics */}
            <div className="col-span-3 h-full overflow-y-auto space-y-2 pl-2">
              <RedFlagPanel evaluations={evaluations} />
              <MetricsPanel metrics={metrics} />
            </div>
          </div>
        </div>
      </div>
    );
  }, [evaluations, metrics]);

  // Interviewer profile (static for now)
  const INTERVIEWER_PROFILE = {
    name: "AI Interview Analyst",
    age: null,
    role: "Quantitative Finance Interview System",
    languages: ["English"],
    experience: "Real-time AI-powered analysis",
    education: "Anthropic Claude Sonnet 4.5",
    specializations: ["Topic Detection", "Difficulty Analysis", "Tone Assessment"],
    keyInsights: [
      "Tracks 11 core quantitative finance topics",
      "Real-time difficulty assessment (Easy/Medium/Hard)",
      "Interviewer tone analysis (Harsh/Neutral/Encouraging)",
      "Automatic red flag detection for off-topic discussions"
    ],
  };

  const AI_REVIEWS = {
    overallScore: evaluations.length > 0
      ? ((metrics.coverageScore + (metrics.scriptAdherence / 10)) / 2).toFixed(1)
      : "N/A",
    biasCheck: {
      status: metrics.biasAlerts === 0 ? "passed" : "warnings",
      notes: metrics.biasAlerts === 0
        ? "No detected bias in questioning"
        : `${metrics.biasAlerts} potential bias indicators detected`,
    },
    strengths: evaluations
      .filter(e => e.subject_relevance === 'on_topic' && e.question_difficulty !== 'easy')
      .slice(-3)
      .map(e => ({
        title: `Focused on ${e.key_topics[0] || 'Core Topics'}`,
        description: e.summary,
        score: e.confidence_subject * 10,
      })),
    improvements: evaluations
      .filter(e => e.flags.length > 0 || e.subject_relevance === 'off_topic')
      .slice(-3)
      .map(e => ({
        title: e.subject_relevance === 'off_topic' ? 'Went Off-Topic' : 'Follow-up Opportunity',
        description: e.summary,
        severity: e.subject_relevance === 'off_topic' ? 'high' : 'medium',
        suggestion: e.flags[0] || 'Consider steering back to quantitative finance topics',
      })),
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg-primary">
      <DashboardHeader
        sessionId={roomName}
        sessionStatus={sessionStatus}
        duration={duration}
        onPause={handlePause}
        onEnd={handleEnd}
        demoMode={demoMode}
        onToggleDemo={handleToggleDemo}
      />

      {/* Video Area - Always Visible Above Tabs */}
      <div className="border-b border-border-subtle p-4 shrink-0">
        <div className="max-w-7xl mx-auto">
          <VideoArea onRoomCreated={handleRoomCreated} />

          {/* Connection status indicator */}
          {!demoMode && (
            <div className="mt-3 flex items-center gap-2 text-xs">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-muted-foreground">
                {isConnected ? 'Live data streaming' : 'Disconnected'}
                {sseError && ` - ${sseError}`}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="border-b border-border-subtle px-6">
            <TabsList className="h-12">
              <TabsTrigger value="session">Dashboard</TabsTrigger>
              <TabsTrigger value="transcripts">Live Transcription</TabsTrigger>
              <TabsTrigger value="profile">System Info</TabsTrigger>
              <TabsTrigger value="reviews">AI Analysis</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="session" className="flex-1 m-0 overflow-hidden">
            {dashboardContent}
          </TabsContent>

          <TabsContent value="transcripts" className="flex-1 m-0 overflow-auto p-6">
            <div className="max-w-7xl mx-auto">
              <LiveTranscriptPanel
                messages={transcriptFeedData}
                isLive={sessionStatus === 'active'}
              />
            </div>
          </TabsContent>

          <TabsContent value="profile" className="flex-1 m-0 overflow-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-8 w-8 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-2xl">{INTERVIEWER_PROFILE.name}</CardTitle>
                        <CardDescription className="text-base mt-1">{INTERVIEWER_PROFILE.role}</CardDescription>
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-sm">
                      {isConnected && !demoMode ? 'Live' : 'Demo Mode'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <Globe className="h-4 w-4" />
                        <span>Language</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.languages.join(', ')}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <Briefcase className="h-4 w-4" />
                        <span>Model</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.education}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <TrendingUp className="h-4 w-4" />
                        <span>Evaluations</span>
                      </div>
                      <p className="font-medium">{evaluations.length}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Capabilities</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {INTERVIEWER_PROFILE.keyInsights.map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Topic Taxonomy</CardTitle>
                  <CardDescription>11 core quantitative finance topics tracked</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {['CV_TECHNIQUES', 'REGULARIZATION', 'FEATURE_SELECTION', 'STATIONARITY',
                      'TIME_SERIES_MODELS', 'OPTIMIZATION_PYTHON', 'LOOKAHEAD_BIAS',
                      'DATA_PIPELINE', 'BEHAVIORAL_PRESSURE', 'BEHAVIORAL_TEAMWORK', 'EXTRA'].map(topic => (
                      <Badge key={topic} variant="outline" className="justify-center">
                        {topic.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="reviews" className="flex-1 m-0 overflow-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              {evaluations.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <p className="text-muted-foreground">No evaluations yet. Analysis will appear as the interview progresses.</p>
                  </CardContent>
                </Card>
              ) : (
                <>
                  <Card className="border-primary/20 bg-primary/5">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-3xl">Overall Performance</CardTitle>
                          <CardDescription className="text-base mt-1">AI-powered interview analysis</CardDescription>
                        </div>
                        <div className="text-right">
                          <div className="text-5xl font-bold text-primary">{AI_REVIEWS.overallScore}</div>
                          <div className="text-sm text-muted-foreground">out of 10</div>
                        </div>
                      </div>
                    </CardHeader>
                  </Card>

                  {AI_REVIEWS.strengths.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <CheckCircle2 className="h-5 w-5 text-primary" />
                          Effective Moments
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {AI_REVIEWS.strengths.map((strength, idx) => (
                            <div key={idx}>
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold">{strength.title}</h4>
                                <Badge variant="default">{strength.score.toFixed(1)}/10</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{strength.description}</p>
                              {idx < AI_REVIEWS.strengths.length - 1 && <Separator className="mt-4" />}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {AI_REVIEWS.improvements.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <TrendingUp className="h-5 w-5 text-accent" />
                          Areas for Improvement
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {AI_REVIEWS.improvements.map((improvement, idx) => (
                            <div key={idx}>
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold">{improvement.title}</h4>
                                <Badge variant="outline">{improvement.severity}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mb-2">{improvement.description}</p>
                              <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
                                <p className="text-sm font-medium text-accent mb-1">💡 Suggestion:</p>
                                <p className="text-sm">{improvement.suggestion}</p>
                              </div>
                              {idx < AI_REVIEWS.improvements.length - 1 && <Separator className="mt-4" />}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
