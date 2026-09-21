import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Alert,
  Tooltip,
  Fab,
  Drawer,
  useTheme
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Save,
  Map,
  Person,
  Place,
  Inventory,
  Book,
  Public,
  Brush,
  DragIndicator,
  Visibility,
  VisibilityOff,
  ExpandMore,
  Settings,
  Palette,
  Terrain,
  Castle,
  Forest,
  Mountain,
  City,
  Home,
  DoorFront,
  Key,
  Lock,
  LockOpen
} from '@mui/icons-material';

import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { useCampaign } from '../../contexts/CampaignContext';
import LocationMap from '../../components/WorldBuilder/LocationMap';
import LocationEditor from '../../components/WorldBuilder/LocationEditor';
import NPCEditor from '../../components/WorldBuilder/NPCEditor';
import ItemEditor from '../../components/WorldBuilder/ItemEditor';
import QuestEditor from '../../components/WorldBuilder/QuestEditor';
import WorldOverview from '../../components/WorldBuilder/WorldOverview';
import DragDropContext from '../../components/WorldBuilder/DragDropContext';

const WorldBuilder = ({ campaignId }) => {
  const theme = useTheme();
  const {
    currentCampaign,
    locations,
    characters,
    npcs,
    items,
    quests,
    addLocation,
    addCharacter,
    addQuest,
    loading
  } = useCampaign();

  const [activeTab, setActiveTab] = useState(0);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedNPC, setSelectedNPC] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedQuest, setSelectedQuest] = useState(null);
  const [locationDialog, setLocationDialog] = useState(false);
  const [npcDialog, setNPCDialog] = useState(false);
  const [itemDialog, setItemDialog] = useState(false);
  const [questDialog, setQuestDialog] = useState(false);
  const [settingsDrawer, setSettingsDrawer] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [showConnections, setShowConnections] = useState(true);
  const [viewMode, setViewMode] = useState('map'); // 'map', 'list', 'tree'

  const [newLocation, setNewLocation] = useState({
    name: '',
    type: 'room',
    description: '',
    position: { x: 0, y: 0 },
    size: { width: 10, height: 10, length: 10 }
  });

  const [newNPC, setNewNPC] = useState({
    name: '',
    type: 'npc',
    level: 1,
    stats: {
      strength: 10,
      dexterity: 10,
      constitution: 10,
      intelligence: 10,
      wisdom: 10,
      charisma: 10
    },
    personality: '',
    backstory: '',
    position: { x: 0, y: 0 }
  });

  const [newItem, setNewItem] = useState({
    name: '',
    type: 'misc',
    rarity: 'common',
    description: '',
    value: 0,
    properties: {}
  });

  const [newQuest, setNewQuest] = useState({
    title: '',
    description: '',
    type: 'side',
    difficulty: 'medium',
    objectives: [],
    rewards: {
      experience: 0,
      gold: 0,
      items: []
    }
  });

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleCreateLocation = async () => {
    if (newLocation.name) {
      await addLocation(campaignId, {
        ...newLocation,
        id: `location_${Date.now()}`,
        position: {
          x: Math.random() * 800,
          y: Math.random() * 600
        }
      });
      setLocationDialog(false);
      setNewLocation({
        name: '',
        type: 'room',
        description: '',
        position: { x: 0, y: 0 },
        size: { width: 10, height: 10, length: 10 }
      });
    }
  };

  const handleCreateNPC = async () => {
    if (newNPC.name) {
      await addCharacter(campaignId, {
        ...newNPC,
        id: `npc_${Date.now()}`,
        health: { current: 10, max: 10, temp: 0 },
        status: 'alive',
        conditions: [],
        inventory: [],
        equipment: {},
        abilities: []
      });
      setNPCDialog(false);
      setNewNPC({
        name: '',
        type: 'npc',
        level: 1,
        stats: {
          strength: 10,
          dexterity: 10,
          constitution: 10,
          intelligence: 10,
          wisdom: 10,
          charisma: 10
        },
        personality: '',
        backstory: '',
        position: { x: 0, y: 0 }
      });
    }
  };

  const handleCreateItem = async () => {
    if (newItem.name) {
      // Add item to campaign (would need to implement this in context)
      setItemDialog(false);
      setNewItem({
        name: '',
        type: 'misc',
        rarity: 'common',
        description: '',
        value: 0,
        properties: {}
      });
    }
  };

  const handleCreateQuest = async () => {
    if (newQuest.title && newQuest.description) {
      await addQuest(campaignId, {
        ...newQuest,
        id: `quest_${Date.now()}`,
        status: 'available',
        objectives: [{
          id: `obj_${Date.now()}`,
          description: 'Complete the quest',
          completed: false,
          required: true
        }]
      });
      setQuestDialog(false);
      setNewQuest({
        title: '',
        description: '',
        type: 'side',
        difficulty: 'medium',
        objectives: [],
        rewards: {
          experience: 0,
          gold: 0,
          items: []
        }
      });
    }
  };

  const getLocationIcon = (type) => {
    switch (type) {
      case 'city': return <City />;
      case 'dungeon': return <Castle />;
      case 'forest': return <Forest />;
      case 'mountain': return <Mountain />;
      case 'building': return <Home />;
      case 'room': return <DoorFront />;
      default: return <Place />;
    }
  };

  const getLocationColor = (type) => {
    switch (type) {
      case 'city': return '#4caf50';
      case 'dungeon': return '#795548';
      case 'forest': return '#2e7d32';
      case 'mountain': return '#616161';
      case 'building': return '#ff9800';
      case 'room': return '#2196f3';
      default: return '#9e9e9e';
    }
  };

  return (
    <DndProvider backend={HTML5Backend}>
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
              World Builder
            </Typography>
            {currentCampaign && (
              <Typography variant="h6" sx={{ color: '#ff6b35' }}>
                {currentCampaign.name}
              </Typography>
            )}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={showGrid}
                  onChange={(e) => setShowGrid(e.target.checked)}
                  sx={{ color: 'white' }}
                />
              }
              label="Grid"
              sx={{ color: 'white' }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showConnections}
                  onChange={(e) => setShowConnections(e.target.checked)}
                  sx={{ color: 'white' }}
                />
              }
              label="Connections"
              sx={{ color: 'white' }}
            />
            <Select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value)}
              size="small"
              sx={{
                bgcolor: 'white',
                color: '#330867',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'white'
                }
              }}
            >
              <MenuItem value="map">Map View</MenuItem>
              <MenuItem value="list">List View</MenuItem>
              <MenuItem value="tree">Tree View</MenuItem>
            </Select>
            <IconButton color="inherit" onClick={() => setSettingsDrawer(true)}>
              <Settings />
            </IconButton>
          </Box>
        </Paper>

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {/* Sidebar - World Elements */}
          <Box sx={{ width: 300, borderRight: 1, borderColor: 'divider', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
                <Tab label="Locations" icon={<Map />} />
                <Tab label="NPCs" icon={<Person />} />
                <Tab label="Items" icon={<Inventory />} />
                <Tab label="Quests" icon={<Book />} />
                <Tab label="Overview" icon={<Public />} />
              </Tabs>
            </Box>

            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              {activeTab === 0 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Locations</Typography>
                    <IconButton size="small" onClick={() => setLocationDialog(true)}>
                      <Add />
                    </IconButton>
                  </Box>
                  <List dense>
                    {locations.map((location) => (
                      <ListItem
                        key={location.id}
                        button
                        onClick={() => setSelectedLocation(location)}
                        selected={selectedLocation?.id === location.id}
                        sx={{
                          borderRadius: 1,
                          mb: 0.5,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <ListItemIcon>
                          <Box sx={{ color: getLocationColor(location.type) }}>
                            {getLocationIcon(location.type)}
                          </Box>
                        </ListItemIcon>
                        <ListItemText
                          primary={location.name}
                          secondary={
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                {location.type}
                              </Typography>
                              {location.connections && location.connections.length > 0 && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {location.connections.length} connections
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Edit location
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {activeTab === 1 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">NPCs</Typography>
                    <IconButton size="small" onClick={() => setNPCDialog(true)}>
                      <Add />
                    </IconButton>
                  </Box>
                  <List dense>
                    {npcs.map((npc) => (
                      <ListItem
                        key={npc.id}
                        button
                        onClick={() => setSelectedNPC(npc)}
                        selected={selectedNPC?.id === npc.id}
                        sx={{
                          borderRadius: 1,
                          mb: 0.5,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <ListItemIcon>
                          <Person color="secondary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={npc.name}
                          secondary={
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Level {npc.level}
                              </Typography>
                              {npc.position && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  Location: {npc.position.locationId || 'Unknown'}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Edit NPC
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {activeTab === 2 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Items</Typography>
                    <IconButton size="small" onClick={() => setItemDialog(true)}>
                      <Add />
                    </IconButton>
                  </Box>
                  <List dense>
                    {items.map((item) => (
                      <ListItem
                        key={item.id}
                        button
                        onClick={() => setSelectedItem(item)}
                        selected={selectedItem?.id === item.id}
                        sx={{
                          borderRadius: 1,
                          mb: 0.5,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <ListItemIcon>
                          <Inventory color="action" />
                        </ListItemIcon>
                        <ListItemText
                          primary={item.name}
                          secondary={
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                {item.type} • {item.rarity}
                              </Typography>
                              {item.value > 0 && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {item.value} gp
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Edit item
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {activeTab === 3 && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Quests</Typography>
                    <IconButton size="small" onClick={() => setQuestDialog(true)}>
                      <Add />
                    </IconButton>
                  </Box>
                  <List dense>
                    {quests.map((quest) => (
                      <ListItem
                        key={quest.id}
                        button
                        onClick={() => setSelectedQuest(quest)}
                        selected={selectedQuest?.id === quest.id}
                        sx={{
                          borderRadius: 1,
                          mb: 0.5,
                          border: '1px solid',
                          borderColor: 'divider'
                        }}
                      >
                        <ListItemIcon>
                          <Book color="info" />
                        </ListItemIcon>
                        <ListItemText
                          primary={quest.title}
                          secondary={
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                {quest.type} • {quest.difficulty}
                              </Typography>
                              <Chip
                                label={quest.status}
                                size="small"
                                color={
                                  quest.status === 'completed' ? 'success' :
                                  quest.status === 'active' ? 'warning' :
                                  quest.status === 'failed' ? 'error' : 'default'
                                }
                                sx={{ mt: 0.5 }}
                              />
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Edit quest
                            }}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {activeTab === 4 && (
                <WorldOverview
                  locations={locations}
                  npcs={npcs}
                  items={items}
                  quests={quests}
                />
              )}
            </Box>
          </Box>

          {/* Main Canvas Area */}
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {viewMode === 'map' && (
              <LocationMap
                locations={locations}
                characters={[...characters, ...npcs]}
                selectedLocation={selectedLocation}
                onLocationSelect={setSelectedLocation}
                onLocationMove={(locationId, newPosition) => {
                  // Handle location movement
                }}
                showGrid={showGrid}
                showConnections={showConnections}
              />
            )}

            {viewMode === 'list' && (
              <Box sx={{ p: 3 }}>
                <Grid container spacing={2}>
                  {locations.map((location) => (
                    <Grid item xs={12} md={6} lg={4} key={location.id}>
                      <Card>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Box sx={{ color: getLocationColor(location.type), mr: 1 }}>
                              {getLocationIcon(location.type)}
                            </Box>
                            <Typography variant="h6">{location.name}</Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {location.description}
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            <Chip label={location.type} size="small" />
                            {location.connections && (
                              <Chip label={`${location.connections.length} connections`} size="small" variant="outlined" />
                            )}
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}

            {viewMode === 'tree' && (
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  World Tree View
                </Typography>
                <Alert severity="info">
                  Tree view is under development. It will show the hierarchical structure of your world.
                </Alert>
              </Box>
            )}

            {/* Selected Element Editor */}
            {selectedLocation && (
              <Box sx={{ width: 350, borderLeft: 1, borderColor: 'divider', p: 2, overflow: 'auto' }}>
                <LocationEditor
                  location={selectedLocation}
                  onUpdate={(updatedLocation) => {
                    // Handle location update
                  }}
                  onClose={() => setSelectedLocation(null)}
                />
              </Box>
            )}

            {selectedNPC && (
              <Box sx={{ width: 350, borderLeft: 1, borderColor: 'divider', p: 2, overflow: 'auto' }}>
                <NPCEditor
                  npc={selectedNPC}
                  onUpdate={(updatedNPC) => {
                    // Handle NPC update
                  }}
                  onClose={() => setSelectedNPC(null)}
                />
              </Box>
            )}

            {selectedItem && (
              <Box sx={{ width: 350, borderLeft: 1, borderColor: 'divider', p: 2, overflow: 'auto' }}>
                <ItemEditor
                  item={selectedItem}
                  onUpdate={(updatedItem) => {
                    // Handle item update
                  }}
                  onClose={() => setSelectedItem(null)}
                />
              </Box>
            )}

            {selectedQuest && (
              <Box sx={{ width: 350, borderLeft: 1, borderColor: 'divider', p: 2, overflow: 'auto' }}>
                <QuestEditor
                  quest={selectedQuest}
                  onUpdate={(updatedQuest) => {
                    // Handle quest update
                  }}
                  onClose={() => setSelectedQuest(null)}
                />
              </Box>
            )}
          </Box>
        </Box>

        {/* Floating Action Buttons */}
        <Fab
          color="primary"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            bgcolor: '#ff6b35'
          }}
          onClick={() => setLocationDialog(true)}
        >
          <Add />
        </Fab>

        {/* Create Location Dialog */}
        <Dialog open={locationDialog} onClose={() => setLocationDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Location</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Location Name"
              value={newLocation.name}
              onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Location Type</InputLabel>
              <Select
                value={newLocation.type}
                onChange={(e) => setNewLocation({ ...newLocation, type: e.target.value })}
              >
                <MenuItem value="room">Room</MenuItem>
                <MenuItem value="building">Building</MenuItem>
                <MenuItem value="city">City</MenuItem>
                <MenuItem value="dungeon">Dungeon</MenuItem>
                <MenuItem value="forest">Forest</MenuItem>
                <MenuItem value="mountain">Mountain</MenuItem>
                <MenuItem value="desert">Desert</MenuItem>
                <MenuItem value="ocean">Ocean</MenuItem>
                <MenuItem value="wilderness">Wilderness</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Description"
              value={newLocation.description}
              onChange={(e) => setNewLocation({ ...newLocation, description: e.target.value })}
              margin="normal"
              multiline
              rows={4}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setLocationDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateLocation} variant="contained">Create Location</Button>
          </DialogActions>
        </Dialog>

        {/* Create NPC Dialog */}
        <Dialog open={npcDialog} onClose={() => setNPCDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New NPC</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="NPC Name"
              value={newNPC.name}
              onChange={(e) => setNewNPC({ ...newNPC, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Level"
              type="number"
              value={newNPC.level}
              onChange={(e) => setNewNPC({ ...newNPC, level: parseInt(e.target.value) })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Personality"
              value={newNPC.personality}
              onChange={(e) => setNewNPC({ ...newNPC, personality: e.target.value })}
              margin="normal"
              multiline
              rows={3}
            />
            <TextField
              fullWidth
              label="Backstory"
              value={newNPC.backstory}
              onChange={(e) => setNewNPC({ ...newNPC, backstory: e.target.value })}
              margin="normal"
              multiline
              rows={4}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNPCDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateNPC} variant="contained">Create NPC</Button>
          </DialogActions>
        </Dialog>

        {/* Create Item Dialog */}
        <Dialog open={itemDialog} onClose={() => setItemDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Create New Item</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Item Name"
              value={newItem.name}
              onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
              margin="normal"
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Item Type</InputLabel>
              <Select
                value={newItem.type}
                onChange={(e) => setNewItem({ ...newItem, type: e.target.value })}
              >
                <MenuItem value="weapon">Weapon</MenuItem>
                <MenuItem value="armor">Armor</MenuItem>
                <MenuItem value="potion">Potion</MenuItem>
                <MenuItem value="scroll">Scroll</MenuItem>
                <MenuItem value="wand">Wand</MenuItem>
                <MenuItem value="misc">Miscellaneous</MenuItem>
                <MenuItem value="treasure">Treasure</MenuItem>
                <MenuItem value="tool">Tool</MenuItem>
                <MenuItem value="container">Container</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Rarity</InputLabel>
              <Select
                value={newItem.rarity}
                onChange={(e) => setNewItem({ ...newItem, rarity: e.target.value })}
              >
                <MenuItem value="common">Common</MenuItem>
                <MenuItem value="uncommon">Uncommon</MenuItem>
                <MenuItem value="rare">Rare</MenuItem>
                <MenuItem value="very_rare">Very Rare</MenuItem>
                <MenuItem value="legendary">Legendary</MenuItem>
                <MenuItem value="artifact">Artifact</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Value (gp)"
              type="number"
              value={newItem.value}
              onChange={(e) => setNewItem({ ...newItem, value: parseInt(e.target.value) })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Description"
              value={newItem.description}
              onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
              margin="normal"
              multiline
              rows={4}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setItemDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateItem} variant="contained">Create Item</Button>
          </DialogActions>
        </Dialog>

        {/* Create Quest Dialog */}
        <Dialog open={questDialog} onClose={() => setQuestDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New Quest</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Quest Title"
              value={newQuest.title}
              onChange={(e) => setNewQuest({ ...newQuest, title: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={newQuest.description}
              onChange={(e) => setNewQuest({ ...newQuest, description: e.target.value })}
              margin="normal"
              multiline
              rows={4}
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Quest Type</InputLabel>
              <Select
                value={newQuest.type}
                onChange={(e) => setNewQuest({ ...newQuest, type: e.target.value })}
              >
                <MenuItem value="main">Main Quest</MenuItem>
                <MenuItem value="side">Side Quest</MenuItem>
                <MenuItem value="personal">Personal Quest</MenuItem>
                <MenuItem value="faction">Faction Quest</MenuItem>
                <MenuItem value="exploration">Exploration</MenuItem>
                <MenuItem value="combat">Combat</MenuItem>
                <MenuItem value="social">Social</MenuItem>
                <MenuItem value="mystery">Mystery</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Difficulty</InputLabel>
              <Select
                value={newQuest.difficulty}
                onChange={(e) => setNewQuest({ ...newQuest, difficulty: e.target.value })}
              >
                <MenuItem value="easy">Easy</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="hard">Hard</MenuItem>
                <MenuItem value="deadly">Deadly</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              label="Experience Reward"
              type="number"
              value={newQuest.rewards.experience}
              onChange={(e) => setNewQuest({
                ...newQuest,
                rewards: { ...newQuest.rewards, experience: parseInt(e.target.value) }
              })}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Gold Reward"
              type="number"
              value={newQuest.rewards.gold}
              onChange={(e) => setNewQuest({
                ...newQuest,
                rewards: { ...newQuest.rewards, gold: parseInt(e.target.value) }
              })}
              margin="normal"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setQuestDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateQuest} variant="contained">Create Quest</Button>
          </DialogActions>
        </Dialog>

        {/* Settings Drawer */}
        <Drawer
          anchor="right"
          open={settingsDrawer}
          onClose={() => setSettingsDrawer(false)}
        >
          <Box sx={{ width: 300, p: 2 }}>
            <Typography variant="h6" gutterBottom>World Builder Settings</Typography>
            <Divider sx={{ mb: 2 }} />

            <Typography variant="subtitle2" gutterBottom>Display Options</Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={showGrid}
                  onChange={(e) => setShowGrid(e.target.checked)}
                />
              }
              label="Show Grid"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={showConnections}
                  onChange={(e) => setShowConnections(e.target.checked)}
                />
              }
              label="Show Connections"
            />

            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>Auto-Save</Typography>
            <Alert severity="info" size="small">
              World changes are automatically saved to your campaign.
            </Alert>
          </Box>
        </Drawer>
      </Box>
    </DndProvider>
  );
};

export default WorldBuilder;