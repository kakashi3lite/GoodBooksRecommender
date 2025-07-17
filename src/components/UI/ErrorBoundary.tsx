/**
 * 🛡️ Error Boundary Component
 * Chain-of-Thought: Graceful error handling with recovery options
 * Memory: Log errors for debugging and improvement
 * Forward-Thinking: Extensible error reporting and recovery
 */

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Dashboard Error:', error, errorInfo)
    this.setState({ error, errorInfo })
    
    // Forward-Thinking: Send to error reporting service
    // this.reportError(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <h1>🚫 Something went wrong</h1>
            <p>The dashboard encountered an unexpected error.</p>
            
            <details className="error-details">
              <summary>Error Details</summary>
              <pre>{this.state.error?.toString()}</pre>
              <pre>{this.state.errorInfo?.componentStack}</pre>
            </details>
            
            <button 
              onClick={() => window.location.reload()}
              className="error-reload-btn"
            >
              🔄 Reload Dashboard
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
