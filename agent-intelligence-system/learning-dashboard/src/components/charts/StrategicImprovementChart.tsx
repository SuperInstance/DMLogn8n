import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ScatterChart, Scatter, Legend } from 'recharts';
import { StrategicImprovement, ChartPreferences } from '../../types';

interface StrategicImprovementChartProps {
  improvements: StrategicImprovement[];
  config: ChartPreferences;
  height?: number;
}

export const StrategicImprovementChart: React.FC<StrategicImprovementChartProps> = ({
  improvements,
  config,
  height = 400
}) => {
  const chartData = useMemo(() => {
    return improvements.map(improvement => ({
      area: improvement.area,
      before: improvement.beforeScore,
      after: improvement.afterScore,
      improvement: improvement.afterScore - improvement.beforeScore,
      improvementPercentage: ((improvement.afterScore - improvement.beforeScore) / improvement.beforeScore) * 100,
      type: improvement.improvementType,
      date: new Date(improvement.measuredAt).toLocaleDateString(),
      factors: improvement.contributingFactors.length,
      quality: improvement.contributingFactors.length > 2 ? 'high' : improvement.contributingFactors.length > 1 ? 'medium' : 'low'
    })).sort((a, b) => b.improvementPercentage - a.improvementPercentage);
  }, [improvements]);

  const scatterData = useMemo(() => {
    return chartData.map(item => ({
      x: item.before,
      y: item.after,
      z: Math.abs(item.improvementPercentage),
      area: item.area,
      improvement: item.improvementPercentage
    }));
  }, [chartData]);

  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    orange: '#F97316',
    red: '#EF4444',
    yellow: '#F59E0B',
    teal: '#14B8A6',
    pink: '#EC4899'
  };

  const getImprovementColor = (improvement: number) => {
    if (improvement > 50) return colors.green;
    if (improvement > 25) return colors.blue;
    if (improvement > 10) return colors.yellow;
    if (improvement > 0) return colors.orange;
    return colors.red;
  };

  const getTypeColor = (type: string) => {
    return type === 'quantitative' ? colors.blue : colors.purple;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold mb-2">{label || data.area}</p>
          <p className="text-gray-400">Before: {data.before}</p>
          <p className="text-green-400">After: {data.after}</p>
          <p className="text-blue-400">Improvement: {data.improvementPercentage.toFixed(1)}%</p>
          <p className="text-purple-400">Type: {data.type}</p>
          <p className="text-yellow-400">Factors: {data.factors}</p>
        </div>
      );
    }
    return null;
  };

  const ScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold mb-2">{data.area}</p>
          <p className="text-gray-400">Before: {data.x}</p>
          <p className="text-green-400">After: {data.y}</p>
          <p className="text-blue-400">Improvement: {data.improvement.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  // Group improvements by area for summary stats
  const areaStats = useMemo(() => {
    const stats = chartData.reduce((acc, item) => {
      if (!acc[item.area]) {
        acc[item.area] = {
          improvements: [],
          totalImprovement: 0,
          count: 0,
          avgImprovement: 0
        };
      }
      acc[item.area].improvements.push(item);
      acc[item.area].totalImprovement += item.improvementPercentage;
      acc[item.area].count += 1;
      acc[item.area].avgImprovement = acc[item.area].totalImprovement / acc[item.area].count;
      return acc;
    }, {} as Record<string, any>);

    return Object.entries(stats)
      .map(([area, data]: [string, any]) => ({
        area,
        ...data,
        bestImprovement: Math.max(...data.improvements.map((i: any) => i.improvementPercentage))
      }))
      .sort((a, b) => b.avgImprovement - a.avgImprovement);
  }, [chartData]);

  const overallStats = useMemo(() => {
    if (chartData.length === 0) return { totalImprovement: 0, avgImprovement: 0, totalAreas: 0 };

    const totalImprovement = chartData.reduce((sum, item) => sum + item.improvementPercentage, 0);
    const avgImprovement = totalImprovement / chartData.length;
    const totalAreas = new Set(chartData.map(item => item.area)).size;

    return {
      totalImprovement: totalImprovement.toFixed(1),
      avgImprovement: avgImprovement.toFixed(1),
      totalAreas,
      topArea: areaStats[0]?.area || 'N/A',
      topImprovement: areaStats[0]?.avgImprovement.toFixed(1) || '0'
    };
  }, [chartData, areaStats]);

  const improvementCategories = useMemo(() => {
    const categories = {
      dramatic: chartData.filter(item => item.improvementPercentage > 50).length,
      significant: chartData.filter(item => item.improvementPercentage > 25 && item.improvementPercentage <= 50).length,
      moderate: chartData.filter(item => item.improvementPercentage > 10 && item.improvementPercentage <= 25).length,
      minimal: chartData.filter(item => item.improvementPercentage > 0 && item.improvementPercentage <= 10).length,
      declined: chartData.filter(item => item.improvementPercentage <= 0).length
    };

    return Object.entries(categories)
      .filter(([_, count]) => count > 0)
      .map(([category, count]) => ({
        category: category.charAt(0).toUpperCase() + category.slice(1),
        count,
        color: category === 'dramatic' ? colors.green :
                category === 'significant' ? colors.blue :
                category === 'moderate' ? colors.yellow :
                category === 'minimal' ? colors.orange : colors.red
      }));
  }, [chartData]);

  return (
    <div className="w-full">
      {/* Overall Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Total Improvements</p>
          <p className="text-xl font-bold text-blue-400">{chartData.length}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Avg Improvement</p>
          <p className="text-xl font-bold text-green-400">{overallStats.avgImprovement}%</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Areas Improved</p>
          <p className="text-xl font-bold text-purple-400">{overallStats.totalAreas}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Top Area</p>
          <p className="text-lg font-bold text-yellow-400 truncate">{overallStats.topArea}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Best Performance</p>
          <p className="text-xl font-bold text-orange-400">{overallStats.topImprovement}%</p>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart - Improvements by Area */}
        <div>
          <h4 className="text-white font-semibold mb-3">Strategic Improvements by Area</h4>
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="area"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                label={{ value: 'Improvement %', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="improvementPercentage"
                name="Improvement %"
                radius={[8, 8, 0, 0]}
                animationDuration={config.animationEnabled ? 1000 : 0}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getImprovementColor(entry.improvementPercentage)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Scatter Chart - Before vs After */}
        <div>
          <h4 className="text-white font-semibold mb-3">Before vs After Performance</h4>
          <ResponsiveContainer width="100%" height={height}>
            <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                type="number"
                dataKey="x"
                name="Before"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                label={{ value: 'Before Score', position: 'insideBottom', offset: -5, style: { fill: '#9CA3AF' } }}
              />
              <YAxis
                type="number"
                dataKey="y"
                name="After"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                label={{ value: 'After Score', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
              />
              <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Scatter
                name="Strategic Improvements"
                data={scatterData}
                fill={colors.purple}
                animationDuration={config.animationEnabled ? 1200 : 0}
              >
                {scatterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getImprovementColor(entry.improvement)} />
                ))}
              </Scatter>
              {/* Reference line (y = x) */}
              <line
                x1={0}
                y1={0}
                x2={100}
                y2={100}
                stroke="#374151"
                strokeWidth={1}
                strokeDasharray="5 5"
              />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="text-gray-500 text-xs mt-2 text-center">Points above the line show improvement</p>
        </div>
      </div>

      {/* Improvement Categories */}
      <div className="mt-6">
        <h4 className="text-white font-semibold mb-3">Improvement Distribution</h4>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {improvementCategories.map((category) => (
            <div key={category.category} className="bg-gray-900 p-4 rounded-lg text-center">
              <div
                className="w-3 h-3 rounded-full mx-auto mb-2"
                style={{ backgroundColor: category.color }}
              ></div>
              <p className="text-white font-semibold">{category.count}</p>
              <p className="text-gray-400 text-sm">{category.category}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Area Rankings */}
      {areaStats.length > 0 && (
        <div className="mt-6">
          <h4 className="text-white font-semibold mb-3">Area Performance Rankings</h4>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {areaStats.slice(0, 6).map((area, index) => (
              <div key={area.area} className="bg-gray-900 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">
                      {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
                    </span>
                    <span className="text-white font-medium">{area.area}</span>
                  </div>
                  <span className="text-green-400 font-bold">+{area.avgImprovement.toFixed(1)}%</span>
                </div>
                <div className="text-sm text-gray-400">
                  {area.count} improvements • Best: +{area.bestImprovement.toFixed(1)}%
                </div>
                <div className="mt-2 w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${Math.min(100, area.avgImprovement * 2)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategic Insights */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Strategic Growth Insights</h4>
        <div className="space-y-2 text-sm text-gray-300">
          {Number(overallStats.avgImprovement) > 30 && (
            <p>🎯 Outstanding strategic development! Agent is showing rapid improvement in decision-making capabilities.</p>
          )}
          {areaStats.length >= 5 && (
            <p>🌟 Well-rounded growth across multiple strategic domains indicates comprehensive cognitive development.</p>
          )}
          {chartData.filter(item => item.type === 'quantitative').length > chartData.filter(item => item.type === 'qualitative').length && (
            <p>📊 Strong quantitative improvements suggest the agent is excelling in measurable performance metrics.</p>
          )}
          {chartData.filter(item => item.type === 'qualitative').length > chartData.filter(item => item.type === 'quantitative').length && (
            <p>🎨 Qualitative improvements indicate enhanced strategic thinking and creative problem-solving abilities.</p>
          )}
          {improvementCategories.find(cat => cat.category === 'Dramatic') && (
            <p>🚀 Breakthrough improvements detected in key strategic areas - these represent significant cognitive leaps.</p>
          )}
        </div>
      </div>
    </div>
  );
};