/**
 * Cellular Automata Dungeon Generation Algorithm
 * Creates organic, cave-like dungeons using cellular automata rules
 */

const BaseAlgorithm = require('./BaseAlgorithm');
const MathUtils = require('../utils/MathUtils');

class CellularAutomata extends BaseAlgorithm {
  constructor(config, logger) {
    super(config, logger);

    // Default parameters for cellular automata
    this.defaultParams = {
      initialFillProbability: 0.45,
      birthLimit: 4,
      deathLimit: 3,
      iterations: 6,
      smoothingPasses: 2,
      minRegionSize: 50,
      maxRegionSize: 1000
    };
  }

  /**
   * Generate dungeon using cellular automata
   */
  async generate(params) {
    const {
      width = 80,
      height = 80,
      seed = Math.random(),
      themeConfig,
      ...options
    } = params;

    this.logger.info('Starting cellular automata generation', { width, height });

    // Merge with default parameters
    const genParams = { ...this.defaultParams, ...options };

    // Set seed
    MathUtils.setSeed(seed);

    // Initialize grid
    let grid = this.initializeGrid(width, height);

    // Random initial fill
    grid = this.randomFill(grid, genParams.initialFillProbability);

    // Run cellular automata iterations
    for (let i = 0; i < genParams.iterations; i++) {
      grid = this.applyCellularRules(grid, genParams.birthLimit, genParams.deathLimit);
    }

    // Smooth the result
    for (let i = 0; i < genParams.smoothingPasses; i++) {
      grid = this.smoothGrid(grid);
    }

    // Remove small regions and identify main cavern
    const processedGrid = this.processRegions(grid, genParams.minRegionSize);

    // Identify features
    const features = this.identifyFeatures(processedGrid);

    // Ensure connectivity
    const connectedGrid = this.ensureConnectivity(processedGrid, features);

    // Post-processing
    const finalGrid = this.postProcess(connectedGrid);

    // Extract rooms (in cellular automata, these are cavern areas)
    const rooms = this.extractCaverns(finalGrid);

    // Create corridors (natural passages between caverns)
    const corridors = this.createNaturalPassages(finalGrid, rooms);

    this.logger.info('Cellular automata generation completed', {
      rooms: rooms.length,
      corridors: corridors.length
    });

    return {
      grid: finalGrid,
      rooms,
      corridors,
      features,
      algorithm: 'cellular',
      parameters: genParams
    };
  }

  /**
   * Randomly fill grid based on probability
   */
  randomFill(grid, fillProbability) {
    const newGrid = grid.map(row => [...row]);

    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (Math.random() < fillProbability) {
          newGrid[y][x] = 'wall';
        } else {
          newGrid[y][x] = 'floor';
        }
      }
    }

    return newGrid;
  }

  /**
   * Apply cellular automata rules
   */
  applyCellularRules(grid, birthLimit, deathLimit) {
    const newGrid = grid.map(row => [...row]);

    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        const wallCount = this.countWallsAround(x, y, grid);

        if (grid[y][x] === 'wall') {
          // Wall stays wall if it has enough wall neighbors
          newGrid[y][x] = wallCount >= deathLimit ? 'wall' : 'floor';
        } else {
          // Floor becomes wall if surrounded by walls
          newGrid[y][x] = wallCount > birthLimit ? 'wall' : 'floor';
        }
      }
    }

    return newGrid;
  }

  /**
   * Smooth grid to remove small artifacts
   */
  smoothGrid(grid) {
    const newGrid = grid.map(row => [...row]);

    for (let y = 2; y < grid.length - 2; y++) {
      for (let x = 2; x < grid[0].length - 2; x++) {
        let wallCount = 0;
        let totalCount = 0;

        // Check 3x3 neighborhood
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            totalCount++;
            if (grid[y + dy][x + dx] === 'wall') {
              wallCount++;
            }
          }
        }

        // Apply smoothing rule
        if (wallCount >= 5) {
          newGrid[y][x] = 'wall';
        } else if (wallCount <= 3) {
          newGrid[y][x] = 'floor';
        }
      }
    }

    return newGrid;
  }

  /**
   * Process regions to remove small disconnected areas
   */
  processRegions(grid, minRegionSize) {
    const width = grid[0].length;
    const height = grid.length;
    const visited = Array(height).fill().map(() => Array(width).fill(false));
    const regions = [];

    // Find all connected floor regions
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (grid[y][x] === 'floor' && !visited[y][x]) {
          const region = this.floodFill(grid, x, y, visited);
          regions.push(region);
        }
      }
    }

    // Keep only the largest region(s)
    regions.sort((a, b) => b.length - a.length);

    const newGrid = this.initializeGrid(width, height);

    // Keep the largest region and any regions above minimum size
    const keptRegions = regions.filter((region, index) =>
      index === 0 || region.length >= minRegionSize
    );

    for (const region of keptRegions) {
      for (const { x, y } of region) {
        newGrid[y][x] = 'floor';
      }
    }

    return newGrid;
  }

  /**
   * Flood fill to find connected regions
   */
  floodFill(grid, startX, startY, visited) {
    const region = [];
    const queue = [{ x: startX, y: startY }];
    const width = grid[0].length;
    const height = grid.length;

    while (queue.length > 0) {
      const { x, y } = queue.shift();

      if (x < 0 || x >= width || y < 0 || y >= height) continue;
      if (visited[y][x] || grid[y][x] !== 'floor') continue;

      visited[y][x] = true;
      region.push({ x, y });

      // Add neighbors
      queue.push({ x: x + 1, y });
      queue.push({ x: x - 1, y });
      queue.push({ x, y: y + 1 });
      queue.push({ x, y: y - 1 });
    }

    return region;
  }

  /**
   * Identify natural features in the cavern
   */
  identifyFeatures(grid) {
    const features = {
      lakes: [],
      pillars: [],
      chokePoints: [],
      openAreas: []
    };

    const width = grid[0].length;
    const height = grid.length;

    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        if (grid[y][x] === 'wall') {
          const floorNeighbors = this.getNeighbors(x, y, grid, false)
            .filter(n => n.value === 'floor').length;

          // Identify pillars (isolated walls)
          if (floorNeighbors === 4) {
            features.pillars.push({ x, y, type: 'pillar' });
          }
        }
      }
    }

    // Find choke points (narrow passages)
    for (let y = 2; y < height - 2; y++) {
      for (let x = 2; x < width - 2; x++) {
        if (grid[y][x] === 'floor') {
          const crossSection = this.getCrossSection(grid, x, y);
          if (crossSection <= 2) {
            features.chokePoints.push({ x, y, width: crossSection });
          }
        }
      }
    }

    return features;
  }

  /**
   * Get cross-section width at a point
   */
  getCrossSection(grid, x, y) {
    let width = 1;

    // Count horizontal floor cells
    let leftX = x - 1;
    while (leftX >= 0 && grid[y][leftX] === 'floor') {
      width++;
      leftX--;
    }

    let rightX = x + 1;
    while (rightX < grid[0].length && grid[y][rightX] === 'floor') {
      width++;
      rightX++;
    }

    return width;
  }

  /**
   * Ensure connectivity between all floor areas
   */
  ensureConnectivity(grid, features) {
    const newGrid = grid.map(row => [...row]);
    const floorCells = this.findFloorCells(grid);

    if (floorCells.length === 0) return newGrid;

    // Find the main connected component
    const mainComponent = this.findLargestConnectedComponent(grid);
    const mainSet = new Set(mainComponent.map(p => `${p.x},${p.y}`));

    // Connect isolated floor cells to main component
    for (const cell of floorCells) {
      const key = `${cell.x},${cell.y}`;
      if (!mainSet.has(key)) {
        const closestMain = this.findClosestInSet(cell, mainSet);
        if (closestMain) {
          this.createTunnel(newGrid, cell, closestMain);
        }
      }
    }

    return newGrid;
  }

  /**
   * Find largest connected component of floor cells
   */
  findLargestConnectedComponent(grid) {
    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));
    let largestComponent = [];

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === 'floor' && !visited[y][x]) {
          const component = this.floodFill(grid, x, y, visited);
          if (component.length > largestComponent.length) {
            largestComponent = component;
          }
        }
      }
    }

    return largestComponent;
  }

  /**
   * Find closest point in a set
   */
  findClosestInSet(point, pointSet) {
    let closest = null;
    let minDistance = Infinity;

    for (const pointKey of pointSet) {
      const [x, y] = pointKey.split(',').map(Number);
      const distance = MathUtils.distance(point.x, point.y, x, y);

      if (distance < minDistance) {
        minDistance = distance;
        closest = { x, y };
      }
    }

    return closest;
  }

  /**
   * Create tunnel between two points
   */
  createTunnel(grid, start, end) {
    // Simple straight line tunnel
    const steps = Math.max(Math.abs(end.x - start.x), Math.abs(end.y - start.y));

    for (let i = 0; i <= steps; i++) {
      const t = steps === 0 ? 0 : i / steps;
      const x = Math.round(start.x + (end.x - start.x) * t);
      const y = Math.round(start.y + (end.y - start.y) * t);

      if (this.isInBounds(x, y, grid[0].length, grid.length)) {
        grid[y][x] = 'floor';
      }
    }
  }

  /**
   * Extract cavern areas as "rooms"
   */
  extractCaverns(grid) {
    const caverns = [];
    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === 'floor' && !visited[y][x]) {
          const cavern = this.floodFill(grid, x, y, visited);

          if (cavern.length > 20) { // Minimum size for a cavern
            const bounds = this.calculateBounds(cavern);

            caverns.push({
              id: MathUtils.generateId(),
              type: 'cavern',
              ...bounds,
              area: cavern.length,
              density: cavern.length / ((bounds.width + 1) * (bounds.height + 1)),
              cells: cavern
            });
          }
        }
      }
    }

    return caverns;
  }

  /**
   * Calculate bounds of a set of points
   */
  calculateBounds(points) {
    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);

    return {
      x: Math.min(...xs),
      y: Math.min(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
      centerX: Math.round((Math.min(...xs) + Math.max(...xs)) / 2),
      centerY: Math.round((Math.min(...ys) + Math.max(...ys)) / 2)
    };
  }

  /**
   * Create natural passages between caverns
   */
  createNaturalPassages(grid, caverns) {
    const passages = [];

    for (let i = 0; i < caverns.length - 1; i++) {
      for (let j = i + 1; j < caverns.length; j++) {
        const cavern1 = caverns[i];
        const cavern2 = caverns[j];

        // Create passage if caverns are close enough
        const distance = MathUtils.distance(
          cavern1.centerX, cavern1.centerY,
          cavern2.centerX, cavern2.centerY
        );

        if (distance < 20) { // Threshold for creating passages
          const passage = this.createCorridor(
            grid,
            cavern1.centerX, cavern1.centerY,
            cavern2.centerX, cavern2.centerY,
            'natural'
          );
          passages.push(passage);
        }
      }
    }

    return passages;
  }
}

module.exports = CellularAutomata;