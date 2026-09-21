import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Rect, Circle, Line, Text, Image, Group } from 'react-konva';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Fab,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  FormControl,
  InputLabel,
  Slider,
  Switch,
  FormControlLabel,
  Chip,
  Divider
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
  GridOn,
  GridOff,
  Link,
  LinkOff,
  Edit,
  Delete,
  Visibility,
  VisibilityOff,
  Save,
  Close
} from '@mui/icons-material';

const LocationMap = ({
  locations = [],
  characters = [],
  selectedLocation,
  onLocationSelect,
  onLocationMove,
  onConnectionCreate,
  onConnectionDelete,
  showGrid = true,
  showConnections = true,
  readOnly = false
}) => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [connecting, setConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [editDialog, setEditDialog] = useState(false);
  const [locationEdit, setLocationEdit] = useState(null);
  const [mapSettings, setMapSettings] = useState({
    gridSize: 50,
    snapToGrid: true,
    showLabels: true,
    showMiniMap: true,
    backgroundColor: '#1a1a1a',
    gridColor: '#333333'
  });

  const stageRef = useRef(null);
  const containerRef = useRef(null);

  // Initialize positions for locations that don't have them
  useEffect(() => {
    locations.forEach(location => {
      if (!location.position) {
        location.position = {
          x: Math.random() * 600 + 100,
          y: Math.random() * 400 + 100
        };
      }
    });
  }, [locations]);

  const handleWheel = useCallback((e) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const oldScale = scale;
    const pointer = stageRef.current.getPointerPosition();

    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale
    };

    const newScale = e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
    const newPos = {
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale
    };

    setScale(Math.max(0.1, Math.min(5, newScale)));
    setPosition(newPos);
  }, [scale, position]);

  const handleStageMouseDown = (e) => {
    if (readOnly) return;

    const clickedOnEmpty = e.target === e.target.getStage();
    if (clickedOnEmpty) {
      setIsDragging(true);
      setDragStart({
        x: e.evt.clientX - position.x,
        y: e.evt.clientY - position.y
      });
    }
  };

  const handleStageMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.evt.clientX - dragStart.x,
        y: e.evt.clientY - dragStart.y
      });
    }
  };

  const handleStageMouseUp = () => {
    setIsDragging(false);
  };

  const snapToGrid = (value) => {
    if (!mapSettings.snapToGrid) return value;
    return Math.round(value / mapSettings.gridSize) * mapSettings.gridSize;
  };

  const handleLocationDragEnd = (e, location) => {
    if (readOnly) return;

    const newPosition = {
      x: snapToGrid(e.target.x()),
      y: snapToGrid(e.target.y())
    };

    if (onLocationMove) {
      onLocationMove(location.id, newPosition);
    }
  };

  const handleLocationClick = (location, e) => {
    if (readOnly) return;

    e.evt.evt.stopPropagation();

    if (connecting && connectionStart) {
      if (connectionStart.id !== location.id) {
        // Create connection
        if (onConnectionCreate) {
          onConnectionCreate(connectionStart.id, location.id);
        }
      }
      setConnecting(false);
      setConnectionStart(null);
    } else {
      onLocationSelect && onLocationSelect(location);
    }
  };

  const handleLocationRightClick = (location, e) => {
    if (readOnly) return;

    e.evt.preventDefault();
    setContextMenu({
      mouseX: e.evt.clientX,
      mouseY: e.evt.clientY,
      location
    });
  };

  const startConnection = (location) => {
    if (readOnly) return;

    setConnecting(true);
    setConnectionStart(location);
  };

  const deleteConnection = (fromId, toId) => {
    if (onConnectionDelete) {
      onConnectionDelete(fromId, toId);
    }
  };

  const resetView = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const getLocationColor = (type) => {
    const colors = {
      city: '#4caf50',
      dungeon: '#795548',
      forest: '#2e7d32',
      mountain: '#616161',
      desert: '#ffc107',
      ocean: '#2196f3',
      building: '#ff9800',
      room: '#9c27b0',
      wilderness: '#689f38',
      custom: '#607d8b'
    };
    return colors[type] || '#9e9e9e';
  };

  const getLocationIcon = (type) => {
    // This would return emoji or icon representations
    const icons = {
      city: '🏰',
      dungeon: '🏛️',
      forest: '🌲',
      mountain: '⛰️',
      desert: '🏜️',
      ocean: '🌊',
      building: '🏠',
      room: '🚪',
      wilderness: '🌿',
      custom: '📍'
    };
    return icons[type] || '📍';
  };

  const renderGrid = () => {
    if (!showGrid) return null;

    const gridLines = [];
    const width = window.innerWidth;
    const height = window.innerHeight;
    const gridSize = mapSettings.gridSize;

    // Vertical lines
    for (let x = -position.x % gridSize; x < width; x += gridSize) {
      gridLines.push(
        <Line
          key={`v-${x}`}
          points={[x, 0, x, height]}
          stroke={mapSettings.gridColor}
          strokeWidth={0.5}
          opacity={0.3}
        />
      );
    }

    // Horizontal lines
    for (let y = -position.y % gridSize; y < height; y += gridSize) {
      gridLines.push(
        <Line
          key={`h-${y}`}
          points={[0, y, width, y]}
          stroke={mapSettings.gridColor}
          strokeWidth={0.5}
          opacity={0.3}
        />
      );
    }

    return gridLines;
  };

  const renderConnections = () => {
    if (!showConnections) return null;

    const connections = [];
    const processedConnections = new Set();

    locations.forEach(location => {
      if (location.connections) {
        location.connections.forEach(connection => {
          const connectionKey = `${location.id}-${connection.locationId}`;
          const reverseKey = `${connection.locationId}-${location.id}`;

          if (!processedConnections.has(connectionKey) && !processedConnections.has(reverseKey)) {
            const targetLocation = locations.find(l => l.id === connection.locationId);
            if (targetLocation) {
              connections.push({
                from: location,
                to: targetLocation,
                locked: connection.locked || false,
                type: connection.type || 'normal'
              });
              processedConnections.add(connectionKey);
            }
          }
        });
      }
    });

    return connections.map((connection, index) => {
      const from = connection.from.position;
      const to = connection.to.position;

      return (
        <Group key={`connection-${index}`}>
          <Line
            points={[from.x, from.y, to.x, to.y]}
            stroke={connection.locked ? '#f44336' : '#666'}
            strokeWidth={connection.locked ? 3 : 2}
            dash={connection.type === 'secret' ? [5, 5] : []}
            opacity={0.6}
          />
          {connection.locked && (
            <Circle
              x={(from.x + to.x) / 2}
              y={(from.y + to.y) / 2}
              radius={8}
              fill="#f44336"
            />
          )}
        </Group>
      );
    });
  };

  return (
    <Box ref={containerRef} sx={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      {/* Controls */}
      <Paper
        elevation={2}
        sx={{
          position: 'absolute',
          top: 16,
          left: 16,
          zIndex: 10,
          p: 1,
          display: 'flex',
          gap: 0.5,
          bgcolor: 'rgba(26, 26, 26, 0.9)'
        }}
      >
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={() => setScale(Math.min(5, scale * 1.2))}>
            <ZoomIn />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={() => setScale(Math.max(0.1, scale / 1.2))}>
            <ZoomOut />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View">
          <IconButton size="small" onClick={resetView}>
            <CenterFocusStrong />
          </IconButton>
        </Tooltip>
        <Divider orientation="vertical" flexItem />
        <Tooltip title={showGrid ? "Hide Grid" : "Show Grid"}>
          <IconButton size="small" onClick={() => setMapSettings(prev => ({ ...prev, showGrid: !prev.showGrid }))}>
            {showGrid ? <GridOn /> : <GridOff />}
          </IconButton>
        </Tooltip>
        <Tooltip title={showConnections ? "Hide Connections" : "Show Connections"}>
          <IconButton size="small" onClick={() => setMapSettings(prev => ({ ...prev, showConnections: !prev.showConnections }))}>
            {showConnections ? <Link /> : <LinkOff />}
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Connection Mode Indicator */}
      {connecting && (
        <Paper
          elevation={2}
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            zIndex: 10,
            p: 2,
            bgcolor: 'warning.main',
            color: 'warning.contrastText'
          }}
        >
          <Typography variant="body2">
            Connecting from {connectionStart?.name}... Click another location to connect or press ESC to cancel.
          </Typography>
          <Button
            size="small"
            onClick={() => {
              setConnecting(false);
              setConnectionStart(null);
            }}
            sx={{ mt: 1 }}
          >
            Cancel
          </Button>
        </Paper>
      )}

      {/* Map Canvas */}
      <Stage
        width={window.innerWidth}
        height={window.innerHeight}
        scaleX={scale}
        scaleY={scale}
        x={position.x}
        y={position.y}
        draggable={!readOnly && !connecting}
        onWheel={handleWheel}
        onMouseDown={handleStageMouseDown}
        onMouseMove={handleStageMouseMove}
        onMouseUp={handleStageMouseUp}
        ref={stageRef}
      >
        <Layer>
          {/* Background */}
          <Rect
            x={-2000}
            y={-2000}
            width={4000}
            height={4000}
            fill={mapSettings.backgroundColor}
          />

          {/* Grid */}
          {renderGrid()}

          {/* Connections */}
          {renderConnections()}

          {/* Locations */}
          {locations.map(location => {
            const isSelected = selectedLocation?.id === location.id;
            const isConnectingSource = connecting && connectionStart?.id === location.id;

            return (
              <Group key={location.id}>
                {/* Location Circle */}
                <Circle
                  x={location.position.x}
                  y={location.position.y}
                  radius={30}
                  fill={getLocationColor(location.type)}
                  stroke={isSelected ? '#ff6b35' : isConnectingSource ? '#4caf50' : '#fff'}
                  strokeWidth={isSelected ? 4 : isConnectingSource ? 3 : 2}
                  draggable={!readOnly}
                  onDragEnd={(e) => handleLocationDragEnd(e, location)}
                  onClick={(e) => handleLocationClick(location, e)}
                  onContextMenu={(e) => handleLocationRightClick(location, e)}
                  opacity={location.hidden ? 0.5 : 1}
                />

                {/* Location Icon */}
                <Text
                  text={getLocationIcon(location.type)}
                  x={location.position.x}
                  y={location.position.y}
                  fontSize={20}
                  offsetX={10}
                  offsetY={10}
                  fill="#fff"
                  draggable={!readOnly}
                  onDragEnd={(e) => handleLocationDragEnd(e, location)}
                  onClick={(e) => handleLocationClick(location, e)}
                  onContextMenu={(e) => handleLocationRightClick(location, e)}
                />

                {/* Location Label */}
                {mapSettings.showLabels && (
                  <Text
                    text={location.name}
                    x={location.position.x}
                    y={location.position.y + 40}
                    fontSize={12}
                    offsetX={location.name.length * 3}
                    fill="#fff"
                    draggable={!readOnly}
                    onDragEnd={(e) => handleLocationDragEnd(e, location)}
                    onClick={(e) => handleLocationClick(location, e)}
                    onContextMenu={(e) => handleLocationRightClick(location, e)}
                  />
                )}

                {/* Character Indicators */}
                {characters
                  .filter(char => char.position?.locationId === location.id)
                  .map((character, index) => (
                    <Circle
                      key={character.id}
                      x={location.position.x + 40 + (index * 15)}
                      y={location.position.y - 20}
                      radius={6}
                      fill={character.type === 'player' ? '#4caf50' : '#ff9800'}
                      stroke="#fff"
                      strokeWidth={1}
                    />
                  ))
                }
              </Group>
            );
          })}
        </Layer>
      </Stage>

      {/* Context Menu */}
      <Menu
        open={contextMenu !== null}
        onClose={() => setContextMenu(null)}
        anchorReference="anchorPosition"
        anchorPosition={
          contextMenu !== null
            ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={() => {
          onLocationSelect(contextMenu.location);
          setContextMenu(null);
        }}>
          <Edit sx={{ mr: 1 }} /> Edit Location
        </MenuItem>
        <MenuItem onClick={() => {
          startConnection(contextMenu.location);
          setContextMenu(null);
        }}>
          <Link sx={{ mr: 1 }} /> Connect To...
        </MenuItem>
        <MenuItem onClick={() => {
          setContextMenu(null);
          // Toggle visibility
        }}>
          <Visibility sx={{ mr: 1 }} /> Toggle Visibility
        </MenuItem>
        <MenuItem onClick={() => {
          setContextMenu(null);
          // Delete location (with confirmation)
        }}>
          <Delete sx={{ mr: 1 }} /> Delete Location
        </MenuItem>
      </Menu>

      {/* Mini Map */}
      {mapSettings.showMiniMap && (
        <Paper
          elevation={2}
          sx={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            width: 200,
            height: 150,
            zIndex: 10,
            overflow: 'hidden',
            bgcolor: 'rgba(26, 26, 26, 0.9)'
          }}
        >
          <Box sx={{ p: 1, borderBottom: '1px solid #333' }}>
            <Typography variant="caption">Mini Map</Typography>
          </Box>
          <Box sx={{ p: 1, height: 'calc(100% - 32px)', position: 'relative' }}>
            {/* Mini map content would go here */}
            <Typography variant="caption" color="text.secondary">
              {locations.length} locations
            </Typography>
          </Box>
        </Paper>
      )}

      {/* Scale Indicator */}
      <Paper
        elevation={2}
        sx={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          zIndex: 10,
          p: 1,
          bgcolor: 'rgba(26, 26, 26, 0.9)'
        }}
      >
        <Typography variant="caption">
          Scale: {Math.round(scale * 100)}%
        </Typography>
      </Paper>

      {/* Edit Location Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Location</DialogTitle>
        <DialogContent>
          {locationEdit && (
            <Box sx={{ pt: 1 }}>
              <TextField
                fullWidth
                label="Name"
                value={locationEdit.name || ''}
                onChange={(e) => setLocationEdit({ ...locationEdit, name: e.target.value })}
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select
                  value={locationEdit.type || 'room'}
                  onChange={(e) => setLocationEdit({ ...locationEdit, type: e.target.value })}
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
                value={locationEdit.description || ''}
                onChange={(e) => setLocationEdit({ ...locationEdit, description: e.target.value })}
                margin="normal"
                multiline
                rows={3}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={locationEdit.hidden || false}
                    onChange={(e) => setLocationEdit({ ...locationEdit, hidden: e.target.checked })}
                  />
                }
                label="Hidden"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>Cancel</Button>
          <Button onClick={() => {
            // Save changes
            setEditDialog(false);
          }} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LocationMap;