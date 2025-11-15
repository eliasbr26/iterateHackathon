import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { useEffect, useState } from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'amber' | 'purple';
}

const MetricCard = ({ label, value, trend, trendValue, icon: Icon, color }: MetricCardProps) => {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  const colorClasses = {
    blue: 'text-accent-blue border-accent-blue/30 glow-blue',
    green: 'text-accent-green border-accent-green/30 glow-green',
    amber: 'text-accent-amber border-accent-amber/30 glow-amber',
    purple: 'text-accent-purple border-accent-purple/30 glow-purple'
  };

  const bgClasses = {
    blue: 'bg-accent-blue/10',
    green: 'bg-accent-green/10',
    amber: 'bg-accent-amber/10',
    purple: 'bg-accent-purple/10'
  };

  const trendColor = trend === 'up' ? 'text-accent-green' : trend === 'down' ? 'text-accent-red' : 'text-text-tertiary';

  return (
    <div 
      className={`
        relative overflow-hidden rounded-xl border bg-bg-secondary p-5
        transition-all duration-300 hover:-translate-y-1
        ${colorClasses[color]}
      `}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-lg ${bgClasses[color]} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${colorClasses[color].split(' ')[0]}`} />
        </div>
        
        {trend && trendValue !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trendColor}`}>
            {trend === 'up' ? (
              <TrendingUp className="w-3 h-3" />
            ) : trend === 'down' ? (
              <TrendingDown className="w-3 h-3" />
            ) : null}
            <span>{trendValue > 0 ? '+' : ''}{trendValue}%</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-sm text-text-tertiary font-medium">{label}</p>
        <p className="text-3xl font-bold text-text-primary metric-value tabular-nums">
          {displayValue}
        </p>
      </div>

      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-bg-tertiary/30 pointer-events-none" />
    </div>
  );
};

export default MetricCard;
