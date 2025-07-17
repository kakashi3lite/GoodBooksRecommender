/**
 * ⚠️ Error Message Component
 * Chain-of-Thought: Handle errors gracefully with retry functionality
 * Memory: Track error state for recovery options
 * Forward-Thinking: Support for different error types and recovery paths
 */

import React from 'react';
import { motion } from 'framer-motion';

interface ErrorMessageProps {
  message: string;
  details?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  details,
  onRetry,
  onDismiss
}) => {
  /**
   * Chain-of-Thought: Use motion animations for smooth error presentation
   * Time Complexity: O(1) animations with optimized rendering
   */
  return (
    <motion.div
      className="error-message-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <div className="error-icon">
        <svg 
          width="32" 
          height="32" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      
      <div className="error-content">
        <h3 className="error-title">Something went wrong</h3>
        <p className="error-message">{message}</p>
        
        {details && (
          <motion.div 
            className="error-details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <pre>{details}</pre>
          </motion.div>
        )}
        
        <div className="error-actions">
          {onRetry && (
            <motion.button
              className="retry-button"
              onClick={onRetry}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              aria-label="Retry"
            >
              Retry
            </motion.button>
          )}
          
          {onDismiss && (
            <motion.button
              className="dismiss-button"
              onClick={onDismiss}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              aria-label="Dismiss"
            >
              Dismiss
            </motion.button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ErrorMessage;
