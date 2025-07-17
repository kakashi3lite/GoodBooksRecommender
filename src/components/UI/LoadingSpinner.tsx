/**
 * ⏳ Loading Spinner Component
 * Chain-of-Thought: Provide visual feedback during async operations
 * Memory: Track loading state for smooth transitions
 * Forward-Thinking: Support for different loading styles
 */

import React from 'react';
import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  color?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'medium',
  color = 'var(--ai-primary, #00D4FF)'
}) => {
  // Determine dimensions based on size
  const dimensions = {
    small: { width: 24, height: 24, strokeWidth: 2 },
    medium: { width: 40, height: 40, strokeWidth: 3 },
    large: { width: 60, height: 60, strokeWidth: 4 }
  }[size];
  
  /**
   * Chain-of-Thought: Use SVG for GPU-accelerated animations
   * Time Complexity: O(1) animation that won't block the main thread
   */
  return (
    <div className="loading-spinner-container">
      <motion.svg
        className="loading-spinner"
        width={dimensions.width}
        height={dimensions.height}
        viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
        initial={{ rotate: 0 }}
        animate={{ rotate: 360 }}
        transition={{ 
          duration: 1.5, 
          ease: "linear", 
          repeat: Infinity,
          repeatType: "loop" 
        }}
        aria-label="Loading"
      >
        <circle
          cx={dimensions.width / 2}
          cy={dimensions.height / 2}
          r={(dimensions.width / 2) - dimensions.strokeWidth}
          strokeWidth={dimensions.strokeWidth}
          stroke={color}
          fill="none"
          strokeDasharray={(dimensions.width - dimensions.strokeWidth) * Math.PI}
          strokeDashoffset={(dimensions.width - dimensions.strokeWidth) * Math.PI * 0.75}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
      </motion.svg>
      
      {message && (
        <motion.p 
          className="loading-message"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {message}
        </motion.p>
      )}
    </div>
  );
};

export default LoadingSpinner;
