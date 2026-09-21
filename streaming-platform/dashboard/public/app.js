class StreamingDashboard {
    constructor() {
        this.socket = io();
        this.currentSection = 'overview';
        this.isStreaming = false;
        this.charts = {};
        this.settings = {};

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupSocketListeners();
        this.loadSettings();
        await this.loadInitialData();
        this.initializeCharts();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.dataset.section;
                this.switchSection(section);
            });
        });

        // Stream controls
        document.getElementById('startStreamBtn')?.addEventListener('click', () => this.startStream());
        document.getElementById('stopStreamBtn')?.addEventListener('click', () => this.stopStream());

        // Date range
        document.getElementById('dateRange')?.addEventListener('change', (e) => {
            this.updateDateRange(e.target.value);
        });

        // Content controls
        document.getElementById('generateHighlightsBtn')?.addEventListener('click', () => this.generateHighlights());
        document.getElementById('createThumbnailBtn')?.addEventListener('click', () => this.createThumbnail());

        // Settings
        document.getElementById('testOBSConnection')?.addEventListener('click', () => this.testOBSConnection());

        // Modal
        document.getElementById('closeModal')?.addEventListener('click', () => this.closeModal());
        document.getElementById('modalConfirm')?.addEventListener('click', () => this.closeModal());
    }

    setupSocketListeners() {
        this.socket.on('stream-status', (data) => {
            this.updateStreamStatus(data);
        });

        this.socket.on('viewer-count', (data) => {
            this.updateViewerCount(data);
        });

        this.socket.on('donation-received', (data) => {
            this.handleDonation(data);
        });

        this.socket.on('new-message', (data) => {
            this.addChatMessage(data);
        });

        this.socket.on('scene-changed', (data) => {
            this.updateActiveScene(data.scene);
        });

        this.socket.on('dice-roll', (data) => {
            this.addActivityItem('dice', `${data.playerName} rolled ${data.total} on ${data.diceType}`);
        });

        this.socket.on('poll-created', (data) => {
            this.addActivityItem('poll', `New poll created: ${data.question}`);
        });
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`)?.parentElement.classList.add('active');

        // Update content
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(sectionName)?.classList.add('active');

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(section) {
        switch (section) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'streaming':
                await this.loadStreamingData();
                break;
            case 'engagement':
                await this.loadEngagementData();
                break;
            case 'monetization':
                await this.loadMonetizationData();
                break;
            case 'content':
                await this.loadContentData();
                break;
        }
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/analytics/overview');
            const data = await response.json();

            this.updateOverviewMetrics(data);
            this.updateCharts(data);
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }

    async loadOverviewData() {
        // Already loaded in loadInitialData
    }

    async loadStreamingData() {
        try {
            // Load scenes
            const scenesResponse = await fetch('/api/streaming/scenes');
            const scenesData = await scenesResponse.json();

            this.renderSceneButtons(scenesData.data.scenes);

            // Load stream status
            const statusResponse = await fetch('/api/streaming/status');
            const statusData = await statusResponse.json();

            this.updateStreamStatus(statusData.data);
        } catch (error) {
            console.error('Failed to load streaming data:', error);
        }
    }

    async loadEngagementData() {
        try {
            const response = await fetch('/api/engagement/stats');
            const data = await response.json();

            this.updateEngagementMetrics(data);
        } catch (error) {
            console.error('Failed to load engagement data:', error);
        }
    }

    async loadMonetizationData() {
        try {
            const response = await fetch('/api/monetization/analytics/revenue');
            const data = await response.json();

            this.updateRevenueData(data);
        } catch (error) {
            console.error('Failed to load monetization data:', error);
        }
    }

    async loadContentData() {
        try {
            const response = await fetch('/api/content/highlights');
            const data = await response.json();

            this.renderHighlights(data.data);
        } catch (error) {
            console.error('Failed to load content data:', error);
        }
    }

    updateOverviewMetrics(data) {
        document.getElementById('totalViewers').textContent = this.formatNumber(data.totalViewers || 0);
        document.getElementById('totalRevenue').textContent = `$${this.formatNumber(data.totalRevenue || 0)}`;
        document.getElementById('subscribers').textContent = this.formatNumber(data.subscribers || 0);
        document.getElementById('streamHours').textContent = this.formatNumber(data.streamHours || 0);
    }

    updateStreamStatus(status) {
        const liveStatus = document.getElementById('liveStatus');
        const statusIndicator = liveStatus.querySelector('.status-indicator');
        const statusText = liveStatus.querySelector('.status-text');
        const startBtn = document.getElementById('startStreamBtn');
        const stopBtn = document.getElementById('stopStreamBtn');

        if (status.isLive) {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'LIVE';
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
            this.isStreaming = true;
        } else {
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'OFFLINE';
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            this.isStreaming = false;
        }

        // Update stream metrics
        if (status.bitrate) {
            document.getElementById('bitrate').textContent = `${status.bitrate} kbps`;
        }
        if (status.fps) {
            document.getElementById('fps').textContent = status.fps;
        }
        if (status.droppedFrames !== undefined) {
            document.getElementById('droppedFrames').textContent = status.droppedFrames;
        }
    }

    renderSceneButtons(scenes) {
        const container = document.getElementById('sceneButtons');
        if (!container) return;

        container.innerHTML = '';

        scenes.forEach(scene => {
            const button = document.createElement('button');
            button.className = 'scene-btn';
            button.textContent = scene;
            button.addEventListener('click', () => this.switchScene(scene));
            container.appendChild(button);
        });
    }

    async switchScene(sceneName) {
        try {
            await fetch('/api/streaming/scenes/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ sceneName })
            });

            this.updateActiveScene(sceneName);
        } catch (error) {
            console.error('Failed to switch scene:', error);
        }
    }

    updateActiveScene(sceneName) {
        document.querySelectorAll('.scene-btn').forEach(btn => {
            btn.classList.toggle('active', btn.textContent === sceneName);
        });
    }

    async startStream() {
        try {
            const response = await fetch('/api/streaming/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    platforms: ['twitch', 'youtube'],
                    title: 'Live D&D Session',
                    description: 'Professional D&D streaming',
                    tags: ['dnd', 'tabletop', 'rpg']
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Stream Started', 'Your stream is now live on all platforms!', 'success');
                this.updateStreamStatus({ isLive: true });
            } else {
                this.showNotification('Error', 'Failed to start stream', 'error');
            }
        } catch (error) {
            console.error('Failed to start stream:', error);
            this.showNotification('Error', 'Failed to start stream', 'error');
        }
    }

    async stopStream() {
        try {
            const response = await fetch('/api/streaming/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Stream Stopped', 'Your stream has been ended', 'info');
                this.updateStreamStatus({ isLive: false });
            } else {
                this.showNotification('Error', 'Failed to stop stream', 'error');
            }
        } catch (error) {
            console.error('Failed to stop stream:', error);
            this.showNotification('Error', 'Failed to stop stream', 'error');
        }
    }

    initializeCharts() {
        // Revenue Chart
        const revenueCtx = document.getElementById('revenueChart');
        if (revenueCtx) {
            this.charts.revenue = new Chart(revenueCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Revenue',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Viewer Chart
        const viewerCtx = document.getElementById('viewerChart');
        if (viewerCtx) {
            this.charts.viewer = new Chart(viewerCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Viewers',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Revenue Source Chart
        const revenueSourceCtx = document.getElementById('revenueSourceChart');
        if (revenueSourceCtx) {
            this.charts.revenueSource = new Chart(revenueSourceCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Donations', 'Subscriptions', 'Merchandise', 'Sponsorships'],
                    datasets: [{
                        data: [30, 40, 20, 10],
                        backgroundColor: [
                            '#667eea',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    updateCharts(data) {
        // Update revenue chart
        if (this.charts.revenue && data.revenueData) {
            this.charts.revenue.data.labels = data.revenueData.labels || [];
            this.charts.revenue.data.datasets[0].data = data.revenueData.values || [];
            this.charts.revenue.update();
        }

        // Update viewer chart
        if (this.charts.viewer && data.viewerData) {
            this.charts.viewer.data.labels = data.viewerData.labels || [];
            this.charts.viewer.data.datasets[0].data = data.viewerData.values || [];
            this.charts.viewer.update();
        }
    }

    addChatMessage(message) {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        messageElement.innerHTML = `
            <div class="chat-username">${message.username}</div>
            <div class="chat-text">${message.message}</div>
        `;

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Keep only last 50 messages
        while (chatContainer.children.length > 50) {
            chatContainer.removeChild(chatContainer.firstChild);
        }
    }

    addActivityItem(type, text) {
        const activityList = document.getElementById('activityList');
        if (!activityList) return;

        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';

        const iconMap = {
            'dice': 'fas fa-dice',
            'poll': 'fas fa-poll',
            'donation': 'fas fa-dollar-sign',
            'subscriber': 'fas fa-star',
            'scene': 'fas fa-tv'
        };

        activityItem.innerHTML = `
            <div class="activity-icon">
                <i class="${iconMap[type] || 'fas fa-info'}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${text}</div>
                <div class="activity-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;

        activityList.insertBefore(activityItem, activityList.firstChild);

        // Keep only last 20 activities
        while (activityList.children.length > 20) {
            activityList.removeChild(activityList.lastChild);
        }
    }

    handleDonation(donation) {
        this.addActivityItem('donation', `${donation.donorName} donated $${donation.amount}`);

        // Update metrics
        const currentRevenue = document.getElementById('totalRevenue');
        const currentValue = parseFloat(currentRevenue.textContent.replace('$', '').replace(',', ''));
        currentRevenue.textContent = `$${(currentValue + donation.amount).toFixed(2)}`;
    }

    showNotification(title, message, type = 'info') {
        const modal = document.getElementById('notificationModal');
        const titleElement = document.getElementById('notificationTitle');
        const bodyElement = document.getElementById('notificationBody');

        titleElement.textContent = title;
        bodyElement.textContent = message;
        modal.classList.add('active');

        // Auto-close after 5 seconds
        setTimeout(() => {
            this.closeModal();
        }, 5000);
    }

    closeModal() {
        const modal = document.getElementById('notificationModal');
        modal.classList.remove('active');
    }

    async generateHighlights() {
        try {
            this.showNotification('Generating Highlights', 'AI is analyzing your stream for highlights...', 'info');

            const response = await fetch('/api/content/highlights/generate', {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Success', `Generated ${result.data.length} highlights`, 'success');
                this.loadContentData();
            } else {
                this.showNotification('Error', 'Failed to generate highlights', 'error');
            }
        } catch (error) {
            console.error('Failed to generate highlights:', error);
            this.showNotification('Error', 'Failed to generate highlights', 'error');
        }
    }

    async createThumbnail() {
        try {
            this.showNotification('Creating Thumbnail', 'AI is generating a custom thumbnail...', 'info');

            const response = await fetch('/api/content/thumbnails/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Epic D&D Session',
                    style: 'fantasy'
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Success', 'Thumbnail created successfully', 'success');
            } else {
                this.showNotification('Error', 'Failed to create thumbnail', 'error');
            }
        } catch (error) {
            console.error('Failed to create thumbnail:', error);
            this.showNotification('Error', 'Failed to create thumbnail', 'error');
        }
    }

    async testOBSConnection() {
        try {
            const response = await fetch('/api/streaming/config');
            const data = await response.json();

            if (data.data.obsConnected) {
                this.showNotification('Success', 'OBS connection successful', 'success');
            } else {
                this.showNotification('Error', 'OBS connection failed', 'error');
            }
        } catch (error) {
            console.error('Failed to test OBS connection:', error);
            this.showNotification('Error', 'OBS connection failed', 'error');
        }
    }

    updateDateRange(range) {
        // Implement date range filtering
        console.log('Date range changed:', range);
        this.loadInitialData();
    }

    updateViewerCount(data) {
        const viewersElement = document.getElementById('totalViewers');
        if (viewersElement) {
            viewersElement.textContent = this.formatNumber(data.count || 0);
        }
    }

    updateEngagementMetrics(data) {
        document.getElementById('totalMessages').textContent = this.formatNumber(data.totalMessages || 0);
        document.getElementById('totalPolls').textContent = this.formatNumber(data.totalPolls || 0);
        document.getElementById('totalRolls').textContent = this.formatNumber(data.totalRolls || 0);
    }

    updateRevenueData(data) {
        if (this.charts.revenueSource && data.data) {
            const revenueData = data.data;
            this.charts.revenueSource.data.datasets[0].data = [
                revenueData.donations?.amount || 0,
                revenueData.subscriptions?.amount || 0,
                revenueData.merchandise?.amount || 0,
                revenueData.sponsorships?.amount || 0
            ];
            this.charts.revenueSource.update();
        }

        // Load recent donations
        this.loadRecentDonations();
    }

    async loadRecentDonations() {
        try {
            const response = await fetch('/api/monetization/donations/session/latest');
            const data = await response.json();

            this.renderRecentDonations(data.data);
        } catch (error) {
            console.error('Failed to load recent donations:', error);
        }
    }

    renderRecentDonations(donations) {
        const container = document.getElementById('recentDonations');
        if (!container) return;

        container.innerHTML = '';

        donations.slice(0, 10).forEach(donation => {
            const donationElement = document.createElement('div');
            donationElement.className = 'donation-item';
            donationElement.innerHTML = `
                <div>
                    <div class="donor-name">${donation.donorName}</div>
                    <div class="donation-message">${donation.message || 'No message'}</div>
                </div>
                <div class="donation-amount">$${donation.amount}</div>
            `;
            container.appendChild(donationElement);
        });
    }

    renderHighlights(highlights) {
        const container = document.getElementById('highlightsGrid');
        if (!container) return;

        container.innerHTML = '';

        highlights.slice(0, 6).forEach(highlight => {
            const highlightElement = document.createElement('div');
            highlightElement.className = 'highlight-card';
            highlightElement.innerHTML = `
                <div class="highlight-thumbnail">
                    <i class="fas fa-play"></i>
                </div>
                <div class="highlight-info">
                    <div class="highlight-title">${highlight.title}</div>
                    <div class="highlight-duration">${Math.floor(highlight.duration / 60)}:${(highlight.duration % 60).toString().padStart(2, '0')}</div>
                </div>
            `;
            container.appendChild(highlightElement);
        });
    }

    loadSettings() {
        // Load settings from localStorage or API
        const savedSettings = localStorage.getItem('dashboardSettings');
        if (savedSettings) {
            this.settings = JSON.parse(savedSettings);
            this.applySettings();
        }
    }

    applySettings() {
        // Apply loaded settings to UI
        if (this.settings.obsUrl) {
            document.getElementById('obsUrl').value = this.settings.obsUrl;
        }
    }

    saveSettings() {
        localStorage.setItem('dashboardSettings', JSON.stringify(this.settings));
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StreamingDashboard();
});