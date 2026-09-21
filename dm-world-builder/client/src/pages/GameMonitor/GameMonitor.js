import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress,
  Avatar,
  Tooltip,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Badge,
  Paper,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Add,
  Edit,
  Delete,
  Visibility,
  VisibilityOff,
  ExpandMore,
  Person,
  Monster,
  Shield,
  Swords,
  Heart,
  Bolt,
  Timer,
  Map,
  Chat,
  Notifications,
  Settings,
  Save,
  CloudUpload,
  Speed,
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';

import { useSocket } from '../../contexts/SocketContext';
import { useCampaign } from '../../contexts/CampaignContext';
import CharacterCard from '../../components/Character/CharacterCard';
import CombatTracker from '../../components/Combat/CombatTracker';
import EventTimeline from '../../components/Events/EventTimeline';
import LocationMap from '../../components/Map/LocationMap';
import QuickActionsPanel from '../../components/GameMonitor/QuickActionsPanel';
import PerformanceMetrics from '../../components/GameMonitor/PerformanceMetrics';
import DMControls from '../../components/GameMonitor/DMControls';

const GameMonitor = ({ campaignId }) => {
  const {
    socket,
    connected,
    gameState,
    clients,
    isDM,
    startCombat,
    injectEvent,
    spawnCreature,
    modifyEnvironment,
    saveCampaign
  } = useSocket();

  const { currentCampaign, characters, locations } = useCampaign();

  const [activeTab, setActiveTab] = useState(0);
  const [selectedCharacter, setSelectedCharacter] = useState(null);
  const [showDMControls, setShowDMControls] = useState(true);
  const [autoSave, setAutoSave] = useState(true);
  const [showNotifications, setShowNotifications] = useState(true);
  const [recording, setRecording] = useState(false);
  const [eventDialog, setEventDialog] = useState(false);
  const [creatureDialog, setCreatureDialog] = useState(false);
  const [environmentDialog, setEnvironmentDialog] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    type: 'custom',
    trigger: 'immediate'
  });
  const [newCreature, setNewCreature] = useState({
    name: '',
    health: 10,
    position: { x: 0, y: 0 }
  });
  const [environmentChange, setEnvironmentChange] = useState({
    weather: 'clear',
    lighting: 'normal',
    atmosphere: ''
  });

  const timelineRef = useRef(null);
  const metricsIntervalRef = useRef(null);

  // Auto-save functionality
  useEffect(() => {
    if (autoSave && currentCampaign) {
      const interval = setInterval(() => {
        if (connected && isDM) {
          saveCampaign();
        }
      }, 5 * 60 * 1000); // Auto-save every 5 minutes

      return () => clearInterval(interval);
    }
  }, [autoSave, connected, isDM, currentCampaign, saveCampaign]);

  // Performance metrics collection
  useEffect(() => {
    if (connected && gameState) {
      metricsIntervalRef.current = setInterval(() => {
        // Collect performance metrics
        const metrics = {
          timestamp: Date.now(),
          connectedClients: clients.length,
          activeCharacters: characters.filter(c => c.status === 'alive').length,
          memoryUsage: performance.memory ? performance.memory.usedJSHeapSize : 0,
          latency: Date.now() - (gameState.lastUpdated?.getTime() || Date.now())
        };

        // Send metrics to server (if needed)
        if (socket && socket.emit) {
          socket.emit('performance_metrics', metrics);
        }
      }, 10000); // Every 10 seconds

      return () => {
        if (metricsIntervalRef.current) {
          clearInterval(metricsIntervalRef.current);
        }
      };
    }
  }, [connected, gameState, clients.length, characters.length, socket]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleStartCombat = () => {
    if (characters.length > 0) {
      startCombat({
        locationId: gameState?.currentLocation || currentCampaign?.currentState?.currentLocation,
        participants: characters.filter(c => c.status === 'alive').map(c => c.id),
        environment: environmentChange
      });
    }
  };

  const handleInjectEvent = () => {
    if (newEvent.title && newEvent.description) {
      injectEvent({
        ...newEvent,
        triggerImmediately: newEvent.trigger === 'immediate'
      });
      setEventDialog(false);
      setNewEvent({
        title: '',
        description: '',
        type: 'custom',
        trigger: 'immediate'
      });
    }
  };

  const handleSpawnCreature = () => {
    if (newCreature.name) {
      spawnCreature({
        ...newCreature,
        stats: {
          strength: 10,
          dexterity: 10,
          constitution: 10,
          intelligence: 10,
          wisdom: 10,
          charisma: 10
        }
      });
      setCreatureDialog(false);
      setNewCreature({
        name: '',
        health: 10,
        position: { x: 0, y: 0 }
      });
    }
  };

  const handleModifyEnvironment = () => {
    modifyEnvironment({
      locationId: gameState?.currentLocation || currentCampaign?.currentState?.currentLocation,
      changes: environmentChange
    });
    setEnvironmentDialog(false);
  };

  const scrollToBottom = () => {
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'alive': return 'success';
      case 'dead': return 'error';
      case 'unconscious': return 'warning';
      case 'stable': return 'info';
      default: return 'default';
    }
  };

  const getHealthPercentage = (character) => {
    if (!character.health) return 0;
    return (character.health.current / character.health.max) * 100;
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #330867 0%, #4a1a8c 100%)'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" className="fantasy-font" sx={{ color: 'white' }}>
            Game Monitor
          </Typography>
          {currentCampaign && (
            <Typography variant="h6" sx={{ color: '#ff6b35' }}>
              {currentCampaign.name}
            </Typography>
          )}
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge
            badgeContent={clients.length}
            color="primary"
            sx={{ mr: 1 }}
          >
            <Chip
              icon={<Person />}
              label={`Clients: ${clients.length}`}
              color={connected ? 'success' : 'error'}
              variant="outlined"
              sx={{ color: 'white', borderColor: 'white' }}
            />
          </Badge>

          <Chip
            icon={recording ? <Timer /> : <PlayArrow />}
            label={recording ? 'Recording' : 'Not Recording'}
            color={recording ? 'warning' : 'default'}
            variant="outlined"
            sx={{ color: 'white', borderColor: 'white' }}
          />

          {isDM && (
            <FormControlLabel
              control={
                <Switch
                  checked={showDMControls}
                  onChange={(e) => setShowDMControls(e.target.checked)}
                  sx={{ color: 'white' }}
                />
              }
              label="DM Controls"
              sx={{ color: 'white' }}
            />
          )}

          <IconButton color="inherit" onClick={() => window.location.reload()}>
            <Refresh />
          </IconButton>
        </Box>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Panel - Characters and Combat */}
        <Box sx={{ width: 350, display: 'flex', flexDirection: 'column', p: 2, gap: 2 }}>
          {/* Character Status */}
          <Card sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, p: 2, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Character Status
              </Typography>
              <List dense>
                {characters.map((character) => (
                  <ListItem
                    key={character.id}
                    button
                    onClick={() => setSelectedCharacter(character)}
                    selected={selectedCharacter?.id === character.id}
                    sx={{
                      borderRadius: 1,
                      mb: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      '&:hover': {
                        bgcolor: 'action.hover'
                      }
                    }}
                  >
                    <ListItemIcon>
                      <Avatar
                        sx={{
                          bgcolor: character.type === 'player' ? 'primary.main' : 'secondary.main',
                          width: 32,
                          height: 32
                        }}
                      >
                        {character.type === 'player' ? <Person /> : <Monster />}
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={character.name}
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Level {character.level} {character.class}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={getHealthPercentage(character)}
                            sx={{ mt: 0.5, height: 4 }}
                            color={getHealthPercentage(character) > 50 ? 'success' : 'error'}
                          />
                          <Typography variant="caption" color="text.secondary">
                            HP: {character.health?.current || 0}/{character.health?.max || 0}
                          </Typography>
                        </Box>
                      }
                    />
                    <Chip
                      label={character.status}
                      size="small"
                      color={getStatusColor(character.status)}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Combat Tracker */}
          {gameState?.combat && (
            <Card>
              <CardContent sx={{ p: 2 }}>
                <CombatTracker combat={gameState.combat} />
              </CardContent>
            </Card>
          )}
        </Box>

        {/* Center - Main Game View */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Map View" icon={<Map />} />
              <Tab label="Event Timeline" icon={<Timer />} />
              <Tab label="Analytics" icon={<TrendingUp />} />
              {isDM && <Tab label="DM Tools" icon={<Settings />} />}
            </Tabs>
          </Box>

          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            {activeTab === 0 && (
              <LocationMap
                locations={locations}
                characters={characters}
                currentLocation={gameState?.currentLocation}
                onCharacterMove={(characterId, position) => {
                  // Handle character movement
                }}
              />
            )}

            {activeTab === 1 && (
              <EventTimeline
                events={gameState?.timeline || []}
                ref={timelineRef}
                onScrollToBottom={scrollToBottom}
              />
            )}

            {activeTab === 2 && (
              <PerformanceMetrics
                gameState={gameState}
                clients={clients}
                characters={characters}
              />
            )}

            {activeTab === 3 && isDM && (
              <DMControls
                onStartCombat={handleStartCombat}
                onInjectEvent={() => setEventDialog(true)}
                onSpawnCreature={() => setCreatureDialog(true)}
                onModifyEnvironment={() => setEnvironmentDialog(true)}
                onSave={saveCampaign}
              />
            )}
          </Box>
        </Box>

        {/* Right Panel - Quick Actions */}
        {showDMControls && isDM && (
          <Box sx={{ width: 300, p: 2 }}>
            <QuickActionsPanel
              onInjectEvent={() => setEventDialog(true)}
              onSpawnCreature={() => setCreatureDialog(true)}
              onModifyEnvironment={() => setEnvironmentDialog(true)}
              onStartCombat={handleStartCombat}
              onSave={saveCampaign}
              recording={recording}
              onToggleRecording={() => setRecording(!recording)}
              autoSave={autoSave}
              onToggleAutoSave={() => setAutoSave(!autoSave)}
            />
          </Box>
        )}
      </Box>

      {/* Floating Action Buttons */}
      {isDM && (
        <Box sx={{ position: 'fixed', bottom: 16, right: 16, display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Fab
            color="primary"
            size="small"
            onClick={() => setEventDialog(true)}
            sx={{ bgcolor: '#ff6b35' }}
          >
            <Add />
          </Fab>
          <Fab
            color="secondary"
            size="small"
            onClick={() => setCreatureDialog(true)}
          >
            <Monster />
          </Fab>
          <Fab
            color="info"
            size="small"
            onClick={handleStartCombat}
          >
            <Swords />
          </Fab>
        </Box>
      )}

      {/* Event Injection Dialog */}
      <Dialog open={eventDialog} onClose={() => setEventDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Inject Event</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Event Title"
            value={newEvent.title}
            onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={newEvent.description}
            onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
            margin="normal"
            multiline
            rows={4}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Event Type</InputLabel>
            <Select
              value={newEvent.type}
              onChange={(e) => setNewEvent({ ...newEvent, type: e.target.value })}
            >
              <MenuItem value="custom">Custom</MenuItem>
              <MenuItem value="combat">Combat</MenuItem>
              <MenuItem value="dialogue">Dialogue</MenuItem>
              <MenuItem value="discovery">Discovery</MenuItem>
              <MenuItem value="trap">Trap</MenuItem>
              <MenuItem value="environmental">Environmental</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Trigger</InputLabel>
            <Select
              value={newEvent.trigger}
              onChange={(e) => setNewEvent({ ...newEvent, trigger: e.target.value })}
            >
              <MenuItem value="immediate">Immediate</MenuItem>
              <MenuItem value="on_enter">On Enter Location</MenuItem>
              <MenuItem value="on_action">On Character Action</MenuItem>
              <MenuItem value="conditional">Conditional</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEventDialog(false)}>Cancel</Button>
          <Button onClick={handleInjectEvent} variant="contained">Inject Event</Button>
        </DialogActions>
      </Dialog>

      {/* Spawn Creature Dialog */}
      <Dialog open={creatureDialog} onClose={() => setCreatureDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Spawn Creature</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Creature Name"
            value={newCreature.name}
            onChange={(e) => setNewCreature({ ...newCreature, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Health Points"
            type="number"
            value={newCreature.health}
            onChange={(e) => setNewCreature({ ...newCreature, health: parseInt(e.target.value) })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Position X"
            type="number"
            value={newCreature.position.x}
            onChange={(e) => setNewCreature({
              ...newCreature,
              position: { ...newCreature.position, x: parseInt(e.target.value) }
            })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Position Y"
            type="number"
            value={newCreature.position.y}
            onChange={(e) => setNewCreature({
              ...newCreature,
              position: { ...newCreature.position, y: parseInt(e.target.value) }
            })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreatureDialog(false)}>Cancel</Button>
          <Button onClick={handleSpawnCreature} variant="contained">Spawn Creature</Button>
        </DialogActions>
      </Dialog>

      {/* Environment Modification Dialog */}
      <Dialog open={environmentDialog} onClose={() => setEnvironmentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Modify Environment</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Weather</InputLabel>
            <Select
              value={environmentChange.weather}
              onChange={(e) => setEnvironmentChange({ ...environmentChange, weather: e.target.value })}
            >
              <MenuItem value="clear">Clear</MenuItem>
              <MenuItem value="cloudy">Cloudy</MenuItem>
              <MenuItem value="rain">Rain</MenuItem>
              <MenuItem value="storm">Storm</MenuItem>
              <MenuItem value="snow">Snow</MenuItem>
              <MenuItem value="fog">Fog</MenuItem>
              <MenuItem value="windy">Windy</MenuItem>
              <MenuItem value="magical">Magical</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Lighting</InputLabel>
            <Select
              value={environmentChange.lighting}
              onChange={(e) => setEnvironmentChange({ ...environmentChange, lighting: e.target.value })}
            >
              <MenuItem value="bright">Bright</MenuItem>
              <MenuItem value="normal">Normal</MenuItem>
              <MenuItem value="dim">Dim</MenuItem>
              <MenuItem value="dark">Dark</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Atmosphere Description"
            value={environmentChange.atmosphere}
            onChange={(e) => setEnvironmentChange({ ...environmentChange, atmosphere: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEnvironmentDialog(false)}>Cancel</Button>
          <Button onClick={handleModifyEnvironment} variant="contained">Apply Changes</Button>
        </DialogActions>
      </Dialog>

      {/* Connection Status */}
      {!connected && (
        <Alert
          severity="error"
          sx={{ position: 'fixed', bottom: 16, left: 16, right: 16 }}
          action={
            <IconButton color="inherit" onClick={() => window.location.reload()}>
              <Refresh />
            </IconButton>
          }
        >
          Disconnected from server. Attempting to reconnect...
        </Alert>
      )}
    </Box>
  );
};

export default GameMonitor;