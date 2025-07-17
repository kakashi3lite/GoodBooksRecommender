/**
 * Real-time 10× Uplift Dashboard Integration
 * ==========================================
 * 
 * Production-grade dashboard for monitoring newsletter transformation impact
 * and validating 10× uplift across all KPIs in real-time.
 */

class UpliftDashboard {
    constructor() {
        this.wsConnection = null;
        this.metricsData = new Map();
        this.chartInstances = new Map();
        this.validationHistory = [];
        this.isConnected = false;
        
        // KPI thresholds for 10× uplift
        this.upliftTargets = {
            user_engagement_rate: { baseline: 0.15, target: 1.5, multiplier: 10 },
            avg_session_duration: { baseline: 180, target: 1800, multiplier: 10 },
            click_through_rate: { baseline: 0.08, target: 0.8, multiplier: 10 },
            conversion_rate: { baseline: 0.03, target: 0.3, multiplier: 10 },
            user_retention_rate: { baseline: 0.25, target: 2.5, multiplier: 10 },
            content_relevance_score: { baseline: 0.6, target: 6.0, multiplier: 10 },
            personalization_accuracy: { baseline: 0.55, target: 5.5, multiplier: 10 },
            response_time_ms: { baseline: 850, target: 85, multiplier: 10, inverse: true },
            system_availability: { baseline: 0.95, target: 0.999, multiplier: 1.05 },
            user_satisfaction_score: { baseline: 3.2, target: 4.8, multiplier: 1.5 }
        };
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing 10× Uplift Dashboard...');
        
        try {
            await this.setupWebSocket();
            this.createDashboardLayout();
            this.initializeCharts();
            this.startMetricsPolling();
            this.bindEventListeners();
            
            console.log('✅ 10× Uplift Dashboard initialized successfully');
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            this.showError('Failed to initialize dashboard. Please refresh the page.');
        }
    }
    
    async setupWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/uplift-metrics`;
        
        try {
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('📡 WebSocket connected for real-time metrics');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealtimeUpdate(data);
            };
            
            this.wsConnection.onclose = () => {
                console.log('📡 WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                this.attemptReconnection();
            };
            
            this.wsConnection.onerror = (error) => {
                console.error('📡 WebSocket error:', error);
            };
            
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }
    
    createDashboardLayout() {
        const container = document.getElementById('uplift-dashboard');
        if (!container) {
            console.error('Dashboard container not found');
            return;
        }
        
        container.innerHTML = `
            <div class="uplift-dashboard">
                <!-- Header Section -->
                <div class="dashboard-header">
                    <h1 class="dashboard-title">
                        🎯 10× Uplift Validation Dashboard
                        <span class="connection-status" id="connection-status">
                            <span class="status-indicator" id="status-indicator"></span>
                            <span id="status-text">Connecting...</span>
                        </span>
                    </h1>
                    <div class="dashboard-controls">
                        <button id="run-validation" class="btn btn-primary">
                            🚀 Run Full Validation
                        </button>
                        <button id="quick-validation" class="btn btn-secondary">
                            ⚡ Quick Check
                        </button>
                        <button id="export-report" class="btn btn-outline">
                            📊 Export Report
                        </button>
                    </div>
                </div>
                
                <!-- Main KPI Overview -->
                <div class="kpi-overview">
                    <div class="kpi-card overall-status" id="overall-status">
                        <h3>Overall 10× Status</h3>
                        <div class="status-indicator-large" id="overall-indicator">
                            <span class="status-text" id="overall-text">Measuring...</span>
                            <span class="status-percentage" id="overall-percentage">---%</span>
                        </div>
                    </div>
                    
                    <div class="kpi-card metrics-summary">
                        <h3>Metrics Summary</h3>
                        <div class="metrics-grid" id="metrics-summary">
                            <div class="metric-item">
                                <span class="metric-label">Passing</span>
                                <span class="metric-value" id="metrics-passing">-/-</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Avg Improvement</span>
                                <span class="metric-value" id="avg-improvement">-×</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Confidence</span>
                                <span class="metric-value" id="confidence-score">--%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Detailed Metrics Grid -->
                <div class="metrics-grid-container">
                    <div class="metrics-grid" id="detailed-metrics">
                        <!-- Metrics cards will be dynamically generated -->
                    </div>
                </div>
                
                <!-- Charts Section -->
                <div class="charts-section">
                    <div class="chart-container">
                        <h3>Real-time Metrics Performance</h3>
                        <canvas id="metrics-chart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Improvement Factors</h3>
                        <canvas id="improvement-chart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <h3>Validation History</h3>
                        <canvas id="history-chart"></canvas>
                    </div>
                </div>
                
                <!-- Recommendations Panel -->
                <div class="recommendations-panel" id="recommendations-panel">
                    <h3>🎯 Optimization Recommendations</h3>
                    <div class="recommendations-list" id="recommendations-list">
                        <p class="no-recommendations">Run validation to get recommendations</p>
                    </div>
                </div>
                
                <!-- Validation Log -->
                <div class="validation-log" id="validation-log">
                    <h3>📋 Validation Log</h3>
                    <div class="log-container" id="log-container">
                        <p class="log-entry">Dashboard initialized. Ready for validation.</p>
                    </div>
                </div>
            </div>
        `;
        
        this.createDetailedMetricsCards();
    }
    
    createDetailedMetricsCards() {
        const container = document.getElementById('detailed-metrics');
        
        Object.entries(this.upliftTargets).forEach(([metricName, config]) => {
            const card = document.createElement('div');
            card.className = 'metric-card';
            card.id = `metric-${metricName}`;
            
            const displayName = metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const unit = this.getMetricUnit(metricName);
            
            card.innerHTML = `
                <div class="metric-header">
                    <h4>${displayName}</h4>
                    <span class="metric-status" id="status-${metricName}">⏳</span>
                </div>
                <div class="metric-values">
                    <div class="value-item">
                        <span class="label">Current</span>
                        <span class="value" id="current-${metricName}">--</span>
                    </div>
                    <div class="value-item">
                        <span class="label">Target</span>
                        <span class="value">${config.target}${unit}</span>
                    </div>
                    <div class="value-item">
                        <span class="label">Improvement</span>
                        <span class="value improvement" id="improvement-${metricName}">--×</span>
                    </div>
                </div>
                <div class="metric-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-${metricName}" style="width: 0%"></div>
                    </div>
                    <span class="progress-text" id="progress-text-${metricName}">0%</span>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    getMetricUnit(metricName) {
        const units = {
            'user_engagement_rate': '%',
            'avg_session_duration': 's',
            'click_through_rate': '%',
            'conversion_rate': '%',
            'user_retention_rate': '%',
            'content_relevance_score': '',
            'personalization_accuracy': '',
            'response_time_ms': 'ms',
            'system_availability': '%',
            'user_satisfaction_score': '/5'
        };
        return units[metricName] || '';
    }
    
    initializeCharts() {
        // Real-time metrics chart
        const metricsCtx = document.getElementById('metrics-chart').getContext('2d');
        this.chartInstances.set('metrics', new Chart(metricsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Average Improvement Factor',
                    data: [],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Improvement Factor (×)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true
                    }
                }
            }
        }));
        
        // Improvement factors chart
        const improvementCtx = document.getElementById('improvement-chart').getContext('2d');
        this.chartInstances.set('improvement', new Chart(improvementCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Current Improvement',
                    data: [],
                    backgroundColor: 'rgba(33, 150, 243, 0.8)',
                    borderColor: '#2196F3',
                    borderWidth: 1
                }, {
                    label: '10× Target',
                    data: [],
                    backgroundColor: 'rgba(255, 193, 7, 0.3)',
                    borderColor: '#FFC107',
                    borderWidth: 2,
                    type: 'line'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Improvement Factor (×)'
                        }
                    }
                }
            }
        }));
        
        // Validation history chart
        const historyCtx = document.getElementById('history-chart').getContext('2d');
        this.chartInstances.set('history', new Chart(historyCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Metrics Passing',
                    data: [],
                    borderColor: '#9C27B0',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    yAxisID: 'y'
                }, {
                    label: 'Average Improvement',
                    data: [],
                    borderColor: '#FF5722',
                    backgroundColor: 'rgba(255, 87, 34, 0.1)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Metrics Passing'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Improvement Factor (×)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        }));
    }
    
    bindEventListeners() {
        // Run full validation
        document.getElementById('run-validation').addEventListener('click', () => {
            this.runFullValidation();
        });
        
        // Quick validation
        document.getElementById('quick-validation').addEventListener('click', () => {
            this.runQuickValidation();
        });
        
        // Export report
        document.getElementById('export-report').addEventListener('click', () => {
            this.exportValidationReport();
        });
    }
    
    async runFullValidation() {
        this.addLogEntry('🚀 Starting comprehensive 10× uplift validation...');
        this.setValidationInProgress(true);
        
        try {
            const response = await fetch('/api/newsletter/validation/run-full', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Validation failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.handleValidationResult(result);
            this.addLogEntry('✅ Full validation completed successfully');
            
        } catch (error) {
            console.error('Validation failed:', error);
            this.addLogEntry(`❌ Validation failed: ${error.message}`);
            this.showError('Validation failed. Please try again.');
        } finally {
            this.setValidationInProgress(false);
        }
    }
    
    async runQuickValidation() {
        this.addLogEntry('⚡ Running quick validation check...');
        this.setValidationInProgress(true);
        
        try {
            const response = await fetch('/api/newsletter/validation/run-quick', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`Quick validation failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.handleQuickValidationResult(result);
            this.addLogEntry('✅ Quick validation completed');
            
        } catch (error) {
            console.error('Quick validation failed:', error);
            this.addLogEntry(`❌ Quick validation failed: ${error.message}`);
        } finally {
            this.setValidationInProgress(false);
        }
    }
    
    handleValidationResult(result) {
        // Update overall status
        this.updateOverallStatus(result);
        
        // Update individual metrics
        if (result.metrics) {
            result.metrics.forEach(metric => {
                this.updateMetricCard(metric);
            });
        }
        
        // Update charts
        this.updateCharts(result);
        
        // Update recommendations
        this.updateRecommendations(result.recommendations || []);
        
        // Store in history
        this.validationHistory.push({
            timestamp: new Date(),
            result: result
        });
        
        // Update history chart
        this.updateHistoryChart();
    }
    
    handleQuickValidationResult(result) {
        this.addLogEntry(`Quick check: ${result.overall_status} (${result.metrics_passing}/${result.metrics_tested} metrics passing)`);
        
        // Update subset of metrics
        if (result.metrics) {
            result.metrics.forEach(metric => {
                this.updateMetricCard({
                    name: metric.name,
                    current_value: 0,  // Quick validation doesn't provide detailed values
                    improvement_factor: parseFloat(metric.improvement.replace('×', '')),
                    target_achieved: metric.status === 'PASS'
                });
            });
        }
    }
    
    updateOverallStatus(result) {
        const indicator = document.getElementById('overall-indicator');
        const text = document.getElementById('overall-text');
        const percentage = document.getElementById('overall-percentage');
        const summary = document.getElementById('metrics-summary');
        
        const isSuccess = result.overall_uplift_achieved || result.success;
        const successRate = result.metrics_passing && result.total_metrics 
            ? (result.metrics_passing / result.total_metrics) * 100 
            : 0;
        
        // Update overall status
        indicator.className = `status-indicator-large ${isSuccess ? 'success' : 'warning'}`;
        text.textContent = isSuccess ? '10× Uplift Achieved!' : 'In Progress';
        percentage.textContent = `${successRate.toFixed(1)}%`;
        
        // Update summary metrics
        document.getElementById('metrics-passing').textContent = 
            `${result.metrics_passing || 0}/${result.total_metrics || 0}`;
        document.getElementById('avg-improvement').textContent = 
            `${(result.average_improvement_factor || 0).toFixed(2)}×`;
        document.getElementById('confidence-score').textContent = 
            `${((result.confidence_score || 0) * 100).toFixed(1)}%`;
    }
    
    updateMetricCard(metric) {
        const metricName = metric.name;
        const config = this.upliftTargets[metricName];
        
        if (!config) return;
        
        // Update status icon
        const statusEl = document.getElementById(`status-${metricName}`);
        if (statusEl) {
            statusEl.textContent = metric.target_achieved ? '✅' : '⏳';
            statusEl.className = `metric-status ${metric.target_achieved ? 'success' : 'pending'}`;
        }
        
        // Update current value
        const currentEl = document.getElementById(`current-${metricName}`);
        if (currentEl) {
            const unit = this.getMetricUnit(metricName);
            currentEl.textContent = `${metric.current_value.toFixed(3)}${unit}`;
        }
        
        // Update improvement factor
        const improvementEl = document.getElementById(`improvement-${metricName}`);
        if (improvementEl) {
            improvementEl.textContent = `${metric.improvement_factor.toFixed(2)}×`;
            improvementEl.className = `value improvement ${metric.improvement_factor >= 10 ? 'excellent' : metric.improvement_factor >= 5 ? 'good' : 'needs-work'}`;
        }
        
        // Update progress bar
        const progressEl = document.getElementById(`progress-${metricName}`);
        const progressTextEl = document.getElementById(`progress-text-${metricName}`);
        if (progressEl && progressTextEl) {
            const progressPercent = config.inverse 
                ? Math.min(100, (config.baseline / metric.current_value / config.multiplier) * 100)
                : Math.min(100, (metric.current_value / config.target) * 100);
            
            progressEl.style.width = `${progressPercent}%`;
            progressTextEl.textContent = `${progressPercent.toFixed(1)}%`;
            
            // Color coding
            if (progressPercent >= 100) {
                progressEl.className = 'progress-fill success';
            } else if (progressPercent >= 70) {
                progressEl.className = 'progress-fill good';
            } else {
                progressEl.className = 'progress-fill needs-work';
            }
        }
    }
    
    updateCharts(result) {
        // Update real-time metrics chart
        const metricsChart = this.chartInstances.get('metrics');
        if (metricsChart && result.average_improvement_factor) {
            const now = new Date().toLocaleTimeString();
            metricsChart.data.labels.push(now);
            metricsChart.data.datasets[0].data.push(result.average_improvement_factor);
            
            // Keep only last 20 data points
            if (metricsChart.data.labels.length > 20) {
                metricsChart.data.labels.shift();
                metricsChart.data.datasets[0].data.shift();
            }
            
            metricsChart.update();
        }
        
        // Update improvement factors chart
        const improvementChart = this.chartInstances.get('improvement');
        if (improvementChart && result.metrics) {
            const labels = result.metrics.map(m => m.name.replace(/_/g, ' '));
            const currentData = result.metrics.map(m => m.improvement_factor);
            const targetData = result.metrics.map(m => {
                const config = this.upliftTargets[m.name];
                return config ? config.multiplier : 10;
            });
            
            improvementChart.data.labels = labels;
            improvementChart.data.datasets[0].data = currentData;
            improvementChart.data.datasets[1].data = targetData;
            improvementChart.update();
        }
    }
    
    updateHistoryChart() {
        const historyChart = this.chartInstances.get('history');
        if (!historyChart || this.validationHistory.length === 0) return;
        
        const labels = this.validationHistory.map(h => h.timestamp.toLocaleTimeString());
        const metricsPassingData = this.validationHistory.map(h => h.result.metrics_passing || 0);
        const avgImprovementData = this.validationHistory.map(h => h.result.average_improvement_factor || 0);
        
        historyChart.data.labels = labels;
        historyChart.data.datasets[0].data = metricsPassingData;
        historyChart.data.datasets[1].data = avgImprovementData;
        historyChart.update();
    }
    
    updateRecommendations(recommendations) {
        const container = document.getElementById('recommendations-list');
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="no-recommendations">All metrics performing well! 🎉</p>';
            return;
        }
        
        container.innerHTML = recommendations.map((rec, index) => `
            <div class="recommendation-item">
                <span class="rec-number">${index + 1}</span>
                <span class="rec-text">${rec}</span>
            </div>
        `).join('');
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        
        if (connected) {
            indicator.className = 'status-indicator connected';
            text.textContent = 'Live';
        } else {
            indicator.className = 'status-indicator disconnected';
            text.textContent = 'Disconnected';
        }
    }
    
    setValidationInProgress(inProgress) {
        const runBtn = document.getElementById('run-validation');
        const quickBtn = document.getElementById('quick-validation');
        
        runBtn.disabled = inProgress;
        quickBtn.disabled = inProgress;
        
        if (inProgress) {
            runBtn.textContent = '⏳ Validating...';
            quickBtn.textContent = '⏳ Checking...';
        } else {
            runBtn.textContent = '🚀 Run Full Validation';
            quickBtn.textContent = '⚡ Quick Check';
        }
    }
    
    addLogEntry(message) {
        const container = document.getElementById('log-container');
        const timestamp = new Date().toLocaleTimeString();
        
        const entry = document.createElement('p');
        entry.className = 'log-entry';
        entry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        
        container.appendChild(entry);
        container.scrollTop = container.scrollHeight;
        
        // Keep only last 100 entries
        const entries = container.querySelectorAll('.log-entry');
        if (entries.length > 100) {
            entries[0].remove();
        }
    }
    
    showError(message) {
        // You could implement a toast notification system here
        console.error(message);
        this.addLogEntry(`❌ Error: ${message}`);
    }
    
    handleRealtimeUpdate(data) {
        if (data.type === 'metric_update') {
            this.updateMetricCard(data.metric);
        } else if (data.type === 'validation_complete') {
            this.handleValidationResult(data.result);
        }
    }
    
    attemptReconnection() {
        if (!this.isConnected) {
            setTimeout(() => {
                console.log('🔄 Attempting to reconnect...');
                this.setupWebSocket();
            }, 5000);
        }
    }
    
    startMetricsPolling() {
        // Poll for metrics updates every 30 seconds
        setInterval(async () => {
            if (!this.isConnected) {
                try {
                    const response = await fetch('/api/newsletter/validation/status');
                    if (response.ok) {
                        const status = await response.json();
                        if (status.last_validation) {
                            this.handleValidationResult(status.last_validation);
                        }
                    }
                } catch (error) {
                    console.warn('Failed to poll metrics:', error);
                }
            }
        }, 30000);
    }
    
    async exportValidationReport() {
        try {
            const response = await fetch('/api/newsletter/validation/export-report', {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error('Failed to export report');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `validation-report-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.addLogEntry('📊 Validation report exported successfully');
            
        } catch (error) {
            console.error('Export failed:', error);
            this.addLogEntry(`❌ Export failed: ${error.message}`);
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.upliftDashboard = new UpliftDashboard();
});

// CSS Styles for the dashboard
const dashboardStyles = `
<style>
.uplift-dashboard {
    padding: 20px;
    background: #f5f5f5;
    min-height: 100vh;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.dashboard-title {
    margin: 0;
    color: #333;
    font-size: 24px;
}

.connection-status {
    font-size: 14px;
    margin-left: 20px;
}

.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 5px;
}

.status-indicator.connected {
    background: #4CAF50;
}

.status-indicator.disconnected {
    background: #f44336;
}

.dashboard-controls {
    display: flex;
    gap: 10px;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
}

.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.btn-primary {
    background: #2196F3;
    color: white;
}

.btn-primary:hover:not(:disabled) {
    background: #1976D2;
}

.btn-secondary {
    background: #FF9800;
    color: white;
}

.btn-outline {
    background: transparent;
    border: 1px solid #ccc;
    color: #666;
}

.kpi-overview {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 30px;
}

.kpi-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-indicator-large {
    text-align: center;
    padding: 20px 0;
}

.status-indicator-large.success {
    color: #4CAF50;
}

.status-indicator-large.warning {
    color: #FF9800;
}

.status-text {
    display: block;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 10px;
}

.status-percentage {
    display: block;
    font-size: 32px;
    font-weight: bold;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.metric-header h4 {
    margin: 0;
    color: #333;
    font-size: 16px;
}

.metric-status {
    font-size: 20px;
}

.metric-values {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-bottom: 15px;
}

.value-item {
    text-align: center;
}

.value-item .label {
    display: block;
    font-size: 12px;
    color: #666;
    margin-bottom: 5px;
}

.value-item .value {
    display: block;
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

.value.improvement.excellent {
    color: #4CAF50;
}

.value.improvement.good {
    color: #FF9800;
}

.value.improvement.needs-work {
    color: #f44336;
}

.metric-progress {
    position: relative;
}

.progress-bar {
    background: #eee;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    transition: width 0.3s ease;
}

.progress-fill.success {
    background: #4CAF50;
}

.progress-fill.good {
    background: #FF9800;
}

.progress-fill.needs-work {
    background: #f44336;
}

.progress-text {
    position: absolute;
    right: 0;
    top: 12px;
    font-size: 12px;
    color: #666;
}

.charts-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-container {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-container h3 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 18px;
}

.recommendations-panel {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.recommendations-list {
    margin-top: 15px;
}

.recommendation-item {
    display: flex;
    align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid #eee;
}

.rec-number {
    background: #2196F3;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    margin-right: 15px;
    flex-shrink: 0;
}

.rec-text {
    flex: 1;
    line-height: 1.5;
}

.validation-log {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.log-container {
    max-height: 300px;
    overflow-y: auto;
    background: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
}

.log-entry {
    margin: 5px 0;
    padding: 0;
}

.log-time {
    color: #666;
    margin-right: 10px;
}

.no-recommendations {
    text-align: center;
    color: #666;
    font-style: italic;
}
</style>
`;

// Add styles to document head
document.head.insertAdjacentHTML('beforeend', dashboardStyles);
