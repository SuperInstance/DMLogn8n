import React, { useEffect, useState } from 'react';
import { LearningMilestone } from '../types';

interface MilestoneCelebrationProps {
  milestone: LearningMilestone;
  onComplete: () => void;
  agentName: string;
}

export const MilestoneCelebration: React.FC<MilestoneCelebrationProps> = ({
  milestone,
  onComplete,
  agentName
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showRewards, setShowRewards] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    setTimeout(() => setIsVisible(true), 100);

    // Show rewards after a delay
    setTimeout(() => setShowRewards(true), 2000);

    // Auto-close after 8 seconds
    const timer = setTimeout(() => {
      handleClose();
    }, 8000);

    return () => clearTimeout(timer);
  }, []);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onComplete, 300);
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      iq: '🧠',
      skill: '⭐',
      memory: '💾',
      strategy: '🎯',
      'meta-learning': '🎓'
    };
    return icons[category as keyof typeof icons] || '🏆';
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      iq: 'from-purple-500 to-blue-500',
      skill: 'from-yellow-500 to-orange-500',
      memory: 'from-blue-500 to-teal-500',
      strategy: 'from-green-500 to-emerald-500',
      'meta-learning': 'from-pink-500 to-rose-500'
    };
    return colors[category as keyof typeof colors] || 'from-gray-500 to-gray-600';
  };

  const getRewardIcon = (type: string) => {
    const icons = {
      badge: '🏅',
      title: '👑',
      ability_unlock: '🔓',
      memory_capacity: '💾',
      skill_bonus: '⚡'
    };
    return icons[type as keyof typeof icons] || '🎁';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
        style={{ opacity: isVisible ? 1 : 0 }}
      />

      {/* Celebration Modal */}
      <div
        className={`relative max-w-lg w-full mx-4 transform transition-all duration-500 ${
          isVisible ? 'scale-100 translate-y-0 opacity-100' : 'scale-75 translate-y-4 opacity-0'
        }`}
      >
        <div className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden">
          {/* Header with Gradient */}
          <div className={`relative h-32 bg-gradient-to-br ${getCategoryColor(milestone.category)} p-6`}>
            <div className="absolute top-4 right-4">
              <button
                onClick={handleClose}
                className="text-white/70 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-5xl animate-bounce">{getCategoryIcon(milestone.category)}</div>
              <div>
                <h2 className="text-2xl font-bold text-white">Milestone Achieved!</h2>
                <p className="text-white/80">{agentName}</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            <div className="text-center mb-6">
              <h3 className="text-xl font-semibold text-white mb-2">{milestone.title}</h3>
              <p className="text-gray-300">{milestone.description}</p>
            </div>

            {/* Milestone Criteria */}
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <h4 className="text-sm font-medium text-gray-400 mb-2">Achievement Criteria</h4>
              <div className="flex items-center justify-between">
                <span className="text-white">{milestone.criteria.metric.replace('_', ' ').toUpperCase()}</span>
                <span className="text-green-400 font-medium">
                  {milestone.criteria.comparison === 'greater_than' ? '>' :
                   milestone.criteria.comparison === 'less_than' ? '<' : '='} {milestone.criteria.value}
                </span>
              </div>
            </div>

            {/* Rewards */}
            <div
              className={`transition-all duration-500 ${
                showRewards ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
              }`}
            >
              <h4 className="text-lg font-semibold text-white mb-3">Rewards Unlocked</h4>
              <div className="grid grid-cols-1 gap-3">
                {milestone.rewards.map((reward, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-3 p-3 bg-gray-800 rounded-lg border border-gray-700"
                  >
                    <span className="text-2xl">{getRewardIcon(reward.type)}</span>
                    <div className="flex-1">
                      <p className="text-white font-medium">
                        {reward.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </p>
                      <p className="text-gray-400 text-sm">{reward.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-blue-400 font-bold">
                        {typeof reward.value === 'number' ? `+${reward.value}` : reward.value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Achievement Timestamp */}
            {milestone.achievedAt && (
              <div className="mt-6 text-center">
                <p className="text-gray-500 text-sm">
                  Achieved on {new Date(milestone.achievedAt).toLocaleDateString()} at{' '}
                  {new Date(milestone.achievedAt).toLocaleTimeString()}
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="px-6 pb-6">
            <div className="flex space-x-3">
              <button
                onClick={handleClose}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
              >
                Continue
              </button>
              <button
                onClick={() => {
                  // Share functionality
                  console.log('Share milestone:', milestone);
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Share
              </button>
            </div>
          </div>
        </div>

        {/* Confetti Effect */}
        {isVisible && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-1/4 w-2 h-2 bg-yellow-400 rounded-full animate-ping"></div>
            <div className="absolute top-1/4 right-1/4 w-3 h-3 bg-blue-400 rounded-full animate-ping animation-delay-200"></div>
            <div className="absolute bottom-1/4 left-1/3 w-2 h-2 bg-purple-400 rounded-full animate-ping animation-delay-400"></div>
            <div className="absolute top-1/2 right-1/3 w-4 h-4 bg-green-400 rounded-full animate-ping animation-delay-600"></div>
            <div className="absolute bottom-0 right-1/4 w-2 h-2 bg-pink-400 rounded-full animate-ping animation-delay-800"></div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        .animation-delay-200 {
          animation-delay: 200ms;
        }
        .animation-delay-400 {
          animation-delay: 400ms;
        }
        .animation-delay-600 {
          animation-delay: 600ms;
        }
        .animation-delay-800 {
          animation-delay: 800ms;
        }
      `}</style>
    </div>
  );
};