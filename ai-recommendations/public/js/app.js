// AI Recommendations App JavaScript
class RecommendationsApp {
    constructor() {
        this.apiBase = '/api/recommendations';
        this.userId = this.getOrCreateUserId();
        this.currentUser = null;
        this.currentPage = 'discover';
        this.currentFilters = {};

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialContent();
        this.animateStats();
    }

    // User Management
    getOrCreateUserId() {
        let userId = localStorage.getItem('userId');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9) + Date.now();
            localStorage.setItem('userId', userId);
        }
        return userId;
    }

    // Event Listeners
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('href').substring(1);
                this.navigateToSection(target);
            });
        });

        // Hero actions
        document.getElementById('getStartedBtn')?.addEventListener('click', () => {
            this.navigateToSection('discover');
        });

        document.getElementById('learnMoreBtn')?.addEventListener('click', () => {
            this.navigateToSection('features');
        });

        // Discovery tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Filter controls
        document.getElementById('categoryFilter')?.addEventListener('change', (e) => {
            this.currentFilters.category = e.target.value;
            this.loadContent();
        });

        document.getElementById('difficultyFilter')?.addEventListener('change', (e) => {
            this.currentFilters.difficulty = e.target.value;
            this.loadContent();
        });

        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.loadContent();
        });

        // Load more
        document.getElementById('loadMoreBtn')?.addEventListener('click', () => {
            this.loadMoreContent();
        });

        // Character form
        document.getElementById('characterForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadPlayerRecommendations();
        });

        // Party form
        document.getElementById('partyForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadEncounterRecommendations();
        });

        // DM tool tabs
        document.querySelectorAll('.dm-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchDMTool(e.target.dataset.tool);
            });
        });

        // User profile
        document.getElementById('userProfileBtn')?.addEventListener('click', () => {
            this.showUserProfile();
        });

        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => {
            this.closeModal();
        });

        // Click outside modal to close
        document.getElementById('userModal')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.closeModal();
            }
        });

        // Track content interactions
        this.setupContentTracking();
    }

    // Navigation
    navigateToSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
            this.currentPage = sectionId;
        }
    }

    // Tab Switching
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

        // Load content based on tab
        this.loadContent(tabName);
    }

    // Content Loading
    async loadContent(tabName = 'personalized') {
        try {
            this.showLoading();

            const params = new URLSearchParams({
                userId: this.userId,
                discoveryType: tabName,
                filters: JSON.stringify(this.currentFilters),
                numRecommendations: 12
            });

            const response = await fetch(`${this.apiBase}/discover?${params}`);
            const data = await response.json();

            if (data.success) {
                this.renderContent(data.recommendations);
            } else {
                this.showError('Failed to load recommendations');
            }
        } catch (error) {
            console.error('Error loading content:', error);
            this.showError('Error loading recommendations');
        }
    }

    async loadMoreContent() {
        // Implementation for loading more content
        console.log('Loading more content...');
    }

    renderContent(recommendations) {
        const contentGrid = document.getElementById('contentGrid');
        if (!contentGrid) return;

        if (!recommendations || recommendations.length === 0) {
            contentGrid.innerHTML = '<div class="no-content"><p>No recommendations available</p></div>';
            return;
        }

        contentGrid.innerHTML = recommendations.map(rec => this.createContentCard(rec)).join('');

        // Add click tracking
        this.attachContentClickHandlers();
    }

    createContentCard(recommendation) {
        const content = recommendation.content || recommendation;
        const score = recommendation.score || 0;
        const methods = recommendation.methods || [];

        return `
            <div class="content-card" data-content-id="${content._id || content.contentId}">
                <div class="content-image">
                    <i class="icon-${this.getContentIcon(content.category || content.type)}"></i>
                </div>
                <div class="content-body">
                    <h3 class="content-title">${content.title || 'Untitled'}</h3>
                    <p class="content-description">${content.description || 'No description available'}</p>
                    <div class="content-meta">
                        <div class="content-rating">
                            <i class="icon-star"></i>
                            <span>${(content.rating || 0).toFixed(1)}</span>
                        </div>
                        <div class="content-category">${content.category || 'General'}</div>
                    </div>
                    ${score > 0 ? `<div class="recommendation-score">Match: ${Math.round(score * 100)}%</div>` : ''}
                    ${methods.length > 0 ? `<div class="recommendation-methods">${methods.join(', ')}</div>` : ''}
                </div>
            </div>
        `;
    }

    getContentIcon(category) {
        const icons = {
            adventure: 'dungeon',
            character: 'character',
            spell: 'spell',
            monster: 'monster',
            item: 'item',
            npc: 'npc',
            homebrew: 'homebrew',
            tools: 'tools'
        };
        return icons[category] || 'default';
    }

    // Player Recommendations
    async loadPlayerRecommendations() {
        try {
            const formData = new FormData(document.getElementById('characterForm'));
            const characterInfo = {
                class: formData.get('class') || document.getElementById('characterClass').value,
                level: parseInt(formData.get('level') || document.getElementById('characterLevel').value),
                playstyle: formData.get('playstyle') || document.getElementById('playstyle').value
            };

            this.showLoading('playerResults');

            // Load character builds
            const buildsResponse = await fetch(`${this.apiBase}/player/${this.userId}?type=builds&characterInfo=${encodeURIComponent(JSON.stringify(characterInfo))}`);
            const buildsData = await buildsResponse.json();

            // Load equipment recommendations
            const equipmentResponse = await fetch(`${this.apiBase}/player/${this.userId}?type=equipment&characterInfo=${encodeURIComponent(JSON.stringify(characterInfo))}`);
            const equipmentData = await equipmentResponse.json();

            // Load spell recommendations if applicable
            let spellsData = { recommendations: [] };
            if (['wizard', 'sorcerer', 'warlock', 'bard', 'cleric', 'druid', 'paladin', 'ranger'].includes(characterInfo.class.toLowerCase())) {
                const spellsResponse = await fetch(`${this.apiBase}/player/${this.userId}?type=spells&characterInfo=${encodeURIComponent(JSON.stringify(characterInfo))}`);
                spellsData = await spellsResponse.json();
            }

            this.renderPlayerRecommendations({
                builds: buildsData.recommendations || buildsData.builds,
                equipment: equipmentData.recommendations || equipmentData.equipment,
                spells: spellsData.recommendations || spellsData.spells
            });

            document.getElementById('playerResults').style.display = 'block';

        } catch (error) {
            console.error('Error loading player recommendations:', error);
            this.showError('Error loading player recommendations');
        }
    }

    renderPlayerRecommendations(recommendations) {
        const playerContent = document.getElementById('playerContent');
        if (!playerContent) return;

        const activeTab = document.querySelector('.result-tab.active')?.dataset.result || 'builds';
        let content = '';

        switch (activeTab) {
            case 'builds':
                content = this.renderCharacterBuilds(recommendations.builds || []);
                break;
            case 'equipment':
                content = this.renderEquipmentRecommendations(recommendations.equipment || []);
                break;
            case 'spells':
                content = this.renderSpellRecommendations(recommendations.spells || []);
                break;
        }

        playerContent.innerHTML = content;

        // Setup tab switching
        document.querySelectorAll('.result-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.result-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.renderPlayerRecommendations(recommendations);
            });
        });
    }

    renderCharacterBuilds(builds) {
        if (!builds || builds.length === 0) {
            return '<p>No character builds available for your selection.</p>';
        }

        return builds.map(build => `
            <div class="build-card">
                <h4>${build.name || 'Unknown Build'}</h4>
                <p>${build.description || 'No description available'}</p>
                <div class="build-stats">
                    <div class="stat"><strong>Class:</strong> ${build.class || 'Unknown'}</div>
                    <div class="stat"><strong>Level:</strong> ${build.level || 'Unknown'}</div>
                    <div class="stat"><strong>Playstyle:</strong> ${build.playstyle || 'Balanced'}</div>
                </div>
                <div class="build-features">
                    ${build.strengths ? `<h5>Strengths:</h5><ul>${build.strengths.map(s => `<li>${s}</li>`).join('')}</ul>` : ''}
                    ${build.progression ? `<h5>Progression:</h5><ul>${build.progression.slice(0, 3).map(p => `<li>Level ${p.level}: ${p.milestone}</li>`).join('')}</ul>` : ''}
                </div>
            </div>
        `).join('');
    }

    renderEquipmentRecommendations(equipment) {
        if (!equipment || equipment.length === 0) {
            return '<p>No equipment recommendations available.</p>';
        }

        return equipment.map(item => `
            <div class="equipment-card">
                <h4>${item.name || 'Unknown Item'}</h4>
                <p class="equipment-type">${item.type || 'Equipment'}</p>
                <p class="equipment-description">${item.description || 'No description available'}</p>
                <div class="equipment-stats">
                    ${item.score ? `<div class="score">Recommendation Score: ${Math.round(item.score * 100)}%</div>` : ''}
                    ${item.cost ? `<div class="cost">Cost: ${item.cost} gp</div>` : ''}
                    ${item.rarity ? `<div class="rarity">${item.rarity}</div>` : ''}
                </div>
                ${item.reasoning ? `<div class="reasoning"><strong>Why this item:</strong> ${item.reasoning}</div>` : ''}
            </div>
        `).join('');
    }

    renderSpellRecommendations(spells) {
        if (!spells || spells.length === 0) {
            return '<p>No spell recommendations available.</p>';
        }

        return spells.map(spell => `
            <div class="spell-card">
                <h4>${spell.name || 'Unknown Spell'}</h4>
                <div class="spell-meta">
                    <span class="spell-level">Level ${spell.level || 0}</span>
                    <span class="spell-school">${spell.school || 'Universal'}</span>
                </div>
                <p class="spell-description">${spell.description || 'No description available'}</p>
                <div class="spell-details">
                    ${spell.casting_time ? `<div><strong>Casting Time:</strong> ${spell.casting_time}</div>` : ''}
                    ${spell.duration ? `<div><strong>Duration:</strong> ${spell.duration}</div>` : ''}
                    ${spell.components ? `<div><strong>Components:</strong> ${spell.components.join(', ')}</div>` : ''}
                </div>
                ${spell.reasoning ? `<div class="reasoning"><strong>Why this spell:</strong> ${spell.reasoning}</div>` : ''}
            </div>
        `).join('');
    }

    // DM Tools
    switchDMTool(toolName) {
        // Update tab buttons
        document.querySelectorAll('.dm-tab').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tool="${toolName}"]`)?.classList.add('active');

        // Show/hide appropriate tool
        document.getElementById('encounterTool').style.display = toolName === 'encounters' ? 'block' : 'none';
        document.getElementById('otherDMTools').style.display = toolName !== 'encounters' ? 'block' : 'none';

        if (toolName !== 'encounters') {
            this.loadOtherDMTool(toolName);
        }
    }

    async loadEncounterRecommendations() {
        try {
            const formData = new FormData(document.getElementById('partyForm'));
            const partyInfo = {
                level: parseInt(document.getElementById('partyLevel').value),
                size: parseInt(document.getElementById('partySize').value),
                composition: [] // Would be populated with actual party composition
            };

            const campaignContext = {
                environment: document.getElementById('environment').value,
                theme: document.getElementById('theme').value,
                difficulty: document.getElementById('difficulty').value
            };

            this.showLoading('encounterResults');

            const response = await fetch(`${this.apiBase}/dm/${this.userId}?type=encounters&partyInfo=${encodeURIComponent(JSON.stringify(partyInfo))}&campaignContext=${encodeURIComponent(JSON.stringify(campaignContext))}`);
            const data = await response.json();

            if (data.success) {
                this.renderEncounterRecommendations(data.recommendations.encounters || []);
                document.getElementById('encounterResults').style.display = 'block';
            } else {
                this.showError('Failed to load encounter recommendations');
            }

        } catch (error) {
            console.error('Error loading encounter recommendations:', error);
            this.showError('Error loading encounter recommendations');
        }
    }

    renderEncounterRecommendations(encounters) {
        const encounterResults = document.getElementById('encounterResults');
        if (!encounterResults) return;

        if (!encounters || encounters.length === 0) {
            encounterResults.innerHTML = '<p>No encounter recommendations available.</p>';
            return;
        }

        encounterResults.innerHTML = encounters.map(encounter => `
            <div class="encounter-card">
                <h4>${encounter.name || 'Unknown Encounter'}</h4>
                <p>${encounter.description || 'No description available'}</p>
                <div class="encounter-difficulties">
                    ${Object.entries(encounter.difficulties || {}).map(([difficulty, details]) => `
                        <div class="difficulty-section">
                            <h5>${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)} (${details.xp} XP)</h5>
                            <div class="enemies">
                                ${details.enemies?.map(enemy => `
                                    <div class="enemy">
                                        <span class="enemy-name">${enemy.name || 'Unknown'}</span>
                                        <span class="enemy-quantity">×${enemy.quantity || 1}</span>
                                        <span class="enemy-cr">CR ${enemy.cr || 'Unknown'}</span>
                                    </div>
                                `).join('') || ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${encounter.tactics ? `<div class="tactics"><strong>Tactics:</strong> ${encounter.tactics.join(', ')}</div>` : ''}
                ${encounter.setupComplexity ? `<div class="complexity"><strong>Setup Complexity:</strong> ${encounter.setupComplexity}</div>` : ''}
            </div>
        `).join('');
    }

    async loadOtherDMTool(toolName) {
        // Placeholder for other DM tools
        const otherDMTools = document.getElementById('otherDMTools');
        if (otherDMTools) {
            otherDMTools.innerHTML = `<p>${toolName} tool content will be implemented here...</p>`;
        }
    }

    // User Profile
    async showUserProfile() {
        try {
            const response = await fetch(`${this.apiBase}/insights/${this.userId}`);
            const data = await response.json();

            if (data.success) {
                this.renderUserProfile(data);
                this.openModal();
            } else {
                this.showError('Failed to load user profile');
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.showError('Error loading user profile');
        }
    }

    renderUserProfile(data) {
        const userModalContent = document.getElementById('userModalContent');
        if (!userModalContent) return;

        userModalContent.innerHTML = `
            <div class="profile-header">
                <h4>User Profile: ${this.userId}</h4>
                <div class="profile-stats">
                    <div class="stat">
                        <span class="stat-label">Segment:</span>
                        <span class="stat-value">${data.segmentation?.behavioral || 'Unknown'}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total Interactions:</span>
                        <span class="stat-value">${data.stats?.totalInteractions || 0}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Sessions:</span>
                        <span class="stat-value">${data.stats?.totalSessions || 0}</span>
                    </div>
                </div>
            </div>
            <div class="profile-insights">
                <h5>Your Insights:</h5>
                ${data.insights?.length > 0 ? data.insights.map(insight => `
                    <div class="insight-item">
                        <strong>${insight.title}</strong>
                        <p>${insight.description}</p>
                    </div>
                `).join('') : '<p>No insights available yet.</p>'}
            </div>
            <div class="profile-recommendations">
                <h5>Recommendations for You:</h5>
                ${data.recommendations?.length > 0 ? data.recommendations.map(rec => `
                    <div class="recommendation-item">
                        <strong>${rec.title}</strong>
                        <p>${rec.description}</p>
                    </div>
                `).join('') : '<p>No recommendations available.</p>'}
            </div>
        `;
    }

    // Content Tracking
    setupContentTracking() {
        // Track impressions when content comes into view
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const contentId = entry.target.dataset.contentId;
                    if (contentId) {
                        this.trackBehavior('view', contentId, 'content');
                        observer.unobserve(entry.target);
                    }
                }
            });
        }, { threshold: 0.5 });

        // Observe content cards as they are added
        const contentGrid = document.getElementById('contentGrid');
        if (contentGrid) {
            const mutationObserver = new MutationObserver(() => {
                contentGrid.querySelectorAll('.content-card').forEach(card => {
                    if (!card.dataset.tracked) {
                        observer.observe(card);
                        card.dataset.tracked = 'true';
                    }
                });
            });

            mutationObserver.observe(contentGrid, { childList: true });
        }
    }

    attachContentClickHandlers() {
        document.querySelectorAll('.content-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const contentId = e.currentTarget.dataset.contentId;
                if (contentId) {
                    this.trackBehavior('click', contentId, 'content');
                    // Could open detail modal or navigate to content page
                }
            });
        });
    }

    async trackBehavior(action, contentId, contentType, metadata = {}) {
        try {
            await fetch(`${this.apiBase}/behavior`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId: this.userId,
                    action,
                    contentId,
                    contentType,
                    metadata,
                    context: {
                        userAgent: navigator.userAgent,
                        timestamp: new Date().toISOString()
                    },
                    sessionId: this.getSessionId()
                })
            });
        } catch (error) {
            console.error('Error tracking behavior:', error);
        }
    }

    getSessionId() {
        let sessionId = sessionStorage.getItem('sessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now();
            sessionStorage.setItem('sessionId', sessionId);
        }
        return sessionId;
    }

    // UI Helpers
    showLoading(targetId = 'contentGrid') {
        const target = document.getElementById(targetId);
        if (target) {
            target.innerHTML = '<div class="loading-skeleton"><div class="skeleton-card"></div><div class="skeleton-card"></div><div class="skeleton-card"></div></div>';
        }
    }

    showError(message) {
        // Simple error display - could be enhanced with toast notifications
        console.error(message);
        const contentGrid = document.getElementById('contentGrid');
        if (contentGrid) {
            contentGrid.innerHTML = `<div class="error-message"><p>${message}</p></div>`;
        }
    }

    openModal() {
        const modal = document.getElementById('userModal');
        if (modal) {
            modal.classList.add('active');
        }
    }

    closeModal() {
        const modal = document.getElementById('userModal');
        if (modal) {
            modal.classList.remove('active');
        }
    }

    // Initial Content Loading
    async loadInitialContent() {
        await this.loadContent();
        await this.loadUserInsights();
    }

    async loadUserInsights() {
        try {
            const response = await fetch(`${this.apiBase}/insights/${this.userId}`);
            const data = await response.json();

            if (data.success) {
                this.updateInsightsDisplay(data);
            }
        } catch (error) {
            console.error('Error loading user insights:', error);
        }
    }

    updateInsightsDisplay(data) {
        // Update user profile section
        const userProfile = document.getElementById('userProfile');
        if (userProfile && data.segmentation) {
            userProfile.innerHTML = `
                <div class="profile-summary">
                    <p><strong>Behavior Type:</strong> ${data.segmentation.behavioral}</p>
                    <p><strong>Content Preference:</strong> ${data.segmentation.content}</p>
                    <p><strong>Engagement Level:</strong> ${data.segmentation.engagement}</p>
                    <p><strong>Total Interactions:</strong> ${data.stats?.totalInteractions || 0}</p>
                </div>
            `;
        }

        // Update charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.updateCharts(data);
        }
    }

    updateCharts(data) {
        // Categories chart
        const categoriesCtx = document.getElementById('categoriesChart');
        if (categoriesCtx && data.segmentation) {
            new Chart(categoriesCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Adventures', 'Characters', 'Spells', 'Monsters', 'Items'],
                    datasets: [{
                        data: [30, 25, 20, 15, 10], // Sample data
                        backgroundColor: [
                            '#6366f1',
                            '#8b5cf6',
                            '#ec4899',
                            '#f59e0b',
                            '#10b981'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Timeline chart
        const timelineCtx = document.getElementById('timelineChart');
        if (timelineCtx) {
            new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Activity',
                        data: [12, 19, 3, 5, 2, 8, 15], // Sample data
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        tension: 0.4
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
        }
    }

    // Animations
    animateStats() {
        const statNumbers = document.querySelectorAll('.stat-number');
        statNumbers.forEach(stat => {
            const target = parseInt(stat.dataset.count);
            let current = 0;
            const increment = target / 100;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                stat.textContent = Math.floor(current).toLocaleString();
            }, 20);
        });
    }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RecommendationsApp();
});

// Add some CSS for new elements
const additionalCSS = `
.content-card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.content-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.recommendation-score {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 8px;
    display: inline-block;
}

.build-card, .equipment-card, .spell-card, .encounter-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}

.build-stats, .equipment-stats, .spell-meta {
    display: flex;
    gap: 16px;
    margin: 12px 0;
    flex-wrap: wrap;
}

.build-stats .stat, .equipment-stats .stat {
    background: #f9fafb;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.875rem;
}

.reasoning {
    background: #f0f9ff;
    border-left: 4px solid #0ea5e9;
    padding: 12px;
    margin-top: 12px;
    border-radius: 4px;
    font-size: 0.875rem;
}

.difficulty-section {
    background: #f9fafb;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
}

.enemy {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #e5e7eb;
}

.enemy:last-child {
    border-bottom: none;
}

.enemy-name {
    font-weight: 500;
}

.enemy-cr {
    background: #6366f1;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
}

.profile-header {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.profile-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin-top: 16px;
}

.profile-stats .stat {
    background: rgba(255,255,255,0.1);
    padding: 12px;
    border-radius: 8px;
    text-align: center;
}

.insight-item, .recommendation-item {
    background: #f9fafb;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
}

.loading-skeleton {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 24px;
}

.skeleton-card {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border-radius: 12px;
    height: 350px;
}

@keyframes loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.error-message {
    text-align: center;
    padding: 40px;
    color: #ef4444;
    background: #fef2f2;
    border-radius: 12px;
    border: 1px solid #fecaca;
}

.no-content {
    text-align: center;
    padding: 40px;
    color: #6b7280;
    background: #f9fafb;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}
`;

// Add the additional CSS to the page
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);