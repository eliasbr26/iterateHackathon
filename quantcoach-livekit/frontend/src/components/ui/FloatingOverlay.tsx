/**
 * FloatingOverlay - Reusable wrapper for floating UI elements
 * Provides transparent backdrop with hover effect
 */

import { ReactNode } from 'react';

interface FloatingOverlayProps {
  children: ReactNode;
  className?: string;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right' | 'left' | 'right' | 'center';
}

const FloatingOverlay = ({ children, className = '', position = 'top-left' }: FloatingOverlayProps) => {
  const positionClasses = {
    'top-left': 'top-20 left-4', // Moved down from top-4 (16px) to top-20 (80px)
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-20 right-4',
    'left': 'top-1/2 left-4 -translate-y-1/2',
    'right': 'top-20 right-4', // Moved down from top-1/2 (center) to top-20 (80px)
    'center': 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
  };

  return (
    <div
      className={`
        absolute
        ${positionClasses[position]}
        opacity-30
        hover:opacity-90
        transition-opacity
        duration-200
        ease-in-out
        backdrop-blur-sm
        rounded-lg
        pointer-events-auto
        ${className}
      `}
      style={{
        backdropFilter: 'blur(8px)',
        zIndex: 20, // Above video container (z-index: 1) but below video controls (z-index: 50)
      }}
    >
      {children}
    </div>
  );
};

export default FloatingOverlay;
