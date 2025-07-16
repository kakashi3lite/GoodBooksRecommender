/**
 * GoodBooks Recommender Dashboard - Charts and Analytics
 * Chart.js integration for data visualization
 */

/**
 * Chart Manager
 */
class ChartManager {
  constructor() {
    this.charts = new Map();
    this.defaultColors = [
      '#2563eb', '#059669', '#dc2626', '#f59e0b', '#8b5cf6',
      '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6366f1'
    ];
  }

  /**
   * Create or update a chart
   */
  createChart(canvasId, config) {
    const existingChart = this.charts.get(canvasId);
    if (existingChart) {
      existingChart.destroy();
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.error(`Canvas element with id '${canvasId}' not found`);
      return null;
    }

    const chart = new Chart(canvas, config);
    this.charts.set(canvasId, chart);
    return chart;
  }

  /**
   * Update chart data
   */
  updateChart(canvasId, newData) {
    const chart = this.charts.get(canvasId);
    if (chart) {
      chart.data = newData;
      chart.update();
    }
  }

  /**
   * Destroy a chart
   */
  destroyChart(canvasId) {
    const chart = this.charts.get(canvasId);
    if (chart) {
      chart.destroy();
      this.charts.delete(canvasId);
    }
  }

  /**
   * Destroy all charts
   */
  destroyAll() {
    this.charts.forEach(chart => chart.destroy());
    this.charts.clear();
  }

  /**
   * Create performance metrics chart
   */
  createPerformanceChart(canvasId, data) {
    const config = {
      type: 'line',
      data: {
        labels: data.timestamps || [],
        datasets: [
          {
            label: 'Requests/min',
            data: data.requests || [],
            borderColor: this.defaultColors[0],
            backgroundColor: this.defaultColors[0] + '20',
            tension: 0.4,
            yAxisID: 'y'
          },
          {
            label: 'Response Time (ms)',
            data: data.responseTime || [],
            borderColor: this.defaultColors[1],
            backgroundColor: this.defaultColors[1] + '20',
            tension: 0.4,
            yAxisID: 'y1'
          },
          {
            label: 'Cache Hit Rate (%)',
            data: data.cacheHitRate || [],
            borderColor: this.defaultColors[2],
            backgroundColor: this.defaultColors[2] + '20',
            tension: 0.4,
            yAxisID: 'y2'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'System Performance (Last 24 Hours)'
          },
          legend: {
            position: 'top'
          }
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Time'
            }
          },
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Requests/min'
            }
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Response Time (ms)'
            },
            grid: {
              drawOnChartArea: false
            }
          },
          y2: {
            type: 'linear',
            display: false,
            min: 0,
            max: 100
          }
        }
      }
    };

    return this.createChart(canvasId, config);
  }

  /**
   * Create recommendation distribution chart
   */
  createRecommendationChart(canvasId, data) {
    const config = {
      type: 'doughnut',
      data: {
        labels: data.labels || ['Content-based', 'Collaborative', 'Hybrid'],
        datasets: [{
          data: data.values || [0, 0, 0],
          backgroundColor: [
            this.defaultColors[0],
            this.defaultColors[1],
            this.defaultColors[2]
          ],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Recommendation Types Distribution'
          },
          legend: {
            position: 'bottom'
          }
        }
      }
    };

    return this.createChart(canvasId, config);
  }

  /**
   * Create genre popularity chart
   */
  createGenreChart(canvasId, data) {
    const config = {
      type: 'bar',
      data: {
        labels: data.genres || [],
        datasets: [{
          label: 'Recommendations',
          data: data.counts || [],
          backgroundColor: this.defaultColors[0] + '80',
          borderColor: this.defaultColors[0],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'Popular Genres'
          },
          legend: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Number of Recommendations'
            }
          }
        }
      }
    };

    return this.createChart(canvasId, config);
  }

  /**
   * Create user activity heatmap
   */
  createActivityHeatmap(canvasId, data) {
    const config = {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'User Activity',
          data: data.points || [],
          backgroundColor: this.defaultColors[0] + '60',
          borderColor: this.defaultColors[0],
          pointRadius: (context) => {
            const value = context.raw.v || 1;
            return Math.max(3, Math.min(20, value / 10));
          }
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: true,
            text: 'User Activity Heatmap'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const point = context.raw;
                return `Hour: ${point.x}, Day: ${point.y}, Activity: ${point.v}`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            position: 'bottom',
            min: 0,
            max: 24,
            title: {
              display: true,
              text: 'Hour of Day'
            }
          },
          y: {
            type: 'linear',
            min: 0,
            max: 7,
            title: {
              display: true,
              text: 'Day of Week'
            }
          }
        }
      }
    };

    return this.createChart(canvasId, config);
  }

  /**
   * Create real-time metrics chart
   */
  createRealTimeChart(canvasId) {
    const maxDataPoints = 50;
    const config = {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Current Load',
            data: [],
            borderColor: this.defaultColors[0],
            backgroundColor: this.defaultColors[0] + '20',
            tension: 0.4,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 0
        },
        plugins: {
          title: {
            display: true,
            text: 'Real-time System Load'
          },
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: 'Time'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Load'
            }
          }
        }
      }
    };

    const chart = this.createChart(canvasId, config);

    // Add method to update real-time data
    if (chart) {
      chart.addData = (label, value) => {
        chart.data.labels.push(label);
        chart.data.datasets[0].data.push(value);

        if (chart.data.labels.length > maxDataPoints) {
          chart.data.labels.shift();
          chart.data.datasets[0].data.shift();
        }

        chart.update('none');
      };
    }

    return chart;
  }

  /**
   * Generate sample data for testing
   */
  generateSampleData() {
    const now = new Date();
    const hours = [];
    const requests = [];
    const responseTime = [];
    const cacheHitRate = [];

    for (let i = 24; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      hours.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
      requests.push(Math.floor(Math.random() * 2000) + 500);
      responseTime.push(Math.floor(Math.random() * 200) + 50);
      cacheHitRate.push(Math.floor(Math.random() * 40) + 60);
    }

    return {
      performance: {
        timestamps: hours,
        requests,
        responseTime,
        cacheHitRate
      },
      recommendations: {
        labels: ['Content-based', 'Collaborative', 'Hybrid'],
        values: [35, 25, 40]
      },
      genres: {
        genres: ['Fiction', 'Fantasy', 'Romance', 'Mystery', 'Sci-Fi', 'Young Adult'],
        counts: [1250, 890, 650, 580, 520, 380]
      },
      activity: {
        points: this.generateActivityPoints()
      }
    };
  }

  generateActivityPoints() {
    const points = [];
    for (let day = 0; day < 7; day++) {
      for (let hour = 0; hour < 24; hour++) {
        const value = Math.floor(Math.random() * 100);
        if (value > 20) { // Only show significant activity
          points.push({ x: hour, y: day, v: value });
        }
      }
    }
    return points;
  }
}

/**
 * Analytics Dashboard
 */
class AnalyticsDashboard {
  constructor(container) {
    this.container = container;
    this.chartManager = new ChartManager();
    this.updateInterval = null;
    this.isRealTimeEnabled = false;
  }

  async initialize() {
    this.render();
    await this.loadData();
    this.setupRealTimeUpdates();
  }

  render() {
    this.container.innerHTML = `
      <div class="analytics-dashboard">
        <div class="dashboard-grid">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">System Performance</h3>
              <div class="card-actions">
                <button class="btn btn-sm btn-ghost" data-action="refresh">🔄</button>
                <button class="btn btn-sm btn-ghost" data-action="toggle-realtime">
                  ${this.isRealTimeEnabled ? '⏸️ Pause' : '▶️ Live'}
                </button>
              </div>
            </div>
            <div class="chart-container">
              <canvas id="performance-chart"></canvas>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Recommendation Types</h3>
            </div>
            <div class="chart-container">
              <canvas id="recommendation-chart"></canvas>
            </div>
          </div>
        </div>

        <div class="dashboard-grid">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Popular Genres</h3>
            </div>
            <div class="chart-container">
              <canvas id="genre-chart"></canvas>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Real-time Load</h3>
            </div>
            <div class="chart-container">
              <canvas id="realtime-chart"></canvas>
            </div>
          </div>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    this.container.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch (action) {
        case 'refresh':
          this.loadData();
          break;
        case 'toggle-realtime':
          this.toggleRealTime();
          break;
      }
    });
  }

  async loadData() {
    try {
      // In a real application, this would call the API
      const data = this.chartManager.generateSampleData();
      
      this.chartManager.createPerformanceChart('performance-chart', data.performance);
      this.chartManager.createRecommendationChart('recommendation-chart', data.recommendations);
      this.chartManager.createGenreChart('genre-chart', data.genres);

      if (!this.realtimeChart) {
        this.realtimeChart = this.chartManager.createRealTimeChart('realtime-chart');
      }

    } catch (error) {
      console.error('Failed to load analytics data:', error);
      Alert.show('Failed to load analytics data', 'error');
    }
  }

  setupRealTimeUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }

    this.updateInterval = setInterval(() => {
      if (this.isRealTimeEnabled && this.realtimeChart) {
        const now = new Date();
        const label = now.toLocaleTimeString();
        const value = Math.floor(Math.random() * 100) + 50;
        
        this.realtimeChart.addData(label, value);
      }
    }, 2000);
  }

  toggleRealTime() {
    this.isRealTimeEnabled = !this.isRealTimeEnabled;
    
    const button = this.container.querySelector('[data-action="toggle-realtime"]');
    if (button) {
      button.innerHTML = this.isRealTimeEnabled ? '⏸️ Pause' : '▶️ Live';
    }

    if (this.isRealTimeEnabled) {
      Alert.show('Real-time updates enabled', 'success');
    } else {
      Alert.show('Real-time updates paused', 'info');
    }
  }

  destroy() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    this.chartManager.destroyAll();
  }
}

/**
 * Health Monitor
 */
class HealthMonitor {
  constructor(container) {
    this.container = container;
    this.healthData = null;
    this.updateInterval = null;
  }

  async initialize() {
    await this.updateHealth();
    this.setupAutoUpdate();
  }

  async updateHealth() {
    try {
      const health = await api.getHealth();
      this.healthData = health;
      this.render();
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      this.renderError();
    }
  }

  render() {
    if (!this.healthData) return;

    const { status, uptime_seconds, checks } = this.healthData;
    const uptimeHours = Math.floor(uptime_seconds / 3600);
    const uptimeMinutes = Math.floor((uptime_seconds % 3600) / 60);

    this.container.innerHTML = `
      <div class="health-monitor">
        <div class="health-status">
          <div class="health-item">
            <span class="health-label">Status</span>
            <span class="health-value ${status.toLowerCase()}">${status}</span>
          </div>
          
          <div class="health-item">
            <span class="health-label">Uptime</span>
            <span class="health-value">${uptimeHours}h ${uptimeMinutes}m</span>
          </div>
          
          ${Object.entries(checks || {}).map(([key, check]) => `
            <div class="health-item">
              <span class="health-label">${this.formatLabel(key)}</span>
              <span class="health-value ${check.status?.toLowerCase() || 'unknown'}">
                ${check.status || 'Unknown'}
              </span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderError() {
    this.container.innerHTML = `
      <div class="health-monitor">
        <div class="alert alert-error">
          <div class="alert-icon">❌</div>
          <div class="alert-content">
            <div class="alert-title">Health Check Failed</div>
            <div class="alert-message">Unable to retrieve system health status</div>
          </div>
        </div>
      </div>
    `;
  }

  formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  setupAutoUpdate() {
    this.updateInterval = setInterval(() => {
      this.updateHealth();
    }, 30000); // Update every 30 seconds
  }

  destroy() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
  }
}

// Export classes
window.ChartManager = ChartManager;
window.AnalyticsDashboard = AnalyticsDashboard;
window.HealthMonitor = HealthMonitor;

console.log('[Charts] Charts and Analytics initialized');
