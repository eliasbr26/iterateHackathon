import { useState, useEffect } from "react";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import MetricsPanel from "@/components/dashboard/MetricsPanel";
import TranscriptFeed from "@/components/dashboard/TranscriptFeed";
import AlertPanel from "@/components/dashboard/AlertPanel";
import CoverageProgressBar from "@/components/dashboard/CoverageProgressBar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2, XCircle, TrendingUp, User, Briefcase, Globe, Calendar } from "lucide-react";

// Demo data for realistic simulation
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
    text: "Absolutely. The Black-Scholes model is a mathematical framework for pricing European options. The key assumptions include: constant volatility, log-normal distribution of returns, no transaction costs, and the ability to short sell. The formula itself derives from solving a partial differential equation that accounts for the option's time decay and the underlying asset's stochastic behavior.", 
    speaker: 'candidate' as const, 
    timestamp: Date.now() - 105000,
    confidence: 0.94
  },
  { 
    id: '3', 
    text: "Good. Now explain Delta and Gamma to me. How do they interact?", 
    speaker: 'interviewer' as const, 
    timestamp: Date.now() - 90000,
    confidence: 0.97
  },
  { 
    id: '4', 
    text: "Delta measures the option's sensitivity to price changes in the underlying - essentially the hedge ratio. Gamma is the second derivative - it measures how Delta itself changes. High Gamma means your hedge becomes unstable quickly, requiring frequent rebalancing. In volatile markets, managing Gamma risk is crucial because your Delta hedge can deteriorate rapidly.", 
    speaker: 'candidate' as const, 
    timestamp: Date.now() - 70000,
    confidence: 0.93
  },
  { 
    id: '5', 
    text: "Impressive. Tell me about a time when you had to make a decision under extreme pressure. How did you handle it?", 
    speaker: 'interviewer' as const, 
    timestamp: Date.now() - 50000,
    confidence: 0.95
  },
  {
    id: '6',
    text: "During my internship at the trading desk, there was a flash crash scenario. I had to quickly assess whether our positions were at risk and communicate with the team. I stayed calm, verified the data twice, and we managed to hedge appropriately before significant losses occurred.",
    speaker: 'candidate' as const,
    timestamp: Date.now() - 35000,
    confidence: 0.91
  }
];

const DEMO_ALERT = {
  id: 'alert-1',
  type: 'suggestion' as const,
  severity: 'low' as const,
  title: 'Follow-up Opportunity',
  message: 'The candidate mentioned risk management. Consider asking about specific quantitative risk metrics they\'ve used.',
  suggestion: 'Ask about VaR, Expected Shortfall, or stress testing methodologies.',
  timestamp: Date.now() - 5000,
  dismissed: false
};

const INTERVIEWER_PROFILE = {
  name: "Marcus Chen",
  age: 34,
  role: "Senior Quantitative Analyst",
  languages: ["English (Native)", "Mandarin (Fluent)", "Spanish (Intermediate)"],
  experience: "8 years",
  education: "PhD in Financial Mathematics, MIT",
  specializations: ["Derivatives Pricing", "Risk Management", "Statistical Arbitrage"],
  keyInsights: [
    "Strong technical questioning approach",
    "Focuses on practical application of theory",
    "Values stress-testing knowledge",
    "Emphasizes real-world trading scenarios"
  ],
  interviewHistory: {
    totalInterviews: 127,
    averageRating: 4.6,
    successRate: 73
  }
};

const AI_REVIEWS = {
  strengths: [
    {
      title: "Clear Technical Questions",
      description: "Questions were well-structured and progressively increased in complexity, from Black-Scholes basics to advanced Greeks interaction.",
      score: 9.2
    },
    {
      title: "Good Follow-up Timing",
      description: "Appropriately transitioned from technical to behavioral questions after establishing candidate's knowledge base.",
      score: 8.8
    },
    {
      title: "Active Listening",
      description: "Demonstrated attention to candidate's responses by asking relevant follow-ups about risk management.",
      score: 8.5
    }
  ],
  improvements: [
    {
      title: "Probe Deeper on Practical Experience",
      description: "While the flash crash story was good, consider asking for specific numbers or outcomes to verify depth of experience.",
      severity: "medium",
      suggestion: "Ask: 'What was the P&L impact?' or 'What specific hedging strategy did you implement?'"
    },
    {
      title: "Diversify Question Types",
      description: "Heavy focus on quantitative finance. Consider adding questions about teamwork, communication, or project management.",
      severity: "low",
      suggestion: "Include questions about cross-functional collaboration or handling disagreements with traders."
    },
    {
      title: "Watch Interruption Patterns",
      description: "Interrupted candidate once during the Greeks explanation. Allow complete answers before moving forward.",
      severity: "low",
      suggestion: "Wait 2-3 seconds after candidate finishes speaking before asking next question."
    }
  ],
  overallScore: 8.7,
  biasCheck: {
    status: "passed",
    notes: "No detected bias in questioning. Maintained professional and objective tone throughout."
  }
};

const Index = () => {
  const [demoMode, setDemoMode] = useState(true);
  const [sessionStatus, setSessionStatus] = useState<'initializing' | 'active' | 'paused' | 'completed'>('active');
  const [duration, setDuration] = useState(847);
  const [transcripts, setTranscripts] = useState(DEMO_TRANSCRIPTS);
  const [alerts, setAlerts] = useState([DEMO_ALERT]);
  const [audioActivity, setAudioActivity] = useState({ interviewer: 0, candidate: 0 });
  const [activeTab, setActiveTab] = useState("session");
  
  const [metrics, setMetrics] = useState({
    coverageScore: 7.2,
    scriptAdherence: 89,
    biasAlerts: 0,
    consistency: 'High' as const
  });

  const [coverage, setCoverage] = useState({
    technical: 0.67,
    behavioral: 0.33,
    market_knowledge: 0.20
  });

  // Demo mode: simulate real-time updates (only on Live Session tab)
  useEffect(() => {
    if (!demoMode || sessionStatus !== 'active' || activeTab !== 'session') return;

    const timer = setInterval(() => {
      setDuration(prev => prev + 1);
      
      // Randomly update audio activity
      if (Math.random() > 0.7) {
        setAudioActivity({
          interviewer: Math.random() > 0.5 ? Math.random() : 0,
          candidate: Math.random() > 0.5 ? Math.random() : 0
        });
      }

      // Gradually improve metrics
      if (Math.random() > 0.9) {
        setMetrics(prev => ({
          ...prev,
          coverageScore: Math.min(10, prev.coverageScore + 0.1),
          scriptAdherence: Math.min(100, prev.scriptAdherence + 1)
        }));
      }

      // Gradually increase coverage
      if (Math.random() > 0.85) {
        setCoverage(prev => ({
          technical: Math.min(1, prev.technical + 0.02),
          behavioral: Math.min(1, prev.behavioral + 0.03),
          market_knowledge: Math.min(1, prev.market_knowledge + 0.02)
        }));
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [demoMode, sessionStatus, activeTab]);

  const handlePause = () => {
    setSessionStatus(prev => prev === 'active' ? 'paused' : 'active');
  };

  const handleEnd = () => {
    if (confirm('Are you sure you want to end this interview session?')) {
      setSessionStatus('completed');
    }
  };

  const handleDismissAlert = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, dismissed: true } : a));
  };

  const DashboardContent = () => {
    return (
      <>
        <div className="flex-1 flex overflow-hidden">
          {/* Metrics Panel - Left 20% */}
          <div className="w-[20%] border-r border-border-subtle p-6 overflow-y-auto">
            <h2 className="text-sm font-semibold text-text-primary mb-4">Performance Metrics</h2>
            <MetricsPanel metrics={metrics} />
          </div>

          {/* Transcript Feed - Center 50% */}
          <div className="w-[50%] border-r border-border-subtle flex flex-col">
            <TranscriptFeed
              messages={transcripts}
              isLive={sessionStatus === 'active'}
              audioActivity={audioActivity}
            />
          </div>

          {/* Alert Panel - Right 30% */}
          <div className="w-[30%] p-6 overflow-y-auto">
            <AlertPanel
              alerts={alerts}
              onDismissAlert={handleDismissAlert}
            />
          </div>
        </div>

        <CoverageProgressBar coverage={coverage} />
      </>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg-primary">
      <DashboardHeader
        sessionId="demo-12847"
        sessionStatus={sessionStatus}
        duration={duration}
        onPause={handlePause}
        onEnd={handleEnd}
        demoMode={demoMode}
        onToggleDemo={() => setDemoMode(!demoMode)}
      />

      <div className="flex-1 overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="border-b border-border-subtle px-6">
            <TabsList className="h-12">
              <TabsTrigger value="session">Live Session</TabsTrigger>
              <TabsTrigger value="profile">Interviewer Profile</TabsTrigger>
              <TabsTrigger value="reviews">AI Reviews</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="session" className="flex-1 m-0 overflow-hidden">
            <DashboardContent />
          </TabsContent>

          <TabsContent value="profile" className="flex-1 m-0 overflow-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Header Section */}
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
                      Active Interviewer
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <Calendar className="h-4 w-4" />
                        <span>Age</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.age} years</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <Briefcase className="h-4 w-4" />
                        <span>Experience</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.experience}</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <TrendingUp className="h-4 w-4" />
                        <span>Success Rate</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.interviewHistory.successRate}%</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm">
                        <Globe className="h-4 w-4" />
                        <span>Rating</span>
                      </div>
                      <p className="font-medium">{INTERVIEWER_PROFILE.interviewHistory.averageRating}/5.0</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Languages & Education */}
              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Languages</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {INTERVIEWER_PROFILE.languages.map((lang, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <Globe className="h-4 w-4 text-muted-foreground" />
                          <span>{lang}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Education</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">{INTERVIEWER_PROFILE.education}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Specializations */}
              <Card>
                <CardHeader>
                  <CardTitle>Specializations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {INTERVIEWER_PROFILE.specializations.map((spec, idx) => (
                      <Badge key={idx} variant="outline">{spec}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Key Insights */}
              <Card>
                <CardHeader>
                  <CardTitle>Key Insights from Conversation</CardTitle>
                  <CardDescription>Behavioral patterns and interviewing style</CardDescription>
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

              {/* Transcript Section */}
              <Card>
                <CardHeader>
                  <CardTitle>Session Transcript</CardTitle>
                  <CardDescription>Complete conversation history</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {transcripts.map((msg) => (
                      <div key={msg.id} className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Badge variant={msg.speaker === 'interviewer' ? 'default' : 'secondary'}>
                            {msg.speaker === 'interviewer' ? 'Interviewer' : 'Candidate'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(msg.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm pl-4">{msg.text}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="reviews" className="flex-1 m-0 overflow-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
              {/* Overall Score */}
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
                <CardContent>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                    <span className="font-medium">{AI_REVIEWS.biasCheck.status === 'passed' ? 'Bias Check Passed' : 'Bias Detected'}</span>
                    <span className="text-muted-foreground">- {AI_REVIEWS.biasCheck.notes}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Strengths */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                    What You Did Right
                  </CardTitle>
                  <CardDescription>Areas of excellence in your interview technique</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {AI_REVIEWS.strengths.map((strength, idx) => (
                      <div key={idx}>
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-base">{strength.title}</h4>
                          <Badge variant="default" className="ml-2">
                            {strength.score}/10
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{strength.description}</p>
                        {idx < AI_REVIEWS.strengths.length - 1 && <Separator className="mt-6" />}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Areas for Improvement */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-accent" />
                    Areas for Improvement
                  </CardTitle>
                  <CardDescription>Actionable feedback to enhance your interview skills</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {AI_REVIEWS.improvements.map((improvement, idx) => (
                      <div key={idx}>
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-base">{improvement.title}</h4>
                          <Badge 
                            variant={improvement.severity === 'medium' ? 'default' : 'secondary'}
                            className="ml-2"
                          >
                            {improvement.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{improvement.description}</p>
                        <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
                          <p className="text-sm font-medium text-accent mb-1">💡 Suggestion:</p>
                          <p className="text-sm">{improvement.suggestion}</p>
                        </div>
                        {idx < AI_REVIEWS.improvements.length - 1 && <Separator className="mt-6" />}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
