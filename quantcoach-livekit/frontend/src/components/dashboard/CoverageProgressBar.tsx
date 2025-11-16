interface CoverageProgressBarProps {
  coverage: {
    technical: number;
    behavioral: number;
    market_knowledge: number;
  };
}

const CoverageProgressBar = ({ coverage }: CoverageProgressBarProps) => {
  const segments = [
    { 
      label: 'Technical', 
      value: coverage.technical, 
      color: 'bg-accent-blue',
      gradient: 'from-accent-blue/80 to-accent-blue',
      questions: ['Black-Scholes', 'Option Greeks', 'Risk Models']
    },
    { 
      label: 'Behavioral', 
      value: coverage.behavioral, 
      color: 'bg-accent-purple',
      gradient: 'from-accent-purple/80 to-accent-purple',
      questions: ['Team dynamics', 'Pressure handling', 'Leadership']
    },
    { 
      label: 'Market Knowledge', 
      value: coverage.market_knowledge, 
      color: 'bg-accent-green',
      gradient: 'from-accent-green/80 to-accent-green',
      questions: ['Market volatility', 'Fed policy', 'Trading strategies']
    }
  ];

  return (
    <div className="border-t border-border-subtle bg-bg-secondary px-6 py-4">
      <h3 className="text-xs font-semibold text-text-tertiary mb-3 uppercase tracking-wider">
        Interview Coverage
      </h3>
      <div className="grid grid-cols-3 gap-4">
        {segments.map((segment) => (
          <div key={segment.label} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-text-secondary">{segment.label}</span>
              <span className="text-xs font-bold text-text-primary tabular-nums">
                {Math.round(segment.value * 100)}%
              </span>
            </div>
            
            <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div 
                className={`h-full bg-gradient-to-r ${segment.gradient} transition-all duration-700 ease-out`}
                style={{ width: `${segment.value * 100}%` }}
              />
            </div>

            <div className="flex flex-wrap gap-1">
              {segment.questions.map((q) => (
                <span 
                  key={q}
                  className="text-xs px-2 py-0.5 rounded-full bg-bg-tertiary text-text-tertiary"
                >
                  {q}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CoverageProgressBar;
