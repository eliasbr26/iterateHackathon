import { useState } from "react";
import AlertCard from "./AlertCard";
import { Sparkles } from "lucide-react";

interface Alert {
  id: string;
  type: 'bias' | 'deviation' | 'suggestion';
  severity: 'low' | 'medium' | 'high';
  title: string;
  message: string;
  suggestion?: string;
  timestamp: number;
  dismissed?: boolean;
}

interface AlertPanelProps {
  alerts: Alert[];
  onDismissAlert: (id: string) => void;
}

const AlertPanel = ({ alerts, onDismissAlert }: AlertPanelProps) => {
  const activeAlerts = alerts.filter(a => !a.dismissed).slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-text-primary mb-3">Alerts & Signals</h2>
        <div className="space-y-3">
          {activeAlerts.length === 0 ? (
            <div className="rounded-xl border border-border-subtle bg-bg-secondary p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-accent-green/20 mx-auto flex items-center justify-center mb-3">
                <span className="text-2xl">✓</span>
              </div>
              <p className="text-sm text-text-secondary">All clear! No alerts at the moment.</p>
            </div>
          ) : (
            activeAlerts.map((alert) => (
              <AlertCard
                key={alert.id}
                {...alert}
                onDismiss={onDismissAlert}
              />
            ))
          )}
        </div>
      </div>

      <div className="rounded-xl border border-accent-purple/30 bg-accent-purple/10 p-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-purple/20 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4 text-accent-purple" />
          </div>
          <div className="flex-1 space-y-2">
            <h3 className="text-sm font-semibold text-text-primary">AI Coaching</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Consider asking follow-up questions about the candidate's experience with risk management in volatile markets.
            </p>
            <p className="text-xs text-text-tertiary">Real-time suggestion</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertPanel;
