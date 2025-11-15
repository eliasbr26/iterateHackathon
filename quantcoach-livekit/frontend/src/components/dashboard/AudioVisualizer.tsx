interface AudioVisualizerProps {
  volume: number; // 0-1
  speaker: 'interviewer' | 'candidate';
}

const AudioVisualizer = ({ volume, speaker }: AudioVisualizerProps) => {
  const bars = [0.3, 0.5, 1, 0.7, 0.4];
  const color = speaker === 'interviewer' ? 'bg-accent-blue' : 'bg-text-tertiary';

  return (
    <div className="flex items-end gap-1 h-6">
      {bars.map((multiplier, i) => (
        <div
          key={i}
          className={`w-1 rounded-full ${color} transition-all duration-150`}
          style={{
            height: `${Math.max(4, volume * multiplier * 100)}%`,
            opacity: volume > 0.1 ? 1 : 0.3
          }}
        />
      ))}
    </div>
  );
};

export default AudioVisualizer;
