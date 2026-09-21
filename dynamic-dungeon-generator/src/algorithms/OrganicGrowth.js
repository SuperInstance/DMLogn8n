/**
 * Organic Growth Dungeon Generation Algorithm
 * Creates natural, flowing dungeons that grow like organic structures
 */

const BaseAlgorithm = require('./BaseAlgorithm');
const MathUtils = require('../utils/MathUtils');
const { noise2D } = require('simplex-noise');

class OrganicGrowth extends BaseAlgorithm {
  constructor(config, logger) {
    super(config, logger);

    // Default parameters for organic growth
    this.defaultParams = {
      seedPoints: { min: 3, max: 8 },
      growthSteps: 150,
      growthRadius: { min: 1, max: 3 },
      branchingProbability: 0.15,
      deathProbability: 0.05,
      flowDirection: { x: 0, y: 0 }, // Bias for directional growth
      noiseScale: 0.1,
      noiseInfluence: 0.3,
      smoothingPasses: 3,
      cavityFormation: 0.2,
      tunnelWidth: { min: 1, max: 3 },
      convergencePoints: { min: 1, max: 3 },
      organicNoise: 'simplex', // 'simplex' or 'perlin'
      growthPattern: 'expanding' // 'expanding', 'flowing', 'branching'
    };
  }

  /**
   * Generate dungeon using organic growth
   */
  async generate(params) {
    const {
      width = 80,
      height = 80,
      seed = Math.random(),
      themeConfig,
      ...options
    } = params;

    this.logger.info('Starting organic growth generation', { width, height });

    // Merge with default parameters
    const genParams = { ...this.defaultParams, ...options };

    // Set seed
    MathUtils.setSeed(seed);

    // Initialize grid
    const grid = this.initializeGrid(width, height);

    // Initialize noise generator
    const noiseGen = this.initializeNoise(seed, genParams.organicNoise);

    // Generate seed points
    const seedPoints = this.generateSeedPoints(grid, genParams);

    // Grow organic structure
    const growthData = this.growOrganicStructure(grid, seedPoints, genParams, noiseGen);

    // Create convergences and connections
    this.createConvergences(grid, growthData, genParams);

    // Form cavities and chambers
    this.formCavities(grid, growthData, genParams);

    // Smooth and refine
    const smoothedGrid = this.smoothOrganicStructure(grid, genParams);

    // Identify features
    const features = this.identifyOrganicFeatures(smoothedGrid, growthData, genParams);

    // Extract rooms and corridors
    const { rooms, corridors } = this.extractStructures(smoothedGrid, features);

    this.logger.info('Organic growth generation completed', {
      seedPoints: seedPoints.length,
      rooms: rooms.length,
      corridors: corridors.length,
      growthSteps: growthData.steps
    });

    return {
      grid: smoothedGrid,
      rooms,
      corridors,
      features,
      growthData,
      algorithm: 'organic',
      parameters: genParams
    };
  }

  /**
   * Initialize noise generator
   */
  initializeNoise(seed, type) {
    if (type === 'simplex') {
      return (x, y) => noise2D(x + seed, y + seed);
    } else {
      // Fallback to simple noise
      return (x, y) => {
        const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
        return n - Math.floor(n);
      };
    }
  }

  /**
   * Generate initial seed points for growth
   */
  generateSeedPoints(grid, params) {
    const seedCount = Math.floor(
      Math.random() * (params.seedPoints.max - params.seedPoints.min + 1) +
      params.seedPoints.min
    );

    const seeds = [];
    const margin = 10;

    // Distribute seeds based on growth pattern
    switch (params.growthPattern) {
      case 'expanding':
        return this.generateExpandingSeeds(grid, seedCount, margin);
      case 'flowing':
        return this.generateFlowingSeeds(grid, seedCount, margin, params.flowDirection);
      case 'branching':
        return this.generateBranchingSeeds(grid, seedCount, margin);
      default:
        return this.generateRandomSeeds(grid, seedCount, margin);
    }
  }

  /**
   * Generate expanding seeds (center and edges)
   */
  generateExpandingSeeds(grid, count, margin) {
    const seeds = [];
    const width = grid[0].length;
    const height = grid.length;

    // Add center seed
    seeds.push({
      x: Math.floor(width / 2),
      y: Math.floor(height / 2),
      energy: 100,
      type: 'primary'
    });

    // Add edge seeds
    const remainingSeeds = count - 1;
    for (let i = 0; i < remainingSeeds; i++) {
      const edge = Math.floor(Math.random() * 4);
      let x, y;

      switch (edge) {
        case 0: // Top
          x = Math.floor(Math.random() * (width - 2 * margin)) + margin;
          y = margin;
          break;
        case 1: // Right
          x = width - margin;
          y = Math.floor(Math.random() * (height - 2 * margin)) + margin;
          break;
        case 2: // Bottom
          x = Math.floor(Math.random() * (width - 2 * margin)) + margin;
          y = height - margin;
          break;
        case 3: // Left
          x = margin;
          y = Math.floor(Math.random() * (height - 2 * margin)) + margin;
          break;
      }

      seeds.push({
        x, y,
        energy: 50 + Math.random() * 50,
        type: 'secondary'
      });
    }

    return seeds;
  }

  /**
   * Generate flowing seeds (with directional bias)
   */
  generateFlowingSeeds(grid, count, margin, flowDirection) {
    const seeds = [];
    const width = grid[0].length;
    const height = grid.length;

    for (let i = 0; i < count; i++) {
      let x, y;

      if (Math.abs(flowDirection.x) > Math.abs(flowDirection.y)) {
        // Horizontal flow
        if (flowDirection.x > 0) {
          x = margin;
        } else {
          x = width - margin;
        }
        y = Math.floor(Math.random() * (height - 2 * margin)) + margin;
      } else {
        // Vertical flow
        if (flowDirection.y > 0) {
          y = margin;
        } else {
          y = height - margin;
        }
        x = Math.floor(Math.random() * (width - 2 * margin)) + margin;
      }

      seeds.push({
        x, y,
        energy: 60 + Math.random() * 40,
        type: 'flow',
        direction: { ...flowDirection }
      });
    }

    return seeds;
  }

  /**
   * Generate branching seeds (hierarchical)
   */
  generateBranchingSeeds(grid, count, margin) {
    const seeds = [];
    const width = grid[0].length;
    const height = grid.length;

    // Primary trunk
    seeds.push({
      x: Math.floor(width / 2),
      y: Math.floor(height / 2),
      energy: 100,
      type: 'trunk',
      generation: 0
    });

    // Branch points
    const branches = Math.floor(count * 0.6);
    for (let i = 0; i < branches; i++) {
      const angle = (Math.PI * 2 * i) / branches + Math.random() * 0.5;
      const distance = 10 + Math.random() * 15;

      seeds.push({
        x: Math.floor(width / 2 + distance * Math.cos(angle)),
        y: Math.floor(height / 2 + distance * Math.sin(angle)),
        energy: 40 + Math.random() * 30,
        type: 'branch',
        generation: 1
      });
    }

    // Leaf nodes
    const leaves = count - seeds.length;
    for (let i = 0; i < leaves; i++) {
      const parentSeed = seeds[Math.floor(Math.random() * seeds.length)];
      const angle = Math.random() * Math.PI * 2;
      const distance = 5 + Math.random() * 8;

      const x = parentSeed.x + Math.floor(distance * Math.cos(angle));
      const y = parentSeed.y + Math.floor(distance * Math.sin(angle));

      if (x > margin && x < width - margin && y > margin && y < height - margin) {
        seeds.push({
          x, y,
          energy: 20 + Math.random() * 20,
          type: 'leaf',
          generation: 2
        });
      }
    }

    return seeds;
  }

  /**
   * Generate random seeds
   */
  generateRandomSeeds(grid, count, margin) {
    const seeds = [];
    const width = grid[0].length;
    const height = grid.length;

    for (let i = 0; i < count; i++) {
      seeds.push({
        x: Math.floor(Math.random() * (width - 2 * margin)) + margin,
        y: Math.floor(Math.random() * (height - 2 * margin)) + margin,
        energy: 50 + Math.random() * 50,
        type: 'random'
      });
    }

    return seeds;
  }

  /**
   * Grow organic structure from seeds
   */
  growOrganicStructure(grid, seedPoints, params, noiseGen) {
    const growthPoints = [...seedPoints];
    const growthHistory = [];
    let steps = 0;

    // Clear grid and place initial seeds
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        grid[y][x] = 'wall';
      }
    }

    // Mark seed positions as floor
    for (const seed of growthPoints) {
      if (this.isInBounds(seed.x, seed.y, grid[0].length, grid.length)) {
        grid[seed.y][seed.x] = 'floor';
      }
    }

    // Growth simulation
    for (let step = 0; step < params.growthSteps && growthPoints.length > 0; step++) {
      const newGrowthPoints = [];

      for (const point of growthPoints) {
        if (point.energy <= 0) continue;

        // Calculate growth influenced by noise
        const noiseValue = noiseGen(
          point.x * params.noiseScale,
          point.y * params.noiseScale
        );

        // Determine growth direction and intensity
        const growthInfluence = this.calculateGrowthInfluence(point, noiseValue, params);

        // Grow in multiple directions
        const growthDirections = this.getGrowthDirections(point, growthInfluence, params);

        for (const direction of growthDirections) {
          const newX = point.x + direction.x;
          const newY = point.y + direction.y;

          if (this.canGrow(grid, newX, newY, params)) {
            grid[newY][newX] = 'floor';

            const energyTransfer = point.energy * 0.7;
            newGrowthPoints.push({
              x: newX,
              y: newY,
              energy: energyTransfer,
              type: point.type,
              generation: (point.generation || 0) + 1,
              parent: point
            });

            point.energy *= 0.8; // Energy depletion
          }
        }

        // Branching
        if (Math.random() < params.branchingProbability && point.energy > 30) {
          const branchDirections = this.getBranchDirections(point, params);
          for (const direction of branchDirections) {
            const branchX = point.x + direction.x;
            const branchY = point.y + direction.y;

            if (this.canGrow(grid, branchX, branchY, params)) {
              grid[branchY][branchX] = 'floor';

              newGrowthPoints.push({
                x: branchX,
                y: branchY,
                energy: point.energy * 0.5,
                type: 'branch',
                generation: (point.generation || 0) + 1,
                parent: point
              });
            }
          }
        }

        // Death probability
        if (Math.random() < params.deathProbability) {
          point.energy = 0;
        }
      }

      // Filter out dead points and merge with new growth
      growthPoints.push(...newGrowthPoints.filter(p => p.energy > 5));
      steps++;

      // Record growth state periodically
      if (step % 20 === 0) {
        growthHistory.push({
          step,
          activePoints: growthPoints.length,
          totalEnergy: growthPoints.reduce((sum, p) => sum + p.energy, 0)
        });
      }
    }

    return {
      steps,
      finalPoints: growthPoints,
      history: growthHistory,
      seedPoints
    };
  }

  /**
   * Calculate growth influence based on noise and parameters
   */
  calculateGrowthInfluence(point, noiseValue, params) {
    const influence = {
      intensity: 0.5 + noiseValue * params.noiseInfluence,
      directionBias: { x: 0, y: 0 }
    };

    // Add flow direction bias
    influence.directionBias.x += params.flowDirection.x * 0.3;
    influence.directionBias.y += params.flowDirection.y * 0.3;

    // Add type-specific behaviors
    switch (point.type) {
      case 'flow':
        influence.intensity *= 1.2;
        break;
      case 'branch':
        influence.intensity *= 0.8;
        break;
      case 'leaf':
        influence.intensity *= 0.6;
        break;
    }

    return influence;
  }

  /**
   * Get growth directions for a point
   */
  getGrowthDirections(point, influence, params) {
    const directions = [];
    const baseRadius = params.growthRadius.min +
                      Math.random() * (params.growthRadius.max - params.growthRadius.min);

    // Cardinal directions with bias
    const cardinalDirections = [
      { x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }
    ];

    for (const dir of cardinalDirections) {
      const adjustedDir = {
        x: dir.x + influence.directionBias.x,
        y: dir.y + influence.directionBias.y
      };

      if (Math.random() < influence.intensity) {
        directions.push({
          x: Math.sign(adjustedDir.x) * Math.ceil(Math.abs(adjustedDir.x) * baseRadius),
          y: Math.sign(adjustedDir.y) * Math.ceil(Math.abs(adjustedDir.y) * baseRadius)
        });
      }
    }

    // Add diagonal growth occasionally
    if (Math.random() < 0.3) {
      const diagonalDirs = [
        { x: 1, y: 1 }, { x: -1, y: 1 }, { x: 1, y: -1 }, { x: -1, y: -1 }
      ];
      const dir = diagonalDirs[Math.floor(Math.random() * diagonalDirs.length)];
      directions.push({
        x: dir.x * Math.ceil(baseRadius * 0.7),
        y: dir.y * Math.ceil(baseRadius * 0.7)
      });
    }

    return directions.slice(0, 3); // Limit directions
  }

  /**
   * Get branch directions
   */
  getBranchDirections(point, params) {
    const angle = Math.random() * Math.PI * 2;
    const distance = params.growthRadius.max;

    return [{
      x: Math.round(Math.cos(angle) * distance),
      y: Math.round(Math.sin(angle) * distance)
    }];
  }

  /**
   * Check if growth can occur at position
   */
  canGrow(grid, x, y, params) {
    if (!this.isInBounds(x, y, grid[0].length, grid.length)) {
      return false;
    }

    if (grid[y][x] !== 'wall') {
      return false; // Already grown
    }

    // Check for growth density (avoid overcrowding)
    let floorCount = 0;
    for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
      const nx = x + dx;
      const ny = y + dy;

      if (this.isInBounds(nx, ny, grid[0].length, grid.length) &&
          grid[ny][nx] === 'floor') {
        floorCount++;
      }
    }

    return floorCount <= 2; // Limit density
  }

  /**
   * Create convergence points where growth meets
   */
  createConvergences(grid, growthData, params) {
    const convergenceCount = Math.floor(
      Math.random() * (params.convergencePoints.max - params.convergencePoints.min + 1) +
      params.convergencePoints.min
    );

    for (let i = 0; i < convergenceCount; i++) {
      // Find areas with high growth density
      const hotspots = this.findGrowthHotspots(grid, growthData);

      if (hotspots.length > 0) {
        const hotspot = hotspots[Math.floor(Math.random() * hotspots.length)];
        this.createConvergenceCavity(grid, hotspot.x, hotspot.y, params);
      }
    }
  }

  /**
   * Find areas with high growth density
   */
  findGrowthHotspots(grid, growthData) {
    const hotspots = [];
    const width = grid[0].length;
    const height = grid.length;

    for (let y = 5; y < height - 5; y += 3) {
      for (let x = 5; x < width - 5; x += 3) {
        let density = 0;

        for (let dy = -2; dy <= 2; dy++) {
          for (let dx = -2; dx <= 2; dx++) {
            if (grid[y + dy][x + dx] === 'floor') {
              density++;
            }
          }
        }

        if (density >= 12) { // High density threshold
          hotspots.push({ x, y, density });
        }
      }
    }

    return hotspots.sort((a, b) => b.density - a.density).slice(0, 5);
  }

  /**
   * Create convergence cavity
   */
  createConvergenceCavity(grid, x, y, params) {
    const radius = Math.floor(Math.random() * 3) + 2;

    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance <= radius) {
          const gridX = x + dx;
          const gridY = y + dy;

          if (this.isInBounds(gridX, gridY, grid[0].length, grid.length)) {
            grid[gridY][gridX] = 'floor';
          }
        }
      }
    }
  }

  /**
   * Form natural cavities
   */
  formCavities(grid, growthData, params) {
    if (Math.random() > params.cavityFormation) return;

    const cavities = Math.floor(Math.random() * 3) + 1;

    for (let i = 0; i < cavities; i++) {
      const x = Math.floor(Math.random() * (grid[0].length - 10)) + 5;
      const y = Math.floor(Math.random() * (grid.length - 10)) + 5;
      const radius = Math.floor(Math.random() * 4) + 2;

      this.createConvergenceCavity(grid, x, y, params);
    }
  }

  /**
   * Smooth organic structure
   */
  smoothOrganicStructure(grid, params) {
    let smoothedGrid = grid.map(row => [...row]);

    for (let pass = 0; pass < params.smoothingPasses; pass++) {
      const newGrid = smoothedGrid.map(row => [...row]);

      for (let y = 1; y < grid.length - 1; y++) {
        for (let x = 1; x < grid[0].length - 1; x++) {
          const neighbors = this.getNeighbors(x, y, smoothedGrid, false);
          const floorCount = neighbors.filter(n => n.value === 'floor').length;

          // Smoothing rules for organic shapes
          if (smoothedGrid[y][x] === 'wall' && floorCount >= 5) {
            newGrid[y][x] = 'floor';
          } else if (smoothedGrid[y][x] === 'floor' && floorCount <= 1) {
            newGrid[y][x] = 'wall';
          }
        }
      }

      smoothedGrid = newGrid;
    }

    return smoothedGrid;
  }

  /**
   * Identify organic features
   */
  identifyOrganicFeatures(grid, growthData, params) {
    return {
      growthPattern: params.growthPattern,
      seedPoints: growthData.seedPoints.length,
      growthSteps: growthData.steps,
      convergences: this.countConvergences(grid),
      tunnels: this.identifyTunnels(grid),
      cavities: this.identifyCavities(grid),
      branching: this.analyzeBranching(growthData),
      flowCharacteristics: this.analyzeFlow(grid, growthData)
    };
  }

  /**
   * Count convergence points
   */
  countConvergences(grid) {
    let count = 0;

    for (let y = 2; y < grid.length - 2; y++) {
      for (let x = 2; x < grid[0].length - 2; x++) {
        if (grid[y][x] === 'floor') {
          let connections = 0;
          for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
            if (grid[y + dy][x + dx] === 'floor') connections++;
          }
          if (connections >= 3) count++;
        }
      }
    }

    return count;
  }

  /**
   * Identify tunnel structures
   */
  identifyTunnels(grid) {
    const tunnels = [];

    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (grid[y][x] === 'floor') {
          const crossSection = this.getCrossSection(grid, x, y);
          if (crossSection <= 2) {
            tunnels.push({ x, y, width: crossSection });
          }
        }
      }
    }

    return tunnels;
  }

  /**
   * Identify cavity areas
   */
  identifyCavities(grid) {
    const cavities = [];
    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === 'floor' && !visited[y][x]) {
          const region = this.floodFill(grid, x, y, visited);
          if (region.length > 10) {
            const bounds = this.calculateBounds(region);
            cavities.push({
              ...bounds,
              area: region.length,
              type: region.length > 30 ? 'large-cavity' : 'small-cavity'
            });
          }
        }
      }
    }

    return cavities;
  }

  /**
   * Analyze branching characteristics
   */
  analyzeBranching(growthData) {
    const generationCounts = {};
    growthData.finalPoints.forEach(point => {
      const gen = point.generation || 0;
      generationCounts[gen] = (generationCounts[gen] || 0) + 1;
    });

    return {
      maxGeneration: Math.max(...Object.keys(generationCounts).map(Number)),
      generationDistribution: generationCounts,
      averageBranchingFactor: Object.values(generationCounts).reduce((a, b) => a + b, 0) / Object.keys(generationCounts).length
    };
  }

  /**
   * Analyze flow characteristics
   */
  analyzeFlow(grid, growthData) {
    const flowSeeds = growthData.seedPoints.filter(s => s.type === 'flow');
    return {
      hasFlow: flowSeeds.length > 0,
      flowDirection: flowSeeds.length > 0 ? flowSeeds[0].direction : { x: 0, y: 0 },
      flowStrength: flowSeeds.reduce((sum, s) => sum + s.energy, 0)
    };
  }

  /**
   * Extract rooms and corridors from organic structure
   */
  extractStructures(grid, features) {
    const rooms = [];
    const corridors = [];

    // Extract cavities as rooms
    for (const cavity of features.cavities) {
      rooms.push({
        id: MathUtils.generateId(),
        x: cavity.x,
        y: cavity.y,
        width: cavity.width,
        height: cavity.height,
        type: cavity.type === 'large-cavity' ? 'chamber' : 'room',
        centerX: cavity.centerX,
        centerY: cavity.centerY,
        connections: [],
        organic: true
      });
    }

    // Extract tunnels as corridors
    for (const tunnel of features.tunnels) {
      corridors.push({
        id: MathUtils.generateId(),
        type: 'tunnel',
        start: { x: tunnel.x, y: tunnel.y },
        end: { x: tunnel.x + 1, y: tunnel.y + 1 },
        width: tunnel.width,
        organic: true
      });
    }

    return { rooms, corridors };
  }
}

module.exports = OrganicGrowth;