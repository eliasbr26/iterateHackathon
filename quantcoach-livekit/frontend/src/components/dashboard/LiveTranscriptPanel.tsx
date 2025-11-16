import { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mic, User } from 'lucide-react';

interface TranscriptMessage {
  timestamp: string;
  speaker: string;
  text: string;
  is_final?: boolean;
}

interface LiveTranscriptPanelProps {
  messages: TranscriptMessage[];
  isLive: boolean;
  className?: string;
}

const LiveTranscriptPanel = ({ messages, isLive, className = '' }: LiveTranscriptPanelProps) => {
  // Group messages by conversation turns for better readability
  const groupedMessages = useMemo(() => {
    const groups: { speaker: string; messages: TranscriptMessage[]; timestamp: string }[] = [];
    let currentGroup: { speaker: string; messages: TranscriptMessage[]; timestamp: string } | null = null;

    messages.forEach((msg) => {
      if (!currentGroup || currentGroup.speaker !== msg.speaker) {
        // Start new group
        currentGroup = {
          speaker: msg.speaker,
          messages: [msg],
          timestamp: msg.timestamp,
        };
        groups.push(currentGroup);
      } else {
        // Add to current group
        currentGroup.messages.push(msg);
      }
    });

    return groups;
  }, [messages]);

  const getSpeakerColor = (speaker: string) => {
    if (speaker === 'recruiter' || speaker === 'interviewer') {
      return 'bg-blue-500/10 border-blue-500/20 text-blue-700';
    }
    return 'bg-green-500/10 border-green-500/20 text-green-700';
  };

  const getSpeakerLabel = (speaker: string) => {
    if (speaker === 'recruiter' || speaker === 'interviewer') {
      return 'Interviewer';
    }
    return 'Candidate';
  };

  const getSpeakerIcon = (speaker: string) => {
    if (speaker === 'recruiter' || speaker === 'interviewer') {
      return <User className="h-4 w-4" />;
    }
    return <Mic className="h-4 w-4" />;
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Live Transcription</CardTitle>
            <CardDescription className="text-xs">
              Real-time conversation transcript with speaker identification
            </CardDescription>
          </div>
          {isLive && (
            <Badge variant="default" className="animate-pulse">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-white rounded-full animate-ping absolute" />
                <span className="w-2 h-2 bg-white rounded-full" />
                Live
              </span>
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {groupedMessages.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-center">
            <div className="space-y-2">
              <Mic className="h-12 w-12 text-muted-foreground mx-auto opacity-50" />
              <p className="text-sm text-muted-foreground">
                Waiting for audio input...
              </p>
              <p className="text-xs text-muted-foreground">
                Transcripts will appear here once participants start speaking
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {groupedMessages.map((group, groupIdx) => {
              const colorClass = getSpeakerColor(group.speaker);
              const label = getSpeakerLabel(group.speaker);
              const icon = getSpeakerIcon(group.speaker);

              return (
                <div
                  key={`group-${groupIdx}`}
                  className={`border rounded-lg p-3 ${colorClass} transition-all duration-200`}
                >
                  {/* Speaker Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex items-center gap-1.5 font-medium text-sm">
                      {icon}
                      <span>{label}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(group.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Messages */}
                  <div className="space-y-1.5">
                    {group.messages.map((msg, msgIdx) => (
                      <div
                        key={`msg-${groupIdx}-${msgIdx}`}
                        className="text-sm leading-relaxed"
                      >
                        {msg.text}
                      </div>
                    ))}
                  </div>

                  {/* Message Count (if multiple messages in group) */}
                  {group.messages.length > 1 && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      {group.messages.length} segments
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Stats Footer */}
        {messages.length > 0 && (
          <div className="mt-4 pt-3 border-t flex items-center justify-between text-xs text-muted-foreground">
            <span>Total messages: {messages.length}</span>
            <span>
              Speakers:{' '}
              {Array.from(new Set(messages.map((m) => getSpeakerLabel(m.speaker)))).join(', ')}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default LiveTranscriptPanel;
