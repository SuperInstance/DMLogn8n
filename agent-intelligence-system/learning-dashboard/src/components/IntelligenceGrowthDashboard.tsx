import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  AgentLearningMetrics,
  TimeframeConfig,
  LearningMilestone,
  WebSocketMessage,
  DashboardConfig
} from '../types';
import { useWebSocket } from '../hooks/useWebSocket';
import { useLearningData } from '../hooks/useLearningData';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { IQProgressionChart } from './charts/IQProgressionChart';
import { SkillRadarChart } from './charts/SkillRadarChart';
import { MemoryUsageChart } from './charts/MemoryUsageChart';
import { LearningVelocityChart } from './charts/LearningVelocityChart';
import { StrategicImprovementChart } from './charts/StrategicImprovementChart';
import { RecentLessonsPanel } from './panels/RecentLessonsPanel';
import { MilestoneCelebration } from './components/MilestoneCelebration';
import { PerformanceComparison } from './panels/PerformanceComparison';
import { AlertSystem } from './components/AlertSystem';
import { ExportPanel } from './panels/ExportPanel';

interface IntelligenceGrowthDashboardProps {
  agentId: string;
  className?: string;
  config?: Partial<DashboardConfig>;
}

export const IntelligenceGrowthDashboard: React.FC<IntelligenceGrowthDashboardProps> = ({
  agentId,
  className = '',
  config: userConfig = {}
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('session');
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(true);
  const [celebrationQueue, setCelebrationQueue] = useState<LearningMilestone[]>([]);
  const [showCelebration, setShowCelebration] = useState(false);

  // Default dashboard configuration
  const defaultConfig: DashboardConfig = {
    refreshInterval: 5000,
    timeframes: [
      { id: 'session', label: 'Current Session', duration: 1, unit: 'hours' },
      { id: 'day', label: 'Last 24 Hours', duration: 1, unit: 'days' },
      { id: 'week', label: 'Last Week', duration: 7, unit: 'days' },
      { id: 'month', label: 'Last Month', duration: 30, unit: 'days' }
    ],
    alertThresholds: [
      { metric: 'learningVelocity', condition: 'below', value: 0.1, severity: 'warning', message: 'Learning velocity has decreased significantly' },
      { metric: 'memoryUtilization', condition: 'above', value: 0.9, severity: 'critical', message: 'Memory capacity nearly full' },
      { metric: 'iqImprovement', condition: 'above', value: 5, severity: 'info', message: 'Significant IQ improvement detected!' }
    ],
    exportFormats: ['pdf', 'csv', 'json'],
    chartPreferences: {
      colorScheme: 'viridis',
      animationEnabled: true,
      showDataLabels: true,
      chartType: 'line'
    }
  };

  const config = { ...defaultConfig, ...userConfig };
  const [configState, setConfigState] = useLocalStorage('dashboard-config', config);

  // Custom hooks for data management
  const {
    data: learningData,
    loading,
    error,
    refetch,
    historicalData
  } = useLearningData(agentId, selectedTimeframe, isRealTimeEnabled);

  const {
    isConnected,
    lastMessage,
    sendMessage
  } = useWebSocket(`/api/v1/agents/${agentId}/learning-stream`);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const message: WebSocketMessage = JSON.parse(lastMessage.data);

    switch (message.type) {
      case 'milestone_achieved':
        const milestone = message.data as LearningMilestone;
        setCelebrationQueue(prev => [...prev, milestone]);
        setShowCelebration(true);
        break;

      case 'metric_update':
        // Data will be refreshed via the learning data hook
        refetch();
        break;

      case 'alert':
        // Handle alerts
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [lastMessage, refetch]);

  // Process celebration queue
  useEffect(() => {
    if (celebrationQueue.length > 0 && !showCelebration) {
      setShowCelebration(true);
    }
  }, [celebrationQueue, showCelebration]);

  const currentMilestone = useMemo(() => {
    return celebrationQueue[0];
  }, [celebrationQueue]);

  const handleCelebrationComplete = useCallback(() => {
    setCelebrationQueue(prev => prev.slice(1));
    setShowCelebration(false);
  }, []);

  const handleTimeframeChange = useCallback((timeframeId: string) => {
    setSelectedTimeframe(timeframeId);
    refetch();
  }, [refetch]);

  const handleExport = useCallback(async (format: string) => {
    try {
      const response = await fetch(`/api/v1/agents/${agentId}/export/${format}?timeframe=${selectedTimeframe}`);
      const result = await response.json();

      if (result.success) {
        // Trigger download
        const link = document.createElement('a');
        link.href = result.downloadUrl;
        link.download = result.filename;
        link.click();
      }
    } catch (error) {
      console.error('Export failed:', error);
    }
  }, [agentId, selectedTimeframe]);

  const toggleRealTime = useCallback(() => {
    setIsRealTimeEnabled(prev => !prev);
  }, []);

  if (loading && !learningData) {
    return (
      <div className={`flex items-center justify-center min-h-screen bg-gray-900 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading intelligence metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center min-h-screen bg-gray-900 ${className}`}>
        <div className="text-center p-8 bg-red-900/20 rounded-lg border border-red-500">
          <h3 className="text-red-400 text-lg font-semibold mb-2">Error Loading Data</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!learningData) {
    return (
      <div className={`flex items-center justify-center min-h-screen bg-gray-900 ${className}`}>
        <div className="text-center p-8 bg-yellow-900/20 rounded-lg border border-yellow-500">
          <h3 className="text-yellow-400 text-lg font-semibold mb-2">No Data Available</h3>
          <p className="text-gray-400">No learning data found for this agent.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-900 text-white p-6 ${className}`}>
      {/* Header */}
      <header className="mb-8">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Intelligence Growth Dashboard</h1>
            <div className="flex items-center space-x-4 text-gray-400">
              <span>Agent: {learningData.agentName}</span>
              <span>•</span>
              <span>Level {learningData.level} {learningData.characterClass}</span>
              <span>•</span>
              <span className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                {isConnected ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Real-time toggle */}
            <button
              onClick={toggleRealTime}
              className={`px-4 py-2 rounded-lg transition-colors ${
                isRealTimeEnabled
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-700 hover:bg-gray-600'
              }`}
            >
              {isRealTimeEnabled ? '🟢 Live' : '⏸ Paused'}
            </button>

            {/* Refresh button */}
            <button
              onClick={refetch}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              🔄 Refresh
            </button>

            {/* Export dropdown */}
            <ExportPanel
              formats={configState.exportFormats}
              onExport={handleExport}
              className="relative"
            />
          </div>
        </div>

        {/* Timeframe selector */}
        <div className="flex space-x-2">
          {configState.timeframes.map(timeframe => (
            <button
              key={timeframe.id}
              onClick={() => handleTimeframeChange(timeframe.id)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                selectedTimeframe === timeframe.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {timeframe.label}
            </button>
          ))}
        </div>
      </header>

      {/* Alert System */}
      <AlertSystem
        thresholds={configState.alertThresholds}
        metrics={learningData}
        className="mb-6"
      />

      {/* Key Metrics Overview */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Current IQ"
          value={learningData.intelligenceMetrics.currentIQ}
          change={learningData.intelligenceMetrics.currentIQ - learningData.intelligenceMetrics.baselineIQ}
          changeType="increase"
          icon="🧠"
          color="blue"
        />

        <MetricCard
          title="Learning Velocity"
          value={learningData.intelligenceMetrics.learningVelocity}
          change={0}
          changeType="neutral"
          icon="📈"
          color="green"
          suffix="pts/hr"
        />

        <MetricCard
          title="Memory Usage"
          value={`${Math.round(learningData.memoryMetrics.memoryUtilization * 100)}%`}
          change={0}
          changeType="neutral"
          icon="💾"
          color="purple"
        />

        <MetricCard
          title="Skill Mastery"
          value={learningData.skillMetrics.masteryDistribution.filter(m => m === 'expert' || m === 'master').length}
          change={0}
          changeType="neutral"
          icon="⭐"
          color="yellow"
          suffix="skills"
        />
      </section>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* IQ Progression Chart */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Intelligence Quotient Progression</h3>
          <IQProgressionChart
            data={learningData.intelligenceMetrics.iqProgression}
            config={configState.chartPreferences}
          />
        </div>

        {/* Skills Radar Chart */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Skill Development Radar</h3>
          <SkillRadarChart
            skills={[
              ...learningData.skillMetrics.combatSkills,
              ...learningData.skillMetrics.socialSkills,
              ...learningData.skillMetrics.strategicSkills
            ]}
            config={configState.chartPreferences}
          />
        </div>

        {/* Memory Usage Chart */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Memory System Analysis</h3>
          <MemoryUsageChart
            memoryMetrics={learningData.memoryMetrics}
            config={configState.chartPreferences}
          />
        </div>

        {/* Learning Velocity Chart */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">Learning Velocity & Retention</h3>
          <LearningVelocityChart
            velocity={learningData.intelligenceMetrics.learningVelocity}
            retention={learningData.intelligenceMetrics.retentionRate}
            historicalData={historicalData}
            config={configState.chartPreferences}
          />
        </div>
      </div>

      {/* Strategic Improvements */}
      <section className="bg-gray-800 p-6 rounded-lg mb-8">
        <h3 className="text-lg font-semibold mb-4">Strategic Decision-Making Improvements</h3>
        <StrategicImprovementChart
          improvements={learningData.learningInsights.strategicImprovements}
          config={configState.chartPreferences}
        />
      </section>

      {/* Two Column Layout for Bottom Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Lessons */}
        <RecentLessonsPanel
          lessons={learningData.learningInsights.recentLessons}
          className="bg-gray-800 p-6 rounded-lg"
        />

        {/* Performance Comparison */}
        <PerformanceComparison
          baseline={learningData.performanceBenchmarks.baselineComparison}
          peer={learningData.performanceBenchmarks.peerComparison}
          personalBests={learningData.performanceBenchmarks.personalBests}
          className="bg-gray-800 p-6 rounded-lg"
        />
      </div>

      {/* Milestone Celebration Modal */}
      {showCelebration && currentMilestone && (
        <MilestoneCelebration
          milestone={currentMilestone}
          onComplete={handleCelebrationComplete}
          agentName={learningData.agentName}
        />
      )}
    </div>
  );
};

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: number | string;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: string;
  color: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
  suffix?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeType,
  icon,
  color,
  suffix = ''
}) => {
  const colorClasses = {
    blue: 'bg-blue-900/20 border-blue-500',
    green: 'bg-green-900/20 border-green-500',
    purple: 'bg-purple-900/20 border-purple-500',
    yellow: 'bg-yellow-900/20 border-yellow-500',
    red: 'bg-red-900/20 border-red-500'
  };

  const changeColorClasses = {
    increase: 'text-green-400',
    decrease: 'text-red-400',
    neutral: 'text-gray-400'
  };

  return (
    <div className={`p-6 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        {change !== 0 && (
          <span className={`text-sm ${changeColorClasses[changeType]}`}>
            {changeType === 'increase' ? '↑' : changeType === 'decrease' ? '↓' : '→'}
            {' '}{Math.abs(change)}{suffix}
          </span>
        )}
      </div>
      <h3 className="text-gray-400 text-sm mb-1">{title}</h3>
      <p className="text-2xl font-bold">
        {value}{suffix}
      </p>
    </div>
  );
};