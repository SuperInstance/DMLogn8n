/**
 * Audio Position Tracker - Tracks and manages 3D positions of audio sources
 * Provides smooth interpolation and velocity calculation for spatial audio
 */

export class AudioPositionTracker {
  constructor() {
    this.trackedSources = new Map();
    this.updateInterval = 16; // ~60fps
    this.lastUpdateTime = Date.now();

    // Interpolation settings
    this.interpolationDuration = 100; // ms
    this.maxInterpolationDistance = 50; // units

    // Performance optimization
    this.isTracking = false;
    this.animationFrameId = null;

    // Event system
    this.eventListeners = new Map();
  }

  /**
   * Start tracking a new audio source
   */
  trackSource(sourceId, sourceObject) {
    const trackingData = {
      source: sourceObject,
      currentPosition: { ...sourceObject.position },
      targetPosition: { ...sourceObject.position },
      previousPosition: { ...sourceObject.position },
      velocity: { x: 0, y: 0, z: 0 },
      interpolationStartTime: Date.now(),
      lastUpdateTime: Date.now(),
      isMoving: false,
      smoothFactor: 0.1
    };

    this.trackedSources.set(sourceId, trackingData);

    if (!this.isTracking) {
      this.startTracking();
    }

    this.emit('sourceTracked', { sourceId, trackingData });
  }

  /**
   * Stop tracking a source
   */
  untrackSource(sourceId) {
    if (this.trackedSources.has(sourceId)) {
      this.trackedSources.delete(sourceId);

      if (this.trackedSources.size === 0) {
        this.stopTracking();
      }

      this.emit('sourceUntracked', { sourceId });
    }
  }

  /**
   * Update target position for a source
   */
  updateSourcePosition(sourceId, newPosition) {
    if (!this.trackedSources.has(sourceId)) return;

    const trackingData = this.trackedSources.get(sourceId);

    // Store previous position for velocity calculation
    trackingData.previousPosition = { ...trackingData.currentPosition };
    trackingData.targetPosition = { ...newPosition };
    trackingData.interpolationStartTime = Date.now();
    trackingData.isMoving = true;

    this.emit('positionUpdate', { sourceId, position: newPosition });
  }

  /**
   * Start the tracking loop
   */
  startTracking() {
    if (this.isTracking) return;

    this.isTracking = true;
    this.lastUpdateTime = Date.now();
    this.updateLoop();
  }

  /**
   * Stop the tracking loop
   */
  stopTracking() {
    if (!this.isTracking) return;

    this.isTracking = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  /**
   * Main update loop for position tracking
   */
  updateLoop() {
    if (!this.isTracking) return;

    const currentTime = Date.now();
    const deltaTime = (currentTime - this.lastUpdateTime) / 1000; // Convert to seconds

    // Update all tracked sources
    for (const [sourceId, trackingData] of this.trackedSources) {
      this.updateSourceTracking(sourceId, trackingData, currentTime, deltaTime);
    }

    this.lastUpdateTime = currentTime;

    // Continue the loop
    this.animationFrameId = requestAnimationFrame(() => this.updateLoop());
  }

  /**
   * Update individual source tracking data
   */
  updateSourceTracking(sourceId, trackingData, currentTime, deltaTime) {
    if (!trackingData.isMoving) return;

    const elapsed = currentTime - trackingData.interpolationStartTime;
    const interpolationProgress = Math.min(elapsed / this.interpolationDuration, 1);

    // Smooth interpolation using easing function
    const easedProgress = this.easeInOutCubic(interpolationProgress);

    // Calculate interpolated position
    const interpolatedPosition = {
      x: trackingData.previousPosition.x +
         (trackingData.targetPosition.x - trackingData.previousPosition.x) * easedProgress,
      y: trackingData.previousPosition.y +
         (trackingData.targetPosition.y - trackingData.previousPosition.y) * easedProgress,
      z: trackingData.previousPosition.z +
         (trackingData.targetPosition.z - trackingData.previousPosition.z) * easedProgress
    };

    // Calculate velocity
    if (deltaTime > 0) {
      trackingData.velocity = {
        x: (interpolatedPosition.x - trackingData.currentPosition.x) / deltaTime,
        y: (interpolatedPosition.y - trackingData.currentPosition.y) / deltaTime,
        z: (interpolatedPosition.z - trackingData.currentPosition.z) / deltaTime
      };
    }

    // Update current position
    trackingData.currentPosition = interpolatedPosition;

    // Update the actual source position
    trackingData.source.position = { ...interpolatedPosition };
    trackingData.source.velocity = { ...trackingData.velocity };

    // Check if interpolation is complete
    if (interpolationProgress >= 1.0) {
      trackingData.isMoving = false;
      trackingData.currentPosition = { ...trackingData.targetPosition };
    }

    // Emit position update event
    this.emit('positionInterpolated', {
      sourceId,
      position: interpolatedPosition,
      velocity: trackingData.velocity,
      progress: interpolationProgress
    });
  }

  /**
   * Easing function for smooth interpolation
   */
  easeInOutCubic(t) {
    return t < 0.5
      ? 4 * t * t * t
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /**
   * Get current position of a tracked source
   */
  getSourcePosition(sourceId) {
    if (!this.trackedSources.has(sourceId)) return null;

    const trackingData = this.trackedSources.get(sourceId);
    return { ...trackingData.currentPosition };
  }

  /**
   * Get current velocity of a tracked source
   */
  getSourceVelocity(sourceId) {
    if (!this.trackedSources.has(sourceId)) return null;

    const trackingData = this.trackedSources.get(sourceId);
    return { ...trackingData.velocity };
  }

  /**
   * Check if a source is currently moving
   */
  isSourceMoving(sourceId) {
    if (!this.trackedSources.has(sourceId)) return false;

    const trackingData = this.trackedSources.get(sourceId);
    return trackingData.isMoving;
  }

  /**
   * Set smooth factor for a source
   */
  setSmoothFactor(sourceId, smoothFactor) {
    if (!this.trackedSources.has(sourceId)) return;

    const trackingData = this.trackedSources.get(sourceId);
    trackingData.smoothFactor = Math.max(0.01, Math.min(1.0, smoothFactor));
  }

  /**
   * Calculate distance between two sources
   */
  getDistanceBetween(sourceId1, sourceId2) {
    if (!this.trackedSources.has(sourceId1) || !this.trackedSources.has(sourceId2)) {
      return null;
    }

    const pos1 = this.getSourcePosition(sourceId1);
    const pos2 = this.getSourcePosition(sourceId2);

    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;

    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * Get all sources within a certain radius
   */
  getSourcesWithinRadius(centerPosition, radius) {
    const sourcesWithinRadius = [];

    for (const [sourceId, trackingData] of this.trackedSources) {
      const distance = this.calculateDistance(
        centerPosition,
        trackingData.currentPosition
      );

      if (distance <= radius) {
        sourcesWithinRadius.push({
          sourceId,
          position: { ...trackingData.currentPosition },
          velocity: { ...trackingData.velocity },
          distance
        });
      }
    }

    return sourcesWithinRadius;
  }

  /**
   * Calculate distance between two positions
   */
  calculateDistance(pos1, pos2) {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * Get tracking statistics
   */
  getTrackingStats() {
    const stats = {
      totalSources: this.trackedSources.size,
      movingSources: 0,
      averageVelocity: { x: 0, y: 0, z: 0 },
      updateRate: this.updateInterval
    };

    let totalVelocityX = 0;
    let totalVelocityY = 0;
    let totalVelocityZ = 0;

    for (const [sourceId, trackingData] of this.trackedSources) {
      if (trackingData.isMoving) {
        stats.movingSources++;
      }

      totalVelocityX += Math.abs(trackingData.velocity.x);
      totalVelocityY += Math.abs(trackingData.velocity.y);
      totalVelocityZ += Math.abs(trackingData.velocity.z);
    }

    if (stats.totalSources > 0) {
      stats.averageVelocity.x = totalVelocityX / stats.totalSources;
      stats.averageVelocity.y = totalVelocityY / stats.totalSources;
      stats.averageVelocity.z = totalVelocityZ / stats.totalSources;
    }

    return stats;
  }

  /**
   * Set interpolation duration globally
   */
  setInterpolationDuration(duration) {
    this.interpolationDuration = Math.max(10, Math.min(1000, duration));
  }

  /**
   * Update interpolation settings
   */
  updateSettings(settings) {
    if (settings.updateInterval) {
      this.updateInterval = Math.max(8, Math.min(100, settings.updateInterval));
    }

    if (settings.interpolationDuration) {
      this.setInterpolationDuration(settings.interpolationDuration);
    }
  }

  /**
   * Event emitter methods
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in position tracker event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy the position tracker
   */
  cleanup() {
    this.stopTracking();
    this.trackedSources.clear();
    this.eventListeners.clear();
  }
}