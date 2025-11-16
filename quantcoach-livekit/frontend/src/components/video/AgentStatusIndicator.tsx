/**
 * AgentStatusIndicator - Shows active agent status with green pulsing dot
 * Displays agent name on hover
 */

import { useState } from 'react';

interface AgentStatusIndicatorProps {
  isActive: boolean;
  agentName?: string;
  className?: string;
}

const AgentStatusIndicator = ({
  isActive,
  agentName = 'AI Interview Agent',
  className = '',
}: AgentStatusIndicatorProps) => {
  const [isHovered, setIsHovered] = useState(false);

  if (!isActive) return null;

  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative flex items-center gap-2 bg-black/40 backdrop-blur-md px-3 py-2 rounded-full transition-all duration-200">
        {/* Pulsing green dot */}
        <div className="relative flex items-center justify-center">
          <div className="absolute w-3 h-3 bg-green-500 rounded-full animate-ping opacity-75" />
          <div className="relative w-3 h-3 bg-green-500 rounded-full" />
        </div>

        {/* Agent name (shows on hover) */}
        <div
          className={`text-white text-sm font-medium whitespace-nowrap transition-all duration-200 overflow-hidden ${
            isHovered ? 'max-w-xs opacity-100' : 'max-w-0 opacity-0'
          }`}
        >
          {agentName}
        </div>
      </div>
    </div>
  );
};

export default AgentStatusIndicator;
