import { X, AlertTriangle, Info, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AlertCardProps {
  id: string;
  type: 'bias' | 'deviation' | 'suggestion';
  severity: 'low' | 'medium' | 'high';
  title: string;
  message: string;
  suggestion?: string;
  timestamp: number;
  onDismiss: (id: string) => void;
}

const AlertCard = ({ id, type, severity, title, message, suggestion, timestamp, onDismiss }: AlertCardProps) => {
  const severityConfig = {
    high: { color: 'border-accent-red', bg: 'bg-accent-red/10', icon: AlertTriangle },
    medium: { color: 'border-accent-amber', bg: 'bg-accent-amber/10', icon: Info },
    low: { color: 'border-accent-blue', bg: 'bg-accent-blue/10', icon: Lightbulb }
  };

  const config = severityConfig[severity];
  const Icon = config.icon;

  const formatTime = (ts: number) => {
    const now = Date.now();
    const diff = now - ts;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  return (
    <div 
      className={`
        slide-in-right rounded-xl border-l-4 ${config.color} ${config.bg}
        bg-bg-secondary p-4 space-y-3 relative
        hover:scale-[1.02] transition-transform duration-200
      `}
    >
      <button
        onClick={() => onDismiss(id)}
        className="absolute top-3 right-3 text-text-tertiary hover:text-text-primary transition-colors"
      >
        <X className="w-4 h-4" />
      </button>

      <div className="flex items-start gap-3 pr-6">
        <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${config.color.replace('border-', 'text-')}`} />
        <div className="flex-1 space-y-1">
          <h3 className="font-semibold text-sm text-text-primary">{title}</h3>
          <p className="text-xs text-text-secondary leading-relaxed">{message}</p>
          <p className="text-xs text-text-tertiary">{formatTime(timestamp)}</p>
        </div>
      </div>

      {suggestion && (
        <div className="pl-8">
          <Button
            size="sm"
            variant="outline"
            className="text-xs h-7 border-border-default hover:bg-bg-elevated"
          >
            Apply Suggestion
          </Button>
        </div>
      )}
    </div>
  );
};

export default AlertCard;
