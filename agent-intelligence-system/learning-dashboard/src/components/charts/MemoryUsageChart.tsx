import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import { MemoryMetrics, ChartPreferences } from '../../types';

interface MemoryUsageChartProps {
  memoryMetrics: MemoryMetrics;
  config: ChartPreferences;
  height?: number;
}

export const MemoryUsageChart: React.FC<MemoryUsageChartProps> = ({
  memoryMetrics,
  config,
  height = 350
}) => {
  const memoryUsageData = useMemo(() => {
    return [
      {
        name: 'Episodic',
        used: memoryMetrics.episodicMemories.count,
        capacity: memoryMetrics.episodicMemories.capacity,
        utilization: (memoryMetrics.episodicMemories.count / memoryMetrics.episodicMemories.capacity) * 100,
        importance: memoryMetrics.episodicMemories.averageImportance,
        retention: memoryMetrics.episodicMemories.retentionRate
      },
      {
        name: 'Semantic',
        used: memoryMetrics.semanticMemories.count,
        capacity: memoryMetrics.semanticMemories.capacity,
        utilization: (memoryMetrics.semanticMemories.count / memoryMetrics.semanticMemories.capacity) * 100,
        importance: memoryMetrics.semanticMemories.averageImportance,
        retention: memoryMetrics.semanticMemories.retentionRate
      },
      {
        name: 'Procedural',
        used: memoryMetrics.proceduralMemories.count,
        capacity: memoryMetrics.proceduralMemories.capacity,
        utilization: (memoryMetrics.proceduralMemories.count / memoryMetrics.proceduralMemories.capacity) * 100,
        importance: memoryMetrics.proceduralMemories.averageImportance,
        retention: memoryMetrics.proceduralMemories.retentionRate
      },
      {
        name: 'Social',
        used: memoryMetrics.socialMemories.count,
        capacity: memoryMetrics.socialMemories.capacity,
        utilization: (memoryMetrics.socialMemories.count / memoryMetrics.socialMemories.capacity) * 100,
        importance: memoryMetrics.socialMemories.averageImportance,
        retention: memoryMetrics.socialMemories.retentionRate
      }
    ];
  }, [memoryMetrics]);

  const consolidationData = useMemo(() => {
    return memoryUsageData.map(type => ({
      name: type.name,
      value: type.consolidationRate * 100,
      fill: type.consolidationRate > 0.7 ? '#10B981' : type.consolidationRate > 0.4 ? '#F59E0B' : '#EF4444'
    }));
  }, [memoryUsageData]);

  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    orange: '#F97316',
    red: '#EF4444',
    yellow: '#F59E0B',
    teal: '#14B8A6'
  };

  const chartColors = useMemo(() => {
    const schemes: Record<string, string[]> = {
      viridis: [colors.blue, colors.teal, colors.green, colors.yellow],
      plasma: [colors.purple, colors.pink, colors.red, colors.orange],
      warm: [colors.red, colors.orange, colors.yellow, colors.pink],
      cool: [colors.blue, colors.teal, colors.green, colors.purple]
    };
    return schemes[config.colorScheme] || schemes.viridis;
  }, [config.colorScheme]);

  const getBarColor = (utilization: number) => {
    if (utilization > 90) return colors.red;
    if (utilization > 75) return colors.yellow;
    return colors.green;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold mb-2">{label} Memory</p>
          <p className="text-blue-400">Usage: {data.used} / {data.capacity}</p>
          <p className="text-yellow-400">Utilization: {data.utilization.toFixed(1)}%</p>
          <p className="text-green-400">Importance: {(data.importance * 100).toFixed(1)}%</p>
          <p className="text-purple-400">Retention: {(data.retention * 100).toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  const totalCapacity = useMemo(() => {
    return memoryUsageData.reduce((sum, type) => sum + type.capacity, 0);
  }, [memoryUsageData]);

  const totalUsed = useMemo(() => {
    return memoryUsageData.reduce((sum, type) => sum + type.used, 0);
  }, [memoryUsageData]);

  const averageRetention = useMemo(() => {
    const totalRetention = memoryUsageData.reduce((sum, type) => sum + type.retention, 0);
    return (totalRetention / memoryUsageData.length) * 100;
  }, [memoryUsageData]);

  const memoryEfficiency = useMemo(() => {
    const weightedImportance = memoryUsageData.reduce((sum, type) =>
      sum + (type.importance * type.used), 0
    );
    return totalUsed > 0 ? (weightedImportance / totalUsed) * 100 : 0;
  }, [memoryUsageData, totalUsed]);

  return (
    <div className="w-full">
      {/* Memory Overview Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Total Used</p>
          <p className="text-lg font-bold text-blue-400">{totalUsed.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Total Capacity</p>
          <p className="text-lg font-bold text-green-400">{totalCapacity.toLocaleString()}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Avg Retention</p>
          <p className="text-lg font-bold text-purple-400">{averageRetention.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Efficiency</p>
          <p className="text-lg font-bold text-yellow-400">{memoryEfficiency.toFixed(1)}%</p>
        </div>
      </div>

      {/* Main Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Memory Usage Bar Chart */}
        <div>
          <h4 className="text-white font-semibold mb-3">Memory Usage by Type</h4>
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={memoryUsageData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="name"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
              />
              <YAxis
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="used"
                name="Used Memory"
                animationDuration={config.animationEnabled ? 1000 : 0}
                radius={[8, 8, 0, 0]}
              >
                {memoryUsageData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={chartColors[index]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Consolidation Rate Pie Chart */}
        <div>
          <h4 className="text-white font-semibold mb-3">Consolidation Rates</h4>
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={consolidationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                animationDuration={config.animationEnabled ? 1200 : 0}
              >
                {consolidationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-gray-800 p-2 rounded border border-gray-700">
                        <p className="text-white text-sm">{payload[0].name}</p>
                        <p className="text-gray-300 text-sm">
                          Consolidation: {payload[0].value.toFixed(1)}%
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Memory Access Patterns */}
      {memoryMetrics.accessPatterns && memoryMetrics.accessPatterns.length > 0 && (
        <div className="mt-6">
          <h4 className="text-white font-semibold mb-3">Recent Access Patterns</h4>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {memoryMetrics.accessPatterns.slice(0, 4).map((pattern, index) => (
              <div key={index} className="bg-gray-900 p-3 rounded-lg">
                <p className="text-gray-400 text-sm capitalize">{pattern.memoryType}</p>
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Frequency:</span>
                    <span className="text-blue-400">{pattern.accessFrequency}/day</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Accuracy:</span>
                    <span className="text-green-400">{(pattern.retrievalAccuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Importance:</span>
                    <span className="text-yellow-400">{(pattern.importanceScore * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Memory Health Insights */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Memory System Health</h4>
        <div className="space-y-2 text-sm">
          {memoryMetrics.memoryUtilization > 0.9 && (
            <p className="text-red-400">⚠️ Critical: Memory utilization is above 90%. Consider memory consolidation.</p>
          )}
          {memoryMetrics.memoryUtilization > 0.75 && memoryMetrics.memoryUtilization <= 0.9 && (
            <p className="text-yellow-400">⚡ Warning: Memory usage is high. Monitor for optimal performance.</p>
          )}
          {averageRetention > 80 && (
            <p className="text-green-400">✅ Excellent: Memory retention rates are very high.</p>
          )}
          {memoryEfficiency > 80 && (
            <p className="text-purple-400">🎯 Efficient: Memory storage is highly optimized with important memories prioritized.</p>
          )}
          {memoryMetrics.consolidationRate > 0.7 && (
            <p className="text-blue-400">🔄 Active: Memory consolidation is processing effectively.</p>
          )}
        </div>
      </div>
    </div>
  );
};