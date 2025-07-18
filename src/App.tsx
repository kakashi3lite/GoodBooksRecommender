/**
 * 🚀 Futuristic Dashboard - Main App Component (Senior Engineer Fix)
 * Production-ready architecture with comprehensive AI integration
 */

import { AnimatePresence, motion } from 'framer-motion'
import React, { Suspense, lazy, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { Route, Routes } from 'react-router-dom'

// Redux hooks and actions
import { useAppDispatch, useAppSelector } from './hooks/redux'
import {
    initializeDashboard,
    togglePerformancePanel,
    trackPerformanceMetrics
} from './stores/dashboard/dashboardSlice'

// Core components
import AIAssistant from './components/AI/AIAssistant'
import { DashboardAnalytics } from './components/Analytics/DashboardAnalytics'
import { PerformancePanel } from './components/Analytics/PerformancePanel'
import NavigationSidebar from './components/Navigation/NavigationSidebar'
import ErrorBoundary from './components/UI/ErrorBoundary'
import LoadingScreen from './components/UI/LoadingScreen'

// Lazy load components for performance
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'))
const ReadingNotes = lazy(() => import('./components/Features/ReadingNotes'))
const CommunityHub = lazy(() => import('./components/Features/CommunityHub'))
const AdvancedAnalytics = lazy(() => import('./components/Features/AdvancedAnalytics'))
const NewsDashboard = lazy(() => import('./components/News/NewsDashboard'))

// Animation variants
const fadeInOut = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
}

const slideInFromLeft = {
  initial: { x: -300, opacity: 0 },
  animate: { x: 0, opacity: 1 },
  exit: { x: -300, opacity: 0 }
}

/**
 * App Shell Component
 * Memory: Remembers layout preferences and user state
 */
const AppShell: React.FC = () => {
  const dispatch = useAppDispatch()
  const { 
    isInitialized, 
    theme, 
    aiMode, 
    layout, 
    performanceMode, 
    performancePanelVisible 
  } = useAppSelector(state => state.dashboard)
  
  // Chain-of-Thought: Initialize AI systems and performance tracking on app mount
  useEffect(() => {
    // Initialize dashboard with AI components
    dispatch(initializeDashboard())
    
    // Set up performance tracking interval based on performance mode
    const trackingInterval = performanceMode === 'battery' ? 60000 : 30000 // 1 minute or 30 seconds
    
    const intervalId = setInterval(() => {
      dispatch(trackPerformanceMetrics())
    }, trackingInterval)
    
    return () => clearInterval(intervalId)
  }, [dispatch, performanceMode])
  
  // Handle keyboard shortcut for performance panel
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Shift + P to toggle performance panel
      if (e.shiftKey && e.key === 'P') {
        dispatch(togglePerformancePanel())
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [dispatch])

  if (!isInitialized) {
    return <LoadingScreen message="Initializing AI systems..." />
  }

  return (
    <div className={`app-shell theme-${theme} ai-mode-${aiMode} layout-${layout} performance-${performanceMode}`}>
      {/* Neural network background animation */}
      <div className="neural-background" />
      
      <AnimatePresence mode="wait">
        <motion.div
          className="app-container"
          variants={fadeInOut}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {/* Navigation Sidebar */}
          <motion.aside
            className="navigation-sidebar"
            variants={slideInFromLeft}
            initial="initial"
            animate="animate"
          >
            <NavigationSidebar />
            
            {/* Show compact analytics in sidebar */}
            <div className="sidebar-analytics">
              <DashboardAnalytics compact={true} />
            </div>
          </motion.aside>

          {/* Main Content Area */}
          <main className="main-content">
            <Suspense fallback={<LoadingScreen message="Loading component..." />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/news" element={<NewsDashboard />} />
                <Route path="/notes" element={<ReadingNotes />} />
                <Route path="/community" element={<CommunityHub />} />
                <Route path="/analytics" element={<AdvancedAnalytics />} />
              </Routes>
            </Suspense>
          </main>

          {/* AI Assistant Overlay */}
          <AIAssistant />
          
          {/* Enhanced Performance Panel */}
          <PerformancePanel />
        </motion.div>
      </AnimatePresence>

      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: 'futuristic-toast',
          style: {
            background: 'var(--glass-bg)',
            color: 'var(--text-primary)',
            backdropFilter: 'blur(20px)',
            border: '1px solid var(--glass-border)'
          }
        }}
      />
      
      {/* Conditionally render performance panel */}
      {performancePanelVisible && <PerformancePanel />}
    </div>
  )
}

/**
 * Main App Component with Error Boundary
 * Forward-Thinking: Ready for additional providers (auth, analytics, etc.)
 */
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AppShell />
    </ErrorBoundary>
  )
}

export default App
