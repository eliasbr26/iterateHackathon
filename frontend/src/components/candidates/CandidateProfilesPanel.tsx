import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  User,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Calendar,
  MessageSquare,
  FileText,
  ChevronRight,
  Loader2,
  Award,
  Languages
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface Candidate {
  id: number;
  name: string;
  email: string;
  created_at: string;
  has_cv: boolean;
  interview_count: number;
}

interface CandidateDetail {
  id: number;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
  cv_text: string;
  cv_parsed_data: {
    personal_info?: {
      name?: string;
      email?: string;
      phone?: string;
      location?: string;
    };
    summary?: string;
    work_experience?: Array<{
      title?: string;
      company?: string;
      duration?: string;
      description?: string;
    }>;
    education?: Array<{
      degree?: string;
      institution?: string;
      year?: string;
    }>;
    skills?: string[];
    languages?: string[];
    certifications?: string[];
    interview_notes?: Array<{
      timestamp: string;
      note: string;
    }>;
  };
  interviews: Array<{
    id: number;
    room_name: string;
    status: string;
    started_at: string;
    ended_at: string;
    transcript_count: number;
    transcripts: Array<{
      id: number;
      speaker: string;
      text: string;
      timestamp: string;
    }>;
    summary?: {
      overall_assessment?: string;
      key_strengths?: string[];
      areas_for_improvement?: string[];
      recommendation?: string;
    };
  }>;
  total_interviews: number;
}

export const CandidateProfilesPanel = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadCandidates();
  }, []);

  const loadCandidates = async () => {
    try {
      setLoading(true);
      const data = await api.listCandidates();
      setCandidates(data.candidates || []);
    } catch (error) {
      console.error('Failed to load candidates:', error);
      toast({
        title: 'Error loading candidates',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadCandidateDetail = async (candidateId: number) => {
    try {
      setLoadingDetail(true);
      const data = await api.getCandidateProfile(candidateId);
      setSelectedCandidate(data);
    } catch (error) {
      console.error('Failed to load candidate detail:', error);
      toast({
        title: 'Error loading candidate profile',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="grid grid-cols-12 gap-6 h-full">
      {/* Candidate List - Left Side */}
      <div className="col-span-4">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <CardTitle>All Candidates</CardTitle>
            <CardDescription>
              {candidates.length} candidate{candidates.length !== 1 ? 's' : ''} total
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : candidates.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <User className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No candidates yet</p>
                <p className="text-sm mt-1">Upload a CV to create a candidate profile</p>
              </div>
            ) : (
              <div className="space-y-2">
                {candidates.map((candidate) => (
                  <button
                    key={candidate.id}
                    onClick={() => loadCandidateDetail(candidate.id)}
                    className={`w-full text-left p-4 rounded-lg border transition-colors ${
                      selectedCandidate?.id === candidate.id
                        ? 'bg-primary/10 border-primary'
                        : 'hover:bg-muted border-border'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{candidate.name}</div>
                        <div className="text-sm text-muted-foreground truncate flex items-center gap-1 mt-1">
                          <Mail className="h-3 w-3" />
                          {candidate.email}
                        </div>
                        <div className="flex gap-2 mt-2">
                          {candidate.has_cv && (
                            <Badge variant="secondary" className="text-xs">
                              CV Uploaded
                            </Badge>
                          )}
                          {candidate.interview_count > 0 && (
                            <Badge variant="outline" className="text-xs">
                              {candidate.interview_count} interview{candidate.interview_count !== 1 ? 's' : ''}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Candidate Detail - Right Side */}
      <div className="col-span-8">
        {loadingDetail ? (
          <Card className="h-full flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </Card>
        ) : !selectedCandidate ? (
          <Card className="h-full flex items-center justify-center">
            <CardContent className="text-center py-8">
              <User className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-lg font-medium">Select a candidate to view their profile</p>
              <p className="text-sm text-muted-foreground mt-1">
                View CV information, interview history, and transcripts
              </p>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex flex-col">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl">{selectedCandidate.name}</CardTitle>
                  <CardDescription className="text-base mt-1">
                    {selectedCandidate.cv_parsed_data?.personal_info?.email || selectedCandidate.email}
                  </CardDescription>
                </div>
                <div className="text-right text-sm text-muted-foreground">
                  <div>Created: {formatDate(selectedCandidate.created_at)}</div>
                  {selectedCandidate.updated_at && (
                    <div>Updated: {formatDate(selectedCandidate.updated_at)}</div>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 overflow-auto">
              <Tabs defaultValue="profile" className="h-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="profile">Profile</TabsTrigger>
                  <TabsTrigger value="interviews">
                    Interviews ({selectedCandidate.total_interviews})
                  </TabsTrigger>
                  <TabsTrigger value="notes">Notes</TabsTrigger>
                </TabsList>

                {/* Profile Tab */}
                <TabsContent value="profile" className="space-y-6">
                  {/* Contact Information */}
                  {selectedCandidate.cv_parsed_data?.personal_info && (
                    <div>
                      <h3 className="font-semibold mb-3">Contact Information</h3>
                      <div className="grid grid-cols-2 gap-3">
                        {selectedCandidate.cv_parsed_data.personal_info.phone && (
                          <div className="flex items-center gap-2 text-sm">
                            <Phone className="h-4 w-4 text-muted-foreground" />
                            <span>{selectedCandidate.cv_parsed_data.personal_info.phone}</span>
                          </div>
                        )}
                        {selectedCandidate.cv_parsed_data.personal_info.location && (
                          <div className="flex items-center gap-2 text-sm">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span>{selectedCandidate.cv_parsed_data.personal_info.location}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {selectedCandidate.cv_parsed_data?.summary && (
                    <div>
                      <h3 className="font-semibold mb-3">Professional Summary</h3>
                      <p className="text-sm text-muted-foreground">
                        {selectedCandidate.cv_parsed_data.summary}
                      </p>
                    </div>
                  )}

                  <Separator />

                  {/* Work Experience */}
                  {selectedCandidate.cv_parsed_data?.work_experience && selectedCandidate.cv_parsed_data.work_experience.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Briefcase className="h-4 w-4" />
                        Work Experience
                      </h3>
                      <div className="space-y-4">
                        {selectedCandidate.cv_parsed_data.work_experience.map((exp, idx) => (
                          <div key={idx} className="border-l-2 border-primary/20 pl-4">
                            <div className="font-medium">{exp.title}</div>
                            <div className="text-sm text-muted-foreground">
                              {exp.company} {exp.duration && `• ${exp.duration}`}
                            </div>
                            {exp.description && (
                              <p className="text-sm mt-1">{exp.description}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Education */}
                  {selectedCandidate.cv_parsed_data?.education && selectedCandidate.cv_parsed_data.education.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <GraduationCap className="h-4 w-4" />
                        Education
                      </h3>
                      <div className="space-y-3">
                        {selectedCandidate.cv_parsed_data.education.map((edu, idx) => (
                          <div key={idx}>
                            <div className="font-medium">{edu.degree}</div>
                            <div className="text-sm text-muted-foreground">
                              {edu.institution} {edu.year && `• ${edu.year}`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Skills */}
                  {selectedCandidate.cv_parsed_data?.skills && selectedCandidate.cv_parsed_data.skills.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3">Skills</h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedCandidate.cv_parsed_data.skills.map((skill, idx) => (
                          <Badge key={idx} variant="secondary">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Languages */}
                  {selectedCandidate.cv_parsed_data?.languages && selectedCandidate.cv_parsed_data.languages.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Languages className="h-4 w-4" />
                        Languages
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {selectedCandidate.cv_parsed_data.languages.map((lang, idx) => (
                          <Badge key={idx} variant="outline">
                            {lang}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Certifications */}
                  {selectedCandidate.cv_parsed_data?.certifications && selectedCandidate.cv_parsed_data.certifications.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Award className="h-4 w-4" />
                        Certifications
                      </h3>
                      <div className="space-y-2">
                        {selectedCandidate.cv_parsed_data.certifications.map((cert, idx) => (
                          <div key={idx} className="text-sm">• {cert}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </TabsContent>

                {/* Interviews Tab */}
                <TabsContent value="interviews" className="space-y-4">
                  {selectedCandidate.interviews.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>No interviews yet</p>
                    </div>
                  ) : (
                    selectedCandidate.interviews.map((interview) => (
                      <Card key={interview.id}>
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <div>
                              <CardTitle className="text-lg">{interview.room_name}</CardTitle>
                              <CardDescription>
                                {interview.started_at && formatDateTime(interview.started_at)}
                              </CardDescription>
                            </div>
                            <Badge variant={interview.status === 'completed' ? 'default' : 'secondary'}>
                              {interview.status}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {/* Interview Summary */}
                          {interview.summary && (
                            <div className="space-y-2">
                              {interview.summary.overall_assessment && (
                                <div>
                                  <div className="text-sm font-medium">Assessment</div>
                                  <p className="text-sm text-muted-foreground">
                                    {interview.summary.overall_assessment}
                                  </p>
                                </div>
                              )}
                              {interview.summary.recommendation && (
                                <div>
                                  <div className="text-sm font-medium">Recommendation</div>
                                  <p className="text-sm text-muted-foreground">
                                    {interview.summary.recommendation}
                                  </p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* Transcripts */}
                          {interview.transcripts && interview.transcripts.length > 0 && (
                            <div>
                              <div className="text-sm font-medium mb-2 flex items-center gap-2">
                                <FileText className="h-4 w-4" />
                                Transcript ({interview.transcript_count} messages)
                              </div>
                              <div className="border rounded-lg p-3 max-h-64 overflow-y-auto space-y-2 text-sm">
                                {interview.transcripts.map((transcript) => (
                                  <div
                                    key={transcript.id}
                                    className={`p-2 rounded ${
                                      transcript.speaker === 'interviewer'
                                        ? 'bg-primary/10'
                                        : 'bg-muted'
                                    }`}
                                  >
                                    <div className="font-medium text-xs capitalize mb-1">
                                      {transcript.speaker}
                                    </div>
                                    <div>{transcript.text}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </TabsContent>

                {/* Notes Tab */}
                <TabsContent value="notes" className="space-y-4">
                  {selectedCandidate.cv_parsed_data?.interview_notes && selectedCandidate.cv_parsed_data.interview_notes.length > 0 ? (
                    <div className="space-y-3">
                      {selectedCandidate.cv_parsed_data.interview_notes.map((note, idx) => (
                        <Card key={idx}>
                          <CardContent className="pt-4">
                            <div className="text-xs text-muted-foreground mb-2">
                              {formatDateTime(note.timestamp)}
                            </div>
                            <p className="text-sm">{note.note}</p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
                      <p>No interview notes yet</p>
                      <p className="text-sm mt-1">
                        Notes from interviews will be automatically added here
                      </p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
