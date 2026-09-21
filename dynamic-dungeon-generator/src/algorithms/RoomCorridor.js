/**
 * Room-Corridor Dungeon Generation Algorithm
 * Creates traditional dungeons with separate rooms connected by corridors
 */

const BaseAlgorithm = require('./BaseAlgorithm');
const MathUtils = require('../utils/MathUtils');

class RoomCorridor extends BaseAlgorithm {
  constructor(config, logger) {
    super(config, logger);

    // Default parameters for room-corridor generation
    this.defaultParams = {
      roomCount: { min: 8, max: 20 },
      roomSize: { min: 4, max: 12 },
      corridorWidth: 1,
      maxCorridorLength: 20,
      connectionAttempts: 50,
      roomSpacing: 2,
      loopProbability: 0.2,
      deadEndProbability: 0.1,
      specialRoomChance: 0.3,
      symmetry: { enabled: false, type: 'horizontal' },
      growthPattern: 'random' // 'spiral', 'branching', 'clustered'
    };
  }

  /**
   * Generate dungeon using room-corridor approach
   */
  async generate(params) {
    const {
      width = 70,
      height = 70,
      seed = Math.random(),
      themeConfig,
      ...options
    } = params;

    this.logger.info('Starting room-corridor generation', { width, height });

    // Merge with default parameters
    const genParams = { ...this.defaultParams, ...options };

    // Set seed
    MathUtils.setSeed(seed);

    // Initialize grid
    const grid = this.initializeGrid(width, height);

    // Determine room count
    const roomCount = Math.floor(
      Math.random() * (genParams.roomCount.max - genParams.roomCount.min + 1) +
      genParams.roomCount.min
    );

    // Generate rooms
    const rooms = this.generateRooms(grid, roomCount, genParams);

    // Connect rooms with corridors
    const corridors = this.connectRooms(grid, rooms, genParams);

    // Add optional loops
    if (genParams.loopProbability > 0) {
      this.addLoops(grid, rooms, corridors, genParams);
    }

    // Create dead ends if desired
    if (genParams.deadEndProbability > 0) {
      this.addDeadEnds(grid, rooms, corridors, genParams);
    }

    // Apply symmetry if enabled
    if (genParams.symmetry.enabled) {
      this.applySymmetry(grid, rooms, corridors, genParams);
    }

    // Post-processing
    const finalGrid = this.postProcess(grid);

    // Identify features
    const features = this.identifyRoomCorridorFeatures(rooms, corridors, genParams);

    this.logger.info('Room-corridor generation completed', {
      rooms: rooms.length,
      corridors: corridors.length,
      connectivity: this.calculateConnectivity(rooms)
    });

    return {
      grid: finalGrid,
      rooms,
      corridors,
      features,
      algorithm: 'roomCorridor',
      parameters: genParams
    };
  }

  /**
   * Generate rooms based on growth pattern
   */
  generateRooms(grid, roomCount, params) {
    const rooms = [];
    const placedRooms = [];

    // Choose growth pattern
    switch (params.growthPattern) {
      case 'spiral':
        return this.generateSpiralRooms(grid, roomCount, params);
      case 'branching':
        return this.generateBranchingRooms(grid, roomCount, params);
      case 'clustered':
        return this.generateClusteredRooms(grid, roomCount, params);
      default:
        return this.generateRandomRooms(grid, roomCount, params);
    }
  }

  /**
   * Generate rooms randomly
   */
  generateRandomRooms(grid, roomCount, params) {
    const rooms = [];
    const maxAttempts = roomCount * 10;
    let attempts = 0;

    while (rooms.length < roomCount && attempts < maxAttempts) {
      const room = this.generateRandomRoom(grid, params);

      if (this.canPlaceRoom(grid, room, params.roomSpacing)) {
        this.placeRoom(grid, room);
        rooms.push(room);
      }

      attempts++;
    }

    // Ensure we have at least some rooms
    if (rooms.length < 3) {
      return this.generateFallbackRooms(grid, Math.min(5, roomCount), params);
    }

    return rooms;
  }

  /**
   * Generate spiral pattern rooms
   */
  generateSpiralRooms(grid, roomCount, params) {
    const rooms = [];
    const centerX = Math.floor(grid[0].length / 2);
    const centerY = Math.floor(grid.length / 2);
    let angle = 0;
    let radius = 0;

    // Place first room at center
    const centerRoom = this.generateRoomAtPosition(grid, centerX, centerY, params);
    if (centerRoom) {
      this.placeRoom(grid, centerRoom);
      rooms.push(centerRoom);
    }

    // Spiral outward
    while (rooms.length < roomCount) {
      const x = Math.round(centerX + radius * Math.cos(angle));
      const y = Math.round(centerY + radius * Math.sin(angle));

      const room = this.generateRoomAtPosition(grid, x, y, params);
      if (room && this.canPlaceRoom(grid, room, params.roomSpacing)) {
        this.placeRoom(grid, room);
        rooms.push(room);
      }

      angle += 0.5;
      radius += 0.3;

      if (radius > Math.min(grid[0].length, grid.length) / 2 - 5) {
        break;
      }
    }

    return rooms;
  }

  /**
   * Generate branching pattern rooms
   */
  generateBranchingRooms(grid, roomCount, params) {
    const rooms = [];
    const branches = [];
    const branchLength = Math.floor(roomCount / 3);

    // Create main trunk
    const startX = Math.floor(grid[0].length / 2);
    const startY = 5;

    for (let i = 0; i < branchLength && rooms.length < roomCount; i++) {
      const y = startY + i * 8;
      const room = this.generateRoomAtPosition(grid, startX, y, params);

      if (room && this.canPlaceRoom(grid, room, params.roomSpacing)) {
        this.placeRoom(grid, room);
        rooms.push(room);
        branches.push({ room, x: startX, y });
      }
    }

    // Add side branches
    for (const branch of branches) {
      if (rooms.length >= roomCount) break;

      const sideCount = Math.floor(Math.random() * 3) + 1;
      for (let i = 0; i < sideCount && rooms.length < roomCount; i++) {
        const sideX = branch.x + (Math.random() < 0.5 ? -10 : 10);
        const sideY = branch.y + Math.floor(Math.random() * 6) - 3;

        const sideRoom = this.generateRoomAtPosition(grid, sideX, sideY, params);
        if (sideRoom && this.canPlaceRoom(grid, sideRoom, params.roomSpacing)) {
          this.placeRoom(grid, sideRoom);
          rooms.push(sideRoom);
        }
      }
    }

    return rooms;
  }

  /**
   * Generate clustered rooms
   */
  generateClusteredRooms(grid, roomCount, params) {
    const rooms = [];
    const clusters = Math.max(2, Math.floor(roomCount / 5));
    const roomsPerCluster = Math.ceil(roomCount / clusters);

    for (let c = 0; c < clusters && rooms.length < roomCount; c++) {
      // Find cluster center
      const clusterCenterX = Math.floor(Math.random() * (grid[0].length - 20)) + 10;
      const clusterCenterY = Math.floor(Math.random() * (grid.length - 20)) + 10;

      // Generate rooms around cluster center
      let clusterRooms = 0;
      const maxClusterAttempts = roomsPerCluster * 3;

      while (clusterRooms < roomsPerCluster && rooms.length < roomCount) {
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.random() * 8 + 2;

        const x = Math.round(clusterCenterX + distance * Math.cos(angle));
        const y = Math.round(clusterCenterY + distance * Math.sin(angle));

        const room = this.generateRoomAtPosition(grid, x, y, params);
        if (room && this.canPlaceRoom(grid, room, params.roomSpacing)) {
          this.placeRoom(grid, room);
          rooms.push(room);
          clusterRooms++;
        }
      }
    }

    return rooms;
  }

  /**
   * Generate fallback rooms (simple guaranteed placement)
   */
  generateFallbackRooms(grid, count, params) {
    const rooms = [];
    const spacing = 8;
    const startX = 10;
    const startY = 10;

    for (let i = 0; i < count; i++) {
      const x = startX + (i % 3) * spacing;
      const y = startY + Math.floor(i / 3) * spacing;

      const room = this.generateRoomAtPosition(grid, x, y, params);
      if (room) {
        this.placeRoom(grid, room);
        rooms.push(room);
      }
    }

    return rooms;
  }

  /**
   * Generate a random room
   */
  generateRandomRoom(grid, params) {
    const roomWidth = Math.floor(
      Math.random() * (params.roomSize.max - params.roomSize.min + 1) +
      params.roomSize.min
    );
    const roomHeight = Math.floor(
      Math.random() * (params.roomSize.max - params.roomSize.min + 1) +
      params.roomSize.min
    );

    const x = Math.floor(Math.random() * (grid[0].length - roomWidth - 2)) + 1;
    const y = Math.floor(Math.random() * (grid.length - roomHeight - 2)) + 1;

    const roomType = this.determineRoomType(params.specialRoomChance);

    return {
      id: MathUtils.generateId(),
      x, y,
      width: roomWidth,
      height: roomHeight,
      type: roomType,
      centerX: x + Math.floor(roomWidth / 2),
      centerY: y + Math.floor(roomHeight / 2),
      connections: [],
      features: []
    };
  }

  /**
   * Generate room at specific position
   */
  generateRoomAtPosition(grid, x, y, params) {
    const roomWidth = Math.floor(
      Math.random() * (params.roomSize.max - params.roomSize.min + 1) +
      params.roomSize.min
    );
    const roomHeight = Math.floor(
      Math.random() * (params.roomSize.max - params.roomSize.min + 1) +
      params.roomSize.min
    );

    const roomX = x - Math.floor(roomWidth / 2);
    const roomY = y - Math.floor(roomHeight / 2);

    // Check bounds
    if (roomX < 1 || roomY < 1 ||
        roomX + roomWidth >= grid[0].length - 1 ||
        roomY + roomHeight >= grid.length - 1) {
      return null;
    }

    const roomType = this.determineRoomType(params.specialRoomChance);

    return {
      id: MathUtils.generateId(),
      x: roomX,
      y: roomY,
      width: roomWidth,
      height: roomHeight,
      type: roomType,
      centerX: x,
      centerY: y,
      connections: [],
      features: []
    };
  }

  /**
   * Determine room type
   */
  determineRoomType(specialChance) {
    const rand = Math.random();

    if (rand < specialChance) {
      const specialTypes = ['treasure', 'trap', 'puzzle', 'boss', 'secret'];
      return specialTypes[Math.floor(Math.random() * specialTypes.length)];
    }

    return 'normal';
  }

  /**
   * Check if room can be placed
   */
  canPlaceRoom(grid, room, spacing) {
    const checkX = Math.max(0, room.x - spacing);
    const checkY = Math.max(0, room.y - spacing);
    const checkWidth = room.width + spacing * 2;
    const checkHeight = room.height + spacing * 2;

    for (let y = checkY; y < Math.min(checkY + checkHeight, grid.length); y++) {
      for (let x = checkX; x < Math.min(checkX + checkWidth, grid[0].length); x++) {
        if (grid[y][x] !== 'wall') {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Place room on grid
   */
  placeRoom(grid, room) {
    // Carve out room
    for (let y = room.y; y < room.y + room.height; y++) {
      for (let x = room.x; x < room.x + room.width; x++) {
        if (y === room.y || y === room.y + room.height - 1 ||
            x === room.x || x === room.x + room.width - 1) {
          grid[y][x] = 'wall';
        } else {
          grid[y][x] = 'floor';
        }
      }
    }

    // Add doors on random edges
    const doorPositions = this.getPotentialDoorPositions(grid, room);
    const doorCount = Math.min(4, Math.floor(Math.random() * 3) + 1);

    for (let i = 0; i < doorCount && i < doorPositions.length; i++) {
      const doorPos = doorPositions[Math.floor(Math.random() * doorPositions.length)];
      grid[doorPos.y][doorPos.x] = 'door';
    }
  }

  /**
   * Get potential door positions for a room
   */
  getPotentialDoorPositions(grid, room) {
    const positions = [];

    // Top and bottom walls
    for (let x = room.x + 1; x < room.x + room.width - 1; x++) {
      if (room.y > 0 && grid[room.y - 1][x] === 'wall') {
        positions.push({ x, y: room.y });
      }
      if (room.y + room.height < grid.length && grid[room.y + room.height][x] === 'wall') {
        positions.push({ x, y: room.y + room.height - 1 });
      }
    }

    // Left and right walls
    for (let y = room.y + 1; y < room.y + room.height - 1; y++) {
      if (room.x > 0 && grid[y][room.x - 1] === 'wall') {
        positions.push({ x: room.x, y });
      }
      if (room.x + room.width < grid[0].length && grid[y][room.x + room.width] === 'wall') {
        positions.push({ x: room.x + room.width - 1, y });
      }
    }

    return positions;
  }

  /**
   * Connect rooms with corridors
   */
  connectRooms(grid, rooms, params) {
    const corridors = [];
    const connected = new Set([rooms[0].id]);
    const unconnected = new Set(rooms.slice(1).map(r => r.id));

    while (unconnected.size > 0) {
      // Find closest connection between connected and unconnected
      let closestConnection = null;
      let minDistance = Infinity;

      for (const connectedId of connected) {
        const connectedRoom = rooms.find(r => r.id === connectedId);

        for (const unconnectedId of unconnected) {
          const unconnectedRoom = rooms.find(r => r.id === unconnectedId);
          const distance = MathUtils.distance(
            connectedRoom.centerX, connectedRoom.centerY,
            unconnectedRoom.centerX, unconnectedRoom.centerY
          );

          if (distance < minDistance) {
            minDistance = distance;
            closestConnection = { from: connectedRoom, to: unconnectedRoom };
          }
        }
      }

      if (closestConnection) {
        const corridor = this.createCorridor(
          grid,
          closestConnection.from.centerX, closestConnection.from.centerY,
          closestConnection.to.centerX, closestConnection.to.centerY,
          'normal'
        );

        corridors.push(corridor);

        // Update connections
        closestConnection.from.connections.push(closestConnection.to.id);
        closestConnection.to.connections.push(closestConnection.from.id);

        // Move room from unconnected to connected
        connected.add(closestConnection.to.id);
        unconnected.delete(closestConnection.to.id);
      } else {
        break; // Can't connect any more rooms
      }
    }

    return corridors;
  }

  /**
   * Add loops to create more interesting layouts
   */
  addLoops(grid, rooms, corridors, params) {
    const loopCandidates = [];

    // Find room pairs that could create loops
    for (let i = 0; i < rooms.length; i++) {
      for (let j = i + 1; j < rooms.length; j++) {
        const room1 = rooms[i];
        const room2 = rooms[j];

        // Skip if already directly connected
        if (room1.connections.includes(room2.id)) continue;

        const distance = MathUtils.distance(
          room1.centerX, room1.centerY,
          room2.centerX, room2.centerY
        );

        if (distance < params.maxCorridorLength * 2) {
          loopCandidates.push({ room1, room2, distance });
        }
      }
    }

    // Sort by distance and add some loops
    loopCandidates.sort((a, b) => a.distance - b.distance);

    const loopsToAdd = Math.floor(loopCandidates.length * params.loopProbability);
    for (let i = 0; i < loopsToAdd && i < loopCandidates.length; i++) {
      const { room1, room2 } = loopCandidates[i];

      if (Math.random() < params.loopProbability) {
        const corridor = this.createCorridor(
          grid,
          room1.centerX, room1.centerY,
          room2.centerX, room2.centerY,
          'loop'
        );

        corridors.push(corridor);
        room1.connections.push(room2.id);
        room2.connections.push(room1.id);
      }
    }
  }

  /**
   * Add dead ends for variety
   */
  addDeadEnds(grid, rooms, corridors, params) {
    const deadEndCandidates = rooms.filter(room => room.connections.length === 1);

    for (const room of deadEndCandidates) {
      if (Math.random() < params.deadEndProbability) {
        // Add dead end corridor
        const direction = Math.floor(Math.random() * 4);
        let endX = room.centerX;
        let endY = room.centerY;
        const length = Math.floor(Math.random() * 5) + 3;

        switch (direction) {
          case 0: endY -= length; break; // Up
          case 1: endX += length; break; // Right
          case 2: endY += length; break; // Down
          case 3: endX -= length; break; // Left
        }

        const corridor = this.createCorridor(
          grid,
          room.centerX, room.centerY,
          endX, endY,
          'dead-end'
        );

        corridors.push(corridor);
      }
    }
  }

  /**
   * Apply symmetry to the dungeon
   */
  applySymmetry(grid, rooms, corridors, params) {
    if (params.symmetry.type === 'horizontal') {
      this.applyHorizontalSymmetry(grid, rooms, corridors);
    } else {
      this.applyVerticalSymmetry(grid, rooms, corridors);
    }
  }

  /**
   * Apply horizontal symmetry
   */
  applyHorizontalSymmetry(grid, rooms, corridors) {
    const midX = Math.floor(grid[0].length / 2);
    const newGrid = grid.map(row => [...row]);

    // Mirror left side to right side
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < midX; x++) {
        const mirrorX = grid[0].length - 1 - x;
        newGrid[y][mirrorX] = grid[y][x];
      }
    }

    // Copy back to original grid
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        grid[y][x] = newGrid[y][x];
      }
    }
  }

  /**
   * Apply vertical symmetry
   */
  applyVerticalSymmetry(grid, rooms, corridors) {
    const midY = Math.floor(grid.length / 2);
    const newGrid = grid.map(row => [...row]);

    // Mirror top to bottom
    for (let y = 0; y < midY; y++) {
      const mirrorY = grid.length - 1 - y;
      for (let x = 0; x < grid[0].length; x++) {
        newGrid[mirrorY][x] = grid[y][x];
      }
    }

    // Copy back to original grid
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        grid[y][x] = newGrid[y][x];
      }
    }
  }

  /**
   * Identify room-corridor specific features
   */
  identifyRoomCorridorFeatures(rooms, corridors, params) {
    return {
      roomTypes: this.categorizeRooms(rooms),
      corridorTypes: this.categorizeCorridors(corridors),
      connectivity: this.calculateConnectivity(rooms),
      loops: corridors.filter(c => c.type === 'loop').length,
      deadEnds: rooms.filter(r => r.connections.length === 1).length,
      growthPattern: params.growthPattern,
      hasSymmetry: params.symmetry.enabled
    };
  }

  /**
   * Categorize rooms by type
   */
  categorizeRooms(rooms) {
    const categories = {};
    rooms.forEach(room => {
      categories[room.type] = (categories[room.type] || 0) + 1;
    });
    return categories;
  }

  /**
   * Categorize corridors by type
   */
  categorizeCorridors(corridors) {
    const categories = {};
    corridors.forEach(corridor => {
      categories[corridor.type] = (categories[corridor.type] || 0) + 1;
    });
    return categories;
  }

  /**
   * Calculate connectivity metrics
   */
  calculateConnectivity(rooms) {
    if (rooms.length === 0) return 0;

    const totalConnections = rooms.reduce((sum, room) => sum + room.connections.length, 0);
    const maxConnections = rooms.length * (rooms.length - 1) / 2;

    return {
      averageConnections: totalConnections / rooms.length,
      connectivityRatio: totalConnections / (maxConnections * 2), // Each connection counted twice
      totalConnections: totalConnections / 2
    };
  }
}

module.exports = RoomCorridor;