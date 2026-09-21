import React, { useMemo } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { SkillProgress, ChartPreferences } from '../../types';

interface SkillRadarChartProps {
  skills: SkillProgress[];
  config: ChartPreferences;
  height?: number;
}

export const SkillRadarChart: React.FC<SkillRadarChartProps> = ({
  skills,
  config,
  height = 400
}) => {
  const chartData = useMemo(() => {
    // Group skills by type and calculate average progress
    const skillGroups = skills.reduce((acc, skill) => {
      if (!acc[skill.skillType]) {
        acc[skill.skillType] = [];
      }
      acc[skill.skillType].push(skill);
      return acc;
    }, {} as Record<string, SkillProgress[]>);

    return Object.entries(skillGroups).map(([type, typeSkills]) => {
      const avgLevel = typeSkills.reduce((sum, skill) => sum + skill.currentLevel, 0) / typeSkills.length;
      const avgProgress = typeSkills.reduce((sum, skill) => sum + (skill.currentXP / skill.nextLevelXP), 0) / typeSkills.length;
      const totalXP = typeSkills.reduce((sum, skill) => sum + skill.totalXP, 0);
      const avgSuccessRate = typeSkills.reduce((sum, skill) => sum + skill.successRate, 0) / typeSkills.length;

      return {
        skillType: type.charAt(0).toUpperCase() + type.slice(1),
        level: Math.round(avgLevel * 20), // Scale to 0-100 for radar chart
        progress: Math.round(avgProgress * 100),
        experience: Math.min(100, Math.round(totalXP / 100)), // Normalize XP
        successRate: Math.round(avgSuccessRate * 100),
        fullMark: 100
      };
    });
  }, [skills]);

  const masteryDistribution = useMemo(() => {
    const distribution = { novice: 0, apprentice: 0, journeyman: 0, expert: 0, master: 0 };
    skills.forEach(skill => {
      distribution[skill.masteryLevel]++;
    });
    return distribution;
  }, [skills]);

  const colors = {
    blue: '#3B82F6',
    green: '#10B981',
    purple: '#8B5CF6',
    orange: '#F97316',
    red: '#EF4444',
    pink: '#EC4899',
    yellow: '#F59E0B',
    teal: '#14B8A6'
  };

  const chartColors = useMemo(() => {
    const schemes: Record<string, string[]> = {
      viridis: [colors.blue, colors.teal, colors.green, colors.yellow, colors.orange],
      plasma: [colors.purple, colors.pink, colors.red, colors.orange, colors.yellow],
      warm: [colors.red, colors.orange, colors.yellow, colors.pink, colors.purple],
      cool: [colors.blue, colors.teal, colors.green, colors.purple, colors.pink]
    };
    return schemes[config.colorScheme] || schemes.viridis;
  }, [config.colorScheme]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-800 p-3 rounded-lg border border-gray-700">
          <p className="text-white font-semibold mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const topSkills = useMemo(() => {
    return skills
      .sort((a, b) => b.currentLevel - a.currentLevel)
      .slice(0, 3);
  }, [skills]);

  const emergingSkills = useMemo(() => {
    return skills
      .filter(skill => skill.masteryLevel === 'apprentice' && skill.progressRate > 0.5)
      .sort((a, b) => b.progressRate - a.progressRate)
      .slice(0, 3);
  }, [skills]);

  return (
    <div className="w-full">
      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={chartData} margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
          <PolarGrid
            gridType="polygon"
            stroke="#374151"
            radialLines={true}
          />
          <PolarAngleAxis
            dataKey="skillType"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            className="font-medium"
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickCount={6}
          />
          <Tooltip content={<CustomTooltip />} />

          {config.showDataLabels && (
            <Legend
              wrapperStyle={{ color: '#9CA3AF', fontSize: 12 }}
              verticalAlign="top"
              height={36}
            />
          )}

          <Radar
            name="Skill Level"
            dataKey="level"
            stroke={chartColors[0]}
            fill={chartColors[0]}
            fillOpacity={0.6}
            strokeWidth={2}
            animationDuration={config.animationEnabled ? 1000 : 0}
          />

          <Radar
            name="Progress"
            dataKey="progress"
            stroke={chartColors[1]}
            fill={chartColors[1]}
            fillOpacity={0.4}
            strokeWidth={2}
            animationDuration={config.animationEnabled ? 1200 : 0}
          />

          <Radar
            name="Success Rate"
            dataKey="successRate"
            stroke={chartColors[2]}
            fill={chartColors[2]}
            fillOpacity={0.3}
            strokeWidth={2}
            animationDuration={config.animationEnabled ? 1400 : 0}
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Skill Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {/* Top Skills */}
        <div className="bg-gray-900 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-3 flex items-center">
            🏆 Top Skills
          </h4>
          <div className="space-y-2">
            {topSkills.map((skill, index) => (
              <div key={skill.skillId} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                  </span>
                  <span className="text-gray-300 text-sm">{skill.skillName}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-white text-sm font-medium">Lvl {skill.currentLevel}</span>
                  <div className="w-16 bg-gray-700 rounded-full h-1.5">
                    <div
                      className="bg-green-500 h-1.5 rounded-full"
                      style={{ width: `${(skill.currentXP / skill.nextLevelXP) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Emerging Skills */}
        <div className="bg-gray-900 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-3 flex items-center">
            🌟 Rapidly Improving
          </h4>
          <div className="space-y-2">
            {emergingSkills.length > 0 ? (
              emergingSkills.map((skill) => (
                <div key={skill.skillId} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm">{skill.skillName}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-400 text-sm">+{(skill.progressRate * 100).toFixed(1)}%</span>
                    <span className="text-gray-400 text-sm">Lvl {skill.currentLevel}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm italic">No rapidly improving skills detected</p>
            )}
          </div>
        </div>
      </div>

      {/* Mastery Distribution */}
      <div className="mt-4 p-3 bg-gray-900 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Mastery Distribution</h4>
        <div className="flex space-x-4 text-sm">
          {Object.entries(masteryDistribution).map(([level, count]) => (
            <div key={level} className="flex items-center space-x-1">
              <span className="text-gray-400 capitalize">{level}:</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};