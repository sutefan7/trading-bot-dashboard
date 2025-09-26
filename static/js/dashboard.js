/**
 * Trading Bot Dashboard - JavaScript
 * Handles real-time data updates and chart rendering
 */

// Global variables
let equityChart = null;
let winLossChart = null;
let portfolioChart = null;
let autoRefreshInterval = null;
let isSyncing = false;

// Configuration
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes
const API_BASE = '/api';

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Trading Bot Dashboard...');
    console.log('✅ JavaScript file loaded successfully');
    
    // Initialize dashboard functionality
    console.log('✅ Dashboard JavaScript loaded successfully');
    
    // Initialize charts
    initializeCharts();
    
    // Initialize Bootstrap tooltips
    initializeTooltips();
    
    // Test collapse functionality
    testCollapseFunctionality();
    
    // Load initial data
    loadAllData();
    
    // Start auto-refresh
    startAutoRefresh();
    
    console.log('✅ Dashboard initialized');
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    console.log('Initializing Bootstrap tooltips...');
    try {
        // Initialize all tooltips
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        console.log('Found tooltip elements:', tooltipTriggerList.length);
        
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        console.log('Initialized tooltips:', tooltipList.length);
    } catch (error) {
        console.error('Error initializing tooltips:', error);
    }
}

/**
 * Test collapse functionality
 */
function testCollapseFunctionality() {
    console.log('Testing collapse functionality...');
    try {
        const collapseElements = document.querySelectorAll('[data-bs-toggle="collapse"]');
        console.log('Found collapse elements:', collapseElements.length);
        
        collapseElements.forEach((element, index) => {
            console.log(`Collapse element ${index}:`, element.getAttribute('data-bs-target'));
            
            // Add manual click handler as fallback
            element.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('data-bs-target');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    if (targetElement.classList.contains('show')) {
                        targetElement.classList.remove('show');
                        this.querySelector('i').classList.remove('fa-chevron-up');
                        this.querySelector('i').classList.add('fa-chevron-down');
                        console.log('Collapsed:', targetId);
                    } else {
                        targetElement.classList.add('show');
                        this.querySelector('i').classList.remove('fa-chevron-down');
                        this.querySelector('i').classList.add('fa-chevron-up');
                        console.log('Expanded:', targetId);
                    }
                }
            });
        });
    } catch (error) {
        console.error('Error testing collapse functionality:', error);
    }
}

/**
 * Initialize Chart.js charts
 */
function initializeCharts() {
    // Equity Curve Chart
    const equityCtx = document.getElementById('equityChart').getContext('2d');
    equityChart = new Chart(equityCtx, {
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

    // Win/Loss Chart
    const winLossCtx = document.getElementById('winLossChart').getContext('2d');
    winLossChart = new Chart(winLossCtx, {
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

    // Portfolio Allocation Chart
    const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(portfolioCtx, {
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

/**
 * Load all dashboard data
 */
async function loadAllData() {
    try {
        console.log('📊 Dashboard data laden...');
        
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
            fetchData('/real-time-alerts').catch(e => { console.error('Real-time alerts error:', e); return {error: 'Real-time alerts failed'}; })
        ];
        
        const [tradingData, portfolioData, portfolioDetails, equityData, statusData, botActivityData, mlInsights, marketIntelligence, realTimeAlerts] = await Promise.all(promises);
        
        // Update UI with data (each function handles errors internally)
        updateTradingPerformance(tradingData);
        updatePortfolioOverview(portfolioData);
        updatePortfolioDetails(portfolioDetails);
        updateEquityCurve(equityData);
        updateBotStatus(statusData);
        updateBotActivity(botActivityData);
        updateMLInsights(mlInsights);
        updateMarketIntelligence(marketIntelligence);
        updateRealTimeAlerts(realTimeAlerts);
        
        // Update last update time
        updateLastUpdateTime();
        
        console.log('✅ Dashboard data loaded');
        
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        showError('Dashboard data laden mislukt: ' + error.message);
    }
}

/**
 * Fetch data from API endpoint
 */
async function fetchData(endpoint) {
    try {
        const response = await fetch(API_BASE + endpoint);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

/**
 * Safely update element text content
 */
function safeUpdateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    } else {
        console.warn(`Element with id '${id}' not found`);
    }
}

/**
 * Safely update multiple elements
 */
function safeUpdateElements(elements) {
    Object.entries(elements).forEach(([id, value]) => {
        if (id && id.trim() !== '') {
            safeUpdateElement(id, value);
        } else {
            console.warn('Empty or invalid element ID:', id);
        }
    });
}

/**
 * Update trading performance section
 */
function updateTradingPerformance(data) {
    if (data.error) {
        console.warn('Trading performance data error:', data.error);
        return;
    }
    
    // Safely update elements that exist
    safeUpdateElements({
        'total-pnl': formatCurrency(data.total_pnl),
        'win-rate': data.win_rate + '%',
        'total-trades': data.total_trades,
        'winning-trades': data.winning_trades,
        'losing-trades': data.losing_trades,
        'avg-win': formatCurrency(data.avg_win),
        'avg-loss': formatCurrency(data.avg_loss),
        'profit-factor': data.profit_factor
    });
    
    // Update win/loss chart
    if (winLossChart) {
        winLossChart.data.datasets[0].data = [data.winning_trades, data.losing_trades];
        winLossChart.update();
    }
    
    // Update P&L color based on value (safely)
    const pnlElement = document.getElementById('total-pnl');
    if (pnlElement) {
    pnlElement.className = data.total_pnl >= 0 ? 'text-success' : 'text-danger';
    }
}

/**
 * Update portfolio overview section
 */
function updatePortfolioOverview(data) {
    console.log('Updating portfolio overview with data:', data);
    
    if (data.error) {
        console.warn('Portfolio data error:', data.error);
        // Show error state instead of "Laden..."
        safeUpdateElements({
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
    
    // Direct update for debugging
    const portfolioValue = document.getElementById('portfolio-value');
    if (portfolioValue) {
        portfolioValue.textContent = formatCurrency(data.total_balance);
        console.log('Updated portfolio-value to:', formatCurrency(data.total_balance));
    } else {
        console.error('Element portfolio-value not found');
    }
    
    const openPositions = document.getElementById('open-positions');
    if (openPositions) {
        openPositions.textContent = data.open_positions;
        console.log('Updated open-positions to:', data.open_positions);
    } else {
        console.error('Element open-positions not found');
    }
    
    const openPositionsDetail = document.getElementById('open-positions-detail');
    if (openPositionsDetail) {
        openPositionsDetail.textContent = data.open_positions;
        console.log('Updated open-positions-detail to:', data.open_positions);
    } else {
        console.error('Element open-positions-detail not found');
    }
    
    // Force update all open-positions elements
    const allOpenPositions = document.querySelectorAll('[id*="open-positions"]');
    console.log('Found open-positions elements:', allOpenPositions.length);
    allOpenPositions.forEach((el, index) => {
        el.textContent = data.open_positions;
        console.log(`Updated open-positions element ${index} to:`, data.open_positions);
    });
    
    // Safely update other portfolio elements
    safeUpdateElements({
        'total-balance': formatCurrency(data.total_balance),
        'available-balance': formatCurrency(data.available_balance),
        'daily-pnl': formatCurrency(data.daily_pnl || 0),
        'portfolio-pnl': formatCurrency(data.total_pnl),
        'win-rate': (data.win_rate || 0) + '%',
        'sharpe-ratio': (data.sharpe_ratio || 0).toFixed(1),
        'api-status': 'Connected',
        'data-freshness': '2 min',
        'memory-usage': '65%'
    });
}

/**
 * Update portfolio details section
 */
function updatePortfolioDetails(data) {
    if (data.error) {
        console.warn('Portfolio details error:', data.error);
        updatePortfolioTable([]);
        updatePortfolioChart([]);
        return;
    }
    
    const holdings = data.holdings || [];
    updatePortfolioTable(holdings);
    updatePortfolioChart(holdings);
}

/**
 * Update portfolio holdings table
 */
function updatePortfolioTable(holdings) {
    const tbody = document.getElementById('portfolio-tbody');
    
    if (holdings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Geen portfolio bezittingen beschikbaar</td></tr>';
        return;
    }
    
    tbody.innerHTML = holdings.map(holding => {
        const pnlClass = holding.pnl >= 0 ? 'text-success' : 'text-danger';
        const statusClass = holding.status === 'open' ? 'badge bg-success' : 'badge bg-secondary';
        
        return `
            <tr>
                <td><strong>${holding.symbol}</strong></td>
                <td><span class="badge ${holding.side === 'buy' ? 'bg-success' : 'bg-danger'}">${holding.side}</span></td>
                <td>${holding.quantity_filled.toFixed(4)}</td>
                <td><span class="${statusClass}">${holding.status}</span></td>
                <td class="${pnlClass}">${formatCurrency(holding.pnl)}</td>
                <td>${formatCurrency(holding.balance)} <small class="text-muted">(${holding.percentage.toFixed(1)}%)</small></td>
            </tr>
        `;
    }).join('');
}

/**
 * Update portfolio allocation chart
 */
function updatePortfolioChart(holdings) {
    if (!portfolioChart) return;
    
    if (holdings.length === 0) {
        portfolioChart.data.labels = ['No Holdings'];
        portfolioChart.data.datasets[0].data = [1];
        portfolioChart.data.datasets[0].backgroundColor = ['#6c757d'];
        portfolioChart.update();
        updatePortfolioLegend([]);
        return;
    }
    
    // Prepare chart data
    const labels = holdings.map(h => h.symbol);
    const data = holdings.map(h => h.balance);
    const colors = portfolioChart.data.datasets[0].backgroundColor.slice(0, holdings.length);
    
    // Update chart
    portfolioChart.data.labels = labels;
    portfolioChart.data.datasets[0].data = data;
    portfolioChart.data.datasets[0].backgroundColor = colors;
    portfolioChart.update();
    
    // Update custom legend
    updatePortfolioLegend(holdings);
}

/**
 * Update portfolio legend
 */
function updatePortfolioLegend(holdings) {
    const legendDiv = document.getElementById('portfolio-legend');
    
    if (holdings.length === 0) {
        legendDiv.innerHTML = '<div class="text-center text-muted">No holdings to display</div>';
        return;
    }
    
    const colors = portfolioChart.data.datasets[0].backgroundColor;
    
    legendDiv.innerHTML = holdings.map((holding, index) => {
        const color = colors[index] || '#6c757d';
        return `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <div class="d-flex align-items-center">
                    <div class="me-2" style="width: 12px; height: 12px; background-color: ${color}; border-radius: 2px;"></div>
                    <span class="small">${holding.symbol}</span>
                </div>
                <div class="text-end">
                    <div class="small fw-bold">${formatCurrency(holding.balance)}</div>
                    <div class="small text-muted">${holding.percentage.toFixed(1)}%</div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Update equity curve chart
 */
function updateEquityCurve(data) {
    if (data.error) {
        console.warn('Equity curve data error:', data.error);
        return;
    }
    
    if (equityChart && data.labels && data.data) {
        equityChart.data.labels = data.labels;
        equityChart.data.datasets[0].data = data.data;
        equityChart.update();
    }
}

/**
 * Update bot status section
 */
function updateBotStatus(data) {
    if (data.error) {
        console.warn('Bot status data error:', data.error);
        return;
    }
    
    // Update bot status (safely)
    const statusElement = document.getElementById('bot-status');
    const statusBadge = document.getElementById('pi-status');
    
    if (statusElement && statusBadge) {
    if (data.pi_online) {
        statusElement.textContent = 'Online';
        statusElement.className = 'text-success';
        statusBadge.textContent = 'Online';
        statusBadge.className = 'badge bg-success';
    } else {
        statusElement.textContent = 'Offline';
        statusElement.className = 'text-danger';
        statusBadge.textContent = 'Offline';
        statusBadge.className = 'badge bg-danger';
        }
    }
    
    // Update system status (safely)
    safeUpdateElement('last-sync', formatDateTime(data.last_sync));
    safeUpdateElement('data-files', data.data_files);
}

/**
 * Update bot activity section
 */
function updateBotActivity(data) {
    console.log('Updating bot activity with data:', data);
    
    if (data.error) {
        console.warn('Bot activity data error:', data.error);
        updateBotActivityTable([]);
        updateBotPerformanceMetrics({});
        return;
    }

    try {
        // Update bot activity metrics
        const uptimeEl = document.getElementById('bot-uptime');
        const frequencyEl = document.getElementById('decision-frequency');
        const nextCheckEl = document.getElementById('next-check');
        
        if (uptimeEl) uptimeEl.textContent = data.uptime || '0h 0m';
        if (frequencyEl) frequencyEl.textContent = data.decision_frequency || '0/hour';
        if (nextCheckEl) nextCheckEl.textContent = data.next_check || '--:--';

        // Update activity timeline
        updateBotActivityTable(data.activity_timeline || []);

        // Update performance metrics
        updateBotPerformanceMetrics(data.performance_metrics || {});

        // Update performance bars
        updatePerformanceBars(data);
        
        // Update decision thresholds
        updateDecisionThresholds(data.decision_thresholds || {});
        
        // Update recent decisions
        updateRecentDecisions(data.recent_decisions || []);
        
        console.log('Bot activity updated successfully');
    } catch (error) {
        console.error('Error updating bot activity:', error);
    }
}

/**
 * Update bot activity timeline table
 */
function updateBotActivityTable(activities) {
    const tbody = document.getElementById('bot-activity-tbody');
    
    if (activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Geen bot activiteit geregistreerd</td></tr>';
        return;
    }
    
    tbody.innerHTML = activities.map(activity => {
        const statusClass = getStatusClass(activity.status);
        const timeFormatted = formatTime(activity.time);
        
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
}

/**
 * Update bot performance metrics
 */
function updateBotPerformanceMetrics(metrics) {
    safeUpdateElement('success-rate', (metrics.success_rate || 0) + '%');
    safeUpdateElement('avg-decision-time', (metrics.avg_decision_time || 0) + 'ms');
}

/**
 * Update performance bars
 */
function updatePerformanceBars(data) {
    // Market Analysis
    const marketAnalysis = data.market_analysis || {score: 0, description: "Marktanalyse", details: "Geen data", status: "Unknown"};
    const marketScore = typeof marketAnalysis === 'object' ? marketAnalysis.score : marketAnalysis;
    safeUpdateElement('market-analysis-label', marketAnalysis.description || "Marktanalyse");
    safeUpdateElement('market-analysis-score', marketScore + '%');
    const marketBar = document.getElementById('market-analysis-bar');
    if (marketBar) {
        marketBar.style.width = marketScore + '%';
        marketBar.className = `progress-bar ${getProgressBarClass(marketScore)}`;
    }
    safeUpdateElement('market-analysis-details', marketAnalysis.details || "Geen data");
    
    // Risk Assessment
    const riskAssessment = data.risk_assessment || {score: 0, description: "Risico Beoordeling", details: "Geen data", status: "Unknown"};
    const riskScore = typeof riskAssessment === 'object' ? riskAssessment.score : riskAssessment;
    safeUpdateElement('risk-assessment-label', riskAssessment.description || "Risico Beoordeling");
    safeUpdateElement('risk-assessment-score', riskScore + '%');
    const riskBar = document.getElementById('risk-assessment-bar');
    if (riskBar) {
        riskBar.style.width = riskScore + '%';
        riskBar.className = `progress-bar ${getRiskBarClass(riskScore)}`;
    }
    safeUpdateElement('risk-assessment-details', riskAssessment.details || "Geen data");
    
    // Execution Speed
    const executionSpeed = data.execution_speed || {score: 0, description: "Data Sync Snelheid", details: "Geen data", status: "Unknown"};
    const speedScore = typeof executionSpeed === 'object' ? executionSpeed.score : executionSpeed;
    safeUpdateElement('execution-speed-label', executionSpeed.description || "Data Sync Snelheid");
    safeUpdateElement('execution-speed-score', speedScore + '%');
    const speedBar = document.getElementById('execution-speed-bar');
    if (speedBar) {
        speedBar.style.width = speedScore + '%';
        speedBar.className = `progress-bar ${getSpeedBarClass(speedScore)}`;
    }
    safeUpdateElement('execution-speed-details', executionSpeed.details || "Geen data");
}

/**
 * Get status class for activity status
 */
function getStatusClass(status) {
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
}

/**
 * Get progress bar class based on score
 */
function getProgressBarClass(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-info';
    if (score >= 40) return 'bg-warning';
    return 'bg-danger';
}

/**
 * Get risk bar class based on score
 */
function getRiskBarClass(score) {
    if (score <= 30) return 'bg-success';  // Low risk
    if (score <= 60) return 'bg-warning';  // Medium risk
    return 'bg-danger';  // High risk
}

/**
 * Get speed bar class based on percentage
 */
function getSpeedBarClass(percentage) {
    if (percentage >= 80) return 'bg-success';  // Fast
    if (percentage >= 60) return 'bg-info';     // Medium
    if (percentage >= 40) return 'bg-warning';  // Slow
    return 'bg-danger';  // Very slow
}

/**
 * Format time for activity timeline
 */
function formatTime(timeString) {
    if (!timeString) return '--:--';
    
    // If the timeString is already formatted (contains -), return as is
    if (timeString.includes('-') && timeString.includes(':')) {
        return timeString;
    }
    
    try {
        const date = new Date(timeString);
        if (isNaN(date.getTime())) {
            return timeString; // Return original if can't parse
        }
        return date.toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } catch (error) {
        return timeString;
    }
}

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
 * Manual sync trigger
 */
async function syncNow() {
    if (isSyncing) {
        console.log('⏳ Sync already in progress...');
        return;
    }
    
    isSyncing = true;
    const syncButton = document.querySelector('button[onclick="syncNow()"]');
    const icon = syncButton.querySelector('i');
    
    try {
        // Show syncing state
        icon.className = 'fas fa-sync-alt syncing';
        syncButton.disabled = true;
        
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
        showError('Synchronisatie fout: ' + error.message);
    } finally {
        // Reset button state
        icon.className = 'fas fa-sync-alt';
        syncButton.disabled = false;
        isSyncing = false;
    }
}

/**
 * Update last update time
 */
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    safeUpdateElement('last-update-time', timeString);
}

/**
 * Format currency values
 */
function formatCurrency(value) {
    if (value === null || value === undefined) return '€0.00';
    return '€' + parseFloat(value).toLocaleString('nl-NL', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format date/time values
 */
function formatDateTime(dateString) {
    if (!dateString) return 'Never';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (error) {
        return 'Invalid Date';
    }
}

/**
 * Update decision thresholds
 */
function updateDecisionThresholds(thresholds) {
    console.log('Updating decision thresholds:', thresholds);
    
    if (!thresholds || Object.keys(thresholds).length === 0) {
        console.log('No thresholds data available');
        return;
    }
    
    try {
        // Update threshold values
        const priceEl = document.getElementById('price-threshold');
        const volumeEl = document.getElementById('volume-threshold');
        const rsiOversoldEl = document.getElementById('rsi-oversold');
        const rsiOverboughtEl = document.getElementById('rsi-overbought');
        const stopLossEl = document.getElementById('stop-loss');
        const takeProfitEl = document.getElementById('take-profit');
        const maxPositionEl = document.getElementById('max-position');
        const riskPerTradeEl = document.getElementById('risk-per-trade');
        
        if (priceEl) priceEl.textContent = thresholds.price_change_threshold || '2.5%';
        if (volumeEl) volumeEl.textContent = thresholds.volume_threshold || '1000';
        if (rsiOversoldEl) rsiOversoldEl.textContent = thresholds.rsi_oversold || '30';
        if (rsiOverboughtEl) rsiOverboughtEl.textContent = thresholds.rsi_overbought || '70';
        if (stopLossEl) stopLossEl.textContent = thresholds.stop_loss || '3%';
        if (takeProfitEl) takeProfitEl.textContent = thresholds.take_profit || '5%';
        if (maxPositionEl) maxPositionEl.textContent = thresholds.max_position_size || '10%';
        if (riskPerTradeEl) riskPerTradeEl.textContent = thresholds.risk_per_trade || '2%';
        
        console.log('Decision thresholds updated successfully');
    } catch (error) {
        console.error('Error updating decision thresholds:', error);
    }
}

/**
 * Update recent decisions table
 */
function updateRecentDecisions(decisions) {
    console.log('Updating recent decisions:', decisions);
    
    const tbody = document.getElementById('recent-decisions-tbody');
    if (!tbody) {
        console.error('Recent decisions tbody element not found');
        return;
    }
    
    if (decisions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Geen recente besluiten</td></tr>';
        return;
    }
    
    try {
        tbody.innerHTML = decisions.map(decision => {
            const statusClass = getStatusClass(decision.status);
            
            return `
                <tr>
                    <td><small>${decision.timestamp}</small></td>
                    <td><span class="badge bg-primary">${decision.action}</span></td>
                    <td>${decision.decision}</td>
                    <td><span class="badge ${statusClass}">${decision.status}</span></td>
                </tr>
            `;
        }).join('');
        
        console.log('Recent decisions updated successfully');
    } catch (error) {
        console.error('Error updating recent decisions:', error);
    }
}

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
    if (equityChart) {
        equityChart.resize();
    }
    if (winLossChart) {
        winLossChart.resize();
    }
    if (portfolioChart) {
        portfolioChart.resize();
    }
});

/**
 * Update ML Insights section
 */
function updateMLInsights(data) {
    console.log('Updating ML insights:', data);
    
    if (data.error) {
        console.warn('ML insights data error:', data.error);
        return;
    }
    
    try {
        const modelPerf = data.model_performance || {};
        const signalQuality = data.signal_quality || {};
        
        // Update model performance
        safeUpdateElement('predictions-today', modelPerf.predictions_today || '0');
        safeUpdateElement('model-accuracy', (modelPerf.model_accuracy || 0) + '%');
        safeUpdateElement('ml-confidence', (modelPerf.avg_confidence || 0) + '%');
        
        // Update signal quality
        safeUpdateElement('signal-strength', signalQuality.signal_strength || '0');
        safeUpdateElement('regime-status', signalQuality.regime_status || 'Unknown');
        safeUpdateElement('market-volatility', signalQuality.market_volatility || 'Unknown');
        safeUpdateElement('trend-direction', signalQuality.trend_direction || 'Unknown');
        
        // Update feature importance
        if (modelPerf.feature_importance) {
            const container = document.getElementById('feature-importance');
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
        
        console.log('ML insights updated successfully');
    } catch (error) {
        console.error('Error updating ML insights:', error);
    }
}

/**
 * Update Market Intelligence section
 */
function updateMarketIntelligence(data) {
    console.log('Updating market intelligence:', data);
    
    if (data.error) {
        console.warn('Market intelligence data error:', data.error);
        return;
    }
    
    try {
        const marketOverview = data.market_overview || {};
        const riskManagement = data.risk_management || {};
        
        // Update market overview
        safeUpdateElement('volatility-index', marketOverview.volatility_index || '0');
        safeUpdateElement('volume-analysis', marketOverview.volume_analysis || 'Unknown');
        
        // Update risk management
        safeUpdateElement('risk-rejects', riskManagement.risk_rejects || '0');
        safeUpdateElement('daily-loss', formatCurrency(riskManagement.daily_loss || 0));
        
        const positionSizes = riskManagement.position_sizes || {};
        safeUpdateElement('max-position', positionSizes.max_position || '0%');
        safeUpdateElement('avg-position', positionSizes.avg_position || '0%');
        safeUpdateElement('total-exposure', positionSizes.total_exposure || '0%');
        
        const correlationMatrix = riskManagement.correlation_matrix || {};
        safeUpdateElement('btc-eth-correlation', (correlationMatrix.btc_eth || 0).toFixed(2));
        safeUpdateElement('btc-ada-correlation', (correlationMatrix.btc_ada || 0).toFixed(2));
        safeUpdateElement('eth-ada-correlation', (correlationMatrix.eth_ada || 0).toFixed(2));
        
        // Update top movers
        if (marketOverview.top_movers) {
            const container = document.getElementById('top-movers');
            container.innerHTML = marketOverview.top_movers.map(mover => `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span><strong>${mover.symbol}</strong></span>
                    <span class="${mover.change.startsWith('+') ? 'text-success' : 'text-danger'}">${mover.change}</span>
                    <small class="text-muted">${mover.volume}</small>
                </div>
            `).join('');
        }
        
        console.log('Market intelligence updated successfully');
    } catch (error) {
        console.error('Error updating market intelligence:', error);
    }
}

/**
 * Update Real-time Alerts section
 */
function updateRealTimeAlerts(data) {
    console.log('Updating real-time alerts:', data);
    
    if (data.error) {
        console.warn('Real-time alerts data error:', data.error);
        return;
    }
    
    try {
        // Update alert count
        safeUpdateElement('total-alerts', data.total_alerts || '0');
        
        // Update critical alerts
        if (data.critical_alerts) {
            const container = document.getElementById('critical-alerts');
            container.innerHTML = data.critical_alerts.map(alert => `
                <div class="alert alert-${getAlertClass(alert.severity)}">
                    <div class="d-flex justify-content-between">
                        <span><i class="fas fa-${getAlertIcon(alert.type)}"></i> ${alert.message}</span>
                        <small class="text-muted">${alert.timestamp}</small>
                    </div>
                </div>
            `).join('');
        }
        
        // Update trading opportunities
        if (data.trading_opportunities) {
            const container = document.getElementById('trading-opportunities');
            container.innerHTML = data.trading_opportunities.map(opportunity => `
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
}

/**
 * Get alert CSS class based on severity
 */
function getAlertClass(severity) {
    switch (severity) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'info';
    }
}

/**
 * Get alert icon based on type
 */
function getAlertIcon(type) {
    switch (type) {
        case 'Error': return 'exclamation-triangle';
        case 'Warning': return 'exclamation-circle';
        case 'Info': return 'info-circle';
        default: return 'info-circle';
    }
}

// Export functions for global access
window.syncNow = syncNow;
