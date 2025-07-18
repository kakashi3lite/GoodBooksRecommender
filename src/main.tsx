/**
 * 🚀 Main Application Entry Point (Production Ready)
 * Enhanced initialization with comprehensive styling and routing
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter as Router } from 'react-router-dom'
import App from './App'
import { store } from './stores/store'

// Import enhanced CSS files for modern UI
import '../dashboard/css/ai-recommendations.css'
import '../dashboard/css/book-card.css'
import '../dashboard/css/brightness-control.css'
import '../dashboard/css/dashboard-analytics.css'
import '../dashboard/css/design-system.css'
import '../dashboard/css/futuristic-dashboard.css'
import '../dashboard/css/react-components.css'
import '../dashboard/css/theme-toggle.css'
import './styles/enhanced-dashboard.css'

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
