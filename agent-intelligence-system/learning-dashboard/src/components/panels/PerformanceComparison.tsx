import React, { useMemo } from 'react';
import { BaselineComparison, PeerComparison, PersonalBest } from '../../types';

interface PerformanceComparisonProps {
  baseline: BaselineComparison;
  peer: PeerComparison;
  personalBests: PersonalBest[];
  className?: string;
}

export const PerformanceComparison: React.FC<PerformanceComparisonProps> = ({
  baseline,
  peer,
  personalBests,
  className = ''
}) => {
  const skillImprovements = useMemo(() => {
    return Object.entries(baseline.skillImprovements).map(([skill, improvement]) => ({
      skill: skill.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      improvement: improvement,
      color: improvement > 50 ? 'text-green-400' : improvement > 20 ? 'text-yellow-400' : improvement > 0 ? 'text-blue-400' : 'text-gray-400'
    })).sort((a, b) => b.improvement - a.improvement);
  }, [baseline.skillImprovements]);

  const topPersonalBests = useMemo(() => {
    return personalBests
      .sort((a, b) => {
        // Prioritize recent achievements
        const aRecency = new Date(a.achievedAt).getTime();
        const bRecency = new Date(b.achievedAt).getTime();
        const recencyDiff = bRecency - aRecency;

        // If within 7 days, prioritize recency, otherwise prioritize value
        if (Math.abs(recencyDiff) < 7 * 24 * 60 * 60 * 1000) {
          return recencyDiff;
        }

        return b.value - a.value;
      })
      .slice(0, 5);
  }, [personalBests]);

  const getPerformanceGrade = (percentile: number) => {
    if (percentile >= 90) return { grade: 'S+', color: 'text-purple-400', label: 'Elite' };
    if (percentile >= 80) return { grade: 'S', color: 'text-blue-400', label: 'Excellent' };
    if (percentile >= 70) return { grade: 'A', color: 'text-green-400', label: 'Great' };
    if (percentile >= 60) return { grade: 'B', color: 'text-yellow-400', label: 'Good' };
    if (percentile >= 50) return { grade: 'C', color: 'text-orange-400', label: 'Average' };
    return { grade: 'D', color: 'text-red-400', label: 'Developing' };
  };

  const getImprovementLevel = (improvement: number) => {
    if (improvement > 100) return { level: 'Exceptional', color: 'text-purple-400', icon: '🚀' };
    if (improvement > 50) return { level: 'Outstanding', color: 'text-blue-400', icon: '⭐' };
    if (improvement > 25) return { level: 'Excellent', color: 'text-green-400', icon: '📈' };
    if (improvement > 10) return { level: 'Good', color: 'text-yellow-400', icon: '👍' };
    if (improvement > 0) return { level: 'Modest', color: 'text-orange-400', icon: '📊' };
    return { level: 'Decline', color: 'text-red-400', icon: '📉' };
  };

  const currentGrade = getPerformanceGrade(peer.percentileRank);
  const iqImprovementLevel = getImprovementLevel(baseline.improvementPercentage);

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - new Date(date).getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    return `${Math.floor(diffInHours / 24)}d ago`;
  };

  return (
    <div className={className}>
      <h3 className="text-lg font-semibold mb-4">Performance Comparison</h3>

      {/* Overall Performance Grade */}
      <div className="bg-gray-900 p-6 rounded-lg mb-6 text-center">
        <div className="mb-4">
          <span className={`text-6xl font-bold ${currentGrade.color}`}>{currentGrade.grade}</span>
        </div>
        <h4 className={`text-xl font-semibold ${currentGrade.color} mb-2`}>{currentGrade.label}</h4>
        <p className="text-gray-400 mb-4">
          Ranked {peer.percentileRank}th out of {peer.totalAgents.toLocaleString()} agents
        </p>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-500">Above Average In</p>
            <div className="flex flex-wrap gap-1 mt-1">
              {peer.aboveAverageIn.slice(0, 3).map((area, index) => (
                <span key={index} className="px-2 py-1 bg-green-900/30 text-green-400 rounded text-xs">
                  {area}
                </span>
              ))}
              {peer.aboveAverageIn.length > 3 && (
                <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                  +{peer.aboveAverageIn.length - 3} more
                </span>
              )}
            </div>
          </div>
          <div>
            <p className="text-gray-500">Below Average In</p>
            <div className="flex flex-wrap gap-1 mt-1">
              {peer.belowAverageIn.slice(0, 3).map((area, index) => (
                <span key={index} className="px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs">
                  {area}
                </span>
              ))}
              {peer.belowAverageIn.length > 3 && (
                <span className="px-2 py-1 bg-gray-700 text-gray-400 rounded text-xs">
                  +{peer.belowAverageIn.length - 3} more
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Baseline Comparison */}
      <div className="bg-gray-800 p-4 rounded-lg mb-6">
        <h4 className="text-white font-semibold mb-3 flex items-center">
          <span className="mr-2">🎯</span>
          Baseline Progress Comparison
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <span className="text-3xl mr-2">{iqImprovementLevel.icon}</span>
            <div className="text-2xl font-bold text-blue-400 mb-1">
              {baseline.currentIQ}
            </div>
            <p className="text-gray-400 text-sm">Current IQ</p>
            <p className={`text-sm ${iqImprovementLevel.color} font-medium mt-1`}>
              {baseline.baselineIQ} → {baseline.currentIQ} (+{baseline.improvementPercentage}%)
            </p>
            <p className="text-xs text-gray-500 mt-1">{iqImprovementLevel.level} Improvement</p>
          </div>

          <div className="text-center p-4 bg-gray-900 rounded-lg">
            <div className="text-2xl font-bold text-green-400 mb-1">
              {baseline.memoryEfficiencyImprovement > 0 ? '+' : ''}{baseline.memoryEfficiencyImprovement.toFixed(1)}%
            </div>
            <p className="text-gray-400 text-sm">Memory Efficiency</p>
            <div className="mt-2">
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, 50 + baseline.memoryEfficiencyImprovement))}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Skill Improvements */}
        <div>
          <p className="text-gray-400 text-sm mb-2">Skill Improvements Since Baseline:</p>
          <div className="grid grid-cols-2 gap-2">
            {skillImprovements.slice(0, 6).map((skill, index) => (
              <div key={skill.skill} className="flex items-center justify-between p-2 bg-gray-900 rounded">
                <span className="text-sm text-gray-300">{skill.skill}</span>
                <span className={`text-sm font-medium ${skill.color}`}>
                  {skill.improvement > 0 ? '+' : ''}{skill.improvement.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Personal Bests */}
      {topPersonalBests.length > 0 && (
        <div className="bg-gray-800 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-3 flex items-center">
            <span className="mr-2">🏆</span>
            Recent Personal Bests
          </h4>
          <div className="space-y-3">
            {topPersonalBests.map((best, index) => (
              <div key={best.metric} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅'}
                  </span>
                  <div>
                    <p className="text-white font-medium">{best.metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</p>
                    <p className="text-gray-400 text-xs">{best.context}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-blue-400 font-bold">{best.value}</p>
                  <p className="text-gray-500 text-xs">{formatTimeAgo(best.achievedAt)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Insights */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h4 className="text-white font-semibold mb-2">Performance Insights</h4>
        <div className="space-y-2 text-sm text-gray-300">
          {peer.percentileRank >= 80 && (
            <p>🌟 Elite performance! Agent is in the top {100 - peer.percentileRank}% of all agents.</p>
          )}
          {baseline.improvementPercentage > 50 && (
            <p>📈 Remarkable growth since baseline - agent is showing exceptional learning capacity.</p>
          )}
          {peer.aboveAverageIn.length > peer.belowAverageIn.length && (
            <p>⚖️ Well-balanced development with strengths in multiple domains.</p>
          )}
          {baseline.learningVelocityImprovement > 30 && (
            <p>🚀 Accelerated learning velocity - agent is becoming more efficient at acquiring new skills.</p>
          )}
          {topPersonalBests.length >= 3 && (
            <p>🎯 Consistent achievement of personal bests shows ongoing progress and motivation.</p>
          )}
        </div>
      </div>
    </div>
  );
};