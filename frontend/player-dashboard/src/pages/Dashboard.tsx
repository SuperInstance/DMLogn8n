import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress,
  Avatar,
  Button,
} from '@mui/material';
import {
  Person as PersonIcon,
  Games as GamesIcon,
  Chat as ChatIcon,
  TrendingUp as TrendingUpIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useQuery } from 'react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatDistanceToNow } from 'date-fns';

import { apiClient } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { StatCard } from '../components/StatCard';
import { ActivityFeed } from '../components/ActivityFeed';
import { QuickActions } from '../components/QuickActions';

interface DashboardStats {
  totalCharacters: number;
  activeGames: number;
  totalPlayTime: number;
  messagesExchanged: number;
  recentActivity: Array<{
    id: string;
    type: string;
    description: string;
    timestamp: string;
  }>;
  performanceData: Array<{
    time: string;
    xp: number;
    level: number;
  }>;
}

export const Dashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: stats, isLoading } = useQuery<DashboardStats>(
    'dashboard-stats',
    async () => {
      const response = await apiClient.get('/api/v1/dashboard/stats');
      return response.data;
    },
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: activeGames } = useQuery(
    'active-games',
    async () => {
      const response = await apiClient.get('/api/v1/games/active');
      return response.data;
    }
  );

  const { data: recentCharacters } = useQuery(
    'recent-characters',
    async () => {
      const response = await apiClient.get('/api/v1/characters?limit=5');
      return response.data;
    }
  );

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <LinearProgress sx={{ width: '300px' }} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Typography variant="h4" gutterBottom>
          Welcome back, {user?.username}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Ready for your next adventure?
        </Typography>
      </motion.div>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <StatCard
              title="Total Characters"
              value={stats?.totalCharacters || 0}
              icon={<PersonIcon />}
              color="#8b5cf6"
              trend={12}
            />
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <StatCard
              title="Active Games"
              value={stats?.activeGames || 0}
              icon={<GamesIcon />}
              color="#06b6d4"
              trend={5}
            />
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <StatCard
              title="Play Time"
              value={`${stats?.totalPlayTime || 0}h`}
              icon={<TrendingUpIcon />}
              color="#10b981"
              trend={8}
            />
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <StatCard
              title="Messages"
              value={stats?.messagesExchanged || 0}
              icon={<ChatIcon />}
              color="#f59e0b"
              trend={15}
            />
          </motion.div>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        {/* Performance Chart */}
        <Grid item xs={12} md={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Paper sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Performance Overview
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats?.performanceData || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="xp"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="level"
                    stroke="#06b6d4"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </motion.div>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <ActivityFeed activities={stats?.recentActivity || []} />
          </motion.div>
        </Grid>

        {/* Active Games */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
          >
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Active Games
              </Typography>
              <List>
                {activeGames?.map((game: any) => (
                  <ListItem
                    key={game.id}
                    sx={{
                      border: '1px solid #334155',
                      borderRadius: 2,
                      mb: 1,
                      '&:hover': {
                        backgroundColor: '#334155',
                      },
                    }}
                  >
                    <Avatar sx={{ mr: 2, bgcolor: '#8b5cf6' }}>
                      <GamesIcon />
                    </Avatar>
                    <ListItemText
                      primary={game.name}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={game.status}
                            size="small"
                            color={game.status === 'active' ? 'success' : 'default'}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {formatDistanceToNow(new Date(game.lastPlayed), {
                              addSuffix: true,
                            })}
                          </Typography>
                        </Box>
                      }
                    />
                    <Button
                      variant="contained"
                      startIcon={<PlayArrowIcon />}
                      size="small"
                      sx={{ ml: 2 }}
                    >
                      Join
                    </Button>
                  </ListItem>
                ))}
                {(!activeGames || activeGames.length === 0) && (
                  <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
                    No active games. Join or create one to get started!
                  </Typography>
                )}
              </List>
            </Paper>
          </motion.div>
        </Grid>

        {/* Recent Characters */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recent Characters
              </Typography>
              <List>
                {recentCharacters?.map((character: any) => (
                  <ListItem key={character.id}>
                    <Avatar
                      src={character.avatar}
                      sx={{ mr: 2, bgcolor: '#06b6d4' }}
                    >
                      {character.name[0]}
                    </Avatar>
                    <ListItemText
                      primary={character.name}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={character.class}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            Level {character.level}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
                {(!recentCharacters || recentCharacters.length === 0) && (
                  <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
                    No characters yet. Create your first character!
                  </Typography>
                )}
              </List>
            </Paper>
          </motion.div>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.9 }}
          >
            <QuickActions />
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
};