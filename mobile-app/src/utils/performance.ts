import { InteractionManager, Platform } from 'react-native';

// Performance optimization utilities
export class PerformanceUtils {
  // Run tasks after interactions/animations complete
  static runAfterInteractions(callback: () => void): void {
    InteractionManager.runAfterInteractions(callback);
  }

  // Check if device is low-end
  static isLowEndDevice(): boolean {
    // This is a simplified check - in a real app you might use
    // react-native-device-info to get more accurate device info
    return Platform.OS === 'android';
  }

  // Optimize image loading based on device capabilities
  static getImageQuality(): number {
    return this.isLowEndDevice() ? 0.7 : 0.9;
  }

  // Get optimal image size for device
  static getOptimalImageSize(): { width: number; height: number } {
    const screenWidth = 375; // Default screen width
    const screenHeight = 667; // Default screen height

    if (this.isLowEndDevice()) {
      return {
        width: Math.min(screenWidth, 800),
        height: Math.min(screenHeight, 800),
      };
    }

    return {
      width: Math.min(screenWidth * 2, 1200),
      height: Math.min(screenHeight * 2, 1200),
    };
  }

  // Debounce function for frequent operations
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(null, args), wait);
    };
  }

  // Throttle function for scroll events
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func.apply(null, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  }

  // Memoize expensive computations
  static memoize<T extends (...args: any[]) => any>(fn: T): T {
    const cache = new Map();
    return ((...args: Parameters<T>) => {
      const key = JSON.stringify(args);
      if (cache.has(key)) {
        return cache.get(key);
      }
      const result = fn(...args);
      cache.set(key, result);
      return result;
    }) as T;
  }

  // Lazy load heavy components
  static lazyLoad<T extends React.ComponentType<any>>(
    importFunc: () => Promise<{ default: T }>
  ): React.LazyExoticComponent<T> {
    return React.lazy(importFunc);
  }

  // Batch state updates
  static batchUpdate(updates: Array<() => void>): void {
    updates.forEach(update => update());
  }

  // Measure component render time
  static measureRenderTime(componentName: string): void {
    if (__DEV__) {
      const startTime = performance.now();
      return () => {
        const endTime = performance.now();
        console.log(`${componentName} render time: ${endTime - startTime}ms`);
      };
    }
    return () => {};
  }

  // Optimize list rendering
  static getItemLayout = (
    data: any[] | null | undefined,
    index: number
  ): { length: number; offset: number; index: number } => {
    const ITEM_HEIGHT = 80; // Adjust based on your item height
    return {
      length: ITEM_HEIGHT,
      offset: ITEM_HEIGHT * index,
      index,
    };
  };

  // Preload critical data
  static async preloadData(preloadFunctions: Array<() => Promise<void>>): Promise<void> {
    try {
      await Promise.all(preloadFunctions.map(fn => fn()));
    } catch (error) {
      console.warn('Error preloading data:', error);
    }
  }

  // Clear memory cache
  static clearMemoryCache(): void {
    // Clear image caches, unused data, etc.
    if (Platform.OS === 'android') {
      // Android specific cleanup
    } else {
      // iOS specific cleanup
    }
  }

  // Monitor memory usage
  static getMemoryUsage(): number {
    // This would typically use native modules to get actual memory usage
    return 0; // Placeholder
  }

  // Optimize bundle loading
  static optimizeBundleLoading(): void {
    // Code splitting and lazy loading strategies
  }
}

// Performance monitoring
export class PerformanceMonitor {
  private static metrics: Map<string, number[]> = new Map();

  static startTimer(name: string): () => void {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      const duration = endTime - startTime;

      if (!this.metrics.has(name)) {
        this.metrics.set(name, []);
      }
      this.metrics.get(name)!.push(duration);

      if (__DEV__) {
        console.log(`${name}: ${duration.toFixed(2)}ms`);
      }
    };
  }

  static getAverageTime(name: string): number {
    const times = this.metrics.get(name);
    if (!times || times.length === 0) return 0;
    return times.reduce((sum, time) => sum + time, 0) / times.length;
  }

  static getMetrics(): Record<string, { average: number; count: number }> {
    const result: Record<string, { average: number; count: number }> = {};
    for (const [name, times] of this.metrics.entries()) {
      result[name] = {
        average: this.getAverageTime(name),
        count: times.length,
      };
    }
    return result;
  }

  static clearMetrics(): void {
    this.metrics.clear();
  }
}

// React hooks for performance optimization
export const usePerformanceOptimization = () => {
  const [isLowEndDevice, setIsLowEndDevice] = React.useState(false);

  React.useEffect(() => {
    setIsLowEndDevice(PerformanceUtils.isLowEndDevice());
  }, []);

  return {
    isLowEndDevice,
    getImageQuality: PerformanceUtils.getImageQuality,
    getOptimalImageSize: PerformanceUtils.getOptimalImageSize,
    runAfterInteractions: PerformanceUtils.runAfterInteractions,
  };
};