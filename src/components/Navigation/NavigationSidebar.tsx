// Navigation Sidebar - placeholder
import React from 'react'

const NavigationSidebar: React.FC = () => {
  return (
    <div className="navigation-sidebar">
      <h2>📚 Navigation</h2>
      <nav>
        <a href="/dashboard">Dashboard</a>
        <a href="/notes">Reading Notes</a>
        <a href="/community">Community</a>
        <a href="/analytics">Analytics</a>
      </nav>
    </div>
  )
}

export default NavigationSidebar
