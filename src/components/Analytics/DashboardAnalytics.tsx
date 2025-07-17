/**
 * 📊 Dashboard Analytics Component
 * Chain-of-Thought: Display performance metrics and reading analytics with O(1) rendering complexity
 * Memory: Track and display metrics trends over time
 * Forward-Thinking: Support for performance optimizations and user-specific analytics
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid
} from 'recharts';
import { useAppSelector, useAppDispatch } from '../../hooks/redux';
import { trackPerformanceMetrics } from '../../stores/dashboard/dashboardSlice';
import { selectPerformanceMetrics, selectPerformanceMode } from '../../stores/dashboard/dashboardSlice';
import { selectBookCache } from '../../stores/books/booksSlice';

interface DashboardAnalyticsProps {
  userId?: string;
  compact?: boolean;
}

export const DashboardAnalytics: React.FC<DashboardAnalyticsProps> = ({
  compact = false
}) => {
  const dispatch = useAppDispatch();
  
  // Get state from Redux
  const performanceMetrics = useAppSelector(selectPerformanceMetrics);
  const performanceMode = useAppSelector(selectPerformanceMode);
  const bookCache = useAppSelector(selectBookCache);
  
  // Local state for reading analytics
  const [readingStats, setReadingStats] = useState({
    booksStarted: 0,
    booksCompleted: 0,
    totalPages: 0,
    readingStreak: 0,
    topGenres: [] as {name: string, count: number}[],
    readingHistory: [] as {date: string, pages: number}[],
    averageRating: 0
  });
  
  /**
   * Chain-of-Thought: Track performance metrics periodically
   * Time Complexity: O(1) operation performed at regular intervals
   */
  useEffect(() => {
    // Fetch performance metrics on mount
    dispatch(trackPerformanceMetrics());
    
    // Set up interval for regular updates if not in battery-saving mode
    const intervalTime = performanceMode === 'battery' ? 60000 : 30000; // 1 min or 30s
    const interval = setInterval(() => {
      dispatch(trackPerformanceMetrics());
    }, intervalTime);
    
    return () => clearInterval(interval);
  }, [dispatch, performanceMode]);
  
  /**
   * Chain-of-Thought: Calculate reading statistics from book cache
   * Time Complexity: O(n) where n is number of books in cache, but runs only once on mount
   */
  useEffect(() => {
    // Process book data to generate reading statistics
    const calculateReadingStats = () => {
      // In a real implementation, this would use actual reading history
      // For now, we'll simulate some reading stats based on the cache
      
      const cachedBooks = Object.values(bookCache);
      if (!cachedBooks.length) return;
      
      // Count genres
      const genreCounts: Record<string, number> = {};
      let totalRating = 0;
      
      cachedBooks.forEach(book => {
        book.genres?.forEach(genre => {
          genreCounts[genre] = (genreCounts[genre] || 0) + 1;
        });
        
        totalRating += book.rating || 0;
      });
      
      // Convert to array and sort
      const topGenres = Object.entries(genreCounts)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 5);
      
      // Generate fake reading history for the last 10 days
      const readingHistory = Array.from({ length: 10 }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (9 - i));
        
        return {
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          pages: Math.floor(Math.random() * 50) + 10 // 10-60 pages per day
        };
      });
      
      setReadingStats({
        booksStarted: Math.min(cachedBooks.length, 12),
        booksCompleted: Math.floor(cachedBooks.length * 0.7),
        totalPages: cachedBooks.reduce((sum, book) => sum + (book.page_count || 300), 0),
        readingStreak: Math.floor(Math.random() * 14) + 1, // 1-15 day streak
        topGenres,
        readingHistory,
        averageRating: totalRating / cachedBooks.length
      });
    };
    
    calculateReadingStats();
  }, [bookCache]);
  
  // Format metrics for display
  const formattedMemory = performanceMetrics.memoryUsage !== null 
    ? `${performanceMetrics.memoryUsage.toFixed(1)} MB` 
    : 'Not available';
    
  const apiLatencyEntries = Object.entries(performanceMetrics.apiLatency)
    .map(([endpoint, latency]) => ({
      endpoint: endpoint.split('/').pop() || endpoint,
      latency: typeof latency === 'number' ? Math.round(latency) : 0
    }))
    .sort((a, b) => b.latency - a.latency)
    .slice(0, 5);
  
  if (compact) {
    // Compact view for dashboard sidebar
    return (
      <motion.div 
        className="dashboard-analytics-compact"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <h3 className="analytics-title">Dashboard Metrics</h3>
        
        <div className="metrics-container">
          <div className="metric-item">
            <span className="metric-label">Load Time</span>
            <span className="metric-value">{Math.round(performanceMetrics.loadTime)}ms</span>
          </div>
          
          <div className="metric-item">
            <span className="metric-label">Memory</span>
            <span className="metric-value">{formattedMemory}</span>
          </div>
          
          <div className="metric-item">
            <span className="metric-label">Books Completed</span>
            <span className="metric-value">{readingStats.booksCompleted}</span>
          </div>
          
          <div className="metric-item">
            <span className="metric-label">Reading Streak</span>
            <span className="metric-value">{readingStats.readingStreak} days</span>
          </div>
        </div>
      </motion.div>
    );
  }
  
  // Full dashboard view
  return (
    <motion.div 
      className="dashboard-analytics-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="analytics-header">
        <h2 className="analytics-title">Dashboard Analytics</h2>
        <div className="analytics-timeframe">
          <span>Last Updated: {new Date(performanceMetrics.lastUpdated).toLocaleTimeString()}</span>
        </div>
      </div>
      
      <div className="analytics-grid">
        {/* Performance Metrics */}
        <div className="analytics-card performance-metrics">
          <h3>Performance Metrics</h3>
          
          <div className="metrics-container">
            <div className="metric-group">
              <div className="metric-item">
                <span className="metric-label">Load Time</span>
                <span className="metric-value">{Math.round(performanceMetrics.loadTime)}ms</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Render Time</span>
                <span className="metric-value">{Math.round(performanceMetrics.renderTime)}ms</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Memory Usage</span>
                <span className="metric-value">{formattedMemory}</span>
              </div>
            </div>
            
            <div className="metric-chart">
              <h4>API Latency</h4>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart
                  data={apiLatencyEntries}
                  margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                  <XAxis dataKey="endpoint" tick={{ fontSize: 10 }} />
                  <YAxis unit="ms" width={40} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(value) => [`${value} ms`, 'Latency']} />
                  <Bar dataKey="latency" fill="var(--ai-primary)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        {/* Reading Analytics */}
        <div className="analytics-card reading-analytics">
          <h3>Reading Analytics</h3>
          
          <div className="metrics-container">
            <div className="metric-group">
              <div className="metric-item">
                <span className="metric-label">Books Started</span>
                <span className="metric-value">{readingStats.booksStarted}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Books Completed</span>
                <span className="metric-value">{readingStats.booksCompleted}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Total Pages</span>
                <span className="metric-value">{readingStats.totalPages.toLocaleString()}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Reading Streak</span>
                <span className="metric-value">{readingStats.readingStreak} days</span>
              </div>
            </div>
            
            <div className="metric-chart">
              <h4>Reading History</h4>
              <ResponsiveContainer width="100%" height={150}>
                <LineChart
                  data={readingStats.readingHistory}
                  margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis unit=" p" width={40} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(value) => [`${value} pages`, 'Read']} />
                  <Line 
                    type="monotone" 
                    dataKey="pages" 
                    stroke="var(--ai-secondary)" 
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        {/* Genre Analysis */}
        <div className="analytics-card genre-analytics">
          <h3>Genre Analysis</h3>
          
          <div className="metrics-container">
            <div className="genre-list">
              {readingStats.topGenres.map((genre, index) => (
                <div className="genre-item" key={genre.name}>
                  <span className="genre-name">{genre.name}</span>
                  <div className="genre-bar-container">
                    <motion.div 
                      className="genre-bar"
                      initial={{ width: 0 }}
                      animate={{ width: `${(genre.count / readingStats.topGenres[0].count) * 100}%` }}
                      transition={{ duration: 0.8, delay: index * 0.1 }}
                      style={{ 
                        background: `var(--gradient-${index % 3 === 0 ? 'primary' : index % 3 === 1 ? 'secondary' : 'accent'})` 
                      }}
                    />
                  </div>
                  <span className="genre-count">{genre.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* AI Recommendations Impact */}
        <div className="analytics-card ai-analytics">
          <h3>AI Recommendation Impact</h3>
          
          <div className="metrics-container">
            <div className="metric-group">
              <div className="metric-item">
                <span className="metric-label">AI Mode</span>
                <span className="metric-value ai-mode">{performanceMode}</span>
              </div>
              
              <div className="metric-item">
                <span className="metric-label">Personalization Score</span>
                <div className="personalization-score">
                  <motion.div 
                    className="score-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${75}%` }}
                    transition={{ duration: 0.8 }}
                  />
                  <span className="score-text">75%</span>
                </div>
              </div>
            </div>
            
            <div className="ai-stats">
              <h4>Recommendation Acceptance Rate</h4>
              <div className="stats-container">
                <div className="stat-item">
                  <div className="stat-circle">
                    <svg viewBox="0 0 36 36">
                      <path
                        className="circle-bg"
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className="circle-fill"
                        strokeDasharray={`${68}, 100`}
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <text x="18" y="20.35" className="circle-text">68%</text>
                    </svg>
                  </div>
                  <span className="stat-label">Click Rate</span>
                </div>
                
                <div className="stat-item">
                  <div className="stat-circle">
                    <svg viewBox="0 0 36 36">
                      <path
                        className="circle-bg"
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path
                        className="circle-fill"
                        strokeDasharray={`${42}, 100`}
                        d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <text x="18" y="20.35" className="circle-text">42%</text>
                    </svg>
                  </div>
                  <span className="stat-label">Completion</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default DashboardAnalytics;
