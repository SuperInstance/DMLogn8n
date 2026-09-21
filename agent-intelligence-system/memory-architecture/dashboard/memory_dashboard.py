"""
Memory Dashboard for Visualization and Management
=================================================

Web-based dashboard for visualizing and managing the hierarchical memory system.
Provides real-time insights into memory usage, consolidation, and performance.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from ..core.memory_base import MemoryBase, MemoryType, MemoryStatus, MemoryStats
from ..memory_types.working_memory import WorkingMemory
from ..memory_types.episodic_memory import EpisodicMemory
from ..memory_types.semantic_memory import SemanticMemory
from ..consolidation.consolidation_engine import ConsolidationEngine
from ..core.forgetting_mechanism import ForgettingMechanism


logger = logging.getLogger(__name__)


@dataclass
class DashboardData:
    """Data structure for dashboard display"""
    timestamp: str
    character_level: int
    memory_stats: Dict[str, Any]
    working_memory_data: Dict[str, Any]
    episodic_memory_data: Dict[str, Any]
    semantic_memory_data: Dict[str, Any]
    consolidation_data: Dict[str, Any]
    forgetting_data: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class MemoryDashboard:
    """
    Dashboard for visualizing and managing the memory system.
    Provides HTML interface and REST API endpoints.
    """

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.creation_time = datetime.now()

        # Dashboard data cache
        self.data_cache: Optional[DashboardData] = None
        self.cache_expiry = timedelta(minutes=5)
        self.last_update = None

        # Activity tracking
        self.activity_log: List[Dict[str, Any]] = []
        self.max_log_entries = 100

        # Performance metrics
        self.performance_history: List[Dict[str, Any]] = []
        self.max_history_entries = 50

    def generate_dashboard_data(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory],
        consolidation_engine: ConsolidationEngine,
        forgetting_mechanism: ForgettingMechanism
    ) -> DashboardData:
        """Generate comprehensive dashboard data"""
        current_time = datetime.now()

        # Check cache
        if (self.data_cache and self.last_update and
            current_time - self.last_update < self.cache_expiry):
            return self.data_cache

        try:
            # Generate memory statistics
            memory_stats = self._generate_memory_stats(
                working_memory, episodic_memories, semantic_memories
            )

            # Generate working memory data
            working_data = self._generate_working_memory_data(working_memory)

            # Generate episodic memory data
            episodic_data = self._generate_episodic_memory_data(episodic_memories)

            # Generate semantic memory data
            semantic_data = self._generate_semantic_memory_data(semantic_memories)

            # Generate consolidation data
            consolidation_data = self._generate_consolidation_data(consolidation_engine)

            # Generate forgetting data
            forgetting_data = self._generate_forgetting_data(forgetting_mechanism)

            # Generate recent activities
            recent_activities = self.activity_log[-20:]  # Last 20 activities

            # Generate performance metrics
            performance_metrics = self._generate_performance_metrics()

            # Create dashboard data
            dashboard_data = DashboardData(
                timestamp=current_time.isoformat(),
                character_level=consolidation_engine.character_level,
                memory_stats=memory_stats,
                working_memory_data=working_data,
                episodic_memory_data=episodic_data,
                semantic_memory_data=semantic_data,
                consolidation_data=consolidation_data,
                forgetting_data=forgetting_data,
                recent_activities=recent_activities,
                performance_metrics=performance_metrics
            )

            # Update cache
            self.data_cache = dashboard_data
            self.last_update = current_time

            return dashboard_data

        except Exception as e:
            logger.error(f"Failed to generate dashboard data: {e}")
            raise

    def generate_html_dashboard(self, dashboard_data: DashboardData) -> str:
        """Generate HTML dashboard from data"""
        html_template = self._get_html_template()

        # Replace placeholders with data
        html = html_template.replace("{{DASHBOARD_DATA}}", json.dumps(asdict(dashboard_data), indent=2))
        html = html.replace("{{CHARACTER_ID}}", self.character_id)
        html = html.replace("{{GENERATION_TIME}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return html

    def log_activity(self, activity_type: str, description: str, details: Dict[str, Any] = None) -> None:
        """Log an activity for dashboard display"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,
            "description": description,
            "details": details or {}
        }

        self.activity_log.append(activity)

        # Trim log if too long
        if len(self.activity_log) > self.max_log_entries:
            self.activity_log = self.activity_log[-self.max_log_entries:]

        logger.debug(f"Logged activity: {activity_type} - {description}")

    def record_performance_metric(self, metric_name: str, value: float, context: Dict[str, Any] = None) -> None:
        """Record a performance metric"""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric_name,
            "value": value,
            "context": context or {}
        }

        self.performance_history.append(metric)

        # Trim history if too long
        if len(self.performance_history) > self.max_history_entries:
            self.performance_history = self.performance_history[-self.max_history_entries:]

    def get_memory_insights(self, dashboard_data: DashboardData) -> List[Dict[str, Any]]:
        """Generate insights from memory data"""
        insights = []

        # Capacity insights
        memory_stats = dashboard_data.memory_stats
        for mem_type, stats in memory_stats.items():
            if isinstance(stats, dict) and "utilization" in stats:
                utilization = stats["utilization"]
                if utilization > 0.9:
                    insights.append({
                        "type": "warning",
                        "category": "capacity",
                        "title": f"High {mem_type.title()} Memory Usage",
                        "description": f"{mem_type.title()} memory is at {utilization:.1%} capacity",
                        "recommendation": "Consider running consolidation or reviewing memory importance"
                    })
                elif utilization < 0.3:
                    insights.append({
                        "type": "info",
                        "category": "capacity",
                        "title": f"Low {mem_type.title()} Memory Usage",
                        "description": f"{mem_type.title()} memory is at {utilization:.1%} capacity",
                        "recommendation": "Memory usage is healthy"
                    })

        # Consolidation insights
        consolidation_data = dashboard_data.consolidation_data
        if consolidation_data.get("success_rate", 1.0) < 0.8:
            insights.append({
                "type": "warning",
                "category": "consolidation",
                "title": "Low Consolidation Success Rate",
                "description": f"Consolidation success rate is {consolidation_data['success_rate']:.1%}",
                "recommendation": "Review consolidation criteria and memory importance scoring"
            })

        # Forgetting insights
        forgetting_data = dashboard_data.forgetting_data
        if forgetting_data.get("total_forgotten", 0) > 10:
            insights.append({
                "type": "info",
                "category": "forgetting",
                "title": "Memory Forgetting Active",
                "description": f"{forgetting_data['total_forgotten']} memories have been forgotten",
                "recommendation": "Review forgetting strategy and protection rules"
            })

        return insights

    def _generate_memory_stats(
        self,
        working_memory: WorkingMemory,
        episodic_memories: List[EpisodicMemory],
        semantic_memories: List[SemanticMemory]
    ) -> Dict[str, Any]:
        """Generate comprehensive memory statistics"""
        # Count memories by type and status
        working_active = len(working_memory)
        episodic_active = len([m for m in episodic_memories if m.status == MemoryStatus.ACTIVE])
        episodic_consolidated = len([m for m in episodic_memories if m.status == MemoryStatus.CONSOLIDATED])
        semantic_active = len([m for m in semantic_memories if m.status == MemoryStatus.ACTIVE])

        total_memories = working_active + episodic_active + semantic_active

        # Calculate average importance
        working_importance = sum(item.memory.importance for item in working_memory.items.values()) / max(working_active, 1)
        episodic_importance = sum(m.importance for m in episodic_memories if m.status == MemoryStatus.ACTIVE) / max(episodic_active, 1)
        semantic_importance = sum(m.importance for m in semantic_memories if m.status == MemoryStatus.ACTIVE) / max(semantic_active, 1)

        # Capacity utilization
        working_capacity = working_memory.capacity
        episodic_capacity = 200  # Based on typical level
        semantic_capacity = 100

        return {
            "working": {
                "active": working_active,
                "capacity": working_capacity,
                "utilization": working_active / working_capacity,
                "average_importance": working_importance,
                "average_activation": working_memory.average_activation
            },
            "episodic": {
                "active": episodic_active,
                "consolidated": episodic_consolidated,
                "capacity": episodic_capacity,
                "utilization": episodic_active / episodic_capacity,
                "average_importance": episodic_importance
            },
            "semantic": {
                "active": semantic_active,
                "capacity": semantic_capacity,
                "utilization": semantic_active / semantic_capacity,
                "average_importance": semantic_importance,
                "average_confidence": sum(m.confidence for m in semantic_memories if m.status == MemoryStatus.ACTIVE) / max(semantic_active, 1)
            },
            "total": {
                "active": total_memories,
                "average_importance": (working_importance + episodic_importance + semantic_importance) / 3
            }
        }

    def _generate_working_memory_data(self, working_memory: WorkingMemory) -> Dict[str, Any]:
        """Generate working memory specific data"""
        items_data = []

        for item_id, item in working_memory.items.items():
            items_data.append({
                "id": item.memory.id,
                "content": item.memory.content.primary_content[:100] + "..." if len(item.memory.content.primary_content) > 100 else item.memory.content.primary_content,
                "activation": item.activation,
                "importance": item.memory.importance,
                "emotional_valence": item.memory.metadata.emotional_valence,
                "tags": item.memory.metadata.tags
            })

        return {
            "capacity": working_memory.capacity,
            "current_count": len(working_memory.items),
            "utilization": len(working_memory.items) / working_memory.capacity,
            "average_activation": working_memory.average_activation,
            "items": items_data,
            "stats": working_memory.get_stats()
        }

    def _generate_episodic_memory_data(self, episodic_memories: List[EpisodicMemory]) -> Dict[str, Any]:
        """Generate episodic memory specific data"""
        active_memories = [m for m in episodic_memories if m.status == MemoryStatus.ACTIVE]

        # Recent memories
        recent_memories = sorted(active_memories, key=lambda m: m.creation_time, reverse=True)[:10]

        recent_data = []
        for memory in recent_memories:
            recent_data.append({
                "id": memory.id,
                "content": memory.content.primary_content[:100] + "..." if len(memory.content.primary_content) > 100 else memory.content.primary_content,
                "timestamp": memory.timestamp.isoformat(),
                "location": memory.metadata.location,
                "participants": memory.metadata.participants,
                "importance": memory.importance,
                "emotional_valence": memory.metadata.emotional_valence,
                "access_count": memory.metadata.access_count,
                "is_landmark": memory.is_temporal_landmark
            })

        # Temporal landmarks
        landmarks = [m for m in active_memories if m.is_temporal_landmark]

        return {
            "active_count": len(active_memories),
            "total_count": len(episodic_memories),
            "recent_memories": recent_data,
            "temporal_landmarks": len(landmarks),
            "landmark_details": [{
                "id": landmark.id,
                "type": landmark.landmark_type,
                "importance": landmark.landmark_importance,
                "description": landmark.content.primary_content[:50]
            } for landmark in landmarks[:5]]
        }

    def _generate_semantic_memory_data(self, semantic_memories: List[SemanticMemory]) -> Dict[str, Any]:
        """Generate semantic memory specific data"""
        active_memories = [m for m in semantic_memories if m.status == MemoryStatus.ACTIVE]

        # Concepts and patterns
        concepts = {}
        patterns = []

        for memory in active_memories:
            if memory.concept:
                if memory.concept not in concepts:
                    concepts[memory.concept] = {
                        "count": 0,
                        "total_importance": 0,
                        "total_confidence": 0,
                        "examples": []
                    }

                concepts[memory.concept]["count"] += 1
                concepts[memory.concept]["total_importance"] += memory.importance
                concepts[memory.concept]["total_confidence"] += memory.confidence

                if len(concepts[memory.concept]["examples"]) < 3:
                    concepts[memory.concept]["examples"].append({
                        "id": memory.id,
                        "content": memory.content.primary_content[:100]
                    })

            patterns.extend(memory.learned_patterns)

        # Calculate averages
        for concept_data in concepts.values():
            concept_data["average_importance"] = concept_data["total_importance"] / concept_data["count"]
            concept_data["average_confidence"] = concept_data["total_confidence"] / concept_data["count"]

        return {
            "active_count": len(active_memories),
            "total_count": len(semantic_memories),
            "concepts": concepts,
            "pattern_count": len(patterns),
            "top_patterns": sorted(
                [(p.description, p.confidence) for p in patterns],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def _generate_consolidation_data(self, consolidation_engine: ConsolidationEngine) -> Dict[str, Any]:
        """Generate consolidation system data"""
        return {
            "character_level": consolidation_engine.character_level,
            "consolidation_threshold": consolidation_engine.consolidation_threshold,
            "total_consolidations": consolidation_engine.total_consolidations,
            "successful_consolidations": consolidation_engine.successful_consolidations,
            "success_rate": consolidation_engine.successful_consolidations / max(consolidation_engine.total_consolidations, 1),
            "patterns_extracted": consolidation_engine.patterns_extracted,
            "last_consolidation": consolidation_engine.last_consolidation_time.isoformat(),
            "queue_size": len(consolidation_engine.consolidation_queue),
            "recent_history": consolidation_engine.consolidation_history[-5:]
        }

    def _generate_forgetting_data(self, forgetting_mechanism: ForgettingMechanism) -> Dict[str, Any]:
        """Generate forgetting mechanism data"""
        return {
            "strategy": forgetting_mechanism.strategy.name,
            "strategy_description": forgetting_mechanism.strategy.description,
            "total_forgotten": forgetting_mechanism.total_forgotten,
            "forgetting_by_type": forgetting_mechanism.forgetting_by_type,
            "forgetting_by_importance": forgetting_mechanism.forgetting_by_importance,
            "protection_rules": list(forgetting_mechanism.protection_rules.keys()),
            "capacity_limits": forgetting_mechanism.capacity_limits,
            "recent_history": forgetting_mechanism.forgetting_history[-5:]
        }

    def _generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance metrics"""
        if not self.performance_history:
            return {}

        # Group metrics by type
        metrics_by_type = defaultdict(list)
        for metric in self.performance_history:
            metrics_by_type[metric["metric"]].append(metric)

        # Calculate recent averages
        recent_metrics = {}
        for metric_name, metric_list in metrics_by_type.items():
            recent_values = [m["value"] for m in metric_list[-10:]]  # Last 10 values
            if recent_values:
                recent_metrics[metric_name] = {
                    "current": recent_values[-1],
                    "average": sum(recent_values) / len(recent_values),
                    "trend": "up" if len(recent_values) > 1 and recent_values[-1] > recent_values[-2] else "down"
                }

        return recent_metrics

    def _get_html_template(self) -> str:
        """Get the HTML template for the dashboard"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Dashboard - {{CHARACTER_ID}}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .card h3 {
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .memory-bar {
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .memory-fill {
            height: 20px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        .activity-log {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 10px;
        }
        .activity-item {
            padding: 5px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .insight {
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }
        .insight.warning {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        .insight.info {
            background-color: #d1ecf1;
            border-left: 4px solid #17a2b8;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-good { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-danger { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Memory Dashboard</h1>
            <p>Character: {{CHARACTER_ID}} | Generated: {{GENERATION_TIME}}</p>
        </div>

        <div class="stats-grid">
            <div class="card">
                <h3>Memory Overview</h3>
                <div id="memory-stats"></div>
            </div>

            <div class="card">
                <h3>Working Memory</h3>
                <div id="working-memory-stats"></div>
            </div>

            <div class="card">
                <h3>Consolidation System</h3>
                <div id="consolidation-stats"></div>
            </div>

            <div class="card">
                <h3>Performance Metrics</h3>
                <div id="performance-metrics"></div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="card">
                <h3>Memory Capacity</h3>
                <div class="chart-container">
                    <canvas id="capacity-chart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>Activity Log</h3>
                <div class="activity-log" id="activity-log"></div>
            </div>
        </div>

        <div class="card">
            <h3>System Insights</h3>
            <div id="insights"></div>
        </div>
    </div>

    <script>
        // Dashboard data
        const dashboardData = {{DASHBOARD_DATA}};

        // Initialize dashboard
        function initDashboard() {
            updateMemoryStats();
            updateWorkingMemory();
            updateConsolidationStats();
            updatePerformanceMetrics();
            updateCapacityChart();
            updateActivityLog();
            generateInsights();
        }

        function updateMemoryStats() {
            const stats = dashboardData.memory_stats;
            let html = '';

            for (const [type, data] of Object.entries(stats)) {
                if (typeof data === 'object' && data.utilization !== undefined) {
                    const utilizationPercent = (data.utilization * 100).toFixed(1);
                    const statusClass = data.utilization > 0.8 ? 'status-danger' :
                                       data.utilization > 0.6 ? 'status-warning' : 'status-good';

                    html += `
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span><span class="status-indicator ${statusClass}"></span>${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                                <span>${data.active || data.current_count || 0}/${data.capacity}</span>
                            </div>
                            <div class="memory-bar">
                                <div class="memory-fill" style="width: ${utilizationPercent}%"></div>
                            </div>
                            <small>Avg Importance: ${(data.average_importance || 0).toFixed(2)}</small>
                        </div>
                    `;
                }
            }

            document.getElementById('memory-stats').innerHTML = html;
        }

        function updateWorkingMemory() {
            const workingData = dashboardData.working_memory_data;
            const utilizationPercent = (workingData.utilization * 100).toFixed(1);

            let html = `
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span>Capacity Usage</span>
                        <span>${workingData.current_count}/${workingData.capacity}</span>
                    </div>
                    <div class="memory-bar">
                        <div class="memory-fill" style="width: ${utilizationPercent}%"></div>
                    </div>
                </div>
                <p><strong>Average Activation:</strong> ${(workingData.average_activation || 0).toFixed(3)}</p>
                <p><strong>Total Items Added:</strong> ${workingData.stats?.total_items_added || 0}</p>
            `;

            document.getElementById('working-memory-stats').innerHTML = html;
        }

        function updateConsolidationStats() {
            const consolidationData = dashboardData.consolidation_data;

            let html = `
                <p><strong>Character Level:</strong> ${consolidationData.character_level}</p>
                <p><strong>Consolidation Threshold:</strong> ${consolidationData.consolidation_threshold}</p>
                <p><strong>Total Consolidations:</strong> ${consolidationData.total_consolidations}</p>
                <p><strong>Success Rate:</strong> ${(consolidationData.success_rate * 100).toFixed(1)}%</p>
                <p><strong>Patterns Extracted:</strong> ${consolidationData.patterns_extracted}</p>
            `;

            document.getElementById('consolidation-stats').innerHTML = html;
        }

        function updatePerformanceMetrics() {
            const metrics = dashboardData.performance_metrics;
            let html = '';

            for (const [metric, data] of Object.entries(metrics)) {
                const trendIcon = data.trend === 'up' ? '📈' : '📉';
                html += `
                    <div style="margin-bottom: 10px;">
                        <strong>${metric.replace(/_/g, ' ').toUpperCase()}:</strong>
                        ${data.current.toFixed(3)} ${trendIcon}
                        <br><small>Avg: ${data.average.toFixed(3)}</small>
                    </div>
                `;
            }

            if (!html) {
                html = '<p>No performance data available yet.</p>';
            }

            document.getElementById('performance-metrics').innerHTML = html;
        }

        function updateCapacityChart() {
            const ctx = document.getElementById('capacity-chart').getContext('2d');
            const stats = dashboardData.memory_stats;

            const labels = [];
            const currentData = [];
            const capacityData = [];

            for (const [type, data] of Object.entries(stats)) {
                if (typeof data === 'object' && data.capacity) {
                    labels.push(type.charAt(0).toUpperCase() + type.slice(1));
                    currentData.push(data.active || data.current_count || 0);
                    capacityData.push(data.capacity);
                }
            }

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Current Usage',
                            data: currentData,
                            backgroundColor: 'rgba(102, 126, 234, 0.8)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Capacity',
                            data: capacityData,
                            backgroundColor: 'rgba(118, 75, 162, 0.3)',
                            borderColor: 'rgba(118, 75, 162, 1)',
                            borderWidth: 1
                        }
                    ]
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

        function updateActivityLog() {
            const activities = dashboardData.recent_activities;
            let html = '';

            activities.reverse().forEach(activity => {
                const time = new Date(activity.timestamp).toLocaleTimeString();
                html += `
                    <div class="activity-item">
                        <strong>${time}</strong> - ${activity.type}: ${activity.description}
                    </div>
                `;
            });

            if (!html) {
                html = '<p>No recent activities.</p>';
            }

            document.getElementById('activity-log').innerHTML = html;
        }

        function generateInsights() {
            // Generate insights based on data
            const insights = [];
            const stats = dashboardData.memory_stats;

            // Capacity insights
            for (const [type, data] of Object.entries(stats)) {
                if (typeof data === 'object' && data.utilization > 0.8) {
                    insights.push({
                        type: 'warning',
                        title: `High ${type} Memory Usage`,
                        description: `${type.charAt(0).toUpperCase() + type.slice(1)} memory is at ${(data.utilization * 100).toFixed(1)}% capacity`
                    });
                }
            }

            let html = '';
            insights.forEach(insight => {
                html += `
                    <div class="insight ${insight.type}">
                        <strong>${insight.title}</strong><br>
                        ${insight.description}
                    </div>
                `;
            });

            if (!html) {
                html = '<p>All systems operating normally.</p>';
            }

            document.getElementById('insights').innerHTML = html;
        }

        // Initialize on load
        document.addEventListener('DOMContentLoaded', initDashboard);

        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
        '''