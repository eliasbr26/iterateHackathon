import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Bot,
  Send,
  Trash2,
  Lightbulb,
  BookOpen,
  RefreshCw,
  User,
  Sparkles
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface RAGAssistantPanelProps {
  interviewId: number;
  interviewContext?: {
    job_title?: string;
    candidate_name?: string;
    duration_minutes?: number;
    questions_asked?: number;
    competencies_covered?: string[];
    coverage_gaps?: string[];
  };
}

interface AssistantMessage {
  role: 'user' | 'assistant';
  question?: string;
  answer?: string;
  suggestions?: string[];
  sources?: string[];
  related_questions?: string[];
  confidence?: number;
  timestamp?: string;
}

export const RAGAssistantPanel = ({
  interviewId,
  interviewContext = {}
}: RAGAssistantPanelProps) => {
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [knowledgeStats, setKnowledgeStats] = useState<any>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadHistory();
    loadKnowledgeStats();
  }, [interviewId]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadHistory = async () => {
    try {
      const response = await api.getAssistantHistory(interviewId);
      if (response.messages && response.messages.length > 0) {
        const formattedMessages: AssistantMessage[] = response.messages.flatMap((entry: any) => {
          // Skip entries with missing data
          if (!entry.question || !entry.response) {
            console.warn('Skipping invalid history entry:', entry);
            return [];
          }

          return [
            { role: 'user' as const, question: entry.question, timestamp: entry.timestamp },
            {
              role: 'assistant' as const,
              answer: entry.response.answer || '',
              suggestions: entry.response.suggestions || [],
              sources: entry.response.sources || [],
              related_questions: entry.response.related_questions || [],
              confidence: entry.response.confidence || 0,
              timestamp: entry.timestamp
            }
          ];
        });
        setMessages(formattedMessages);
      }
    } catch (err) {
      console.error('Failed to load assistant history:', err);
      // Continue anyway - don't block the UI
    }
  };

  const loadKnowledgeStats = async () => {
    try {
      const stats = await api.getKnowledgeStats();
      setKnowledgeStats(stats);
    } catch (err) {
      console.error('Failed to load knowledge stats:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userQuestion = inputValue.trim();
    setInputValue('');

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      question: userQuestion,
      timestamp: new Date().toISOString()
    }]);

    setLoading(true);

    try {
      const response = await api.askAssistant(interviewId, userQuestion, interviewContext);

      // Add assistant response - only extract the fields we need with safe defaults
      setMessages(prev => [...prev, {
        role: 'assistant',
        answer: response.answer || 'No answer provided',
        suggestions: response.suggestions || [],
        sources: response.sources || [],
        related_questions: response.related_questions || [],
        confidence: response.confidence || 0,
        timestamp: response.timestamp || new Date().toISOString()
      }]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response';
      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'destructive',
      });

      // Add error message
      setMessages(prev => [...prev, {
        role: 'assistant',
        answer: `Sorry, I encountered an error: ${errorMessage}`,
        confidence: 0,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear the conversation history?')) return;

    try {
      await api.clearAssistantHistory(interviewId);
      setMessages([]);
      toast({
        title: 'History Cleared',
        description: 'Conversation history has been cleared',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to clear history',
        variant: 'destructive',
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="w-full flex flex-col h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <CardTitle>AI Interview Assistant</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {knowledgeStats && (
              <Badge variant="outline" className="text-xs">
                <BookOpen className="h-3 w-3 mr-1" />
                {knowledgeStats.total_documents || 0} docs
              </Badge>
            )}
            <Button
              onClick={handleClearHistory}
              variant="ghost"
              size="sm"
              disabled={messages.length === 0}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <CardDescription>
          Ask questions and get insights from past interviews and company knowledge
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0">
        {/* Messages Area */}
        <ScrollArea
          className="flex-1 pr-4 mb-4"
          ref={scrollRef}
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <Sparkles className="h-12 w-12 text-primary opacity-50 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Ask me anything!</h3>
              <p className="text-sm text-muted-foreground mb-4">
                I can help you with interview questions, candidate evaluation, and best practices
              </p>
              <div className="space-y-2 text-left">
                <p className="text-xs font-semibold">Try asking:</p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  <li>• "What are good follow-up questions for this role?"</li>
                  <li>• "How should I evaluate technical depth?"</li>
                  <li>• "What competencies haven't been covered yet?"</li>
                  <li>• "What questions worked well in similar interviews?"</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary" />
                    </div>
                  )}

                  <div
                    className={`flex-1 max-w-[80%] ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-lg p-3'
                        : 'space-y-3'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <p className="text-sm">{message.question}</p>
                    ) : (
                      <>
                        {/* Assistant Answer */}
                        <div className="rounded-lg border bg-card p-3">
                          <p className="text-sm whitespace-pre-wrap">{message.answer}</p>
                          {message.confidence !== undefined && (
                            <Badge
                              variant="outline"
                              className="mt-2 text-xs"
                            >
                              {Math.round(message.confidence * 100)}% confidence
                            </Badge>
                          )}
                        </div>

                        {/* Suggestions */}
                        {message.suggestions && message.suggestions.length > 0 && (
                          <div className="rounded-lg border bg-accent/50 p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <Lightbulb className="h-3 w-3 text-primary" />
                              <span className="text-xs font-semibold">Suggestions:</span>
                            </div>
                            <ul className="space-y-1">
                              {message.suggestions.map((suggestion, sIdx) => (
                                <li key={sIdx} className="text-xs text-muted-foreground">
                                  • {suggestion}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <details className="text-xs">
                            <summary className="cursor-pointer text-muted-foreground hover:text-foreground mb-2 flex items-center gap-1">
                              <BookOpen className="h-3 w-3" />
                              Sources ({message.sources.length})
                            </summary>
                            <ul className="list-disc list-inside space-y-1 text-muted-foreground ml-2">
                              {message.sources.map((source, sIdx) => (
                                <li key={sIdx}>{source}</li>
                              ))}
                            </ul>
                          </details>
                        )}

                        {/* Related Questions */}
                        {message.related_questions && message.related_questions.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {message.related_questions.map((q, qIdx) => (
                              <Button
                                key={qIdx}
                                variant="outline"
                                size="sm"
                                className="text-xs h-auto py-1 px-2"
                                onClick={() => setInputValue(q)}
                              >
                                {q}
                              </Button>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                  <div className="rounded-lg border bg-card p-3">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Thinking...
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </ScrollArea>

        <Separator className="mb-4" />

        {/* Input Area */}
        <div className="flex gap-2">
          <Input
            placeholder="Ask a question..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={loading || !inputValue.trim()}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
