import { useEffect, useRef } from "react";

interface TranscriptMessageProps {
  text: string;
  speaker: 'interviewer' | 'candidate';
  timestamp: number;
  confidence?: number;
  highlighted?: boolean;
}

const TranscriptMessage = ({ text, speaker, timestamp, confidence, highlighted }: TranscriptMessageProps) => {
  const messageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messageRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, []);

  const formatTime = (ts: number) => {
    const date = new Date(ts);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const isInterviewer = speaker === 'interviewer';

  return (
    <div 
      ref={messageRef}
      className={`flex ${isInterviewer ? 'justify-start' : 'justify-end'} mb-4 animate-fade-in`}
    >
      <div className={`max-w-[80%] ${isInterviewer ? 'items-start' : 'items-end'} flex flex-col gap-1`}>
        <div className="flex items-center gap-2 px-1">
          <span className="text-xs text-text-tertiary font-medium">
            {isInterviewer ? '🎤 Interviewer' : '👤 Candidate'}
          </span>
          <span className="text-xs text-text-tertiary">
            {formatTime(timestamp)}
          </span>
          {confidence && (
            <span className="text-xs text-text-tertiary">
              ({Math.round(confidence * 100)}%)
            </span>
          )}
        </div>
        
        <div 
          className={`
            rounded-2xl px-4 py-3 
            ${isInterviewer 
              ? 'bg-interviewer-msg/20 border border-accent-blue/30' 
              : 'bg-candidate-msg/20 border border-border-default'
            }
            ${highlighted ? 'ring-2 ring-accent-amber animate-pulse' : ''}
          `}
        >
          <p className="text-sm text-text-primary leading-relaxed">
            {text}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TranscriptMessage;
