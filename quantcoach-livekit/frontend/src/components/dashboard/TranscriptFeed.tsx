import { useRef, useEffect } from "react";
import TranscriptMessage from "./TranscriptMessage";
import AudioVisualizer from "./AudioVisualizer";

interface TranscriptMessage {
  id: string;
  text: string;
  speaker: 'interviewer' | 'candidate';
  timestamp: number;
  confidence?: number;
  highlighted?: boolean;
}

interface TranscriptFeedProps {
  messages: TranscriptMessage[];
  isLive: boolean;
  audioActivity?: {
    interviewer: number;
    candidate: number;
  };
}

const TranscriptFeed = ({ messages, isLive, audioActivity }: TranscriptFeedProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas quand un nouveau message arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border-subtle bg-bg-secondary px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-text-primary">Live Transcript</h2>
          {isLive && (
            <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-accent-green/20">
              <div className="w-2 h-2 rounded-full bg-accent-green pulse-dot" />
              <span className="text-xs font-medium text-accent-green">Recording</span>
            </div>
          )}
        </div>

        {audioActivity && (audioActivity.interviewer > 0.1 || audioActivity.candidate > 0.1) && (
          <div className="flex items-center gap-4">
            {audioActivity.interviewer > 0.1 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-tertiary">Interviewer</span>
                <AudioVisualizer volume={audioActivity.interviewer} speaker="interviewer" />
              </div>
            )}
            {audioActivity.candidate > 0.1 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-tertiary">Candidate</span>
                <AudioVisualizer volume={audioActivity.candidate} speaker="candidate" />
              </div>
            )}
          </div>
        )}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-2 scroll-smooth min-h-0"
      >
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center space-y-2">
              <div className="w-16 h-16 rounded-full bg-bg-tertiary mx-auto flex items-center justify-center mb-4">
                <span className="text-2xl">🎤</span>
              </div>
              <p className="text-text-tertiary text-sm">Waiting for conversation to start...</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <TranscriptMessage key={message.id} {...message} />
          ))
        )}
      </div>
    </div>
  );
};

export default TranscriptFeed;
