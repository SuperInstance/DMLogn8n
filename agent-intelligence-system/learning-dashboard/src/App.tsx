import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { IntelligenceGrowthDashboard } from './components/IntelligenceGrowthDashboard';
import { MobileNavigation } from './components/MobileNavigation';
import { useAccessibility } from './hooks/useAccessibility';
import './styles/globals.css';

const App: React.FC = () => {
  const { announceToScreenReader, settings } = useAccessibility();

  // Sample agent data - replace with real data from your system
  const agentData = {
    id: 'agent_wizard_001',
    name: 'Merlin',
    level: 7,
    class: 'Wizard',
    isConnected: true
  };

  const handleTimeframeChange = (timeframe: string) => {
    announceToScreenReader(`Timeframe changed to ${timeframe}`);
  };

  const handleExport = () => {
    announceToScreenReader('Opening export options');
  };

  const handleToggleRealTime = () => {
    announceToScreenReader(agentData.isConnected ? 'Live updates paused' : 'Live updates resumed');
  };

  return (
    <div className={`min-h-screen bg-gray-900 text-white ${settings.fontSize} ${settings.reducedMotion ? 'reduce-motion' : ''} ${settings.highContrast ? 'high-contrast' : ''}`}>
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Router>
        <div className="min-h-screen">
          {/* Mobile Navigation */}
          <MobileNavigation
            agentName={agentData.name}
            agentLevel={agentData.level}
            agentClass={agentData.class}
            isConnected={agentData.isConnected}
            onToggleRealTime={handleToggleRealTime}
            isRealTimeEnabled={true}
            onExport={handleExport}
          />

          {/* Main Content */}
          <main id="main-content" className="lg:pt-0">
            <Routes>
              <Route
                path="/"
                element={
                  <IntelligenceGrowthDashboard
                    agentId={agentData.id}
                    className="pt-16 lg:pt-0"
                  />
                }
              />
              <Route
                path="/agent/:agentId"
                element={
                  <IntelligenceGrowthDashboard
                    agentId={agentData.id}
                    className="pt-16 lg:pt-0"
                  />
                }
              />
            </Routes>
          </main>

          {/* Screen reader announcements */}
          <div
            id="screen-reader-announcements"
            className="sr-only"
            aria-live="polite"
            aria-atomic="true"
          />
        </div>
      </Router>

      {/* Global event listeners for mobile navigation */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
            // Handle timeframe changes from mobile navigation
            window.addEventListener('timeframeChange', (event) => {
              console.log('Timeframe changed to:', event.detail);
              // Update dashboard with new timeframe
            });
          `
        }}
      />
    </div>
  );
};

export default App;