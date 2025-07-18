/**
 * ⏳ Loading Screen Component
 * Enhanced loading experience with modern animations
 */

import { motion } from 'framer-motion'
import React from 'react'

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
  const pulseVariants = {
    animate: {
      scale: [1, 1.1, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: "linear"
      }
    }
  }

  return (
    <div className="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg z-50 flex items-center justify-center">
      <div className="text-center p-8">
        {/* AI Brain Animation */}
        <motion.div 
          className="text-6xl mb-4"
          variants={pulseVariants}
          animate="animate"
        >
          🧠
        </motion.div>
        
        {/* Spinning Loader */}
        <motion.div
          className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-6"
          variants={spinnerVariants}
          animate="animate"
        />
        
        {/* Loading Message */}
        <motion.h2
          className="text-xl font-semibold text-gray-900 dark:text-white mb-4"
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
        
        {/* Loading Tips */}
        <motion.p
          className="text-gray-600 dark:text-gray-400 text-sm mt-4 max-w-md"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          Initializing AI systems and preparing your personalized reading experience...
        </motion.p>
      </div>
    </div>
  )
}

export default LoadingScreen
