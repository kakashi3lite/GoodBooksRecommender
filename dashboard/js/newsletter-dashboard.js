/**
 * Newsletter Dashboard Integration
 * Integrates newsletter functionality into the main dashboard
 */

class NewsletterDashboard extends Component {
  constructor(container) {
    super(container);
    this.state = {
      campaigns: [],
      subscribers: 0,
      engagementMetrics: {},
      realtimeMetrics: {},
      templates: [],
      workflows: [],
      loading: true,
      selectedCampaign: null,
      privacySettings: {},
      consentStatus: {}
    };
    
    this.websocket = null;
    this.metricsInterval = null;
    this.setupWebSocket();
  }

  async initialize() {
    try {
      this.setState({ loading: true });
      
      // Load initial data
      await Promise.all([
        this.loadCampaigns(),
        this.loadSubscriberCount(),
        this.loadEngagementMetrics(),
        this.loadTemplates(),
        this.loadWorkflows(),
        this.loadPrivacySettings()
      ]);
      
      this.setState({ loading: false });
      this.startRealtimeUpdates();
      
    } catch (error) {
      logger.error('Failed to initialize newsletter dashboard:', error);
      Alert.show('Failed to load newsletter dashboard', 'error');
    }
  }

  async loadCampaigns() {
    try {
      const campaigns = await api.get('/newsletter/campaigns');
      this.setState({ campaigns: campaigns.campaigns || [] });
    } catch (error) {
      logger.error('Failed to load campaigns:', error);
    }
  }

  async loadSubscriberCount() {
    try {
      const stats = await api.get('/newsletter/analytics/stats');
      this.setState({ subscribers: stats.subscriber_count || 0 });
    } catch (error) {
      logger.error('Failed to load subscriber count:', error);
    }
  }

  async loadEngagementMetrics() {
    try {
      const metrics = await api.get('/newsletter/analytics/engagement');
      this.setState({ engagementMetrics: metrics });
    } catch (error) {
      logger.error('Failed to load engagement metrics:', error);
    }
  }

  async loadTemplates() {
    try {
      const templates = await api.get('/newsletter/templates');
      this.setState({ templates: templates.templates || [] });
    } catch (error) {
      logger.error('Failed to load templates:', error);
    }
  }

  async loadWorkflows() {
    try {
      const workflows = await api.get('/newsletter/workflows');
      this.setState({ workflows: workflows.workflows || [] });
    } catch (error) {
      logger.error('Failed to load workflows:', error);
    }
  }

  async loadPrivacySettings() {
    try {
      const privacy = await api.get('/newsletter/privacy/dashboard');
      this.setState({ 
        privacySettings: privacy.data_retention || {},
        consentStatus: privacy.consents || []
      });
    } catch (error) {
      logger.error('Failed to load privacy settings:', error);
    }
  }

  setupWebSocket() {
    try {
      const wsUrl = `ws://localhost:8000/newsletter/ws/metrics`;
      this.websocket = new WebSocket(wsUrl);
      
      this.websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleRealtimeUpdate(data);
      };
      
      this.websocket.onerror = (error) => {
        logger.error('WebSocket error:', error);
      };
      
      this.websocket.onclose = () => {
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.setupWebSocket(), 5000);
      };
      
    } catch (error) {
      logger.error('Failed to setup WebSocket:', error);
    }
  }

  handleRealtimeUpdate(data) {
    if (data.type === 'engagement_update') {
      this.setState({
        realtimeMetrics: {
          ...this.state.realtimeMetrics,
          ...data.metrics
        }
      });
    } else if (data.type === 'campaign_update') {
      this.updateCampaignStatus(data.campaign_id, data.status);
    }
  }

  updateCampaignStatus(campaignId, status) {
    const campaigns = this.state.campaigns.map(campaign => 
      campaign.id === campaignId ? { ...campaign, status } : campaign
    );
    this.setState({ campaigns });
  }

  startRealtimeUpdates() {
    // Update metrics every 30 seconds
    this.metricsInterval = setInterval(() => {
      this.loadEngagementMetrics();
    }, 30000);
  }

  async createCampaign(campaignData) {
    try {
      const response = await api.post('/newsletter/campaigns', campaignData);
      await this.loadCampaigns();
      Alert.show('Campaign created successfully', 'success');
      return response.campaign_id;
    } catch (error) {
      logger.error('Failed to create campaign:', error);
      Alert.show('Failed to create campaign', 'error');
      throw error;
    }
  }

  async sendCampaign(campaignId) {
    try {
      await api.post(`/newsletter/campaigns/${campaignId}/send`);
      Alert.show('Campaign sent successfully', 'success');
      await this.loadCampaigns();
    } catch (error) {
      logger.error('Failed to send campaign:', error);
      Alert.show('Failed to send campaign', 'error');
    }
  }

  async updatePrivacyConsent(consentType, purpose, granted) {
    try {
      await api.post('/newsletter/privacy/consent', {
        consent_type: consentType,
        purpose: purpose,
        granted: granted
      });
      
      await this.loadPrivacySettings();
      Alert.show('Privacy settings updated', 'success');
    } catch (error) {
      logger.error('Failed to update privacy consent:', error);
      Alert.show('Failed to update privacy settings', 'error');
    }
  }

  render() {
    const { 
      campaigns, 
      subscribers, 
      engagementMetrics, 
      realtimeMetrics,
      templates,
      workflows,
      loading,
      selectedCampaign,
      privacySettings,
      consentStatus
    } = this.state;

    if (loading) {
      return this.renderLoading();
    }

    this.container.innerHTML = `
      <div class="newsletter-dashboard">
        <!-- Header -->
        <div class="dashboard-header">
          <div class="header-content">
            <div class="header-info">
              <h1>📧 Newsletter Dashboard</h1>
              <p class="text-muted">AI-powered newsletter management and analytics</p>
            </div>
            <div class="header-actions">
              <button class="btn btn-primary" onclick="newsletterDashboard.showCreateCampaign()">
                ✉️ New Campaign
              </button>
              <button class="btn btn-secondary" onclick="newsletterDashboard.showPrivacySettings()">
                🔒 Privacy Settings
              </button>
            </div>
          </div>
        </div>

        <!-- Metrics Overview -->
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-icon">👥</div>
            <div class="metric-content">
              <div class="metric-value">${this.formatNumber(subscribers)}</div>
              <div class="metric-label">Total Subscribers</div>
              ${realtimeMetrics.new_subscribers ? `
                <div class="metric-change positive">+${realtimeMetrics.new_subscribers} today</div>
              ` : ''}
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-content">
              <div class="metric-value">${(engagementMetrics.open_rate * 100 || 0).toFixed(1)}%</div>
              <div class="metric-label">Open Rate</div>
              ${realtimeMetrics.open_rate_change ? `
                <div class="metric-change ${realtimeMetrics.open_rate_change > 0 ? 'positive' : 'negative'}">
                  ${realtimeMetrics.open_rate_change > 0 ? '+' : ''}${realtimeMetrics.open_rate_change.toFixed(1)}%
                </div>
              ` : ''}
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon">👆</div>
            <div class="metric-content">
              <div class="metric-value">${(engagementMetrics.click_rate * 100 || 0).toFixed(1)}%</div>
              <div class="metric-label">Click Rate</div>
              ${realtimeMetrics.click_rate_change ? `
                <div class="metric-change ${realtimeMetrics.click_rate_change > 0 ? 'positive' : 'negative'}">
                  ${realtimeMetrics.click_rate_change > 0 ? '+' : ''}${realtimeMetrics.click_rate_change.toFixed(1)}%
                </div>
              ` : ''}
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon">🎯</div>
            <div class="metric-content">
              <div class="metric-value">${(engagementMetrics.personalization_score * 100 || 0).toFixed(0)}</div>
              <div class="metric-label">AI Personalization Score</div>
              <div class="metric-sublabel">Privacy-compliant</div>
            </div>
          </div>
        </div>

        <!-- Main Content Tabs -->
        <div class="dashboard-tabs">
          <div class="tab-nav">
            <button class="tab-btn active" onclick="newsletterDashboard.showTab('campaigns')">
              📋 Campaigns
            </button>
            <button class="tab-btn" onclick="newsletterDashboard.showTab('analytics')">
              📊 Analytics
            </button>
            <button class="tab-btn" onclick="newsletterDashboard.showTab('templates')">
              🎨 Templates
            </button>
            <button class="tab-btn" onclick="newsletterDashboard.showTab('automation')">
              ⚡ Automation
            </button>
            <button class="tab-btn" onclick="newsletterDashboard.showTab('privacy')">
              🔒 Privacy
            </button>
          </div>

          <div class="tab-content">
            <!-- Campaigns Tab -->
            <div id="campaigns-tab" class="tab-pane active">
              ${this.renderCampaignsTab(campaigns)}
            </div>

            <!-- Analytics Tab -->
            <div id="analytics-tab" class="tab-pane">
              ${this.renderAnalyticsTab(engagementMetrics, realtimeMetrics)}
            </div>

            <!-- Templates Tab -->
            <div id="templates-tab" class="tab-pane">
              ${this.renderTemplatesTab(templates)}
            </div>

            <!-- Automation Tab -->
            <div id="automation-tab" class="tab-pane">
              ${this.renderAutomationTab(workflows)}
            </div>

            <!-- Privacy Tab -->
            <div id="privacy-tab" class="tab-pane">
              ${this.renderPrivacyTab(privacySettings, consentStatus)}
            </div>
          </div>
        </div>
      </div>

      <!-- Modals -->
      <div id="create-campaign-modal" class="modal" style="display: none;">
        ${this.renderCreateCampaignModal()}
      </div>

      <div id="privacy-settings-modal" class="modal" style="display: none;">
        ${this.renderPrivacySettingsModal()}
      </div>
    `;

    this.attachEventListeners();
  }

  renderCampaignsTab(campaigns) {
    return `
      <div class="campaigns-section">
        <div class="section-header">
          <h3>Newsletter Campaigns</h3>
          <div class="section-actions">
            <select class="form-select" onchange="newsletterDashboard.filterCampaigns(this.value)">
              <option value="all">All Campaigns</option>
              <option value="draft">Drafts</option>
              <option value="scheduled">Scheduled</option>
              <option value="sent">Sent</option>
            </select>
          </div>
        </div>

        <div class="campaigns-grid">
          ${campaigns.length > 0 ? campaigns.map(campaign => `
            <div class="campaign-card" data-campaign-id="${campaign.id}">
              <div class="campaign-header">
                <div class="campaign-status status-${campaign.status}">
                  ${this.getStatusIcon(campaign.status)} ${campaign.status}
                </div>
                <div class="campaign-actions">
                  <button class="btn-icon" onclick="newsletterDashboard.editCampaign('${campaign.id}')" title="Edit">
                    ✏️
                  </button>
                  <button class="btn-icon" onclick="newsletterDashboard.viewCampaign('${campaign.id}')" title="View">
                    👁️
                  </button>
                  ${campaign.status === 'draft' ? `
                    <button class="btn-icon" onclick="newsletterDashboard.sendCampaign('${campaign.id}')" title="Send">
                      📤
                    </button>
                  ` : ''}
                </div>
              </div>
              
              <div class="campaign-content">
                <h4>${campaign.name}</h4>
                <p class="campaign-description">${campaign.description || 'No description'}</p>
                
                <div class="campaign-meta">
                  <div class="meta-item">
                    <span class="meta-label">📅 Created:</span>
                    <span class="meta-value">${this.formatDate(campaign.created_at)}</span>
                  </div>
                  ${campaign.sent_at ? `
                    <div class="meta-item">
                      <span class="meta-label">📤 Sent:</span>
                      <span class="meta-value">${this.formatDate(campaign.sent_at)}</span>
                    </div>
                  ` : ''}
                  ${campaign.recipient_count ? `
                    <div class="meta-item">
                      <span class="meta-label">👥 Recipients:</span>
                      <span class="meta-value">${this.formatNumber(campaign.recipient_count)}</span>
                    </div>
                  ` : ''}
                </div>

                ${campaign.metrics ? `
                  <div class="campaign-metrics-preview">
                    <div class="metric-pill">
                      📧 ${(campaign.metrics.open_rate * 100).toFixed(1)}% opens
                    </div>
                    <div class="metric-pill">
                      👆 ${(campaign.metrics.click_rate * 100).toFixed(1)}% clicks
                    </div>
                  </div>
                ` : ''}
              </div>
            </div>
          `).join('') : `
            <div class="empty-state">
              <div class="empty-icon">📭</div>
              <h3>No campaigns yet</h3>
              <p>Create your first AI-powered newsletter campaign</p>
              <button class="btn btn-primary" onclick="newsletterDashboard.showCreateCampaign()">
                Create Campaign
              </button>
            </div>
          `}
        </div>
      </div>
    `;
  }

  renderAnalyticsTab(metrics, realtimeMetrics) {
    return `
      <div class="analytics-section">
        <div class="analytics-header">
          <h3>Newsletter Analytics</h3>
          <div class="time-range-selector">
            <select class="form-select" onchange="newsletterDashboard.changeTimeRange(this.value)">
              <option value="7d">Last 7 days</option>
              <option value="30d" selected>Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="1y">Last year</option>
            </select>
          </div>
        </div>

        <div class="analytics-grid">
          <!-- Engagement Chart -->
          <div class="chart-container">
            <div class="chart-header">
              <h4>📈 Engagement Trends</h4>
              <div class="chart-legend">
                <div class="legend-item">
                  <div class="legend-color" style="background: #007bff;"></div>
                  <span>Open Rate</span>
                </div>
                <div class="legend-item">
                  <div class="legend-color" style="background: #28a745;"></div>
                  <span>Click Rate</span>
                </div>
              </div>
            </div>
            <canvas id="engagement-chart" width="400" height="200"></canvas>
          </div>

          <!-- Personalization Impact -->
          <div class="chart-container">
            <div class="chart-header">
              <h4>🎯 AI Personalization Impact</h4>
              <div class="personalization-score">
                Score: ${(metrics.personalization_score * 100 || 0).toFixed(0)}/100
              </div>
            </div>
            <canvas id="personalization-chart" width="400" height="200"></canvas>
          </div>

          <!-- Subscriber Growth -->
          <div class="chart-container">
            <div class="chart-header">
              <h4>👥 Subscriber Growth</h4>
              <div class="growth-rate">
                ${realtimeMetrics.growth_rate ? `+${realtimeMetrics.growth_rate.toFixed(1)}% this month` : ''}
              </div>
            </div>
            <canvas id="subscriber-chart" width="400" height="200"></canvas>
          </div>

          <!-- Real-time Activity -->
          <div class="realtime-activity">
            <h4>⚡ Real-time Activity</h4>
            <div class="activity-feed" id="activity-feed">
              ${realtimeMetrics.recent_activities ? realtimeMetrics.recent_activities.map(activity => `
                <div class="activity-item">
                  <div class="activity-icon">${this.getActivityIcon(activity.type)}</div>
                  <div class="activity-content">
                    <div class="activity-text">${activity.description}</div>
                    <div class="activity-time">${this.formatTimeAgo(activity.timestamp)}</div>
                  </div>
                </div>
              `).join('') : '<div class="no-activity">No recent activity</div>'}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderTemplatesTab(templates) {
    return `
      <div class="templates-section">
        <div class="section-header">
          <h3>Newsletter Templates</h3>
          <button class="btn btn-primary" onclick="newsletterDashboard.createTemplate()">
            ➕ New Template
          </button>
        </div>

        <div class="templates-grid">
          ${templates.map(template => `
            <div class="template-card">
              <div class="template-preview">
                <img src="${template.preview_url || '/placeholder-template.png'}" alt="${template.name}" />
              </div>
              <div class="template-info">
                <h4>${template.name}</h4>
                <p>${template.description}</p>
                <div class="template-stats">
                  <span>📊 ${template.usage_count || 0} uses</span>
                  <span>⭐ ${(template.rating || 0).toFixed(1)}</span>
                </div>
                <div class="template-actions">
                  <button class="btn btn-sm btn-primary" onclick="newsletterDashboard.useTemplate('${template.id}')">
                    Use Template
                  </button>
                  <button class="btn btn-sm btn-secondary" onclick="newsletterDashboard.editTemplate('${template.id}')">
                    Edit
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderAutomationTab(workflows) {
    return `
      <div class="automation-section">
        <div class="section-header">
          <h3>Newsletter Automation</h3>
          <button class="btn btn-primary" onclick="newsletterDashboard.createWorkflow()">
            ⚡ New Workflow
          </button>
        </div>

        <div class="workflows-grid">
          ${workflows.map(workflow => `
            <div class="workflow-card">
              <div class="workflow-header">
                <div class="workflow-status ${workflow.is_active ? 'active' : 'inactive'}">
                  ${workflow.is_active ? '🟢 Active' : '🔴 Inactive'}
                </div>
                <div class="workflow-toggle">
                  <label class="toggle-switch">
                    <input type="checkbox" ${workflow.is_active ? 'checked' : ''} 
                           onchange="newsletterDashboard.toggleWorkflow('${workflow.id}', this.checked)">
                    <span class="toggle-slider"></span>
                  </label>
                </div>
              </div>
              
              <div class="workflow-content">
                <h4>${workflow.name}</h4>
                <p>${workflow.description}</p>
                
                <div class="workflow-trigger">
                  <strong>Trigger:</strong> ${workflow.trigger_type}
                </div>
                
                <div class="workflow-stats">
                  <div class="stat-item">
                    <span class="stat-value">${workflow.executions || 0}</span>
                    <span class="stat-label">Executions</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">${(workflow.success_rate * 100 || 0).toFixed(1)}%</span>
                    <span class="stat-label">Success Rate</span>
                  </div>
                </div>
                
                <div class="workflow-actions">
                  <button class="btn btn-sm btn-secondary" onclick="newsletterDashboard.editWorkflow('${workflow.id}')">
                    Edit
                  </button>
                  <button class="btn btn-sm btn-info" onclick="newsletterDashboard.viewWorkflowLogs('${workflow.id}')">
                    Logs
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  renderPrivacyTab(privacySettings, consentStatus) {
    return `
      <div class="privacy-section">
        <div class="privacy-header">
          <h3>🔒 Privacy & GDPR Compliance</h3>
          <div class="compliance-status">
            <span class="status-badge status-compliant">✅ GDPR Compliant</span>
          </div>
        </div>

        <div class="privacy-grid">
          <!-- Consent Management -->
          <div class="privacy-card">
            <div class="card-header">
              <h4>User Consent Management</h4>
              <p class="text-muted">Manage user consent for data processing</p>
            </div>
            
            <div class="consent-controls">
              ${Object.entries(this.getConsentTypes()).map(([type, description]) => `
                <div class="consent-item">
                  <div class="consent-info">
                    <strong>${this.formatConsentType(type)}</strong>
                    <p>${description}</p>
                  </div>
                  <div class="consent-control">
                    <label class="toggle-switch">
                      <input type="checkbox" 
                             ${this.isConsentGranted(consentStatus, type) ? 'checked' : ''}
                             onchange="newsletterDashboard.updateConsent('${type}', this.checked)">
                      <span class="toggle-slider"></span>
                    </label>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Data Retention -->
          <div class="privacy-card">
            <div class="card-header">
              <h4>Data Retention Policy</h4>
              <p class="text-muted">How long we keep your data</p>
            </div>
            
            <div class="retention-info">
              ${Object.entries(privacySettings).map(([type, policy]) => `
                <div class="retention-item">
                  <div class="retention-type">${this.formatDataType(type)}</div>
                  <div class="retention-policy">${policy}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Privacy Rights -->
          <div class="privacy-card">
            <div class="card-header">
              <h4>Your Privacy Rights</h4>
              <p class="text-muted">GDPR rights and how to exercise them</p>
            </div>
            
            <div class="rights-list">
              <div class="right-item">
                <div class="right-icon">📋</div>
                <div class="right-content">
                  <strong>Right to Access</strong>
                  <p>Get a copy of your personal data</p>
                  <button class="btn btn-sm btn-outline" onclick="newsletterDashboard.requestDataAccess()">
                    Request Data
                  </button>
                </div>
              </div>
              
              <div class="right-item">
                <div class="right-icon">✏️</div>
                <div class="right-content">
                  <strong>Right to Rectification</strong>
                  <p>Correct inaccurate personal data</p>
                  <button class="btn btn-sm btn-outline" onclick="newsletterDashboard.requestDataCorrection()">
                    Request Correction
                  </button>
                </div>
              </div>
              
              <div class="right-item">
                <div class="right-icon">🗑️</div>
                <div class="right-content">
                  <strong>Right to Erasure</strong>
                  <p>Delete your personal data</p>
                  <button class="btn btn-sm btn-outline btn-danger" onclick="newsletterDashboard.requestDataErasure()">
                    Delete My Data
                  </button>
                </div>
              </div>
              
              <div class="right-item">
                <div class="right-icon">📦</div>
                <div class="right-content">
                  <strong>Right to Portability</strong>
                  <p>Export your data in portable format</p>
                  <button class="btn btn-sm btn-outline" onclick="newsletterDashboard.requestDataExport()">
                    Export Data
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Utility methods
  getStatusIcon(status) {
    const icons = {
      'draft': '📝',
      'scheduled': '⏰',
      'sending': '📤',
      'sent': '✅',
      'failed': '❌'
    };
    return icons[status] || '❓';
  }

  getActivityIcon(type) {
    const icons = {
      'open': '📧',
      'click': '👆',
      'subscribe': '➕',
      'unsubscribe': '➖',
      'bounce': '⚠️'
    };
    return icons[type] || '•';
  }

  formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  formatTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  }

  getConsentTypes() {
    return {
      'necessary': 'Essential for newsletter delivery',
      'personalization': 'AI-powered content personalization',
      'analytics': 'Engagement analytics and optimization',
      'marketing': 'Marketing communications and promotions'
    };
  }

  formatConsentType(type) {
    const formatted = {
      'necessary': 'Necessary',
      'personalization': 'Personalization',
      'analytics': 'Analytics',
      'marketing': 'Marketing'
    };
    return formatted[type] || type;
  }

  formatDataType(type) {
    const formatted = {
      'consent_records': 'Consent Records',
      'preference_data': 'Preference Data',
      'audit_logs': 'Audit Logs',
      'analytics_data': 'Analytics Data'
    };
    return formatted[type] || type;
  }

  isConsentGranted(consentStatus, type) {
    return consentStatus.some(consent => 
      consent.consent_type === type && consent.granted
    );
  }

  // Event handlers and interactions will be added in the next part
  showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-pane').forEach(tab => {
      tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.querySelector(`[onclick="newsletterDashboard.showTab('${tabName}')"]`).classList.add('active');
  }

  destroy() {
    if (this.websocket) {
      this.websocket.close();
    }
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }
    super.destroy();
  }
}

// Global instance
let newsletterDashboard = null;

// Initialize newsletter dashboard
function initializeNewsletterDashboard(container) {
  newsletterDashboard = new NewsletterDashboard(container);
  return newsletterDashboard;
}
