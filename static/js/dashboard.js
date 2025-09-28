/**
 * Trading Bot Dashboard - JavaScript
 * Modular structure: domRefs, utils, state, ui
 */

// ============================================================================
// 1) DOM REFERENCES (domRefs)
// ============================================================================
const domRefs = {
    // Charts
    equityChart: null,
    winLossChart: null,
    portfolioChart: null,
    
    // Global elements
    globalAlert: null,
    syncBanner: null,
    
    // Portfolio elements
    portfolioValue: null,
    totalBalance: null,
    availableBalance: null,
    dailyPnl: null,
    openPositions: null,
    portfolioTbody: null,
    portfolioLegend: null,
    
    // Bot activity elements
    botUptime: null,
    decisionFrequency: null,
    nextCheck: null,
    botActivityTbody: null,
    
    // Performance elements
    marketAnalysisBar: null,
    riskAssessmentBar: null,
    executionSpeedBar: null,
    
    // System elements
    lastUpdateTime: null,
    totalAlerts: null,
    criticalAlerts: null,
    tradingOpportunities: null
};

// ============================================================================
// 2) UTILITIES (utils)
// ============================================================================
const utils = {
    // Formatters
    fmt: new Intl.NumberFormat('nl-NL'),
    fmtCurrency: new Intl.NumberFormat('nl-NL', { style: 'currency', currency: 'EUR' }),
    
    formatCurrency(v) { 
        return this.isFinite(v) ? this.fmtCurrency.format(v) : '—'; 
    },
    
    formatPercent(v, digits = 1) { 
        return this.isFinite(v) ? `${v.toFixed(digits)}%` : '—'; 
    },
    
    safeNumber(v, def = 0) { 
        const n = Number(v); 
        return Number.isFinite(n) ? n : def; 
    },
    
    isFinite(v) {
        return typeof v === 'number' && Number.isFinite(v);
    },
    
    // DOM helpers
    safeUpdateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        } else {
            console.warn(`Element with id '${id}' not found`);
        }
    },
    
    safeUpdateElements(elements) {
        Object.entries(elements).forEach(([id, value]) => {
            if (id && id.trim() !== '') {
                this.safeUpdateElement(id, value);
            }
        });
    },
    
    renderEmptyState(container, message = 'Geen data beschikbaar') {
        if (container) {
            container.innerHTML = `
                <div class="p-3 text-center text-muted border rounded-3">
                    ${message}
                </div>`;
        }
    },
    
    ensureChartDataOrPlaceholder(chart, labels, data, placeholderLabel = 'Geen data') {
        if (!chart) return;
        
        if (!data?.length || data.every(v => v === 0 || v == null)) {
            chart.data.labels = [placeholderLabel];
            chart.data.datasets[0].data = [1];
            chart.data.datasets[0].backgroundColor = ['#adb5bd'];
        } else {
            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
        }
        chart.update();
    },
    
    // Error handling
    async withTry(asyncFn, onError) {
        try { 
            return await asyncFn(); 
        } catch (e) {
            console.error(e);
            onError?.(e);
            // Only show error if it's a real connection error, not just missing data
            if (domRefs.globalAlert && e.message && e.message.includes('fetch')) {
                domRefs.globalAlert.innerHTML = `
                    <div class="alert alert-warning d-flex align-items-center" role="alert">
                        <i class="fa-solid fa-triangle-exclamation me-2"></i>
                        <div>Kon data niet ophalen. Probeer later opnieuw.</div>
                    </div>`;
            } else if (domRefs.globalAlert) {
                // Clear any existing alerts for data loading issues
                domRefs.globalAlert.innerHTML = '';
            }
            return null;
        }
    }
};

// ============================================================================
// 3) STATE MANAGEMENT (state)
// ============================================================================
const state = {
    lastSyncAt: null, // ISO string
    dataFreshnessMin: 0, // integer, minuten
    system: {
        apiConnected: false,
        piConnected: false,
        autoRefresh: true
    },
    portfolio: {},
    positions: {},
    ml: {},
    risk: {},
    alerts: []
};

// ============================================================================
// 4) UI RENDERERS (ui)
// ============================================================================
const ui = {
    renderSyncBanner() {
        if (!domRefs.syncBanner) return;
        
        const last = state.lastSyncAt ? new Date(state.lastSyncAt) : null;
        const mins = state.dataFreshnessMin;
        
        if (last) {
            domRefs.syncBanner.innerHTML = `
                Laatste update: ${last.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                <span class="text-muted ms-2">(${mins} min geleden)</span>
            `;
        } else {
            domRefs.syncBanner.innerHTML = 'Nooit gesynchroniseerd';
        }
        if (domRefs.syncBanner && domRefs.syncBanner.style) domRefs.syncBanner.style.display = 'block';
    },
    
    renderStatusBadge(element, status) {
        if (!element) return;
        
        const statusMap = {
            'online': { text: 'Online', class: 'badge bg-success' },
            'offline': { text: 'Offline', class: 'badge bg-danger' },
            'warning': { text: 'Warning', class: 'badge bg-warning' },
            'error': { text: 'Error', class: 'badge bg-danger' }
        };
        
        const statusInfo = statusMap[status] || statusMap['offline'];
        element.textContent = statusInfo.text;
        element.className = statusInfo.class;
    }
};

// ============================================================================
// GLOBAL VARIABLES & CONFIGURATION
// ============================================================================
let autoRefreshInterval = null;
let dataFreshnessInterval = null;
let isSyncing = false;
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
const API_BASE = '/api';

// ============================================================================
// GLOBAL INITIALIZATION
// ============================================================================

/**
 * Initialize DOM references
 */
function initializeDOMReferences() {
    // Global elements
    domRefs.globalAlert = document.getElementById('global-alert');
    domRefs.syncBanner = document.getElementById('sync-banner');
    
    // Portfolio elements
    domRefs.portfolioValue = document.getElementById('portfolio-value');
    domRefs.totalBalance = document.getElementById('total-balance');
    domRefs.availableBalance = document.getElementById('available-balance');
    domRefs.dailyPnl = document.getElementById('daily-pnl');
    domRefs.openPositions = document.getElementById('open-positions');
    domRefs.portfolioTbody = document.getElementById('portfolio-tbody');
    domRefs.portfolioLegend = document.getElementById('portfolio-legend');
    
    // Bot activity elements
    domRefs.botUptime = document.getElementById('bot-uptime');
    domRefs.decisionFrequency = document.getElementById('decision-frequency');
    domRefs.nextCheck = document.getElementById('next-check');
    domRefs.botActivityTbody = document.getElementById('bot-activity-tbody');
    
    // Performance elements
    domRefs.marketAnalysisBar = document.getElementById('market-analysis-bar');
    domRefs.riskAssessmentBar = document.getElementById('risk-assessment-bar');
    domRefs.executionSpeedBar = document.getElementById('execution-speed-bar');
    
    // System elements
    domRefs.lastUpdateTime = document.getElementById('last-update-time');
    domRefs.totalAlerts = document.getElementById('total-alerts');
    domRefs.criticalAlerts = document.getElementById('critical-alerts');
    domRefs.tradingOpportunities = document.getElementById('trading-opportunities');
    
    console.log('✅ DOM references initialized');
}

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Bootstrap tooltips (fallback for existing elements)
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });
    
    console.log('✅ Bootstrap components initialized');
}

// ============================================================================
// CHART INITIALIZATION
// ============================================================================

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Equity Curve Chart
    const equityCtx = document.getElementById('equityChart')?.getContext('2d');
    if (equityCtx) {
        domRefs.equityChart = new Chart(equityCtx, {
        type: 'line',
        data: {
                labels: ['Start'],
            datasets: [{
                    label: 'Portfolio Saldo',
                    data: [1000],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
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
                    display: true,
                    title: {
                        display: true,
                            text: 'Saldo (€)'
                    },
                    ticks: {
                        callback: function(value) {
                                return '€' + value.toLocaleString();
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
    }

    // Win/Loss Chart
    const winLossCtx = document.getElementById('winLossChart')?.getContext('2d');
    if (winLossCtx) {
        domRefs.winLossChart = new Chart(winLossCtx, {
        type: 'doughnut',
        data: {
            labels: ['Winning Trades', 'Losing Trades'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#28a745', '#dc3545'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

    // Portfolio Allocation Chart
    const portfolioCtx = document.getElementById('portfolioChart')?.getContext('2d');
    if (portfolioCtx) {
        domRefs.portfolioChart = new Chart(portfolioCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1',
                        '#fd7e14', '#20c997', '#e83e8c', '#6c757d', '#17a2b8'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        display: false // We'll show custom legend
                    }
                }
            }
        });
    }
    
    console.log('✅ Charts initialized');
}

// ============================================================================
// DATA LOADING
// ============================================================================

/**
 * Load all dashboard data
 */
async function loadAllData() {
    return await utils.withTry(async () => {
        console.log('📊 Dashboard data laden...');
        console.log('🔧 API_BASE:', API_BASE);
        
        // Update state
        state.lastSyncAt = new Date().toISOString();
        state.dataFreshnessMin = 0;
        
        // Load data in parallel with error handling for each
        const promises = [
            fetchData('/trading-performance').catch(e => { console.error('Trading performance error:', e); return {error: 'Trading performance failed'}; }),
            fetchData('/portfolio').catch(e => { console.error('Portfolio error:', e); return {error: 'Portfolio failed'}; }),
            fetchData('/portfolio-details').catch(e => { console.error('Portfolio details error:', e); return {error: 'Portfolio details failed'}; }),
            fetchData('/equity-curve').catch(e => { console.error('Equity curve error:', e); return {error: 'Equity curve failed'}; }),
            fetchData('/bot-status').catch(e => { console.error('Bot status error:', e); return {error: 'Bot status failed'}; }),
            fetchData('/bot-activity').catch(e => { console.error('Bot activity error:', e); return {error: 'Bot activity failed'}; }),
            fetchData('/ml-insights').catch(e => { console.error('ML insights error:', e); return {error: 'ML insights failed'}; }),
            fetchData('/market-intelligence').catch(e => { console.error('Market intelligence error:', e); return {error: 'Market intelligence failed'}; }),
            fetchData('/real-time-alerts').catch(e => { console.error('Real-time alerts error:', e); return {error: 'Real-time alerts failed'}; }),
            fetchData('/ml-models').catch(e => { console.error('ML models error:', e); return {error: 'ML models failed'}; })
        ];
        
        const [tradingData, portfolioData, portfolioDetails, equityData, statusData, botActivityData, mlInsights, marketIntelligence, realTimeAlerts, mlModelsData] = await Promise.all(promises);
        
        // Update state
        state.portfolio = portfolioData;
        state.positions = portfolioDetails;
        state.ml = mlInsights;
        state.risk = marketIntelligence;
        state.alerts = realTimeAlerts;
        state.mlModels = mlModelsData;
        
        // Update UI with data (each function handles errors internally)
        ui.updateTradingPerformance(tradingData);
        ui.updatePortfolioOverview(portfolioData);
        ui.updatePortfolioDetails(portfolioDetails);
        ui.updateEquityCurve(equityData);
        ui.updateBotStatus(statusData);
        ui.updateBotActivity(botActivityData);
        ui.updateMLInsights(mlInsights);
        ui.updateMarketIntelligence(marketIntelligence);
        ui.updateRealTimeAlerts(realTimeAlerts);
        ui.updateMLModels(mlModelsData);
        
        // Update sync timestamp
        state.lastSyncAt = new Date().toISOString();
        state.dataFreshnessMin = 0;
        
        // Update sync banner
        ui.renderSyncBanner();
        
        // Start data freshness timer
        startDataFreshnessTimer();
        
        console.log('✅ Dashboard data loaded');
    });
}

/**
 * Fetch data from API endpoint
 */
async function fetchData(endpoint) {
    try {
        const url = API_BASE + endpoint;
        console.log('🔧 Fetching:', url);
        const response = await fetch(url);
        console.log('🔧 Response status:', response.status, response.statusText);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        console.log('🔧 Data received for', endpoint, ':', data);
        return data;
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

// ============================================================================
// UI RENDERERS (continued)
// ============================================================================

// Extend ui object with renderer functions
Object.assign(ui, {
    updateTradingPerformance(data) {
    if (data.error) {
        console.warn('Trading performance data error:', data.error);
        return;
    }
    
        // Safely update elements that exist
        utils.safeUpdateElements({
            'total-pnl': utils.formatCurrency(data.total_pnl),
            'win-rate': utils.formatPercent(data.win_rate),
            'total-trades': data.total_trades,
            'winning-trades': data.winning_trades,
            'losing-trades': data.losing_trades,
            'avg-win': utils.formatCurrency(data.avg_win),
            'avg-loss': utils.formatCurrency(data.avg_loss),
            'profit-factor': data.profit_factor
        });
    
    // Update win/loss chart
        if (domRefs.winLossChart) {
            domRefs.winLossChart.data.datasets[0].data = [data.winning_trades, data.losing_trades];
            domRefs.winLossChart.update();
        }
        
        // Update P&L color based on value (safely)
    const pnlElement = document.getElementById('total-pnl');
        if (pnlElement) {
    pnlElement.className = data.total_pnl >= 0 ? 'text-success' : 'text-danger';
}
    },
    
    updatePortfolioOverview(data) {
        console.log('Updating portfolio overview with data:', data);
        
    if (data.error) {
        console.warn('Portfolio data error:', data.error);
            // Show error state instead of "Laden..."
            utils.safeUpdateElements({
                'portfolio-value': '⚠️ Geen data',
                'total-balance': '⚠️ Geen data',
                'available-balance': '⚠️ Geen data',
                'daily-pnl': '⚠️ Geen data',
                'open-positions': '⚠️ Geen data',
                'open-positions-detail': '⚠️ Geen data',
                'portfolio-pnl': '⚠️ Geen data'
            });
        return;
    }
    
    // Check if this is demo mode
    if (data.demo_mode) {
        console.log('Portfolio in demo mode - showing start capital');
    }
    
        // Update KPIs with color logic
        this.updateKPIs(data);
        
        // Update other portfolio elements
        utils.safeUpdateElements({
            'total-balance': utils.formatCurrency(data.total_balance),
            'available-balance': utils.formatCurrency(data.available_balance),
            'open-positions-detail': data.open_positions,
            'portfolio-pnl': utils.formatCurrency(data.total_pnl),
            'win-rate': utils.formatPercent(data.win_rate || 0),
            'sharpe-ratio': (data.sharpe_ratio || 0).toFixed(1),
            'api-status': 'Connected',
            'data-freshness': '2 min',
            'memory-usage': '65%'
        });
    },
    
    updatePortfolioDetails(data) {
        if (data.error) {
            console.warn('Portfolio details error:', data.error);
            this.updatePortfolioTable([]);
            this.updatePortfolioChart([]);
            return;
        }
        
        const holdings = data.holdings || [];
        this.updatePortfolioTable(holdings);
        this.updatePortfolioChart(holdings);
    },
    
    updatePortfolioTable(holdings) {
        if (!domRefs.portfolioTbody) return;
        
        if (holdings.length === 0) {
            domRefs.portfolioTbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Geen portfolio bezittingen beschikbaar</td></tr>';
            return;
        }
        
        domRefs.portfolioTbody.innerHTML = holdings.map(holding => {
            const pnlClass = holding.pnl >= 0 ? 'text-success' : 'text-danger';
            const statusClass = holding.status === 'open' ? 'badge bg-success' : 'badge bg-secondary';
            
            return `
                <tr>
                    <td><strong>${holding.symbol}</strong></td>
                    <td><span class="badge ${holding.side === 'buy' ? 'bg-success' : 'bg-danger'}">${holding.side}</span></td>
                    <td>${holding.quantity_filled.toFixed(4)}</td>
                    <td><span class="${statusClass}">${holding.status}</span></td>
                    <td class="${pnlClass}">${utils.formatCurrency(holding.pnl)}</td>
                    <td>${utils.formatCurrency(holding.balance)} <small class="text-muted">(${holding.percentage.toFixed(1)}%)</small></td>
                </tr>
            `;
        }).join('');
    },
    
    updatePortfolioChart(holdings) {
        if (!domRefs.portfolioChart) return;
        
        if (holdings.length === 0) {
            utils.ensureChartDataOrPlaceholder(domRefs.portfolioChart, ['Geen data'], [1], 'Geen data');
            this.updatePortfolioLegend([]);
            return;
        }
        
        // Prepare chart data
        const labels = holdings.map(h => h.symbol);
        const data = holdings.map(h => h.balance);
        const colors = domRefs.portfolioChart.data.datasets[0].backgroundColor.slice(0, holdings.length);
        
        // Update chart
        domRefs.portfolioChart.data.labels = labels;
        domRefs.portfolioChart.data.datasets[0].data = data;
        domRefs.portfolioChart.data.datasets[0].backgroundColor = colors;
        domRefs.portfolioChart.update();
        
        // Update custom legend
        this.updatePortfolioLegend(holdings);
    },
    
    updatePortfolioLegend(holdings) {
        if (!domRefs.portfolioLegend) return;
        
        if (holdings.length === 0) {
            domRefs.portfolioLegend.innerHTML = '<div class="text-center text-muted">Geen holdings</div>';
            return;
        }
        
        const colors = domRefs.portfolioChart.data.datasets[0].backgroundColor;
        
        domRefs.portfolioLegend.innerHTML = holdings.map((holding, index) => {
            const color = colors[index] || '#6c757d';
            return `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <div class="d-flex align-items-center">
                        <div class="me-2" style="width: 12px; height: 12px; background-color: ${color}; border-radius: 2px;"></div>
                        <span class="small">${holding.symbol}</span>
                    </div>
                    <div class="text-end">
                        <div class="small fw-bold">${utils.formatCurrency(holding.balance)}</div>
                        <div class="small text-muted">${holding.percentage.toFixed(1)}%</div>
                    </div>
                </div>
            `;
        }).join('');
    },
    
    updateEquityCurve(data) {
    if (data.error) {
        console.warn('Equity curve data error:', data.error);
        return;
    }
    
        if (domRefs.equityChart && data.labels && data.data) {
            utils.ensureChartDataOrPlaceholder(domRefs.equityChart, data.labels, data.data, 'Startkapitaal');
        }
    },
    
    updateBotStatus(data) {
        if (data.error) {
            console.warn('Bot status data error:', data.error);
            return;
        }
        
        // Update Pi connection status (safely)
        const statusBadge = document.getElementById('pi-status');
        
        if (statusBadge) {
            if (data.pi_online) {
                this.renderStatusBadge(statusBadge, 'online');
            } else {
                this.renderStatusBadge(statusBadge, 'offline');
            }
        }
        
        // Update system status (safely)
        utils.safeUpdateElement('last-sync', data.last_sync || 'Onbekend');
        utils.safeUpdateElement('data-files', data.data_files || 0);
        
        // Update last update time in header
        utils.safeUpdateElement('last-update-time', data.last_sync || 'Onbekend');
    },
    
    updateBotActivity(data) {
        console.log('Updating bot activity with data:', data);
        
        if (data.error) {
            console.warn('Bot activity data error:', data.error);
            this.updateBotActivityTable([]);
            this.updateBotPerformanceMetrics({});
            return;
        }

        try {
            // Update bot activity metrics
            utils.safeUpdateElements({
                'bot-uptime': data.uptime || '0h 0m',
                'decision-frequency': data.decision_frequency || '0/hour',
                'next-check': data.next_check || '--:--'
            });

            // Update activity timeline (combine with decisions)
            this.updateBotActivityTable(data.activity_timeline || [], data.recent_decisions || []);

            // Update performance metrics
            this.updateBotPerformanceMetrics(data.performance_metrics || {});

            // Update performance bars
            this.updatePerformanceBars(data);
            
            // Update decision thresholds
            this.updateDecisionThresholds(data.decision_thresholds || {});
            
            
            console.log('Bot activity updated successfully');
        } catch (error) {
            console.error('Error updating bot activity:', error);
        }
    },
    
    updateBotActivityTable(activities, decisions = []) {
        if (!domRefs.botActivityTbody) return;
        
        // Convert decisions to activity format
        const decisionActivities = decisions.map(decision => ({
            timestamp: decision.timestamp,
            action: decision.action,
            decision: decision.decision,
            reason: decision.reason,
            status: decision.status
        }));
        
        // Combine activities and decisions, sort by timestamp (newest first)
        const allActivities = [...activities, ...decisionActivities]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10); // Show max 10 items
        
        if (allActivities.length === 0) {
            domRefs.botActivityTbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Geen bot activiteit geregistreerd</td></tr>';
            return;
        }
        
        domRefs.botActivityTbody.innerHTML = allActivities.map(activity => {
            const statusClass = this.getStatusClass(activity.status);
            const timeFormatted = this.formatTime(activity.timestamp || activity.time);
            
            return `
                <tr>
                    <td><small>${timeFormatted}</small></td>
                    <td><span class="badge bg-primary">${activity.action}</span></td>
                    <td>${activity.decision}</td>
                    <td><small class="text-muted">${activity.reason}</small></td>
                    <td><span class="badge ${statusClass}">${activity.status}</span></td>
                </tr>
            `;
        }).join('');
    },
    
    updateBotPerformanceMetrics(metrics) {
        utils.safeUpdateElements({
            'success-rate': utils.formatPercent(metrics.success_rate || 0),
            'avg-decision-time': (metrics.avg_decision_time || 0) + 'ms'
        });
    },
    
    updatePerformanceBars(data) {
        // Market Analysis
        const marketAnalysis = data.market_analysis || {score: 0, description: "Marktanalyse", details: "Geen data", status: "Unknown"};
        const marketScore = typeof marketAnalysis === 'object' ? marketAnalysis.score : marketAnalysis;
        utils.safeUpdateElement('market-analysis-label', marketAnalysis.description || "Marktanalyse");
        utils.safeUpdateElement('market-analysis-score', marketScore + '%');
        const marketBar = document.getElementById('market-analysis-bar');
        if (marketBar) {
            marketBar.style.width = marketScore + '%';
            marketBar.className = `progress-bar ${this.getProgressBarClass(marketScore)}`;
        }
        utils.safeUpdateElement('market-analysis-details', marketAnalysis.details || "Geen data");
        
        // Risk Assessment
        const riskAssessment = data.risk_assessment || {score: 0, description: "Risico Beoordeling", details: "Geen data", status: "Unknown"};
        const riskScore = typeof riskAssessment === 'object' ? riskAssessment.score : riskAssessment;
        utils.safeUpdateElement('risk-assessment-label', riskAssessment.description || "Risico Beoordeling");
        utils.safeUpdateElement('risk-assessment-score', riskScore + '%');
        const riskBar = document.getElementById('risk-assessment-bar');
        if (riskBar) {
            riskBar.style.width = riskScore + '%';
            riskBar.className = `progress-bar ${this.getRiskBarClass(riskScore)}`;
        }
        utils.safeUpdateElement('risk-assessment-details', riskAssessment.details || "Geen data");
        
        // Execution Speed
        const executionSpeed = data.execution_speed || {score: 0, description: "Data Sync Snelheid", details: "Geen data", status: "Unknown"};
        const speedScore = typeof executionSpeed === 'object' ? executionSpeed.score : executionSpeed;
        utils.safeUpdateElement('execution-speed-label', executionSpeed.description || "Data Sync Snelheid");
        utils.safeUpdateElement('execution-speed-score', speedScore + '%');
        const speedBar = document.getElementById('execution-speed-bar');
        if (speedBar) {
            speedBar.style.width = speedScore + '%';
            speedBar.className = `progress-bar ${this.getSpeedBarClass(speedScore)}`;
        }
        utils.safeUpdateElement('execution-speed-details', executionSpeed.details || "Geen data");
    },
    
    updateDecisionThresholds(thresholds) {
        console.log('Updating decision thresholds:', thresholds);
        
        if (!thresholds || Object.keys(thresholds).length === 0) {
            console.log('No thresholds data available');
            return;
        }
        
        try {
            utils.safeUpdateElements({
                'price-threshold': thresholds.price_change_threshold || '2.5%',
                'volume-threshold': thresholds.volume_threshold || '1000',
                'rsi-oversold': thresholds.rsi_oversold || '30',
                'rsi-overbought': thresholds.rsi_overbought || '70',
                'stop-loss': thresholds.stop_loss || '3%',
                'take-profit': thresholds.take_profit || '5%',
                'max-position': thresholds.max_position_size || '10%',
                'risk-per-trade': thresholds.risk_per_trade || '2%'
            });
            
            console.log('Decision thresholds updated successfully');
        } catch (error) {
            console.error('Error updating decision thresholds:', error);
        }
    },
    
    
    updateMLInsights(data) {
        console.log('Updating ML insights:', data);
        
        if (data.error) {
            console.warn('ML insights data error:', data.error);
            return;
        }
        
        try {
            const modelPerf = data.model_performance || {};
            const signalQuality = data.signal_quality || {};
            
            // Update model performance
            utils.safeUpdateElements({
                'predictions-today': modelPerf.predictions_today || '0',
                'model-accuracy': utils.formatPercent(modelPerf.model_accuracy || 0),
                'ml-confidence': utils.formatPercent(modelPerf.avg_confidence || 0),
                'signal-strength': signalQuality.signal_strength || '0',
                'regime-status': signalQuality.regime_status || 'Unknown',
                'market-volatility': signalQuality.market_volatility || 'Unknown',
                'trend-direction': signalQuality.trend_direction || 'Unknown'
            });
            
            // Update feature importance
            if (modelPerf.feature_importance) {
                const container = document.getElementById('feature-importance');
                if (container) {
                    container.innerHTML = modelPerf.feature_importance.map(feature => `
                        <div class="d-flex justify-content-between mb-1">
                            <span>${feature.feature}</span>
                            <span>${(feature.importance * 100).toFixed(0)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 6px;">
                            <div class="progress-bar" style="width: ${feature.importance * 100}%"></div>
                        </div>
                    `).join('');
                }
            }
            
            console.log('ML insights updated successfully');
        } catch (error) {
            console.error('Error updating ML insights:', error);
        }
    },
    
    updateMarketIntelligence(data) {
        console.log('Updating market intelligence:', data);
        
        if (data.error) {
            console.warn('Market intelligence data error:', data.error);
            return;
        }
        
        try {
            const marketOverview = data.market_overview || {};
            const riskManagement = data.risk_management || {};
            
            // Update market overview
            utils.safeUpdateElements({
                'volatility-index': marketOverview.volatility_index || '0',
                'volume-analysis': marketOverview.volume_analysis || 'Unknown',
                'risk-rejects': riskManagement.risk_rejects || '0',
                'daily-loss': utils.formatCurrency(riskManagement.daily_loss || 0)
            });
            
            const positionSizes = riskManagement.position_sizes || {};
            utils.safeUpdateElements({
                'max-position': positionSizes.max_position || '0%',
                'avg-position': positionSizes.avg_position || '0%',
                'total-exposure': positionSizes.total_exposure || '0%'
            });
            
            const correlationMatrix = riskManagement.correlation_matrix || {};
            utils.safeUpdateElements({
                'btc-eth-correlation': (correlationMatrix.btc_eth || 0).toFixed(2),
                'btc-ada-correlation': (correlationMatrix.btc_ada || 0).toFixed(2),
                'eth-ada-correlation': (correlationMatrix.eth_ada || 0).toFixed(2)
            });
            
            // Update top movers
            if (marketOverview.top_movers) {
                const container = document.getElementById('top-movers');
                if (container) {
                    container.innerHTML = marketOverview.top_movers.map(mover => `
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span><strong>${mover.symbol}</strong></span>
                            <span class="${mover.change.startsWith('+') ? 'text-success' : 'text-danger'}">${mover.change}</span>
                            <small class="text-muted">${mover.volume}</small>
                        </div>
                    `).join('');
                }
            }
            
            // Update universe selection
            this.updateUniverseSelection(marketOverview.universe_selection || []);
            
            console.log('Market intelligence updated successfully');
        } catch (error) {
            console.error('Error updating market intelligence:', error);
        }
    },
    
    updateUniverseSelection(coins) {
        // Find the universe selection container by ID
        const universeContainer = document.getElementById('universe-selection');
        if (!universeContainer) {
            console.warn('Universe selection container not found');
            return;
        }
        
        if (coins.length === 0) {
            universeContainer.innerHTML = '<span class="text-muted">Geen coins geselecteerd</span>';
            return;
        }
        
        // Create badges for each coin
        universeContainer.innerHTML = coins.map(coin => 
            `<span class="badge bg-primary">${coin}</span>`
        ).join('');
        
        console.log('Universe selection updated with coins:', coins);
    },
    
    updateRealTimeAlerts(data) {
        console.log('Updating real-time alerts:', data);
        
        if (data.error) {
            console.warn('Real-time alerts data error:', data.error);
            return;
        }
        
        try {
            // Update alert count
            utils.safeUpdateElement('total-alerts', data.total_alerts || '0');
            
            // Update top critical alert banner
            if (data.critical_alerts) {
                this.updateCriticalAlertBanner(data.critical_alerts);
            }
            
            // Update critical alerts
            if (data.critical_alerts && domRefs.criticalAlerts) {
                domRefs.criticalAlerts.innerHTML = data.critical_alerts.map(alert => `
                    <div class="alert alert-${this.getAlertClass(alert.severity)}">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-${this.getAlertIcon(alert.type)}"></i> ${alert.message}</span>
                            <small class="text-muted">${alert.timestamp}</small>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update trading opportunities
            if (data.trading_opportunities && domRefs.tradingOpportunities) {
                domRefs.tradingOpportunities.innerHTML = data.trading_opportunities.map(opportunity => `
                    <div class="alert alert-warning">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-signal"></i> ${opportunity.message}</span>
                            <small class="text-muted">${opportunity.timestamp}</small>
                        </div>
                        <small class="text-muted">Confidence: ${opportunity.confidence}% - Status: ${opportunity.status}</small>
                    </div>
                `).join('');
            }
            
            console.log('Real-time alerts updated successfully');
        } catch (error) {
            console.error('Error updating real-time alerts:', error);
        }
    },
    
    // Helper functions
    getStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'success':
            case 'completed':
            case 'active':
            case 'online':
            case 'veilig':
            case 'succesvol':
                return 'bg-success';
            case 'warning':
            case 'pending':
            case 'monitoring':
            case 'geen actie':
                return 'bg-warning';
            case 'error':
            case 'failed':
            case 'offline':
                return 'bg-danger';
            case 'info':
            case 'neutral':
                return 'bg-info';
            default:
                return 'bg-secondary';
        }
    },
    
    getProgressBarClass(score) {
        if (score >= 80) return 'bg-success';
        if (score >= 60) return 'bg-info';
        if (score >= 40) return 'bg-warning';
        return 'bg-danger';
    },
    
    getRiskBarClass(score) {
        if (score <= 30) return 'bg-success';  // Low risk
        if (score <= 60) return 'bg-warning';  // Medium risk
        return 'bg-danger';  // High risk
    },
    
    getSpeedBarClass(percentage) {
        if (percentage >= 80) return 'bg-success';  // Fast
        if (percentage >= 60) return 'bg-info';     // Medium
        if (percentage >= 40) return 'bg-warning';  // Slow
        return 'bg-danger';  // Very slow
    },
    
    getAlertClass(severity) {
        switch (severity) {
            case 'high': return 'danger';
            case 'medium': return 'warning';
            case 'low': return 'info';
            default: return 'info';
        }
    },
    
    getAlertIcon(type) {
        switch (type) {
            case 'Error': return 'exclamation-triangle';
            case 'Warning': return 'exclamation-circle';
            case 'Info': return 'info-circle';
            default: return 'info-circle';
        }
    },
    
    formatTime(timeString) {
        if (!timeString) return '--:--';
        
        try {
            const date = new Date(timeString);
            if (isNaN(date.getTime())) {
                return timeString; // Return original if can't parse
            }
            
            // Format as Dutch date and time
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Europe/Amsterdam'
            };
            
            return date.toLocaleString('nl-NL', options);
        } catch (error) {
            return timeString;
        }
    },
    
    formatDateTime(dateString) {
        if (!dateString) return 'Nooit';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Ongeldige Datum';
            }
            
            // Format as Dutch date and time
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Europe/Amsterdam'
            };
            
            return date.toLocaleString('nl-NL', options);
        } catch (error) {
            return 'Ongeldige Datum';
        }
    }
});

// ============================================================================
// AUTO-REFRESH & SYNC
// ============================================================================

/**
 * Start auto-refresh timer
 */
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        console.log('🔄 Auto-refreshing dashboard data...');
        loadAllData();
    }, REFRESH_INTERVAL);
    
    console.log(`⏰ Auto-refresh started (${REFRESH_INTERVAL / 1000}s interval)`);
}

/**
 * Start data freshness timer
 */
function startDataFreshnessTimer() {
    if (dataFreshnessInterval) {
        clearInterval(dataFreshnessInterval);
    }
    
    dataFreshnessInterval = setInterval(() => {
        if (state.lastSyncAt) {
            const now = new Date();
            const lastSync = new Date(state.lastSyncAt);
            const diffMinutes = Math.floor((now - lastSync) / (1000 * 60));
            state.dataFreshnessMin = diffMinutes;
            ui.renderSyncBanner();
        }
    }, 60000); // Update every minute
}

/**
 * Manual sync trigger
 */
async function syncNow() {
    if (isSyncing) {
        console.log('⏳ Sync already in progress...');
        return;
    }
    
    isSyncing = true;
    const syncButton = document.querySelector('button[onclick="syncNow()"]');
    const icon = syncButton?.querySelector('i');
    
    try {
        // Show syncing state
        if (icon) {
        icon.className = 'fas fa-sync-alt syncing';
        }
        if (syncButton) {
        syncButton.disabled = true;
        }
        
        console.log('🔄 Triggering manual sync...');
        
        // Trigger sync
        const response = await fetch(API_BASE + '/sync-now', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ Manual sync completed');
            showSuccess('Synchronisatie succesvol voltooid');
            
            // Update sync timestamp immediately
            state.lastSyncAt = new Date().toISOString();
            state.dataFreshnessMin = 0;
            ui.renderSyncBanner();
            
            // Reload data after sync
            setTimeout(() => {
                loadAllData();
            }, 1000);
        } else {
            console.error('❌ Manual sync failed:', result.message);
            showError('Synchronisatie mislukt: ' + result.message);
        }
        
    } catch (error) {
        console.error('❌ Error during manual sync:', error);
        showError('Synchronisatie fout: ' + error);
    } finally {
        // Reset button state
        if (icon) {
        icon.className = 'fas fa-sync-alt';
        }
        if (syncButton) {
        syncButton.disabled = false;
        }
        isSyncing = false;
    }
}

// ============================================================================
// ALERT FUNCTIONS
// ============================================================================

/**
 * Show success message
 */
function showSuccess(message) {
    showAlert(message, 'success');
}

/**
 * Show error message
 */
function showError(message) {
    showAlert(message, 'danger');
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

/**
 * Handle page visibility change
 */
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('📱 Page hidden - pausing auto-refresh');
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
    } else {
        console.log('📱 Page visible - resuming auto-refresh');
        startAutoRefresh();
        loadAllData(); // Load fresh data when page becomes visible
    }
});

/**
 * Handle window resize
 */
window.addEventListener('resize', function() {
    // Resize charts when window resizes
    if (domRefs.equityChart) {
        domRefs.equityChart.resize();
    }
    if (domRefs.winLossChart) {
        domRefs.winLossChart.resize();
    }
    if (domRefs.portfolioChart) {
        domRefs.portfolioChart.resize();
    }
});

// ============================================================================
// PANEL COLLAPSE FUNCTIONALITY
// ============================================================================

/**
 * Initialize panel collapse functionality
 */
function initializePanelCollapse() {
    console.log('🔧 Initializing panel collapse...');
    
    // Event delegation for panel headers
    document.addEventListener('click', (e) => {
        const header = e.target.closest('.panel-header');
        if (!header) {
            console.log('🔧 Click not on panel header');
            return;
        }
        
        console.log('🔧 Panel header clicked!');
        const panel = header.closest('.panel');
        const expanded = header.getAttribute('aria-expanded') === 'true';
        
        console.log('🔧 Panel expanded:', expanded, '->', !expanded);
        header.setAttribute('aria-expanded', String(!expanded));
        panel.setAttribute('aria-expanded', String(!expanded));
    });
    
    // Global controls
    const collapseAll = document.getElementById('collapse-all');
    const expandAll = document.getElementById('expand-all');
    
    if (collapseAll) {
        collapseAll.addEventListener('click', () => {
            console.log('🔧 Collapse all clicked');
            setAllPanels(false);
        });
    }
    
    if (expandAll) {
        expandAll.addEventListener('click', () => {
            console.log('🔧 Expand all clicked');
            setAllPanels(true);
        });
    }
    
    console.log('✅ Panel collapse functionality initialized');
}

/**
 * Set all panels to expanded or collapsed
 */
function setAllPanels(expand = true) {
    document.querySelectorAll('.panel').forEach(p => {
        p.setAttribute('aria-expanded', String(expand));
        p.querySelector('.panel-header')?.setAttribute('aria-expanded', String(expand));
    });
}

// ============================================================================
// KPI COLOR LOGIC
// ============================================================================

/**
 * Determine KPI class based on metric and value
 */
function kpiClassFromMetric(key, value) {
    const T = {
        // Portfolio metrics
        portfolio: { ok: 1000, warn: 500 },     // portfolio waarde
        pnl: { ok: 0, warn: -100 },             // positief = goed
        positions: { ok: 5, warn: 10, invert: true }, // minder posities = beter
        risk: { ok: 3, warn: 5, invert: true }, // lager = beter
        
        // Performance metrics
        winrate: { ok: 0.6, warn: 0.5 },       // ≥60% groen, 50–60% oranje, <50% rood
        sharpe: { ok: 1.2, warn: 0.8 },
        drawdown: { ok: 0.1, warn: 0.2, invert: true }, // lager = beter
        
        // ML metrics
        accuracy: { ok: 0.8, warn: 0.6 },      // model accuracy
        confidence: { ok: 0.8, warn: 0.6 },    // model confidence
        latency: { ok: 100, warn: 500, invert: true }, // lager = beter
        
        // System metrics
        uptime: { ok: 24, warn: 12 },          // hours uptime
        errors: { ok: 0, warn: 5, invert: true }, // lager = beter
        alerts: { ok: 0, warn: 3, invert: true } // lager = beter
    };
    
    const t = T[key];
    if (!t) return 'ok'; // default to ok if no threshold defined
    
    if (t.invert) {
        if (value <= t.ok) return 'ok';
        if (value <= t.warn) return 'warn';
        return 'risk';
    } else {
        if (value >= t.ok) return 'ok';
        if (value >= t.warn) return 'warn';
        return 'risk';
    }
}

/**
 * Render KPI with appropriate color class
 */
function renderKpi(el, { key, label, value, fmt }) {
    if (!el) return;
    
    const state = kpiClassFromMetric(key, value);
    el.className = `kpi ${state}`;
    el.innerHTML = `
        <div class="label">${label}</div>
        <div class="value">${fmt ? fmt(value) : value}</div>
    `;
}

// ============================================================================
// TOOLTIP FUNCTIONALITY
// ============================================================================

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
    console.log('🔧 Initializing tooltips...');
    let tooltipEl;
    
    function showTooltip(target) {
        const text = target.getAttribute('data-tooltip');
        if (!text) {
            console.log('🔧 No tooltip text found');
            return;
        }
        
        console.log('🔧 Showing tooltip:', text.substring(0, 50) + '...');
        tooltipEl ??= Object.assign(document.createElement('div'), { className: 'tooltip' });
        tooltipEl.textContent = text;
        document.body.appendChild(tooltipEl);
        
        const r = target.getBoundingClientRect();
        
        // Simple positioning - always below the button
        const left = r.left + r.width / 2;
        const top = r.bottom + 8;
        
        tooltipEl.style.left = `${left}px`;
        tooltipEl.style.top = `${top}px`;
        tooltipEl.style.transform = 'translate(-50%, 0)';
        
        requestAnimationFrame(() => tooltipEl.classList.add('visible'));
    }
    
    function hideTooltip() {
        tooltipEl?.classList.remove('visible');
    }
    
    document.addEventListener('mouseover', e => {
        const t = e.target.closest('.info-btn');
        if (t) {
            console.log('🔧 Info button hovered');
            showTooltip(t);
        }
    });
    
    document.addEventListener('mouseout', e => {
        if (e.target.closest('.info-btn')) {
            console.log('🔧 Info button unhovered');
            hideTooltip();
        }
    });
    
    console.log('✅ Tooltip functionality initialized');
}

// ============================================================================
// ENHANCED UI RENDERERS
// ============================================================================

// Extend ui object with KPI rendering
Object.assign(ui, {
    updateKPIs(data) {
        // Portfolio KPI
        renderKpi(document.getElementById('kpi-portfolio'), {
            key: 'portfolio',
            label: '💰 Portfolio Waarde',
            value: data.total_balance || 1000,
            fmt: v => utils.formatCurrency(v)
        });
        
        // Daily P&L KPI
        renderKpi(document.getElementById('kpi-daily-pnl'), {
            key: 'pnl',
            label: '📈 Dagelijkse P&L',
            value: data.daily_pnl || 0,
            fmt: v => utils.formatCurrency(v)
        });
        
        // Open Positions KPI
        renderKpi(document.getElementById('kpi-positions'), {
            key: 'positions',
            label: '📊 Open Posities',
            value: data.open_positions || 0,
            fmt: v => v.toString()
        });
        
        // Risk Score KPI
        renderKpi(document.getElementById('kpi-risk'), {
            key: 'risk',
            label: '⚠️ Risico Score',
            value: data.risk_score || 3.5,
            fmt: v => v.toFixed(1)
        });
    }
});

// ============================================================================
// ENHANCED INITIALIZATION
// ============================================================================

// Update the main initialization to include new functionality
const originalDOMContentLoaded = document.addEventListener;
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Enhanced Trading Bot Dashboard...');
    
    // Initialize DOM references
    initializeDOMReferences();
    
    // Initialize Bootstrap components
    initializeBootstrapComponents();
    
    // Initialize new functionality
    initializePanelCollapse();
    initializeTooltips();
    
    // Initialize charts
    initializeCharts();
    
    // Load initial data
    loadAllData();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Initial critical alert banner if data already present
    if (state.alerts && state.alerts.critical_alerts) {
        ui.updateCriticalAlertBanner(state.alerts.critical_alerts);
    }

    console.log('✅ Enhanced Dashboard initialized');
    console.log('🔧 Testing API connection...');
    
    // Test API connection
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            console.log('🔧 API Health Check:', data);
        })
        .catch(error => {
            console.error('🔧 API Health Check Failed:', error);
        });
});

// ============================================================================
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// ============================================================================
window.syncNow = syncNow;
window.setAllPanels = setAllPanels;
window.renderKpi = renderKpi;
window.showModelDetails = showModelDetails;
window.updateMLModels = ui.updateMLModels;
window.updateCriticalAlertBanner = ui.updateCriticalAlertBanner;

// ============================================================================
// END OF MODULAR DASHBOARD.JS
// ============================================================================
