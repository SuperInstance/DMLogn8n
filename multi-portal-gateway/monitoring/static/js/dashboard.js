// DMLogn8n Monitoring Dashboard JavaScript

class Dashboard {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.currentSection = 'overview';
        this.refreshInterval = null;
        this.data = {
            system: {},
            agents: {},
            business: {},
            alerts: []
        };

        this.init();
    }

    async init() {
        console.log('Initializing DMLogn8n Dashboard...');

        // Initialize WebSocket connection
        this.initWebSocket();

        // Load initial data
        await this.loadInitialData();

        // Setup charts
        this.setupCharts();

        // Start auto-refresh
        this.startAutoRefresh();

        // Setup event listeners
        this.setupEventListeners();

        console.log('Dashboard initialized successfully');
    }

    initWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.initWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'initial_data':
                this.data = data.data;
                this.updateDashboard();
                break;
            case 'metrics_update':
                Object.assign(this.data, data.data);
                this.updateDashboard();
                break;
            case 'alert':
                this.handleNewAlert(data.data);
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.querySelector('.pulse');
        if (connected) {
            statusElement.classList.add('bg-green-400');
            statusElement.classList.remove('bg-red-400');
        } else {
            statusElement.classList.add('bg-red-400');
            statusElement.classList.remove('bg-green-400');
        }
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/dashboard/summary');
            const data = await response.json();
            this.data = data;
            this.updateDashboard();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    setupCharts() {
        // System Performance Chart
        const systemCtx = document.getElementById('systemPerformanceChart').getContext('2d');
        this.charts.systemPerformance = new Chart(systemCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU Usage (%)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Memory Usage (%)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // User Activity Chart
        const userCtx = document.getElementById('userActivityChart').getContext('2d');
        this.charts.userActivity = new Chart(userCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Active Users',
                    data: [],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Initialize other charts as needed
        this.setupAgentCharts();
        this.setupSystemCharts();
        this.setupBusinessCharts();
        this.setupAICharts();
        this.setupDatabaseCharts();
    }

    setupAgentCharts() {
        const throughputCtx = document.getElementById('agentThroughputChart');
        if (throughputCtx) {
            this.charts.agentThroughput = new Chart(throughputCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Requests/sec',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        const responseTimeCtx = document.getElementById('agentResponseTimeChart');
        if (responseTimeCtx) {
            this.charts.agentResponseTime = new Chart(responseTimeCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    setupSystemCharts() {
        const resourceCtx = document.getElementById('resourceUsageChart');
        if (resourceCtx) {
            this.charts.resourceUsage = new Chart(resourceCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Free'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['rgba(255, 99, 132, 0.8)', 'rgba(54, 162, 235, 0.8)'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        const networkCtx = document.getElementById('networkIOChart');
        if (networkCtx) {
            this.charts.networkIO = new Chart(networkCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Bytes Sent',
                            data: [],
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Bytes Received',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    setupBusinessCharts() {
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            this.charts.revenue = new Chart(revenueCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Daily Revenue ($)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        const engagementCtx = document.getElementById('engagementChart');
        if (engagementCtx) {
            this.charts.engagement = new Chart(engagementCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['Stories', 'Characters', 'Worlds', 'Sessions'],
                    datasets: [{
                        label: 'Engagement Score',
                        data: [85, 72, 68, 90],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 205, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    }

    setupAICharts() {
        const performanceCtx = document.getElementById('modelPerformanceChart');
        if (performanceCtx) {
            this.charts.modelPerformance = new Chart(performanceCtx.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: ['Accuracy', 'Speed', 'Cost', 'Reliability', 'Scalability'],
                    datasets: [{
                        label: 'GPT-4',
                        data: [95, 70, 40, 90, 85],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    }, {
                        label: 'Claude',
                        data: [90, 85, 60, 95, 80],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }

        const costsCtx = document.getElementById('aiCostsChart');
        if (costsCtx) {
            this.charts.aiCosts = new Chart(costsCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Cost per Hour ($)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    setupDatabaseCharts() {
        const dbPerformanceCtx = document.getElementById('dbPerformanceChart');
        if (dbPerformanceCtx) {
            this.charts.dbPerformance = new Chart(dbPerformanceCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Query Time (ms)',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Connections',
                            data: [],
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        const queryStatsCtx = document.getElementById('queryStatsChart');
        if (queryStatsCtx) {
            this.charts.queryStats = new Chart(queryStatsCtx.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
                    datasets: [{
                        data: [60, 20, 15, 5],
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(255, 205, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
    }

    setupEventListeners() {
        // Time range selector
        const timeRange = document.getElementById('timeRange');
        if (timeRange) {
            timeRange.addEventListener('change', (e) => {
                this.changeTimeRange(e.target.value);
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshData();
                        break;
                    case '1':
                        e.preventDefault();
                        this.showSection('overview');
                        break;
                    case '2':
                        e.preventDefault();
                        this.showSection('agents');
                        break;
                    case '3':
                        e.preventDefault();
                        this.showSection('system');
                        break;
                }
            }
        });
    }

    startAutoRefresh() {
        // Refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000);

        // Keep WebSocket alive with ping every 30 seconds
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    async refreshData() {
        try {
            const response = await fetch('/api/dashboard/summary');
            const data = await response.json();
            this.data = data;
            this.updateDashboard();
            this.updateLastRefreshTime();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    updateDashboard() {
        this.updateOverviewMetrics();
        this.updateCharts();
        this.updateTables();
        this.updateAlerts();
        this.updateLastRefreshTime();
    }

    updateOverviewMetrics() {
        // Update key metrics
        const metrics = this.data.system_metrics || {};

        this.updateMetric('activeUsers', metrics.active_users || 0);
        this.updateMetric('cpuUsage', `${metrics.cpu_usage || 0}%`);
        this.updateMetric('memoryUsage', `${metrics.memory_usage || 0}%`);
        this.updateMetric('activeAlerts', this.data.alerts?.active_alerts || 0);

        // Update progress bars
        this.updateProgressBar('cpuBar', metrics.cpu_usage || 0);
        this.updateProgressBar('memoryBar', metrics.memory_usage || 0);
    }

    updateMetric(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateProgressBar(id, percentage) {
        const element = document.getElementById(id);
        if (element) {
            element.style.width = `${Math.min(percentage, 100)}%`;

            // Change color based on percentage
            if (percentage > 80) {
                element.classList.add('bg-red-600');
                element.classList.remove('bg-green-600', 'bg-yellow-600');
            } else if (percentage > 60) {
                element.classList.add('bg-yellow-600');
                element.classList.remove('bg-green-600', 'bg-red-600');
            } else {
                element.classList.add('bg-green-600');
                element.classList.remove('bg-yellow-600', 'bg-red-600');
            }
        }
    }

    updateCharts() {
        // Update system performance chart
        if (this.charts.systemPerformance && this.data.system_metrics) {
            const now = new Date().toLocaleTimeString();
            const cpu = this.data.system_metrics.cpu_usage || 0;
            const memory = this.data.system_metrics.memory_usage || 0;

            // Keep only last 20 data points
            if (this.charts.systemPerformance.data.labels.length > 20) {
                this.charts.systemPerformance.data.labels.shift();
                this.charts.systemPerformance.data.datasets[0].data.shift();
                this.charts.systemPerformance.data.datasets[1].data.shift();
            }

            this.charts.systemPerformance.data.labels.push(now);
            this.charts.systemPerformance.data.datasets[0].data.push(cpu);
            this.charts.systemPerformance.data.datasets[1].data.push(memory);
            this.charts.systemPerformance.update('none');
        }

        // Update user activity chart
        if (this.charts.userActivity && this.data.business_metrics) {
            const users = this.data.business_metrics.active_users || 0;
            const hour = new Date().getHours();

            // Simplified - in real implementation, this would be more sophisticated
            this.charts.userActivity.data.datasets[0].data = [users];
            this.charts.userActivity.update('none');
        }
    }

    updateTables() {
        this.updateAgentsTable();
        this.updateAIModelsTable();
    }

    updateAgentsTable() {
        const tbody = document.getElementById('agentsTableBody');
        if (!tbody) return;

        // Mock data - in real implementation, this would come from the API
        const agents = [
            {
                id: 'dungeon_master_1',
                type: 'Dungeon Master',
                status: 'active',
                throughput: 45,
                responseTime: 234,
                errorRate: 0.02
            },
            {
                id: 'dialogue_engine_1',
                type: 'Dialogue Engine',
                status: 'active',
                throughput: 120,
                responseTime: 156,
                errorRate: 0.01
            },
            {
                id: 'world_builder_1',
                type: 'World Builder',
                status: 'busy',
                throughput: 25,
                responseTime: 450,
                errorRate: 0.05
            }
        ];

        tbody.innerHTML = agents.map(agent => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${agent.id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${agent.type}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        agent.status === 'active' ? 'bg-green-100 text-green-800' :
                        agent.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                    }">
                        ${agent.status}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${agent.throughput}/s</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${agent.responseTime}ms</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(agent.errorRate * 100).toFixed(2)}%</td>
            </tr>
        `).join('');
    }

    updateAIModelsTable() {
        const tbody = document.getElementById('aiModelsTableBody');
        if (!tbody) return;

        // Mock data
        const models = [
            {
                name: 'GPT-4',
                type: 'Language Model',
                latency: 2.3,
                accuracy: 95,
                cost: 0.50,
                status: 'active'
            },
            {
                name: 'Claude-3',
                type: 'Language Model',
                latency: 1.8,
                accuracy: 92,
                cost: 0.35,
                status: 'active'
            },
            {
                name: 'DALL-E',
                type: 'Image Generation',
                latency: 5.2,
                accuracy: 88,
                cost: 0.80,
                status: 'busy'
            }
        ];

        tbody.innerHTML = models.map(model => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${model.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${model.type}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${model.latency}s</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${model.accuracy}%</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${model.cost}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        model.status === 'active' ? 'bg-green-100 text-green-800' :
                        model.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                    }">
                        ${model.status}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    updateAlerts() {
        this.updateRecentAlerts();
        this.updateAlertsList();
    }

    updateRecentAlerts() {
        const container = document.getElementById('recentAlerts');
        if (!container) return;

        // Mock alerts
        const alerts = [
            {
                severity: 'critical',
                title: 'High CPU Usage',
                description: 'CPU usage is above 90%',
                time: '2 minutes ago'
            },
            {
                severity: 'warning',
                title: 'Agent Response Time',
                description: 'Dungeon Master agent response time is elevated',
                time: '5 minutes ago'
            },
            {
                severity: 'info',
                title: 'New User Registration',
                description: 'User registration spike detected',
                time: '10 minutes ago'
            }
        ];

        container.innerHTML = alerts.map(alert => `
            <div class="border-l-4 p-4 alert-${alert.severity}">
                <div class="flex">
                    <div class="flex-1">
                        <p class="text-sm font-medium">
                            ${alert.title}
                        </p>
                        <p class="text-sm text-gray-600">
                            ${alert.description}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0">
                        <span class="text-xs text-gray-500">${alert.time}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateAlertsList() {
        const container = document.getElementById('alertsList');
        if (!container) return;

        // Similar to recent alerts but more detailed
        this.updateRecentAlerts(); // For now, reuse the same method
    }

    updateLastRefreshTime() {
        const element = document.getElementById('lastUpdated');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    changeTimeRange(range) {
        console.log('Changing time range to:', range);
        // In real implementation, this would fetch data for the specified time range
        this.refreshData();
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.dashboard-section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        const selectedSection = document.getElementById(`${sectionName}-section`);
        if (selectedSection) {
            selectedSection.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[href="#${sectionName}"]`).classList.add('active');

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        try {
            switch (section) {
                case 'agents':
                    await this.loadAgentsData();
                    break;
                case 'system':
                    await this.loadSystemData();
                    break;
                case 'business':
                    await this.loadBusinessData();
                    break;
                case 'ai':
                    await this.loadAIData();
                    break;
                case 'alerts':
                    await this.loadAlertsData();
                    break;
                case 'database':
                    await this.loadDatabaseData();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${section} data:`, error);
        }
    }

    async loadAgentsData() {
        try {
            const response = await fetch('/api/dashboard/agents');
            const data = await response.json();
            // Update agents section with data
        } catch (error) {
            console.error('Error loading agents data:', error);
        }
    }

    async loadSystemData() {
        try {
            const response = await fetch('/api/dashboard/system');
            const data = await response.json();
            // Update system section with data
            this.updateSystemInfo(data);
        } catch (error) {
            console.error('Error loading system data:', error);
        }
    }

    async loadBusinessData() {
        try {
            const response = await fetch('/api/dashboard/business');
            const data = await response.json();
            // Update business section with data
        } catch (error) {
            console.error('Error loading business data:', error);
        }
    }

    async loadAIData() {
        // Load AI models data
        this.updateAIModelsTable();
    }

    async loadAlertsData() {
        try {
            const response = await fetch('/api/alerts/active');
            const alerts = await response.json();
            // Update alerts section with data
        } catch (error) {
            console.error('Error loading alerts data:', error);
        }
    }

    async loadDatabaseData() {
        // Load database data
        this.updateDatabaseInfo();
    }

    updateSystemInfo(data) {
        const cpuInfo = document.getElementById('cpuInfo');
        if (cpuInfo && data.metrics) {
            cpuInfo.innerHTML = `
                <div class="flex justify-between">
                    <span>Cores:</span>
                    <span>${data.metrics.cpu_cores || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span>Usage:</span>
                    <span>${data.metrics.cpu_usage || 0}%</span>
                </div>
                <div class="flex justify-between">
                    <span>Temperature:</span>
                    <span>${data.metrics.cpu_temp || 'N/A'}°C</span>
                </div>
            `;
        }

        const memoryInfo = document.getElementById('memoryInfo');
        if (memoryInfo && data.metrics) {
            memoryInfo.innerHTML = `
                <div class="flex justify-between">
                    <span>Total:</span>
                    <span>${data.metrics.memory_total || 'N/A'} GB</span>
                </div>
                <div class="flex justify-between">
                    <span>Used:</span>
                    <span>${data.metrics.memory_used || 0} GB</span>
                </div>
                <div class="flex justify-between">
                    <span>Available:</span>
                    <span>${data.metrics.memory_available || 'N/A'} GB</span>
                </div>
            `;
        }

        const diskInfo = document.getElementById('diskInfo');
        if (diskInfo && data.metrics) {
            diskInfo.innerHTML = `
                <div class="flex justify-between">
                    <span>Total:</span>
                    <span>${data.metrics.disk_total || 'N/A'} GB</span>
                </div>
                <div class="flex justify-between">
                    <span>Used:</span>
                    <span>${data.metrics.disk_used || 0} GB</span>
                </div>
                <div class="flex justify-between">
                    <span>Free:</span>
                    <span>${data.metrics.disk_free || 'N/A'} GB</span>
                </div>
            `;
        }
    }

    updateDatabaseInfo() {
        // Update database metrics
        this.updateMetric('dbConnections', '45/100');
        this.updateMetric('queryRate', '1,234/s');
        this.updateMetric('cacheHitRate', '94.2%');
    }

    handleNewAlert(alert) {
        // Show notification for new alert
        this.showNotification(alert.title, alert.description, alert.severity);

        // Update alerts display
        this.updateAlerts();
    }

    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg max-w-sm alert-${type} z-50`;
        notification.innerHTML = `
            <div class="flex">
                <div class="flex-1">
                    <p class="font-medium">${title}</p>
                    <p class="text-sm mt-1">${message}</p>
                </div>
                <button class="ml-4 text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    showError(message) {
        this.showNotification('Error', message, 'critical');
    }
}

// Global functions for onclick handlers
window.showSection = function(sectionName) {
    window.dashboard.showSection(sectionName);
};

window.refreshData = function() {
    window.dashboard.refreshData();
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, reduce refresh frequency
        if (window.dashboard.refreshInterval) {
            clearInterval(window.dashboard.refreshInterval);
        }
    } else {
        // Page is visible, resume normal refresh
        window.dashboard.startAutoRefresh();
        window.dashboard.refreshData();
    }
});