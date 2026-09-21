import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import io from 'socket.io-client';

// Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import CharacterPortal from './pages/CharacterPortal';
import DMPortal from './pages/DMPortal';
import CoderPortal from './pages/CoderPortal';
import SystemMonitor from './pages/SystemMonitor';

// Hooks
import { useWebSocket } from './hooks/useWebSocket';
import { useSystemStatus } from './hooks/useSystemStatus';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard');
  const [portalType, setPortalType] = useState(null);

  // Custom hooks
  const {
    isConnected,
    messages,
    sendMessage,
    lastMessage
  } = useWebSocket('ws://localhost:8000/ws');

  const {
    systemStatus,
    loading: statusLoading,
    error: statusError
  } = useSystemStatus();

  useEffect(() => {
    // Handle WebSocket messages
    if (lastMessage) {
      console.log('Received message:', lastMessage);
    }
  }, [lastMessage]);

  const handleNavigation = (view) => {
    setCurrentView(view);
  };

  const handlePortalSelect = (type) => {
    setPortalType(type);
    setCurrentView('portal');
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Header
            sidebarOpen={sidebarOpen}
            setSidebarOpen={setSidebarOpen}
            isConnected={isConnected}
            systemStatus={systemStatus}
          />

          <Sidebar
            open={sidebarOpen}
            onNavigate={handleNavigation}
            onPortalSelect={handlePortalSelect}
            currentView={currentView}
            systemStatus={systemStatus}
          />

          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              mt: 8, // Header height
              ml: sidebarOpen ? 30 : 8, // Sidebar width
              transition: 'margin 0.3s ease',
            }}
          >
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route
                path="/dashboard"
                element={
                  <Dashboard
                    systemStatus={systemStatus}
                    wsMessages={messages}
                    onPortalSelect={handlePortalSelect}
                  />
                }
              />
              <Route
                path="/character/:characterId"
                element={
                  <CharacterPortal
                    characterId={portalType === 'character' ? window.location.pathname.split('/')[2] : null}
                    wsConnection={{ isConnected, sendMessage }}
                  />
                }
              />
              <Route
                path="/dm"
                element={
                  <DMPortal
                    wsConnection={{ isConnected, sendMessage }}
                  />
                }
              />
              <Route
                path="/coder"
                element={
                  <CoderPortal
                    wsConnection={{ isConnected, sendMessage }}
                  />
                }
              />
              <Route
                path="/monitor"
                element={
                  <SystemMonitor
                    systemStatus={systemStatus}
                    wsMessages={messages}
                  />
                }
              />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;