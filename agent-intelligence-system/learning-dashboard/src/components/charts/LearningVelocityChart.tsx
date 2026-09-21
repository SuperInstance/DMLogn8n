import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ComposedChart, Bar } from 'recharts';
import { ChartPreferences, HistoricalDataResponse } from '../../types';

interface LearningVelocityChartProps {
  velocity: number;
  retention: number;
  historicalData?: HistoricalDataResponse['data'] | null;
  config: ChartPreferences;
  height?: number;
}

export const LearningVelocityChart: React.FC<LearningVelocityChartProps> = ({
  velocity,
  retention,
  historicalData,
  config,
  height = 300
}) => {
  const chartData = useMemo(() => {
    if (!historicalData) {
      // Generate sample data if no historical data available
      const now = new Date();
      return Array.from({ length: 30 }, (_, i) => {
        const date = new Date(now.getTime() - (29 - i) * 24 * 60 * 60 * 1000);
        const baseVelocity = velocity * (0.8 + Math.random() * 0.4);
        const baseRetention = retention * (0.85 + Math.random() * 0.15);

        return {
          date: date.toLocaleDateString(),
          fullDate: date,
          velocity: Math.max(0, baseVelocity + (Math.random() - 0.5) * 0.2),
          retention: Math.min(100, Math.max(0, baseRetention + (Math.random() - 0.5) * 10)),
          efficiency: (baseVelocity * baseRetention) / 100,
          learningEvents: Math.floor(Math.random() * 10) + 5
        };
      });
    }

    // Process real historical data
    const allData = [];
    const timeframes = ['daily', 'weekly', 'monthly'];

    timeframes.forEach(timeframe => {
      if (historicalData[timeframe]) {
        historicalData[timeframe].forEach(data => {
          allData.push({
            date: new Date(data.timestamp).toLocaleDateString(),
            fullDate: new Date(data.timestamp),
            velocity: data.intelligenceMetrics.learningVelocity,
            retention: data.intelligenceMetrics.retentionRate * 100,
            efficiency: data.intelligenceMetrics.learningVelocity * data.intelligenceMetrics.retentionRate,
            learningEvents: data.metaLearningMetrics.selfReflectionQuality * 20
          });
        });
      }
    });

    return allData.sort((a, b) => a.fullDate.getTime() - b.fullDate.getTime());
  }, [velocity, retention, historicalData]);

  const trendlines = useMemo(() => {
    if (chartData.length < 2) return { velocity: 0, retention: 0, efficiency: 0 };

    const calculateTrend = (key: 'velocity' | 'retention' | 'efficiency') => {
      const n = chartData.length;
      const firstHalf = chartData.slice(0, Math.floor(n / 2));
      const secondHalf = chartData.slice(Math.floor(n / 2));

      const firstAvg = firstHalf.reduce((sum, d) => sum + d[key], 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((sum, d) => sum + d[key], 0) / secondHalf.length;

      return ((secondAvg - firstAvg) / firstAvg) * 100;
    };

    return {
      velocity: calculateTrend('velocity'),
      retention: calculateTrend('retention'),
      efficiency: calculateTrend('efficiency')
    };
  }, [chartData]);

  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    orange: '#F97316',
    red: '#EF4444',
    teal: '#14B8A6',
    yellow: '#F59E0B'
  };

  const chartColors = useMemo(() => {
    const schemes: Record<string, any> = {
      viridis: { primary: colors.blue, secondary: colors.teal, tertiary: colors.green },
      plasma: { primary: colors.purple, secondary: colors.pink, tertiary: colors.red },
      warm: { primary: colors.orange, secondary: colors.red, tertiary: colors.yellow },
      cool: { primary: colors.blue, secondary: colors.teal, tertiary: colors.purple }
    };
    return schemes[config.colorScheme] || schemes.viridis;
  }, [config.colorScheme]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold mb-2">{label}</p>
          <p className="text-blue-400">Velocity: {data.velocity.toFixed(3)} pts/hr</p>
          <p className="text-green-400">Retention: {data.retention.toFixed(1)}%</p>
          <p className="text-purple-400">Efficiency: {data.efficiency.toFixed(3)}</p>
          <p className="text-orange-400">Learning Events: {data.learningEvents}</p>
        </div>
      );
    }
    return null;
  };

  const currentPerformance = useMemo(() => {
    const latest = chartData[chartData.length - 1];
    return {
      velocity: latest.velocity.toFixed(3),
      retention: latest.retention.toFixed(1),
      efficiency: latest.efficiency.toFixed(3)
    };
  }, [chartData]);

  const getPerformanceLevel = (value: number, metric: 'velocity' | 'retention' | 'efficiency') => {
    const thresholds = {
      velocity: [
        { max: 0.1, level: 'Slow', color: 'text-red-400' },
        { max: 0.3, level: 'Moderate', color: 'text-yellow-400' },
        { max: Infinity, level: 'Fast', color: 'text-green-400' }
      ],
      retention: [
        { max: 60, level: 'Poor', color: 'text-red-400' },
        { max: 80, level: 'Good', color: 'text-yellow-400' },
        { max: Infinity, level: 'Excellent', color: 'text-green-400' }
      ],
      efficiency: [
        { max: 0.1, level: 'Low', color: 'text-red-400' },
        { max: 0.25, level: 'Medium', color: 'text-yellow-400' },
        { max: Infinity, level: 'High', color: 'text-green-400' }
      ]
    };

    const levels = thresholds[metric];
    return levels.find(l => value <= l.max) || levels[levels.length - 1];
  };

  return (
    <div className="w-full">
      {/* Current Performance Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Learning Velocity</p>
          <p className={`text-xl font-bold ${getPerformanceLevel(Number(currentPerformance.velocity), 'velocity').color}`}>
            {currentPerformance.velocity} pts/hr
          </p>
          <p className={`text-xs ${trendlines.velocity >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trendlines.velocity >= 0 ? '↑' : '↓'} {Math.abs(trendlines.velocity).toFixed(1)}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Knowledge Retention</p>
          <p className={`text-xl font-bold ${getPerformanceLevel(Number(currentPerformance.retention), 'retention').color}`}>
            {currentPerformance.retention}%
          </p>
          <p className={`text-xs ${trendlines.retention >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trendlines.retention >= 0 ? '↑' : '↓'} {Math.abs(trendlines.retention).toFixed(1)}%
          </p>
        </div>
        <div className="text-center">
          <p className="text-gray-400 text-sm">Learning Efficiency</p>
          <p className={`text-xl font-bold ${getPerformanceLevel(Number(currentPerformance.efficiency), 'efficiency').color}`}>
            {currentPerformance.efficiency}
          </p>
          <p className={`text-xs ${trendlines.efficiency >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trendlines.efficiency >= 0 ? '↑' : '↓'} {Math.abs(trendlines.efficiency).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Main Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="colorVelocity" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColors.primary} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={chartColors.primary} stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColors.secondary} stopOpacity={0.6}/>
              <stop offset="95%" stopColor={chartColors.secondary} stopOpacity={0.1}/>
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="left"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            label={{ value: 'Velocity (pts/hr)', angle: -90, position: 'insideLeft', style: { fill: '#9CA3AF' } }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            label={{ value: 'Retention (%)', angle: 90, position: 'insideRight', style: { fill: '#9CA3AF' } }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Learning Events as Bars */}
          <Bar
            yAxisId="left"
            dataKey="learningEvents"
            fill={chartColors.tertiary}
            fillOpacity={0.3}
            name="Learning Events"
            animationDuration={config.animationEnabled ? 800 : 0}
          />

          {/* Velocity Area */}
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="velocity"
            stroke={chartColors.primary}
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorVelocity)"
            name="Learning Velocity"
            animationDuration={config.animationEnabled ? 1000 : 0}
          />

          {/* Retention Line */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="retention"
            stroke={chartColors.secondary}
            strokeWidth={2}
            dot={false}
            name="Knowledge Retention"
            animationDuration={config.animationEnabled ? 1200 : 0}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Learning Insights */}
      <div className="mt-6 space-y-3">
        <div className="bg-gray-900 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-2">Learning Performance Analysis</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-400 mb-1">Velocity Assessment:</p>
              <p className="text-white">
                {Number(currentPerformance.velocity) > 0.3
                  ? '🚀 Excellent learning pace. Agent is rapidly acquiring new knowledge and skills.'
                  : Number(currentPerformance.velocity) > 0.1
                  ? '📈 Good learning momentum. Consider introducing more complex challenges.'
                  : '🐌 Learning velocity is slow. May need motivation or curriculum adjustment.'}
              </p>
            </div>
            <div>
              <p className="text-gray-400 mb-1">Retention Analysis:</p>
              <p className="text-white">
                {Number(currentPerformance.retention) > 80
                  ? '🧠 Outstanding memory retention. Agent effectively consolidates learning.'
                  : Number(currentPerformance.retention) > 60
                  ? '💾 Good retention with room for improvement through review.'
                  : '⚠️ Poor retention detected. Implement spaced repetition and review strategies.'}
              </p>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-gray-900 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-2">Personalized Recommendations</h4>
          <ul className="space-y-2 text-sm text-gray-300">
            {trendlines.velocity < -10 && (
              <li>• Learning velocity declining - consider reducing difficulty or increasing motivation</li>
            )}
            {trendlines.retention < -5 && (
              <li>• Retention rates dropping - implement review sessions and memory consolidation</li>
            )}
            {Number(currentPerformance.efficiency) < 0.1 && (
              <li>• Low learning efficiency - focus on quality over quantity of experiences</li>
            )}
            {Number(currentPerformance.velocity) > 0.5 && Number(currentPerformance.retention) < 70 && (
              <li>• Fast learning but poor retention - add reflection and review periods</li>
            )}
            {Number(currentPerformance.velocity) < 0.1 && Number(currentPerformance.retention) > 80 && (
              >li>• Good retention but slow pace - increase challenge complexity and variety</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};