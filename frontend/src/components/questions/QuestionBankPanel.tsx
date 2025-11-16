import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  MessageCircleQuestion,
  Sparkles,
  Search,
  Filter,
  Copy,
  RefreshCw,
  TrendingUp,
  Target,
  Clock
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface QuestionBankPanelProps {
  interviewId: number;
  jobTitle?: string;
  currentCompetency?: string;
}

interface QuestionSuggestion {
  question_text: string;
  question_type: string;
  competency: string;
  difficulty: 'easy' | 'medium' | 'hard';
  reason: string;
  expected_answer_outline: string;
  follow_up_questions: string[];
  evaluation_criteria: string[];
  average_response_time_seconds: number;
  success_rate: number;
}

interface QuestionContext {
  current_competencies_covered: string[];
  questions_asked_count: number;
  duration_minutes: number;
  candidate_level: string;
}

export const QuestionBankPanel = ({
  interviewId,
  jobTitle = '',
  currentCompetency = ''
}: QuestionBankPanelProps) => {
  const [suggestions, setSuggestions] = useState<QuestionSuggestion[]>([]);
  const [allQuestions, setAllQuestions] = useState<QuestionSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompetency, setSelectedCompetency] = useState<string>(currentCompetency || 'all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const { toast } = useToast();

  const fetchSuggestions = async () => {
    try {
      setLoadingSuggestions(true);
      const context: QuestionContext = {
        current_competencies_covered: [],
        questions_asked_count: 0,
        duration_minutes: 0,
        candidate_level: 'mid'
      };

      const response = await api.getQuestionSuggestions(interviewId, context);
      setSuggestions(response.suggested_questions || []);
    } catch (err) {
      console.error('Failed to fetch question suggestions:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const fetchAllQuestions = async () => {
    try {
      setLoadingQuestions(true);
      const response = await api.getAllQuestions(
        selectedCompetency !== 'all' ? selectedCompetency : undefined
      );
      setAllQuestions(response.questions || []);
    } catch (err) {
      console.error('Failed to fetch all questions:', err);
    } finally {
      setLoadingQuestions(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
    fetchAllQuestions();
  }, [interviewId]);

  useEffect(() => {
    fetchAllQuestions();
  }, [selectedCompetency]);

  const handleCopyQuestion = (question: string) => {
    navigator.clipboard.writeText(question);
    toast({
      title: 'Copied!',
      description: 'Question copied to clipboard',
    });
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'hard':
        return 'destructive';
      case 'medium':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const filteredQuestions = allQuestions.filter((q) => {
    const matchesSearch = q.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         q.competency.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDifficulty = selectedDifficulty === 'all' || q.difficulty === selectedDifficulty;
    return matchesSearch && matchesDifficulty;
  });

  const uniqueCompetencies = Array.from(
    new Set([...suggestions, ...allQuestions].map(q => q.competency))
  ).sort();

  const QuestionCard = ({ question, isAISuggested = false }: { question: QuestionSuggestion; isAISuggested?: boolean }) => (
    <div
      className="rounded-lg border p-4 hover:bg-accent/50 transition-colors group"
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {isAISuggested && (
            <Badge className="bg-primary/10 text-primary border-primary/20">
              <Sparkles className="h-3 w-3 mr-1" />
              AI Suggested
            </Badge>
          )}
          <Badge variant={getDifficultyColor(question.difficulty) as any}>
            {question.difficulty}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {question.competency}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => handleCopyQuestion(question.question_text)}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Copy className="h-4 w-4" />
        </Button>
      </div>

      <p className="text-sm font-medium mb-2">
        {question.question_text}
      </p>

      {question.reason && (
        <p className="text-xs text-muted-foreground mb-3">
          💡 {question.reason}
        </p>
      )}

      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
        {question.average_response_time_seconds > 0 && (
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{Math.round(question.average_response_time_seconds / 60)} min avg</span>
          </div>
        )}
        {question.success_rate > 0 && (
          <div className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            <span>{Math.round(question.success_rate * 100)}% success rate</span>
          </div>
        )}
      </div>

      {question.follow_up_questions && question.follow_up_questions.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground mb-2">
            {question.follow_up_questions.length} follow-up questions
          </summary>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            {question.follow_up_questions.map((followUp, idx) => (
              <li key={idx}>{followUp}</li>
            ))}
          </ul>
        </details>
      )}

      {question.evaluation_criteria && question.evaluation_criteria.length > 0 && (
        <details className="text-xs mt-2">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground mb-2">
            Evaluation criteria
          </summary>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
            {question.evaluation_criteria.map((criteria, idx) => (
              <li key={idx}>{criteria}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageCircleQuestion className="h-5 w-5 text-primary" />
            <CardTitle>Question Bank</CardTitle>
          </div>
          <Button
            onClick={() => {
              fetchSuggestions();
              fetchAllQuestions();
            }}
            variant="ghost"
            size="sm"
            disabled={loadingSuggestions || loadingQuestions}
          >
            <RefreshCw className={`h-4 w-4 ${(loadingSuggestions || loadingQuestions) ? 'animate-spin' : ''}`} />
          </Button>
        </div>
        <CardDescription>
          AI-powered question suggestions and curated question library
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="suggested" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="suggested">
              <Sparkles className="h-4 w-4 mr-2" />
              AI Suggested ({suggestions.length})
            </TabsTrigger>
            <TabsTrigger value="browse">
              <Search className="h-4 w-4 mr-2" />
              Browse All ({filteredQuestions.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="suggested" className="space-y-4 mt-4">
            {loadingSuggestions ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : suggestions.length > 0 ? (
              <ScrollArea className="h-[500px] pr-4">
                <div className="space-y-3">
                  {suggestions.map((question, idx) => (
                    <QuestionCard key={idx} question={question} isAISuggested />
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <MessageCircleQuestion className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No AI suggestions available yet</p>
                <p className="text-xs mt-1">Start the interview to get personalized suggestions</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="browse" className="space-y-4 mt-4">
            {/* Filters */}
            <div className="space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search questions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              <div className="flex gap-2">
                <Select value={selectedCompetency} onValueChange={setSelectedCompetency}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Competency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Competencies</SelectItem>
                    {uniqueCompetencies.map((comp) => (
                      <SelectItem key={comp} value={comp}>
                        {comp}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Difficulty" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="hard">Hard</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Questions List */}
            {loadingQuestions ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredQuestions.length > 0 ? (
              <ScrollArea className="h-[500px] pr-4">
                <div className="space-y-3">
                  {filteredQuestions.map((question, idx) => (
                    <QuestionCard key={idx} question={question} />
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Filter className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No questions found</p>
                <p className="text-xs mt-1">Try adjusting your search or filters</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
