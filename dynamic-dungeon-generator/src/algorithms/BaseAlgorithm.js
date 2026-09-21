/**
 * Base Algorithm Class
 * Provides common functionality for all dungeon generation algorithms
 */

const Grid = require('../utils/Grid');
const MathUtils = require('../utils/MathUtils');

class BaseAlgorithm {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
  }

  /**
   * Generate dungeon layout - to be implemented by subclasses
   */
  async generate(params) {
    throw new Error('generate method must be implemented by subclass');
  }

  /**
   * Initialize grid with walls
   */
  initializeGrid(width, height) {
    return Grid.create(width, height, 'wall');
  }

  /**
   * Check if position is within bounds
   */
  isInBounds(x, y, width, height) {
    return x >= 0 && x < width && y >= 0 && y < height;
  }

  /**
   * Get neighboring cells
   */
  getNeighbors(x, y, grid, diagonal = false) {
    const neighbors = [];
    const directions = diagonal
      ? [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
      : [[-1, 0], [1, 0], [0, -1], [0, 1]];

    for (const [dx, dy] of directions) {
      const nx = x + dx;
      const ny = y + dy;

      if (this.isInBounds(nx, ny, grid[0].length, grid.length)) {
        neighbors.push({ x: nx, y: ny, value: grid[ny][nx] });
      }
    }

    return neighbors;
  }

  /**
   * Count walls around position
   */
  countWallsAround(x, y, grid) {
    let count = 0;
    const neighbors = this.getNeighbors(x, y, grid, true);

    for (const neighbor of neighbors) {
      if (neighbor.value === 'wall') {
        count++;
      }
    }

    return count;
  }

  /**
   * Create room at specified position
   */
  createRoom(grid, x, y, width, height, roomType = 'normal') {
    const room = {
      id: MathUtils.generateId(),
      x, y, width, height,
      type: roomType,
      centerX: x + Math.floor(width / 2),
      centerY: y + Math.floor(height / 2),
      connections: [],
      features: []
    };

    // Carve out room
    for (let dy = 0; dy < height; dy++) {
      for (let dx = 0; dx < width; dx++) {
        const gridX = x + dx;
        const gridY = y + dy;

        if (this.isInBounds(gridX, gridY, grid[0].length, grid.length)) {
          // Make walls around room edges
          if (dx === 0 || dx === width - 1 || dy === 0 || dy === height - 1) {
            grid[gridY][gridX] = 'wall';
          } else {
            grid[gridY][gridX] = 'floor';
          }
        }
      }
    }

    return room;
  }

  /**
   * Create corridor between two points
   */
  createCorridor(grid, x1, y1, x2, y2, corridorType = 'normal') {
    const corridor = {
      id: MathUtils.generateId(),
      start: { x: x1, y: y1 },
      end: { x: x2, y: y2 },
      type: corridorType,
      path: []
    };

    // Simple L-shaped corridor
    const path = [];
    let currentX = x1;
    let currentY = y1;

    // Move horizontally first
    while (currentX !== x2) {
      path.push({ x: currentX, y: currentY });
      currentX += currentX < x2 ? 1 : -1;
    }

    // Then move vertically
    while (currentY !== y2) {
      path.push({ x: currentX, y: currentY });
      currentY += currentY < y2 ? 1 : -1;
    }

    path.push({ x: x2, y: y2 });

    // Carve out corridor
    for (const point of path) {
      if (this.isInBounds(point.x, point.y, grid[0].length, grid.length)) {
        grid[point.y][point.x] = 'floor';

        // Add walls around corridor
        for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
          const wallX = point.x + dx;
          const wallY = point.y + dy;

          if (this.isInBounds(wallX, wallY, grid[0].length, grid.length)) {
            if (grid[wallY][wallX] === 'wall') {
              // Keep as wall
            } else if (grid[wallY][wallX] === 'void') {
              grid[wallY][wallX] = 'wall';
            }
          }
        }
      }
    }

    corridor.path = path;
    return corridor;
  }

  /**
   * Find all floor cells
   */
  findFloorCells(grid) {
    const floors = [];
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === 'floor') {
          floors.push({ x, y });
        }
      }
    }
    return floors;
  }

  /**
   * Connect rooms with corridors
   */
  connectRooms(grid, rooms) {
    const corridors = [];
    const connected = new Set([rooms[0].id]);

    for (let i = 1; i < rooms.length; i++) {
      const room = rooms[i];

      // Find closest connected room
      let closestRoom = null;
      let minDistance = Infinity;

      for (const connectedRoomId of connected) {
        const connectedRoom = rooms.find(r => r.id === connectedRoomId);
        const distance = MathUtils.distance(
          room.centerX, room.centerY,
          connectedRoom.centerX, connectedRoom.centerY
        );

        if (distance < minDistance) {
          minDistance = distance;
          closestRoom = connectedRoom;
        }
      }

      if (closestRoom) {
        const corridor = this.createCorridor(
          grid,
          room.centerX, room.centerY,
          closestRoom.centerX, closestRoom.centerY
        );

        corridors.push(corridor);
        connected.add(room.id);

        // Update room connections
        room.connections.push(closestRoom.id);
        closestRoom.connections.push(room.id);
      }
    }

    return corridors;
  }

  /**
   * Validate generated dungeon
   */
  validate(grid, rooms, corridors) {
    // Check if all rooms are accessible
    const accessible = new Set();
    const queue = [rooms[0].centerX, rooms[0].centerY];
    const visited = new Set();

    while (queue.length > 0) {
      const x = queue.shift();
      const y = queue.shift();
      const key = `${x},${y}`;

      if (visited.has(key)) continue;
      visited.add(key);

      if (grid[y][x] === 'floor') {
        // Check if this is a room center
        const room = rooms.find(r => r.centerX === x && r.centerY === y);
        if (room) {
          accessible.add(room.id);
        }

        // Add neighbors
        for (const [dx, dy] of [[0, 1], [1, 0], [0, -1], [-1, 0]]) {
          const nx = x + dx;
          const ny = y + dy;

          if (this.isInBounds(nx, ny, grid[0].length, grid.length) &&
              grid[ny][nx] === 'floor') {
            queue.push(nx, ny);
          }
        }
      }
    }

    return accessible.size === rooms.length;
  }

  /**
   * Apply post-processing to clean up dungeon
   */
  postProcess(grid) {
    // Remove isolated wall sections
    // Fill small holes
    // Smooth corners

    const width = grid[0].length;
    const height = grid.length;
    const newGrid = Grid.copy(grid);

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        // Smooth corners
        if (grid[y][x] === 'wall') {
          const floorNeighbors = this.getNeighbors(x, y, grid, false)
            .filter(n => n.value === 'floor').length;

          if (floorNeighbors >= 3) {
            newGrid[y][x] = 'floor';
          }
        }
      }
    }

    return newGrid;
  }
}

module.exports = BaseAlgorithm;