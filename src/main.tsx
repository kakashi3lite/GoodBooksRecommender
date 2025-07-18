/**
 * 🚀 Main Application Entry Point (Senior Engineer Fix)
 * Production-ready initialization with comprehensive architecture
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter as Router } from 'react-router-dom'
import App from './App'
import { store } from './stores/store'

// Import CSS files with proper paths for comprehensive styling
import '../dashboard/css/design-system.css'
import '../dashboard/css/futuristic-dashboard.css'
import '../dashboard/css/book-card.css'
import '../dashboard/css/brightness-control.css'
import '../dashboard/css/theme-toggle.css'
import '../dashboard/css/ai-recommendations.css'
import '../dashboard/css/react-components.css'
import '../dashboard/css/dashboard-analytics.css'

// Initialize the application with full Redux and routing
const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement)

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <Router>
        <App />
      </Router>
    </Provider>
  </React.StrictMode>
)
