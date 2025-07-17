/**
 * 🚀 Main Application Entry Point (Senior Engineer Fix)
 * Simplified initialization for immediate dashboard functionality
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import SimpleApp from './SimpleApp'

// Initialize the application
const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)

root.render(
  <React.StrictMode>
    <SimpleApp />
  </React.StrictMode>
)
