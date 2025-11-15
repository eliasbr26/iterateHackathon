import { Target, CheckCircle, AlertTriangle, TrendingUp } from "lucide-react";
import MetricCard from "./MetricCard";

interface MetricsPanelProps {
  metrics: {
    coverageScore: number;
    scriptAdherence: number;
    biasAlerts: number;
    consistency: 'Low' | 'Medium' | 'High';
  };
}

const MetricsPanel = ({ metrics }: MetricsPanelProps) => {
  return (
    <div className="space-y-4">
      <MetricCard
        label="Coverage Score"
        value={`${metrics.coverageScore.toFixed(1)}/10`}
        trend="up"
        trendValue={42}
        icon={Target}
        color="blue"
      />
      
      <MetricCard
        label="Script Adherence"
        value={`${metrics.scriptAdherence}%`}
        trend="up"
        trendValue={37}
        icon={CheckCircle}
        color="green"
      />
      
      <MetricCard
        label="Bias Alerts"
        value={metrics.biasAlerts}
        trend={metrics.biasAlerts > 0 ? 'up' : 'neutral'}
        trendValue={metrics.biasAlerts > 0 ? 100 : 0}
        icon={AlertTriangle}
        color="amber"
      />
      
      <MetricCard
        label="Consistency"
        value={metrics.consistency}
        trend="up"
        trendValue={28}
        icon={TrendingUp}
        color="purple"
      />
    </div>
  );
};

export default MetricsPanel;
