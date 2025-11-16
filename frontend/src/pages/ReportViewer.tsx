import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import {
  FileText,
  Download,
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Star,
  Award,
  AlertTriangle
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

export default function ReportViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const interviewId = parseInt(id || '0');

  const [interview, setInterview] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [reports, setReports] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('full');

  useEffect(() => {
    fetchData();
  }, [interviewId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [interviewData, reportsData] = await Promise.all([
        api.getInterview(interviewId),
        api.getReports(interviewId)
      ]);
      setInterview(interviewData);
      setReports(reportsData);
      setSummary(interviewData.summary);
    } catch (err) {
      console.error('Failed to fetch report data:', err);
      toast({
        title: 'Error',
        description: 'Failed to load interview data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    try {
      setGenerating(true);
      const response = await api.generateSummary(interviewId);
      setSummary(response);
      toast({
        title: 'Summary Generated',
        description: 'Interview summary has been generated successfully',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to generate summary',
        variant: 'destructive',
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateReport = async (reportType: string, format: string) => {
    try {
      setGenerating(true);
      const response = await api.generateReport(interviewId, reportType, format);

      if (format === 'html' || format === 'markdown') {
        // Create download link
        const blob = new Blob([response], {
          type: format === 'html' ? 'text/html' : 'text/markdown'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `interview_${interviewId}_${reportType}.${format === 'html' ? 'html' : 'md'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      toast({
        title: 'Report Generated',
        description: `${reportType} report has been generated`,
      });

      fetchData(); // Refresh to show new report
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to generate report',
        variant: 'destructive',
      });
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/interviews')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Interview Report</h1>
              <p className="text-muted-foreground mt-1">
                {interview?.candidate_name} - {interview?.job_title}
              </p>
            </div>
          </div>
        </div>

        {/* Summary Card */}
        {summary ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl">Executive Summary</CardTitle>
                  <CardDescription>AI-generated interview analysis</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {summary.overall_score && (
                    <Badge className="text-2xl px-4 py-2">
                      {Math.round(summary.overall_score)}/100
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Executive Summary */}
              {summary.executive_summary && (
                <div>
                  <h3 className="font-semibold mb-2">Overview</h3>
                  <p className="text-sm text-muted-foreground">{summary.executive_summary}</p>
                </div>
              )}

              <Separator />

              {/* Key Highlights */}
              {summary.key_highlights && summary.key_highlights.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Star className="h-4 w-4 text-yellow-500" />
                    Key Highlights
                  </h3>
                  <ul className="space-y-2">
                    {summary.key_highlights.map((highlight: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                        <span>{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-2 gap-6">
                {/* Strengths */}
                {summary.strengths && summary.strengths.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center gap-2 text-green-600">
                      <Award className="h-4 w-4" />
                      Strengths
                    </h3>
                    <ul className="space-y-2">
                      {summary.strengths.map((strength: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <TrendingUp className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                          <span>{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Weaknesses */}
                {summary.weaknesses && summary.weaknesses.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center gap-2 text-orange-600">
                      <AlertCircle className="h-4 w-4" />
                      Areas for Development
                    </h3>
                    <ul className="space-y-2">
                      {summary.weaknesses.map((weakness: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <AlertTriangle className="h-4 w-4 text-orange-500 shrink-0 mt-0.5" />
                          <span>{weakness}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Hiring Recommendation */}
              {summary.hiring_recommendation && (
                <>
                  <Separator />
                  <div className="rounded-lg bg-primary/5 p-4">
                    <h3 className="font-semibold mb-2">Hiring Recommendation</h3>
                    <p className="text-sm mb-2">
                      <Badge className="mr-2">{summary.hiring_recommendation}</Badge>
                      {summary.recommendation_confidence && (
                        <span className="text-xs text-muted-foreground">
                          Confidence: {Math.round(summary.recommendation_confidence * 100)}%
                        </span>
                      )}
                    </p>
                    {summary.recommendation_reasoning && (
                      <p className="text-sm text-muted-foreground">
                        {summary.recommendation_reasoning}
                      </p>
                    )}
                  </div>
                </>
              )}

              {/* Concerns */}
              {summary.concerns && summary.concerns.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h3 className="font-semibold mb-3 flex items-center gap-2 text-red-600">
                      <AlertTriangle className="h-4 w-4" />
                      Concerns
                    </h3>
                    <ul className="space-y-2">
                      {summary.concerns.map((concern: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                          <span>{concern}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground mb-4">No summary generated yet</p>
              <Button onClick={handleGenerateSummary} disabled={generating}>
                {generating ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>Generate Summary</>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Reports */}
        <Card>
          <CardHeader>
            <CardTitle>Generate Reports</CardTitle>
            <CardDescription>
              Export interview data in different formats for various stakeholders
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={selectedReportType} onValueChange={setSelectedReportType}>
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="ats">ATS</TabsTrigger>
                <TabsTrigger value="hiring_manager">Hiring Manager</TabsTrigger>
                <TabsTrigger value="recruiter">Recruiter</TabsTrigger>
                <TabsTrigger value="full">Full Report</TabsTrigger>
              </TabsList>

              <TabsContent value="ats" className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Simplified pass/fail summary with key scores for ATS integration
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleGenerateReport('ats', 'json')}
                    disabled={generating}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="hiring_manager" className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Detailed competency breakdown with strengths, weaknesses, and recommendations
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleGenerateReport('hiring_manager', 'html')}
                    disabled={generating}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download HTML
                  </Button>
                  <Button
                    onClick={() => handleGenerateReport('hiring_manager', 'json')}
                    disabled={generating}
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="recruiter" className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  High-level overview for quick candidate assessment
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleGenerateReport('recruiter', 'html')}
                    disabled={generating}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download HTML
                  </Button>
                  <Button
                    onClick={() => handleGenerateReport('recruiter', 'markdown')}
                    disabled={generating}
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Markdown
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="full" className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Complete interview data including transcripts, evaluations, and all metrics
                </p>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleGenerateReport('full', 'json')}
                    disabled={generating}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                  <Button
                    onClick={() => handleGenerateReport('full', 'html')}
                    disabled={generating}
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download HTML
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
