/**
 * Grid Utilities
 * Helper functions for grid manipulation and analysis
 */

class Grid {
  /**
   * Create a new grid filled with specified value
   */
  static create(width, height, fillValue = 'wall') {
    const grid = [];
    for (let y = 0; y < height; y++) {
      const row = [];
      for (let x = 0; x < width; x++) {
        row.push(fillValue);
      }
      grid.push(row);
    }
    return grid;
  }

  /**
   * Create a copy of a grid
   */
  static copy(grid) {
    return grid.map(row => [...row]);
  }

  /**
   * Get grid dimensions
   */
  static getDimensions(grid) {
    return {
      width: grid[0].length,
      height: grid.length
    };
  }

  /**
   * Check if position is valid
   */
  static isValid(grid, x, y) {
    return x >= 0 && x < grid[0].length && y >= 0 && y < grid.length;
  }

  /**
   * Get value at position
   */
  static get(grid, x, y) {
    if (!this.isValid(grid, x, y)) return null;
    return grid[y][x];
  }

  /**
   * Set value at position
   */
  static set(grid, x, y, value) {
    if (this.isValid(grid, x, y)) {
      grid[y][x] = value;
      return true;
    }
    return false;
  }

  /**
   * Check if position is a specific value
   */
  static is(grid, x, y, value) {
    return this.get(grid, x, y) === value;
  }

  /**
   * Find all cells with specific value
   */
  static findCells(grid, value) {
    const cells = [];
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === value) {
          cells.push({ x, y });
        }
      }
    }
    return cells;
  }

  /**
   * Count cells with specific value
   */
  static count(grid, value) {
    let count = 0;
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === value) count++;
      }
    }
    return count;
  }

  /**
   * Replace all instances of a value
   */
  static replace(grid, oldValue, newValue) {
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === oldValue) {
          grid[y][x] = newValue;
        }
      }
    }
  }

  /**
   * Get neighboring cells
   */
  static getNeighbors(grid, x, y, diagonal = false) {
    const neighbors = [];
    const directions = diagonal
      ? [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
      : [[-1, 0], [1, 0], [0, -1], [0, 1]];

    for (const [dx, dy] of directions) {
      const nx = x + dx;
      const ny = y + dy;

      if (this.isValid(grid, nx, ny)) {
        neighbors.push({ x: nx, y: ny, value: grid[ny][nx] });
      }
    }

    return neighbors;
  }

  /**
   * Count neighboring cells with specific value
   */
  static countNeighbors(grid, x, y, value, diagonal = false) {
    const neighbors = this.getNeighbors(grid, x, y, diagonal);
    return neighbors.filter(n => n.value === value).length;
  }

  /**
   * Perform flood fill from position
   */
  static floodFill(grid, startX, startY, targetValue, replacementValue) {
    if (!this.isValid(grid, startX, startY)) return [];
    if (grid[startY][startX] !== targetValue) return [];

    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));
    const queue = [{ x: startX, y: startY }];
    const filled = [];

    while (queue.length > 0) {
      const { x, y } = queue.shift();

      if (visited[y][x]) continue;
      visited[y][x] = true;

      if (grid[y][x] === targetValue) {
        grid[y][x] = replacementValue;
        filled.push({ x, y });

        // Add neighbors
        const neighbors = [
          { x: x + 1, y },
          { x: x - 1, y },
          { x, y: y + 1 },
          { x, y: y - 1 }
        ];

        for (const neighbor of neighbors) {
          if (this.isValid(grid, neighbor.x, neighbor.y) && !visited[neighbor.y][neighbor.x]) {
            queue.push(neighbor);
          }
        }
      }
    }

    return filled;
  }

  /**
   * Find connected components
   */
  static findConnectedComponents(grid, value = 'floor') {
    const components = [];
    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === value && !visited[y][x]) {
          const component = this.floodFill(grid, x, y, value, value);
          components.push(component);

          // Mark visited
          for (const cell of component) {
            visited[cell.y][cell.x] = true;
          }
        }
      }
    }

    return components;
  }

  /**
   * Calculate distance between two positions
   */
  static distance(x1, y1, x2, y2) {
    return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
  }

  /**
   * Calculate Manhattan distance
   */
  static manhattanDistance(x1, y1, x2, y2) {
    return Math.abs(x2 - x1) + Math.abs(y2 - y1);
  }

  /**
   * Find path between two positions (BFS)
   */
  static findPath(grid, startX, startY, endX, endY, passableValues = ['floor']) {
    if (!this.isValid(grid, startX, startY) || !this.isValid(grid, endX, endY)) {
      return null;
    }

    const queue = [{ x: startX, y: startY, path: [] }];
    const visited = Array(grid.length).fill().map(() => Array(grid[0].length).fill(false));
    visited[startY][startX] = true;

    while (queue.length > 0) {
      const { x, y, path } = queue.shift();

      // Check if reached destination
      if (x === endX && y === endY) {
        return [...path, { x, y }];
      }

      // Check neighbors
      const neighbors = [
        { x: x + 1, y },
        { x: x - 1, y },
        { x, y: y + 1 },
        { x, y: y - 1 }
      ];

      for (const neighbor of neighbors) {
        if (this.isValid(grid, neighbor.x, neighbor.y) &&
            !visited[neighbor.y][neighbor.x] &&
            passableValues.includes(grid[neighbor.y][neighbor.x])) {

          visited[neighbor.y][neighbor.x] = true;
          queue.push({
            x: neighbor.x,
            y: neighbor.y,
            path: [...path, { x, y }]
          });
        }
      }
    }

    return null; // No path found
  }

  /**
   * Get rectangular region
   */
  static getRegion(grid, x, y, width, height) {
    const region = [];

    for (let dy = 0; dy < height; dy++) {
      const row = [];
      for (let dx = 0; dx < width; dx++) {
        const gridX = x + dx;
        const gridY = y + dy;

        if (this.isValid(grid, gridX, gridY)) {
          row.push(grid[gridY][gridX]);
        } else {
          row.push(null);
        }
      }
      region.push(row);
    }

    return region;
  }

  /**
   * Set rectangular region
   */
  static setRegion(grid, x, y, region) {
    for (let dy = 0; dy < region.length; dy++) {
      for (let dx = 0; dx < region[dy].length; dx++) {
        const gridX = x + dx;
        const gridY = y + dy;

        if (this.isValid(grid, gridX, gridY)) {
          grid[gridY][gridX] = region[dy][dx];
        }
      }
    }
  }

  /**
   * Rotate grid 90 degrees clockwise
   */
  static rotate(grid) {
    const height = grid.length;
    const width = grid[0].length;
    const rotated = Array(width).fill().map(() => Array(height).fill(null));

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        rotated[x][height - 1 - y] = grid[y][x];
      }
    }

    return rotated;
  }

  /**
   * Flip grid horizontally
   */
  static flipHorizontal(grid) {
    return grid.map(row => [...row].reverse());
  }

  /**
   * Flip grid vertically
   */
  static flipVertical(grid) {
    return [...grid].reverse();
  }

  /**
   * Scale grid by factor
   */
  static scale(grid, scaleX, scaleY) {
    const originalHeight = grid.length;
    const originalWidth = grid[0].length;
    const scaledHeight = originalHeight * scaleY;
    const scaledWidth = originalWidth * scaleX;
    const scaled = Array(scaledHeight).fill().map(() => Array(scaledWidth).fill(null));

    for (let y = 0; y < scaledHeight; y++) {
      for (let x = 0; x < scaledWidth; x++) {
        const originalX = Math.floor(x / scaleX);
        const originalY = Math.floor(y / scaleY);
        scaled[y][x] = grid[originalY][originalX];
      }
    }

    return scaled;
  }

  /**
   * Convert grid to string representation
   */
  static toString(grid, cellMapping = {}) {
    const mapping = {
      'wall': '#',
      'floor': '.',
      'door': '+',
      'water': '~',
      'lava': '^',
      'pit': 'O',
      ...cellMapping
    };

    return grid.map(row =>
      row.map(cell => mapping[cell] || '?').join('')
    ).join('\n');
  }

  /**
   * Parse grid from string representation
   */
  static fromString(str, cellMapping = {}) {
    const mapping = {
      '#': 'wall',
      '.': 'floor',
      '+': 'door',
      '~': 'water',
      '^': 'lava',
      'O': 'pit',
      ...cellMapping
    };

    const lines = str.trim().split('\n');
    const grid = [];

    for (const line of lines) {
      const row = [];
      for (const char of line.trim()) {
        row.push(mapping[char] || 'wall');
      }
      grid.push(row);
    }

    return grid;
  }

  /**
   * Validate grid structure
   */
  static validate(grid) {
    if (!Array.isArray(grid) || grid.length === 0) {
      return { valid: false, error: 'Grid must be a non-empty array' };
    }

    const width = grid[0].length;
    for (let y = 0; y < grid.length; y++) {
      if (!Array.isArray(grid[y])) {
        return { valid: false, error: `Row ${y} is not an array` };
      }
      if (grid[y].length !== width) {
        return { valid: false, error: `Row ${y} has inconsistent width` };
      }
    }

    return { valid: true };
  }
}

module.exports = Grid;