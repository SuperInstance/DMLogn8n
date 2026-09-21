import React, { useState } from 'react';

interface MobileNavigationProps {
  agentName: string;
  agentLevel: number;
  agentClass: string;
  isConnected: boolean;
  onToggleRealTime: () => void;
  isRealTimeEnabled: boolean;
  onExport: () => void;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  agentName,
  agentLevel,
  agentClass,
  isConnected,
  onToggleRealTime,
  isRealTimeEnabled,
  onExport
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleAction = (action: () => void) => {
    action();
    setIsMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Header */}
      <header className="lg:hidden bg-gray-900 border-b border-gray-800 sticky top-0 z-40">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Agent Info */}
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleMenu}
                className="p-2 text-gray-400 hover:text-white transition-colors"
                aria-label="Toggle navigation menu"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg font-semibold text-white truncate max-w-[120px]">
                  {agentName}
                </h1>
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <span>Lvl {agentLevel}</span>
                  <span>•</span>
                  <span className="truncate max-w-[80px]">{agentClass}</span>
                  <span>•</span>
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-1 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="sr-only">{isConnected ? 'Connected' : 'Offline'}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleAction(onToggleRealTime)}
                className={`p-2 rounded-lg transition-colors ${
                  isRealTimeEnabled ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300'
                }`}
                aria-label={isRealTimeEnabled ? 'Pause live updates' : 'Resume live updates'}
              >
                {isRealTimeEnabled ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </button>

              <button
                onClick={() => handleAction(onExport)}
                className="p-2 bg-gray-700 text-gray-300 rounded-lg transition-colors"
                aria-label="Export data"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Timeframe Selector - Always visible on mobile */}
        <div className="px-4 pb-3">
          <div className="flex space-x-2 overflow-x-auto scrollbar-hide">
            {['session', 'day', 'week', 'month'].map((timeframe) => (
              <button
                key={timeframe}
                className="px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg text-sm font-medium whitespace-nowrap transition-colors hover:bg-gray-700 focus:bg-blue-600 focus:text-white"
                onClick={() => {
                  // Handle timeframe change
                  const event = new CustomEvent('timeframeChange', { detail: timeframe });
                  window.dispatchEvent(event);
                }}
              >
                {timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {isMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsMenuOpen(false)}
          />

          {/* Menu Panel */}
          <div className="fixed left-0 top-0 h-full w-80 bg-gray-900 border-r border-gray-800 overflow-y-auto">
            <div className="p-4">
              {/* Menu Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white">Dashboard Menu</h2>
                <button
                  onClick={() => setIsMenuOpen(false)}
                  className="p-2 text-gray-400 hover:text-white transition-colors"
                  aria-label="Close menu"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Agent Details */}
              <div className="bg-gray-800 rounded-lg p-4 mb-6">
                <h3 className="text-white font-medium mb-2">Agent Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Name:</span>
                    <span className="text-white">{agentName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Level:</span>
                    <span className="text-white">{agentLevel}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Class:</span>
                    <span className="text-white">{agentClass}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className={`flex items-center ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                      <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      {isConnected ? 'Online' : 'Offline'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="bg-gray-800 rounded-lg p-4 mb-6">
                <h3 className="text-white font-medium mb-3">Quick Stats</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-gray-900 rounded-lg">
                    <div className="text-lg font-bold text-blue-400">118</div>
                    <div className="text-xs text-gray-400">IQ</div>
                  </div>
                  <div className="text-center p-3 bg-gray-900 rounded-lg">
                    <div className="text-lg font-bold text-green-400">87%</div>
                    <div className="text-xs text-gray-400">Retention</div>
                  </div>
                  <div className="text-center p-3 bg-gray-900 rounded-lg">
                    <div className="text-lg font-bold text-purple-400">71%</div>
                    <div className="text-xs text-gray-400">Memory</div>
                  </div>
                  <div className="text-center p-3 bg-gray-900 rounded-lg">
                    <div className="text-lg font-bold text-yellow-400">5</div>
                    <div className="text-xs text-gray-400">Masters</div>
                  </div>
                </div>
              </div>

              {/* Navigation Sections */}
              <nav className="space-y-2">
                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">📊 Intelligence Metrics</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">⭐ Skill Development</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">💾 Memory System</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">📈 Learning Progress</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">🎯 Performance</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>

                <button className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between">
                  <span className="text-white">🏆 Milestones</span>
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </nav>

              {/* Actions */}
              <div className="mt-6 space-y-3">
                <button
                  onClick={() => handleAction(onExport)}
                  className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                >
                  📤 Export Report
                </button>

                <button
                  onClick={() => handleAction(onToggleRealTime)}
                  className={`w-full px-4 py-3 rounded-lg transition-colors font-medium ${
                    isRealTimeEnabled
                      ? 'bg-green-600 hover:bg-green-700 text-white'
                      : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                  }`}
                >
                  {isRealTimeEnabled ? '⏸️ Pause Live Updates' : '▶️ Resume Live Updates'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};