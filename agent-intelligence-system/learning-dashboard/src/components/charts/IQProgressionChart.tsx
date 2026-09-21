import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { IQDataPoint, ChartPreferences } from '../../types';

interface IQProgressionChartProps {
  data: IQDataPoint[];
  config: ChartPreferences;
  height?: number;
  showTrendline?: boolean;
}

export const IQProgressionChart: React.FC<IQProgressionChartProps> = ({
  data,
  config,
  height = 300,
  showTrendline = true
}) => {
  const chartData = useMemo(() => {
    return data.map(point => ({
      timestamp: new Date(point.timestamp).toLocaleDateString(),
      fullDate: new Date(point.timestamp),
      iq: point.iq,
      sessionId: point.sessionId,
      testType: point.testType,
      confidence: point.confidence,
      formattedTime: new Date(point.timestamp).toLocaleTimeString()
    })).sort((a, b) => a.fullDate.getTime() - b.fullDate.getTime());
  }, [data]);

  const trendlineData = useMemo(() => {
    if (chartData.length < 2) return [];

    // Simple linear regression for trendline
    const n = chartData.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    chartData.forEach((point, index) => {
      sumX += index;
      sumY += point.iq;
      sumXY += index * point.iq;
      sumX2 += index * index;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return chartData.map((point, index) => ({
      ...point,
      trend: slope * index + intercept
    }));
  }, [chartData]);

  const averageIQ = useMemo(() => {
    if (chartData.length === 0) return 0;
    return Math.round(chartData.reduce((sum, point) => sum + point.iq, 0) / chartData.length);
  }, [chartData]);

  const peakIQ = useMemo(() => {
    if (chartData.length === 0) return 0;
    return Math.max(...chartData.map(point => point.iq));
  }, [chartData]);

  const improvementRate = useMemo(() => {
    if (chartData.length < 2) return 0;
    const first = chartData[0].iq;
    const last = chartData[chartData.length - 1].iq;
    return ((last - first) / first * 100).toFixed(1);
  }, [chartData]);

  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    orange: '#F97316',
    red: '#EF4444'
  };

  const chartColors = useMemo(() => {
    const schemes: Record<string, any> = {
      viridis: { primary: colors.blue, secondary: colors.purple },
      plasma: { primary: colors.purple, secondary: colors.pink },
      warm: { primary: colors.orange, secondary: colors.red },
      cool: { primary: colors.blue, secondary: colors.green }
    };
    return schemes[config.colorScheme] || schemes.viridis;
  }, [config.colorScheme]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold">{label}</p>
          <p className="text-blue-400">IQ: {data.iq}</p>
          <p className="text-gray-400 text-sm">Session: {data.sessionId}</p>
          <p className="text-gray-400 text-sm">Type: {data.testType}</p>
          <p className="text-gray-400 text-sm">Confidence: {(data.confidence * 100).toFixed(1)}%</p>
          {showTrendline && data.trend && (
            <p className="text-purple-400 text-sm">Trend: {Math.round(data.trend)}</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Average IQ</p>
          <p className="text-xl font-bold text-blue-400">{averageIQ}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Peak IQ</p>
          <p className="text-xl font-bold text-green-400">{peakIQ}</p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Improvement</p>
          <p className={`text-xl font-bold ${Number(improvementRate) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {Number(improvementRate) >= 0 ? '+' : ''}{improvementRate}%
          </p>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={trendlineData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="colorIQ" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0.1}/>
            </linearGradient>
            {showTrendline && (
              <linearGradient id="colorTrend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColors.secondary} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={chartColors.secondary} stopOpacity={0}/>
              </linearGradient>
            )}
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="timestamp"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
          />
          <YAxis
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            domain={['dataMin - 5', 'dataMax + 5']}
          />
          <Tooltip content={<CustomTooltip />} />
          {config.showDataLabels && (
            <Legend
              wrapperStyle={{ color: '#9CA3AF' }}
            />
          )}

          <Area
            type="monotone"
            dataKey="iq"
            stroke={chartColors.primary}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorIQ)"
            name="IQ Score"
            animationDuration={config.animationEnabled ? 1000 : 0}
          />

          {showTrendline && (
            <Line
              type="monotone"
              dataKey="trend"
              stroke={chartColors.secondary}
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="Trend"
              animationDuration={config.animationEnabled ? 1500 : 0}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>

      {/* Insights */}
      <div className="mt-4 p-3 bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-400">
          {Number(improvementRate) > 10
            ? '🚀 Excellent progress! Agent shows rapid cognitive development.'
            : Number(improvementRate) > 0
            ? '📈 Positive growth trajectory. Agent is consistently improving.'
            : Number(improvementRate) === 0
            ? '➡️ Stable performance. Consider introducing new challenges.'
            : '📉 Performance decline detected. Review learning strategies.'
          }
        </p>
      </div>
    </div>
  );
};