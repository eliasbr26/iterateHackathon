import { Play, Pause, Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DashboardHeaderProps {
  sessionId: string;
  sessionStatus: 'initializing' | 'active' | 'paused' | 'completed';
  duration: number;
  onPause: () => void;
  onEnd: () => void;
  demoMode: boolean;
  onToggleDemo: () => void;
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const DashboardHeader = ({
  sessionId,
  sessionStatus,
  duration,
  onPause,
  onEnd,
  demoMode,
  onToggleDemo
}: DashboardHeaderProps) => {
  const statusConfig = {
    initializing: { color: 'bg-accent-amber', label: 'Initializing' },
    active: { color: 'bg-accent-green', label: 'Live' },
    paused: { color: 'bg-accent-amber', label: 'Paused' },
    completed: { color: 'bg-text-tertiary', label: 'Completed' }
  };

  const status = statusConfig[sessionStatus];

  return (
    <header className="h-16 border-b border-border-subtle bg-bg-secondary/80 backdrop-blur-sm flex items-center justify-between px-6">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-blue/20 flex items-center justify-center">
            <span className="text-accent-blue font-bold text-sm">AI</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-text-primary">Interview Session</h1>
            <p className="text-xs text-text-tertiary">#{sessionId}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bg-tertiary border border-border-subtle">
          <div className={`w-2 h-2 rounded-full ${status.color} ${sessionStatus === 'active' ? 'pulse-dot' : ''}`} />
          <span className="text-xs font-medium text-text-secondary">{status.label}</span>
        </div>

        <div className="text-2xl font-bold text-text-primary tabular-nums">
          {formatDuration(duration)}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={demoMode}
            onChange={onToggleDemo}
            className="rounded border-border-default"
          />
          Demo Mode
        </label>

        {sessionStatus === 'active' && (
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={onPause}
              className="gap-2 border-border-default hover:bg-bg-elevated"
            >
              <Pause className="w-4 h-4" />
              Pause
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={onEnd}
              className="gap-2"
            >
              <Square className="w-4 h-4" />
              End
            </Button>
          </>
        )}

        {sessionStatus === 'paused' && (
          <Button
            variant="default"
            size="sm"
            onClick={onPause}
            className="gap-2 bg-accent-green hover:bg-accent-green/90"
          >
            <Play className="w-4 h-4" />
            Resume
          </Button>
        )}
      </div>
    </header>
  );
};

export default DashboardHeader;
