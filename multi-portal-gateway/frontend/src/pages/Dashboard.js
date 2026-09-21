import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Button,
  Alert
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';

const Dashboard = ({ systemStatus, wsMessages, onPortalSelect }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState([]);
  const [portalActivity, setPortalActivity] = useState([]);

  useEffect(() => {
    // Process system metrics for charts
    if (systemStatus) {
      setSystemMetrics([
        { name: 'Portals', value: systemStatus.portals?.total || 0 },
        { name: 'Connections', value: systemStatus.communication?.active_connections || 0 },
        { name: 'Messages', value: systemStatus.communication?.total_messages_sent || 0 }
      ]);

      // Simulate portal activity data
      setPortalActivity([
        { time: '00:00', characters: 2, dm: 1, coder: 0 },
        { time: '04:00', characters: 3, dm: 1, coder: 0 },
        { time: '08:00', characters: 5, dm: 1, coder: 1 },
        { time: '12:00', characters: 7, dm: 1, coder: 2 },
        { time: '16:00', characters: 6, dm: 1, coder: 3 },
        { time: '20:00', characters: 8, dm: 1, coder: 1 },
        { time: '23:59', characters: 4, dm: 1, coder: 0 }
      ]);
    }
  }, [systemStatus]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const handleStartAllPortals = () => {
    // This would start all available portals
    console.log('Starting all portals');
  };

  const handleStopAllPortals = () => {
    // This would stop all active portals
    console.log('Stopping all portals');
  };

  const COLORS = ['#2196F3', '#F50057', '#4CAF50', '#FF9800', '#9C27B0'];

  const pieData = systemStatus?.portals ? [
    { name: 'Characters', value: systemStatus.portals.character || 0 },
    { name: 'DM', value: systemStatus.portals.dm || 0 },
    { name: 'Coder', value: systemStatus.portals.coder || 0 },
    { name: 'Inactive', value: Math.max(0, 10 - (systemStatus.portals.character || 0) - (systemStatus.portals.dm || 0) - (systemStatus.portals.coder || 0)) }
  ] : [];

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={handleStartAllPortals}
            size="small"
          >
            Start All
          </Button>
          <Button
            variant="outlined"
            startIcon={<StopIcon />}
            onClick={handleStopAllPortals}
            size="small"
          >
            Stop All
          </Button>
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* System Status Alert */}
      {systemStatus && (
        <Alert severity="success" sx={{ mb: 3 }}>
          System is operational with {systemStatus.portals?.total || 0} active portals
        </Alert>
      )}

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Portals
              </Typography>
              <Typography variant="h4">
                {systemStatus?.portals?.total || 0}
              </Typography>
              <Box sx={{ mt: 1 }}>
                {systemStatus?.portals && (
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    <Chip label={`Characters: ${systemStatus.portals.character || 0}`} size="small" />
                    <Chip label={`DM: ${systemStatus.portals.dm || 0}`} size="small" />
                    <Chip label={`Coder: ${systemStatus.portals.coder || 0}`} size="small" />
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Connections
              </Typography>
              <Typography variant="h4">
                {systemStatus?.system?.active_connections || 0}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, ((systemStatus?.system?.active_connections || 0) / 20) * 100)}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Messages Sent
              </Typography>
              <Typography variant="h4">
                {systemStatus?.communication?.total_messages_sent || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                +{systemStatus?.communication?.messages_per_second || 0}/sec
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Health
              </Typography>
              <Typography variant="h4">
                {systemStatus?.system?.health || 'Good'}
              </Typography>
              <Chip
                label="Operational"
                color="success"
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Portal Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portal Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Portal Activity Over Time */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portal Activity (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={portalActivity}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="characters"
                    stackId="1"
                    stroke="#2196F3"
                    fill="#2196F3"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="dm"
                    stackId="1"
                    stroke="#F50057"
                    fill="#F50057"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="coder"
                    stackId="1"
                    stroke="#4CAF50"
                    fill="#4CAF50"
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Messages */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Messages
              </Typography>
              <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                {wsMessages.slice(-10).reverse().map((message, index) => (
                  <Box key={message.id} sx={{ mb: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      {format(message.timestamp, 'HH:mm:ss')}
                    </Typography>
                    <Typography variant="body2">
                      {message.type === 'event' ? `Event: ${message.data.event_type}` : 'System Message'}
                    </Typography>
                  </Box>
                ))}
                {wsMessages.length === 0 && (
                  <Typography variant="body2" color="textSecondary">
                    No recent messages
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<PlayIcon />}
                    onClick={() => onPortalSelect('character')}
                  >
                    Create Character Portal
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<PlayIcon />}
                    onClick={() => onPortalSelect('dm')}
                  >
                    Start DM Portal
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<PlayIcon />}
                    onClick={() => onPortalSelect('coder')}
                  >
                    Start Coder Workshop
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<SettingsIcon />}
                  >
                    System Settings
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;