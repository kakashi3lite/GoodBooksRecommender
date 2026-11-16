/**
 * 🚀 Futuristic Dashboard - Main App Component (Senior Engineer Fix)
 * Production-ready architecture with comprehensive AI integration
 */

import { AnimatePresence, motion } from 'framer-motion'
import { Menu, Moon, Sun, X } from 'lucide-react'
import React, { Suspense, lazy, useEffect, useMemo } from 'react'
import { Toaster } from 'react-hot-toast'
import { Route, Routes, useLocation } from 'react-router-dom'

// Redux hooks and actions
import { useAppDispatch, useAppSelector } from './hooks/redux'
import {
  closeMobileNav,
  initializeDashboard,
  setTheme,
  toggleMobileNav,
  togglePerformancePanel,
  trackPerformanceMetrics
} from './stores/dashboard/dashboardSlice'
import { syncAccountToServer } from './stores/user/userSlice'

// Core components
import AIAssistant from './components/AI/AIAssistant'
import { CompactAnalytics } from './components/Analytics/CompactAnalytics'
import { PerformancePanel } from './components/Analytics/PerformancePanel'
import MobileBottomNav from './components/Navigation/MobileBottomNav'
import NavigationSidebar from './components/Navigation/NavigationSidebar'
import ErrorBoundary from './components/UI/ErrorBoundary'
import CommandPalette from './components/UI/CommandPalette'
import LoadingScreen from './components/UI/LoadingScreen'

// Lazy load components for performance
const Dashboard = lazy(() => import('./components/Dashboard/Dashboard'))
const ReadingNotes = lazy(() => import('./components/Features/ReadingNotes'))
const CommunityHub = lazy(() => import('./components/Features/CommunityHub'))
const AdvancedAnalytics = lazy(() => import('./components/Features/AdvancedAnalytics'))
const NewsDashboard = lazy(() => import('./components/News/NewsDashboard'))
const Discover = lazy(() => import('./components/Features/Discover'))
const CurrentlyReading = lazy(() => import('./components/Features/CurrentlyReading'))
const Wishlist = lazy(() => import('./components/Features/Wishlist'))
const BookDetail = lazy(() => import('./components/Features/BookDetail'))
const OnboardingFlow = lazy(() => import('./components/Onboarding/OnboardingFlow'))

// Animation variants
const fadeInOut = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
}

/**
 * App Shell Component
 * Memory: Remembers layout preferences and user state
 */
const AppShell: React.FC = () => {
  const dispatch = useAppDispatch()
  const location = useLocation()
  const {
    isInitialized,
    theme,
    aiMode,
    layout,
    performanceMode,
    performancePanelVisible,
    sidebarCollapsed,
    mobileNavOpen
  } = useAppSelector(state => state.dashboard)

  // Chain-of-Thought: Close the mobile drawer on navigation so the reader
  // lands on the new page with a clear view.
  useEffect(() => {
    if (mobileNavOpen) dispatch(closeMobileNav())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

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

  // Chain-of-Thought: Sync Redux theme to the DOM so Tailwind `dark:` variants
  // and the design-system `[data-theme]` selectors both respond to the toggle.
  // `data-theme` receives the RESOLVED theme ('light' | 'dark') — the design
  // tokens only define values for those two, so writing 'auto' left them
  // undefined and the page background transparent.
  useEffect(() => {
    const root = document.documentElement
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    const isDark = theme === 'dark' || (theme === 'auto' && prefersDark)
    root.classList.toggle('dark', isDark)
    root.dataset.theme = isDark ? 'dark' : 'light'
    root.dataset.themePreference = theme
  }, [theme])

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

  // Chain-of-Thought: Gate the app on account creation + taste onboarding so
  // every user gets personalized recommendations from their first session.
  // A sessionStorage fallback lets readers who completed onboarding (or chose
  // the guest path) in a storage-restricted browser (in-app, private mode)
  // get straight in instead of being blocked by the gate on every reload.
  const isAuthenticated = useAppSelector((state) => state.user.isAuthenticated)
  const hasCompletedOnboarding = useAppSelector(
    (state) => state.user.hasCompletedOnboarding
  )
  const onboardedThisSession = useMemo(() => {
    try {
      return sessionStorage.getItem('goodbooks_onboarded') === '1'
    } catch {
      return false
    }
  }, [])
  const showOnboarding =
    (!isAuthenticated || !hasCompletedOnboarding) && !onboardedThisSession

  // Chain-of-Thought: When a returning user is restored from localStorage, push
  // their account to the database (best-effort) so it stays in sync.
  useEffect(() => {
    if (isAuthenticated && hasCompletedOnboarding) {
      dispatch(syncAccountToServer())
    }
  }, [dispatch, isAuthenticated, hasCompletedOnboarding])

  if (!isInitialized) {
    return <LoadingScreen message="Initializing AI systems..." />
  }

  return (
    <div className={`app-shell theme-${theme} ai-mode-${aiMode} layout-${layout} performance-${performanceMode}${sidebarCollapsed ? ' layout-collapsed' : ''}${mobileNavOpen ? ' mobile-open' : ''}`}>
      {/* Neural network background animation */}
      <div className="neural-background" />

      {/* Mobile top bar — hamburger + brand + theme toggle (visible < 768px) */}
      <header className="mobile-topbar">
        <button
          type="button"
          className="mobile-menu-button"
          onClick={() => dispatch(toggleMobileNav())}
          aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileNavOpen}
        >
          {mobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
        <span className="mobile-topbar-brand">📚 GoodBooks</span>
        <button
          type="button"
          className="mobile-menu-button ml-auto"
          onClick={() => dispatch(setTheme(theme === 'dark' ? 'light' : 'dark'))}
          aria-label="Toggle dark mode"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </header>

      {/* Mobile drawer backdrop (closes the menu on tap outside) */}
      {mobileNavOpen && (
        <button
          type="button"
          className="mobile-backdrop"
          aria-label="Close menu"
          onClick={() => dispatch(closeMobileNav())}
        />
      )}

      {/* Mobile bottom tab bar — primary thumb-zone nav (< 768px) */}
      <MobileBottomNav />

      <AnimatePresence mode="wait">
        <motion.div
          className="app-container"
          variants={fadeInOut}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {/* Navigation Sidebar (CSS handles the mobile drawer transition) */}
          <aside className="navigation-sidebar">
            <NavigationSidebar />

            {/* Show compact analytics in sidebar */}
            <div className="sidebar-analytics">
              <CompactAnalytics />
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="main-content">
            <Suspense fallback={<LoadingScreen message="Loading component..." />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/discover" element={<Discover />} />
                <Route path="/reading" element={<CurrentlyReading />} />
                <Route path="/wishlist" element={<Wishlist />} />
                <Route path="/book/:id" element={<BookDetail />} />
                <Route path="/news" element={<NewsDashboard />} />
                <Route path="/notes" element={<ReadingNotes />} />
                <Route path="/community" element={<CommunityHub />} />
                <Route path="/analytics" element={<AdvancedAnalytics />} />
              </Routes>
            </Suspense>
          </main>

          {/* AI Assistant Overlay */}
          <AIAssistant />
        </motion.div>
      </AnimatePresence>

      {/* ⌘K command palette — actions + live book search (premium surface) */}
      <CommandPalette />

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

      {/* Performance panel (conditionally rendered via Redux state) */}
      {performancePanelVisible && <PerformancePanel />}

      {/* Onboarding gate — first-run account creation + taste quiz */}
      {showOnboarding && (
        <Suspense fallback={null}>
          <OnboardingFlow />
        </Suspense>
      )}
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
