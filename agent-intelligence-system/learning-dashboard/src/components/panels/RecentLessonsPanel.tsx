import React, { useState, useMemo } from 'react';
import { LearningLesson } from '../../types';

interface RecentLessonsPanelProps {
  lessons: LearningLesson[];
  className?: string;
  maxItems?: number;
}

export const RecentLessonsPanel: React.FC<RecentLessonsPanelProps> = ({
  lessons,
  className = '',
  maxItems = 5
}) => {
  const [filter, setFilter] = useState<'all' | 'success' | 'failure' | 'insight' | 'breakthrough'>('all');
  const [sortBy, setSortBy] = useState<'recent' | 'impact' | 'retention'>('recent');

  const filteredAndSortedLessons = useMemo(() => {
    let filtered = lessons.filter(lesson =>
      filter === 'all' || lesson.lessonType === filter
    );

    // Sort based on selected criteria
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        case 'impact':
          return b.impact - a.impact;
        case 'retention':
          return b.retentionScore - a.retentionScore;
        default:
          return 0;
      }
    });

    return filtered.slice(0, maxItems);
  }, [lessons, filter, sortBy, maxItems]);

  const lessonStats = useMemo(() => {
    const stats = {
      total: lessons.length,
      success: lessons.filter(l => l.lessonType === 'success').length,
      failure: lessons.filter(l => l.lessonType === 'failure').length,
      insight: lessons.filter(l => l.lessonType === 'insight').length,
      breakthrough: lessons.filter(l => l.lessonType === 'breakthrough').length,
      avgImpact: lessons.length > 0 ? lessons.reduce((sum, l) => sum + l.impact, 0) / lessons.length : 0,
      highRetention: lessons.filter(l => l.retentionScore > 0.8).length
    };

    return stats;
  }, [lessons]);

  const getLessonIcon = (type: string) => {
    const icons = {
      success: '✅',
      failure: '❌',
      insight: '💡',
      breakthrough: '🎯'
    };
    return icons[type as keyof typeof icons] || '📚';
  };

  const getLessonColor = (type: string) => {
    const colors = {
      success: 'text-green-400 border-green-500 bg-green-900/20',
      failure: 'text-red-400 border-red-500 bg-red-900/20',
      insight: 'text-yellow-400 border-yellow-500 bg-yellow-900/20',
      breakthrough: 'text-purple-400 border-purple-500 bg-purple-900/20'
    };
    return colors[type as keyof typeof colors] || 'text-gray-400 border-gray-500 bg-gray-900/20';
  };

  const getImpactBadge = (impact: number) => {
    if (impact > 0.8) return { label: 'High', color: 'bg-red-500' };
    if (impact > 0.5) return { label: 'Medium', color: 'bg-yellow-500' };
    return { label: 'Low', color: 'bg-green-500' };
  };

  const formatTimeAgo = (timestamp: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - new Date(timestamp).getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    return `${Math.floor(diffInHours / 24)}d ago`;
  };

  return (
    <div className={className}>
      {/* Header with Stats */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Recent Learning Lessons</h3>
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-gray-400">Total:</span>
          <span className="text-white font-medium">{lessonStats.total}</span>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <div className="text-center p-2 bg-green-900/20 rounded border border-green-500">
          <p className="text-green-400 text-lg font-bold">{lessonStats.success}</p>
          <p className="text-gray-400 text-xs">Successes</p>
        </div>
        <div className="text-center p-2 bg-red-900/20 rounded border border-red-500">
          <p className="text-red-400 text-lg font-bold">{lessonStats.failure}</p>
          <p className="text-gray-400 text-xs">Failures</p>
        </div>
        <div className="text-center p-2 bg-yellow-900/20 rounded border border-yellow-500">
          <p className="text-yellow-400 text-lg font-bold">{lessonStats.insight}</p>
          <p className="text-gray-400 text-xs">Insights</p>
        </div>
        <div className="text-center p-2 bg-purple-900/20 rounded border border-purple-500">
          <p className="text-purple-400 text-lg font-bold">{lessonStats.breakthrough}</p>
          <p className="text-gray-400 text-xs">Breakthroughs</p>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 space-y-2 sm:space-y-0">
        <div className="flex space-x-2">
          {(['all', 'success', 'failure', 'insight', 'breakthrough'] as const).map(type => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === type
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="bg-gray-700 text-gray-300 text-xs rounded px-2 py-1 border border-gray-600 focus:border-blue-500 focus:outline-none"
        >
          <option value="recent">Most Recent</option>
          <option value="impact">Highest Impact</option>
          <option value="retention">Best Retention</option>
        </select>
      </div>

      {/* Lessons List */}
      <div className="space-y-3">
        {filteredAndSortedLessons.length > 0 ? (
          filteredAndSortedLessons.map((lesson) => (
            <div
              key={lesson.id}
              className={`p-4 rounded-lg border transition-all hover:shadow-lg ${getLessonColor(lesson.lessonType)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getLessonIcon(lesson.lessonType)}</span>
                  <span className="text-xs text-gray-400 capitalize">
                    {lesson.lessonType} • {formatTimeAgo(lesson.timestamp)}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded ${getImpactBadge(lesson.impact).color} text-white`}>
                    {getImpactBadge(lesson.impact).label} Impact
                  </span>
                  <span className="text-xs text-gray-400">
                    {(lesson.retentionScore * 100).toFixed(0)}% retained
                  </span>
                </div>
              </div>

              <h4 className="font-medium text-white mb-1">{lesson.title}</h4>
              <p className="text-sm text-gray-300 mb-2">{lesson.description}</p>

              {lesson.appliedIn.length > 0 && (
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <span>Applied in:</span>
                  <div className="flex space-x-1">
                    {lesson.appliedIn.slice(0, 3).map((context, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-800 rounded">
                        {context}
                      </span>
                    ))}
                    {lesson.appliedIn.length > 3 && (
                      <span className="px-2 py-1 bg-gray-800 rounded">
                        +{lesson.appliedIn.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No lessons found</p>
            <p className="text-sm">Try adjusting the filters or check back later.</p>
          </div>
        )}
      </div>

      {/* Learning Insights */}
      {lessonStats.total > 0 && (
        <div className="mt-6 p-4 bg-gray-900 rounded-lg">
          <h4 className="text-white font-semibold mb-2">Learning Pattern Analysis</h4>
          <div className="space-y-2 text-sm text-gray-300">
            {lessonStats.breakthrough > 0 && (
              <p>🎯 {lessonStats.breakthrough} breakthrough{lessonStats.breakthrough > 1 ? 's' : ''} detected - agent is making significant cognitive leaps!</p>
            )}
            {lessonStats.success / lessonStats.total > 0.7 && (
              <p>📈 High success rate ({Math.round(lessonStats.success / lessonStats.total * 100)}%) - agent is learning effectively from experiences.</p>
            )}
            {lessonStats.failure / lessonStats.total > 0.3 && (
              <p>🧠 Active learning from failures - {Math.round(lessonStats.failure / lessonStats.total * 100)}% of lessons come from mistakes, showing growth mindset.</p>
            )}
            {lessonStats.highRetention / lessonStats.total > 0.6 && (
              <p>💪 Excellent knowledge retention - {Math.round(lessonStats.highRetention / lessonStats.total * 100)}% of lessons are well-retained.</p>
            )}
            {lessonStats.avgImpact > 0.6 && (
              <p>⚡ High-impact learning - average lesson impact of {(lessonStats.avgImpact * 100).toFixed(1)}% indicates meaningful cognitive development.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};