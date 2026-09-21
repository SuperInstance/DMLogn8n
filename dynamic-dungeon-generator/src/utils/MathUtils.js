/**
 * Math Utilities
 * Mathematical helper functions for dungeon generation
 */

const seedrandom = require('seedrandom');

class MathUtils {
  constructor() {
    this.rng = Math.random;
  }

  /**
   * Set random seed for reproducible generation
   */
  static setSeed(seed) {
    if (typeof seed === 'string') {
      MathUtils.rng = seedrandom(seed);
    } else {
      MathUtils.rng = seedrandom(seed.toString());
    }
  }

  /**
   * Get random number between min and max (inclusive)
   */
  static random(min = 0, max = 1) {
    return MathUtils.rng() * (max - min) + min;
  }

  /**
   * Get random integer between min and max (inclusive)
   */
  static randomInt(min, max) {
    return Math.floor(MathUtils.random(min, max + 1));
  }

  /**
   * Get random element from array
   */
  static randomChoice(array) {
    if (!array || array.length === 0) return null;
    return array[Math.floor(MathUtils.random(0, array.length))];
  }

  /**
   * Get random weighted choice
   */
  static weightedChoice(options) {
    const totalWeight = options.reduce((sum, option) => sum + option.weight, 0);
    let random = MathUtils.random(0, totalWeight);

    for (const option of options) {
      random -= option.weight;
      if (random <= 0) {
        return option.value;
      }
    }

    return options[options.length - 1].value;
  }

  /**
   * Shuffle array in place
   */
  static shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(MathUtils.random(0, i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  /**
   * Generate unique ID
   */
  static generateId() {
    return MathUtils.randomInt(100000, 999999).toString(36) + Date.now().toString(36);
  }

  /**
   * Calculate Euclidean distance between two points
   */
  static distance(x1, y1, x2, y2) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Calculate Manhattan distance between two points
   */
  static manhattanDistance(x1, y1, x2, y2) {
    return Math.abs(x2 - x1) + Math.abs(y2 - y1);
  }

  /**
   * Calculate Chebyshev distance (for grid movement)
   */
  static chebyshevDistance(x1, y1, x2, y2) {
    return Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1));
  }

  /**
   * Clamp value between min and max
   */
  static clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  /**
   * Linear interpolation between two values
   */
  static lerp(start, end, t) {
    return start + (end - start) * MathUtils.clamp(t, 0, 1);
  }

  /**
   * Smooth interpolation using ease-in-out
   */
  static smoothStep(t) {
    t = MathUtils.clamp(t, 0, 1);
    return t * t * (3 - 2 * t);
  }

  /**
   * Check if point is inside rectangle
   */
  static pointInRect(x, y, rectX, rectY, rectWidth, rectHeight) {
    return x >= rectX && x < rectX + rectWidth &&
           y >= rectY && y < rectY + rectHeight;
  }

  /**
   * Check if two rectangles intersect
   */
  static rectIntersect(x1, y1, w1, h1, x2, y2, w2, h2) {
    return x1 < x2 + w2 && x1 + w1 > x2 &&
           y1 < y2 + h2 && y1 + h1 > y2;
  }

  /**
   * Get angle between two points in radians
   */
  static angle(x1, y1, x2, y2) {
    return Math.atan2(y2 - y1, x2 - x1);
  }

  /**
   * Convert degrees to radians
   */
  static degToRad(degrees) {
    return degrees * Math.PI / 180;
  }

  /**
   * Convert radians to degrees
   */
  static radToDeg(radians) {
    return radians * 180 / Math.PI;
  }

  /**
   * Normalize angle to 0-2π range
   */
  static normalizeAngle(angle) {
    while (angle < 0) angle += 2 * Math.PI;
    while (angle >= 2 * Math.PI) angle -= 2 * Math.PI;
    return angle;
  }

  /**
   * Calculate point at distance and angle from origin
   */
  static pointFromAngle(x, y, angle, distance) {
    return {
      x: x + Math.cos(angle) * distance,
      y: y + Math.sin(angle) * distance
    };
  }

  /**
   * Round to nearest multiple of value
   */
  static roundToMultiple(value, multiple) {
    return Math.round(value / multiple) * multiple;
  }

  /**
   * Check if value is approximately equal to target
   */
  static approxEqual(value, target, epsilon = 0.0001) {
    return Math.abs(value - target) < epsilon;
  }

  /**
   * Map value from one range to another
   */
  static map(value, fromMin, fromMax, toMin, toMax) {
    const normalized = (value - fromMin) / (fromMax - fromMin);
    return MathUtils.lerp(toMin, toMax, normalized);
  }

  /**
   * Gaussian random number (Box-Muller transform)
   */
  static gaussianRandom(mean = 0, stdDev = 1) {
    let u = 0, v = 0;
    while (u === 0) u = MathUtils.random();
    while (v === 0) v = MathUtils.random();

    const num = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
    return num * stdDev + mean;
  }

  /**
   * Perlin-like noise function
   */
  static noise(x, y, octaves = 4, persistence = 0.5, scale = 0.01) {
    let total = 0;
    let frequency = scale;
    let amplitude = 1;
    let maxValue = 0;

    for (let i = 0; i < octaves; i++) {
      total += this.simpleNoise(x * frequency, y * frequency) * amplitude;
      maxValue += amplitude;
      amplitude *= persistence;
      frequency *= 2;
    }

    return total / maxValue;
  }

  /**
   * Simple noise function
   */
  static simpleNoise(x, y) {
    const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
    return (n - Math.floor(n)) * 2 - 1;
  }

  /**
   * Fibonacci sequence generator
   */
  static fibonacci(n) {
    if (n <= 1) return n;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
      const temp = a + b;
      a = b;
      b = temp;
    }
    return b;
  }

  /**
   * Generate golden ratio point
   */
  static goldenRatio(index) {
    const phi = (1 + Math.sqrt(5)) / 2;
    return (index * phi) % 1;
  }

  /**
   * Calculate area of polygon using shoelace formula
   */
  static polygonArea(points) {
    let area = 0;
    for (let i = 0; i < points.length; i++) {
      const j = (i + 1) % points.length;
      area += points[i].x * points[j].y;
      area -= points[j].x * points[i].y;
    }
    return Math.abs(area) / 2;
  }

  /**
   * Check if point is inside polygon
   */
  static pointInPolygon(x, y, points) {
    let inside = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const xi = points[i].x, yi = points[i].y;
      const xj = points[j].x, yj = points[j].y;

      const intersect = ((yi > y) !== (yj > y))
          && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }

  /**
   * Generate spiral points
   */
  static spiralPoints(centerX, centerY, maxRadius, step = 1) {
    const points = [];
    let angle = 0;
    let radius = 0;

    while (radius <= maxRadius) {
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      points.push({ x: Math.round(x), y: Math.round(y) });

      angle += step * 0.1;
      radius += step * 0.01;
    }

    return points;
  }

  /**
   * Generate grid points in circle
   */
  static circlePoints(centerX, centerY, radius, filled = true) {
    const points = [];

    for (let y = -radius; y <= radius; y++) {
      for (let x = -radius; x <= radius; x++) {
        const distance = Math.sqrt(x * x + y * y);
        if (filled ? distance <= radius : Math.abs(distance - radius) < 1) {
          points.push({ x: centerX + x, y: centerY + y });
        }
      }
    }

    return points;
  }

  /**
   * Generate grid points in ellipse
   */
  static ellipsePoints(centerX, centerY, radiusX, radiusY, filled = true) {
    const points = [];

    for (let y = -radiusY; y <= radiusY; y++) {
      for (let x = -radiusX; x <= radiusX; x++) {
        const normalizedX = x / radiusX;
        const normalizedY = y / radiusY;
        const distance = Math.sqrt(normalizedX * normalizedX + normalizedY * normalizedY);

        if (filled ? distance <= 1 : Math.abs(distance - 1) < 0.1) {
          points.push({ x: centerX + x, y: centerY + y });
        }
      }
    }

    return points;
  }

  /**
   * Calculate bounding box of points
   */
  static boundingBox(points) {
    if (points.length === 0) return null;

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);

    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
      width: Math.max(...xs) - Math.min(...xs),
      height: Math.max(...ys) - Math.min(...ys),
      centerX: (Math.min(...xs) + Math.max(...xs)) / 2,
      centerY: (Math.min(...ys) + Math.max(...ys)) / 2
    };
  }

  /**
   * Calculate centroid of points
   */
  static centroid(points) {
    if (points.length === 0) return { x: 0, y: 0 };

    const sum = points.reduce((acc, point) => ({
      x: acc.x + point.x,
      y: acc.y + point.y
    }), { x: 0, y: 0 });

    return {
      x: sum.x / points.length,
      y: sum.y / points.length
    };
  }
}

// Store RNG instance
MathUtils.rng = Math.random;

module.exports = MathUtils;