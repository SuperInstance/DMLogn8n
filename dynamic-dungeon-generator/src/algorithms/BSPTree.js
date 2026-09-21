/**
 * Binary Space Partitioning (BSP) Dungeon Generation Algorithm
 * Creates structured, room-based dungeons using recursive subdivision
 */

const BaseAlgorithm = require('./BaseAlgorithm');
const MathUtils = require('../utils/MathUtils');

class BSPTree extends BaseAlgorithm {
  constructor(config, logger) {
    super(config, logger);

    // Default parameters for BSP generation
    this.defaultParams = {
      minRoomSize: 6,
      maxRoomSize: 15,
      minSplitSize: 10,
      maxSplitDepth: 8,
      corridorWidth: 2,
      splitRatio: { min: 0.3, max: 0.7 },
      roomPadding: 1,
      connectionType: 'corridor', // 'corridor' or 'direct'
      asymmetryFactor: 0.2
    };
  }

  /**
   * Generate dungeon using BSP tree
   */
  async generate(params) {
    const {
      width = 60,
      height = 60,
      seed = Math.random(),
      themeConfig,
      ...options
    } = params;

    this.logger.info('Starting BSP tree generation', { width, height });

    // Merge with default parameters
    const genParams = { ...this.defaultParams, ...options };

    // Set seed
    MathUtils.setSeed(seed);

    // Initialize grid
    const grid = this.initializeGrid(width, height);

    // Build BSP tree
    const bspTree = this.buildBSPTree({
      x: 0, y: 0, width, height
    }, genParams);

    // Generate rooms from leaf nodes
    const rooms = this.generateRoomsFromBSP(bspTree, grid, genParams);

    // Connect rooms with corridors
    const corridors = this.connectRoomsBSP(bspTree, grid, genParams);

    // Post-processing
    const finalGrid = this.postProcess(grid);

    // Add BSP-specific features
    const features = this.identifyBSPFeatures(bspTree, rooms, corridors);

    this.logger.info('BSP tree generation completed', {
      rooms: rooms.length,
      corridors: corridors.length,
      treeDepth: this.calculateTreeDepth(bspTree)
    });

    return {
      grid: finalGrid,
      rooms,
      corridors,
      features,
      tree: bspTree,
      algorithm: 'bsp',
      parameters: genParams
    };
  }

  /**
   * Build BSP tree through recursive subdivision
   */
  buildBSPTree(node, params, depth = 0) {
    const nodeData = {
      ...node,
      depth,
      children: null,
      room: null,
      type: 'node'
    };

    // Check if we should stop splitting
    if (depth >= params.maxSplitDepth ||
        node.width < params.minSplitSize * 2 ||
        node.height < params.minSplitSize * 2) {
      return nodeData;
    }

    // Determine split direction
    const splitHorizontal = this.shouldSplitHorizontal(node, depth);

    // Calculate split position
    const splitPos = this.calculateSplitPosition(node, splitHorizontal, params);

    // Create child nodes
    if (splitHorizontal) {
      const leftHeight = Math.floor(splitPos * node.height);
      const rightHeight = node.height - leftHeight;

      if (leftHeight >= params.minSplitSize && rightHeight >= params.minSplitSize) {
        nodeData.children = [
          this.buildBSPTree({
            x: node.x,
            y: node.y,
            width: node.width,
            height: leftHeight
          }, params, depth + 1),

          this.buildBSPTree({
            x: node.x,
            y: node.y + leftHeight,
            width: node.width,
            height: rightHeight
          }, params, depth + 1)
        ];
        nodeData.split = { horizontal: true, position: splitPos };
      }
    } else {
      const leftWidth = Math.floor(splitPos * node.width);
      const rightWidth = node.width - leftWidth;

      if (leftWidth >= params.minSplitSize && rightWidth >= params.minSplitSize) {
        nodeData.children = [
          this.buildBSPTree({
            x: node.x,
            y: node.y,
            width: leftWidth,
            height: node.height
          }, params, depth + 1),

          this.buildBSPTree({
            x: node.x + leftWidth,
            y: node.y,
            width: rightWidth,
            height: node.height
          }, params, depth + 1)
        ];
        nodeData.split = { horizontal: false, position: splitPos };
      }
    }

    return nodeData;
  }

  /**
   * Determine if split should be horizontal
   */
  shouldSplitHorizontal(node, depth) {
    // Alternate splits, but with some randomness
    if (node.width > node.height * 1.5) {
      return false; // Split vertically
    } else if (node.height > node.width * 1.5) {
      return true; // Split horizontally
    } else {
      return Math.random() < 0.5;
    }
  }

  /**
   * Calculate split position
   */
  calculateSplitPosition(node, horizontal, params) {
    const ratio = params.splitRatio;
    let position = Math.random() * (ratio.max - ratio.min) + ratio.min;

    // Add asymmetry factor
    if (Math.random() < params.asymmetryFactor) {
      position = position < 0.5 ? 0.3 : 0.7;
    }

    return position;
  }

  /**
   * Generate rooms from BSP leaf nodes
   */
  generateRoomsFromBSP(bspTree, grid, params) {
    const leaves = this.findLeafNodes(bspTree);
    const rooms = [];

    for (const leaf of leaves) {
      const room = this.generateRoomInLeaf(leaf, grid, params);
      if (room) {
        rooms.push(room);
        leaf.room = room;
      }
    }

    return rooms;
  }

  /**
   * Find all leaf nodes in BSP tree
   */
  findLeafNodes(node, leaves = []) {
    if (!node.children) {
      leaves.push(node);
    } else {
      this.findLeafNodes(node.children[0], leaves);
      this.findLeafNodes(node.children[1], leaves);
    }
    return leaves;
  }

  /**
   * Generate room within a BSP leaf
   */
  generateRoomInLeaf(leaf, grid, params) {
    // Calculate room size (with padding)
    const roomWidth = Math.min(
      Math.floor(Math.random() * (params.maxRoomSize - params.minRoomSize) + params.minRoomSize),
      leaf.width - params.roomPadding * 2
    );
    const roomHeight = Math.min(
      Math.floor(Math.random() * (params.maxRoomSize - params.minRoomSize) + params.minRoomSize),
      leaf.height - params.roomPadding * 2
    );

    // Skip if room is too small
    if (roomWidth < params.minRoomSize || roomHeight < params.minRoomSize) {
      return null;
    }

    // Calculate room position (with padding)
    const x = leaf.x + params.roomPadding + Math.floor(Math.random() * (leaf.width - roomWidth - params.roomPadding * 2));
    const y = leaf.y + params.roomPadding + Math.floor(Math.random() * (leaf.height - roomHeight - params.roomPadding * 2));

    // Determine room type based on position and size
    const roomType = this.determineRoomType(leaf, roomWidth, roomHeight);

    const room = this.createRoom(grid, x, y, roomWidth, roomHeight, roomType);
    room.leafId = leaf.depth + '_' + leaf.x + '_' + leaf.y;
    room.treeDepth = leaf.depth;

    return room;
  }

  /**
   * Determine room type based on characteristics
   */
  determineRoomType(leaf, width, height) {
    // Large rooms at deep levels could be boss rooms
    if (leaf.depth >= 6 && (width >= 12 || height >= 12)) {
      return Math.random() < 0.3 ? 'boss' : 'large';
    }

    // Entrance rooms at shallow levels
    if (leaf.depth <= 2) {
      return Math.random() < 0.5 ? 'entrance' : 'normal';
    }

    // Special rooms at medium depth
    if (leaf.depth >= 3 && leaf.depth <= 5) {
      const rand = Math.random();
      if (rand < 0.2) return 'treasure';
      if (rand < 0.3) return 'trap';
      if (rand < 0.4) return 'puzzle';
    }

    return 'normal';
  }

  /**
   * Connect rooms using BSP structure
   */
  connectRoomsBSP(bspTree, grid, params) {
    const corridors = [];

    // Connect rooms based on tree structure
    this.connectNodeChildren(bspTree, grid, corridors, params);

    return corridors;
  }

  /**
   * Recursively connect child nodes
   */
  connectNodeChildren(node, grid, corridors, params) {
    if (!node.children) return;

    const leftChild = node.children[0];
    const rightChild = node.children[1];

    // Find rooms in each child
    const leftRoom = this.findRoomInNode(leftChild);
    const rightRoom = this.findRoomInNode(rightChild);

    if (leftRoom && rightRoom) {
      // Create connection between rooms
      const connection = this.createBSPConnection(
        leftRoom, rightRoom, grid, params
      );
      corridors.push(connection);

      // Update room connections
      leftRoom.connections.push(rightRoom.id);
      rightRoom.connections.push(leftRoom.id);
    }

    // Recursively connect children
    this.connectNodeChildren(leftChild, grid, corridors, params);
    this.connectNodeChildren(rightChild, grid, corridors, params);
  }

  /**
   * Find a room in a node (or its children)
   */
  findRoomInNode(node) {
    if (node.room) return node.room;

    if (node.children) {
      const leftRoom = this.findRoomInNode(node.children[0]);
      if (leftRoom) return leftRoom;

      const rightRoom = this.findRoomInNode(node.children[1]);
      if (rightRoom) return rightRoom;
    }

    return null;
  }

  /**
   * Create connection between two rooms
   */
  createBSPConnection(room1, room2, grid, params) {
    if (params.connectionType === 'direct') {
      // Direct corridor between room centers
      return this.createCorridor(
        grid,
        room1.centerX, room1.centerY,
        room2.centerX, room2.centerY,
        'bsp-corridor'
      );
    } else {
      // L-shaped corridor with room edge connections
      const edge1 = this.getRandomRoomEdge(room1);
      const edge2 = this.getRandomRoomEdge(room2);

      return this.createLShapedCorridor(
        grid, edge1, edge2, params.corridorWidth
      );
    }
  }

  /**
   * Get random edge point on room
   */
  getRandomRoomEdge(room) {
    const edges = [];

    // Top edge
    for (let x = room.x + 1; x < room.x + room.width - 1; x++) {
      edges.push({ x, y: room.y });
    }

    // Bottom edge
    for (let x = room.x + 1; x < room.x + room.width - 1; x++) {
      edges.push({ x, y: room.y + room.height - 1 });
    }

    // Left edge
    for (let y = room.y + 1; y < room.y + room.height - 1; y++) {
      edges.push({ x: room.x, y });
    }

    // Right edge
    for (let y = room.y + 1; y < room.y + room.height - 1; y++) {
      edges.push({ x: room.x + room.width - 1, y });
    }

    return edges[Math.floor(Math.random() * edges.length)];
  }

  /**
   * Create L-shaped corridor
   */
  createLShapedCorridor(grid, start, end, width) {
    const corridor = {
      id: MathUtils.generateId(),
      type: 'l-corridor',
      start,
      end,
      width,
      path: []
    };

    // Choose turn point (middle or random)
    const turnPoint = {
      x: Math.random() < 0.5 ? start.x : end.x,
      y: Math.random() < 0.5 ? start.y : end.y
    };

    // Create corridor segments
    this.createCorridorSegment(grid, start, turnPoint, width);
    this.createCorridorSegment(grid, turnPoint, end, width);

    // Record path
    corridor.path = [
      ...this.getSegmentPath(start, turnPoint),
      ...this.getSegmentPath(turnPoint, end)
    ];

    return corridor;
  }

  /**
   * Create corridor segment
   */
  createCorridorSegment(grid, start, end, width) {
    const halfWidth = Math.floor(width / 2);

    // Determine if horizontal or vertical
    const horizontal = start.y === end.y;

    if (horizontal) {
      const y = start.y;
      const x1 = Math.min(start.x, end.x);
      const x2 = Math.max(start.x, end.x);

      for (let x = x1; x <= x2; x++) {
        for (let dy = -halfWidth; dy <= halfWidth; dy++) {
          const gridY = y + dy;
          const gridX = x;

          if (this.isInBounds(gridX, gridY, grid[0].length, grid.length)) {
            grid[gridY][gridX] = 'floor';
          }
        }
      }
    } else {
      const x = start.x;
      const y1 = Math.min(start.y, end.y);
      const y2 = Math.max(start.y, end.y);

      for (let y = y1; y <= y2; y++) {
        for (let dx = -halfWidth; dx <= halfWidth; dx++) {
          const gridX = x + dx;
          const gridY = y;

          if (this.isInBounds(gridX, gridY, grid[0].length, grid.length)) {
            grid[gridY][gridX] = 'floor';
          }
        }
      }
    }
  }

  /**
   * Get path for corridor segment
   */
  getSegmentPath(start, end) {
    const path = [];
    const horizontal = start.y === end.y;

    if (horizontal) {
      const y = start.y;
      const x1 = Math.min(start.x, end.x);
      const x2 = Math.max(start.x, end.x);

      for (let x = x1; x <= x2; x++) {
        path.push({ x, y });
      }
    } else {
      const x = start.x;
      const y1 = Math.min(start.y, end.y);
      const y2 = Math.max(start.y, end.y);

      for (let y = y1; y <= y2; y++) {
        path.push({ x, y });
      }
    }

    return path;
  }

  /**
   * Identify BSP-specific features
   */
  identifyBSPFeatures(bspTree, rooms, corridors) {
    const features = {
      hierarchicalLayout: true,
      naturalProgression: this.calculateProgression(rooms),
      chokePoints: this.findChokePoints(corridors),
      deadEnds: this.findDeadEnds(rooms),
      hubRooms: this.findHubRooms(rooms),
      criticalPath: this.calculateCriticalPath(bspTree, rooms)
    };

    return features;
  }

  /**
   * Calculate natural progression through dungeon
   */
  calculateProgression(rooms) {
    const progression = rooms
      .filter(room => room.treeDepth !== undefined)
      .sort((a, b) => a.treeDepth - b.treeDepth)
      .map(room => ({
        roomId: room.id,
        depth: room.treeDepth,
        type: room.type
      }));

    return progression;
  }

  /**
   * Find choke points in corridors
   */
  findChokePoints(corridors) {
    return corridors
      .filter(corridor => corridor.type === 'l-corridor' && corridor.width <= 2)
      .map(corridor => ({
        location: corridor.path[Math.floor(corridor.path.length / 2)],
        width: corridor.width,
        type: 'choke-point'
      }));
  }

  /**
   * Find dead end rooms
   */
  findDeadEnds(rooms) {
    return rooms
      .filter(room => room.connections.length === 1)
      .map(room => ({
        ...room,
        type: 'dead-end'
      }));
  }

  /**
   * Find hub rooms (rooms with many connections)
  */
  findHubRooms(rooms) {
    const maxConnections = Math.max(...rooms.map(r => r.connections.length));
    const threshold = Math.max(2, Math.floor(maxConnections * 0.7));

    return rooms
      .filter(room => room.connections.length >= threshold)
      .map(room => ({
        ...room,
        type: 'hub',
        connectionCount: room.connections.length
      }));
  }

  /**
   * Calculate critical path through dungeon
   */
  calculateCriticalPath(bspTree, rooms) {
    const deepestRooms = rooms
      .filter(room => room.treeDepth !== undefined)
      .sort((a, b) => b.treeDepth - a.treeDepth)
      .slice(0, 3);

    return deepestRooms.map(room => ({
      roomId: room.id,
      depth: room.treeDepth,
      importance: room.type === 'boss' ? 'critical' : 'important'
    }));
  }

  /**
   * Calculate tree depth
   */
  calculateTreeDepth(node, depth = 0) {
    if (!node.children) return depth;

    const leftDepth = this.calculateTreeDepth(node.children[0], depth + 1);
    const rightDepth = this.calculateTreeDepth(node.children[1], depth + 1);

    return Math.max(leftDepth, rightDepth);
  }
}

module.exports = BSPTree;