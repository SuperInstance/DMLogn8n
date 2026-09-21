import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';

import { SocketProvider } from './contexts/SocketContext';
import { AuthProvider } from './contexts/AuthContext';
import { CampaignProvider } from './contexts/CampaignContext';

import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import CampaignList from './pages/Campaign/CampaignList';
import CampaignView from './pages/Campaign/CampaignView';
import WorldBuilder from './pages/WorldBuilder/WorldBuilder';
import GameMonitor from './pages/GameMonitor/GameMonitor';
import CharacterManager from './pages/Character/CharacterManager';
import QuestManager from './pages/Quest/QuestManager';
import InventoryManager from './pages/Inventory/InventoryManager';
import SessionPlanner from './pages/SessionPlanner/SessionPlanner';
import AIAssistant from './pages/AIAssistant/AIAssistant';
import Settings from './pages/Settings/Settings';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';

import { useAuth } from './hooks/useAuth';

// Create dark theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#ff6b35',
      light: '#ff8c61',
      dark: '#cc5528',
    },
    secondary: {
      main: '#330867',
      light: '#4a1a8c',
      dark: '#22064d',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#cccccc',
    },
    error: {
      main: '#ff4444',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
    info: {
      main: '#2196f3',
    },
  },
  typography: {
    fontFamily: "'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: {
      fontFamily: "'Cinzel', serif",
      fontWeight: 600,
    },
    h2: {
      fontFamily: "'Cinzel', serif",
      fontWeight: 600,
    },
    h3: {
      fontFamily: "'Cinzel', serif",
      fontWeight: 600,
    },
    h4: {
      fontFamily: "'Cinzel', serif",
      fontWeight: 600,
    },
    body1: {
      fontFamily: "'Crimson Text', serif",
    },
    body2: {
      fontFamily: "'Crimson Text', serif",
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: '#6a6a6a #1a1a1a',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#1a1a1a',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#4a4a4a',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: '#6a6a6a',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)',
          border: '1px solid #333',
          borderRadius: '8px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          textTransform: 'none',
          fontWeight: 500,
        },
        contained: {
          background: 'linear-gradient(135deg, #ff6b35 0%, #ff8c61 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #cc5528 0%, #ff6b35 100%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #330867 0%, #4a1a8c 100%)',
          boxShadow: '0 2px 10px rgba(0,0,0,0.3)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%)',
          borderRight: '1px solid #333',
        },
      },
    },
  },
});

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#0a0a0a'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          border: '4px solid rgba(255, 255, 255, 0.1)',
          borderTop: '4px solid #ff6b35',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Public route component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#0a0a0a'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          border: '4px solid rgba(255, 255, 255, 0.1)',
          borderTop: '4px solid #ff6b35',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
    );
  }

  return !isAuthenticated ? children : <Navigate to="/dashboard" />;
};

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="campaigns" element={<CampaignList />} />
          <Route path="campaigns/:id" element={<CampaignView />} />
          <Route path="world-builder/:campaignId" element={<WorldBuilder />} />
          <Route path="game-monitor/:campaignId" element={<GameMonitor />} />
          <Route path="characters/:campaignId" element={<CharacterManager />} />
          <Route path="quests/:campaignId" element={<QuestManager />} />
          <Route path="inventory/:campaignId" element={<InventoryManager />} />
          <Route path="session-planner/:campaignId" element={<SessionPlanner />} />
          <Route path="ai-assistant/:campaignId" element={<AIAssistant />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

function App() {
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    // Check if auth context is ready
    const timer = setTimeout(() => {
      setAuthReady(true);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  if (!authReady) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: '#0a0a0a'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          border: '4px solid rgba(255, 255, 255, 0.1)',
          borderTop: '4px solid #ff6b35',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
    );
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AuthProvider>
        <SocketProvider>
          <CampaignProvider>
            <AppContent />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#1a1a1a',
                  color: '#ffffff',
                  border: '1px solid #333',
                  borderRadius: '6px',
                },
                success: {
                  style: {
                    borderLeft: '4px solid #4caf50',
                  },
                },
                error: {
                  style: {
                    borderLeft: '4px solid #ff4444',
                  },
                },
                loading: {
                  style: {
                    borderLeft: '4px solid #2196f3',
                  },
                },
              }}
            />
          </CampaignProvider>
        </SocketProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;