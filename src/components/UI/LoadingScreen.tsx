/**
 * ⏳ Loading Screen Component
 * Chain-of-Thought: Engaging loading experience with AI initialization feedback
 * Memory: Show loading progress and system status
 * Forward-Thinking: Extensible for different loading states
 */

import React from 'react'
import { motion } from 'framer-motion'
import { loadingSpinner, neuralPulse } from '@utils/animations'

interface LoadingScreenProps {
  message?: string
  progress?: number
  showProgress?: boolean
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  message = "Loading...",
  progress = 0,
  showProgress = false
}) => {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        {/* AI Brain Animation */}
        <motion.div 
          className="loading-icon"
          variants={neuralPulse}
          animate="animate"
        >
          🧠
        </motion.div>
        
        {/* Spinning Loader */}
        <motion.div
          className="loading-spinner"
          variants={loadingSpinner}
          animate="animate"
        />
        
        {/* Loading Message */}
        <motion.h2
          className="loading-message"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          {message}
        </motion.h2>
        
        {/* Progress Bar */}
        {showProgress && (
          <motion.div
            className="loading-progress"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "100%", opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div 
              className="loading-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </motion.div>
        )}
        
        {/* Loading Steps */}
        <div className="loading-steps">
          <div className="loading-step active">
            <span className="step-icon">🔧</span>
            <span className="step-text">Initializing AI Systems</span>
          </div>
          <div className="loading-step">
            <span className="step-icon">📚</span>
            <span className="step-text">Loading Book Database</span>
          </div>
          <div className="loading-step">
            <span className="step-icon">🎨</span>
            <span className="step-text">Preparing Interface</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoadingScreen
