import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import RNFS from 'react-native-fs';

interface CacheEntry {
  uri: string;
  timestamp: number;
  size: number;
  accessCount: number;
  lastAccessed: number;
}

class ImageCacheManager {
  private cacheDir: string;
  private maxCacheSize: number;
  private maxAge: number;
  private cache: Map<string, CacheEntry> = new Map();

  constructor() {
    this.cacheDir = `${RNFS.CachesDirectoryPath}/images`;
    this.maxCacheSize = 100 * 1024 * 1024; // 100MB
    this.maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days
    this.initializeCache();
  }

  private async initializeCache(): Promise<void> {
    try {
      // Ensure cache directory exists
      await RNFS.mkdir(this.cacheDir);

      // Load cache metadata
      const cacheData = await AsyncStorage.getItem('imageCache');
      if (cacheData) {
        const entries = JSON.parse(cacheData) as CacheEntry[];
        this.cache = new Map(entries.map(entry => [entry.uri, entry]));
      }

      // Clean up old entries
      await this.cleanup();
    } catch (error) {
      console.error('Failed to initialize image cache:', error);
    }
  }

  async cacheImage(uri: string, imageData: string): Promise<string> {
    try {
      const fileName = this.generateFileName(uri);
      const filePath = `${this.cacheDir}/${fileName}`;

      // Save image to file system
      await RNFS.writeFile(filePath, imageData, 'base64');

      // Get file size
      const stat = await RNFS.stat(filePath);
      const fileSize = stat.size;

      // Update cache metadata
      const entry: CacheEntry = {
        uri,
        timestamp: Date.now(),
        size: fileSize,
        accessCount: 0,
        lastAccessed: Date.now(),
      };

      this.cache.set(uri, entry);
      await this.saveCacheMetadata();

      // Check if cache cleanup is needed
      await this.checkCacheSize();

      return `file://${filePath}`;
    } catch (error) {
      console.error('Failed to cache image:', error);
      return uri;
    }
  }

  async getCachedImage(uri: string): Promise<string | null> {
    try {
      const entry = this.cache.get(uri);
      if (!entry) return null;

      // Check if entry is expired
      if (Date.now() - entry.timestamp > this.maxAge) {
        await this.removeEntry(uri);
        return null;
      }

      // Update access statistics
      entry.accessCount++;
      entry.lastAccessed = Date.now();
      await this.saveCacheMetadata();

      const fileName = this.generateFileName(uri);
      const filePath = `${this.cacheDir}/${fileName}`;

      if (await RNFS.exists(filePath)) {
        return `file://${filePath}`;
      }

      // File doesn't exist, remove from cache
      await this.removeEntry(uri);
      return null;
    } catch (error) {
      console.error('Failed to get cached image:', error);
      return null;
    }
  }

  private generateFileName(uri: string): string {
    // Generate a safe filename from URI
    return Buffer.from(uri).toString('base64').replace(/[+/=]/g, '').substring(0, 20);
  }

  private async removeEntry(uri: string): Promise<void> {
    try {
      const entry = this.cache.get(uri);
      if (!entry) return;

      const fileName = this.generateFileName(uri);
      const filePath = `${this.cacheDir}/${fileName}`;

      if (await RNFS.exists(filePath)) {
        await RNFS.unlink(filePath);
      }

      this.cache.delete(uri);
      await this.saveCacheMetadata();
    } catch (error) {
      console.error('Failed to remove cache entry:', error);
    }
  }

  private async saveCacheMetadata(): Promise<void> {
    try {
      const entries = Array.from(this.cache.values());
      await AsyncStorage.setItem('imageCache', JSON.stringify(entries));
    } catch (error) {
      console.error('Failed to save cache metadata:', error);
    }
  }

  private async cleanup(): Promise<void> {
    const now = Date.now();
    const expiredEntries: string[] = [];

    for (const [uri, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.maxAge) {
        expiredEntries.push(uri);
      }
    }

    for (const uri of expiredEntries) {
      await this.removeEntry(uri);
    }
  }

  private async checkCacheSize(): Promise<void> {
    const totalSize = Array.from(this.cache.values())
      .reduce((sum, entry) => sum + entry.size, 0);

    if (totalSize > this.maxCacheSize) {
      await this.evictLeastUsed();
    }
  }

  private async evictLeastUsed(): Promise<void> {
    // Sort by access frequency and recency
    const entries = Array.from(this.cache.entries()).sort((a, b) => {
      const scoreA = a[1].accessCount / (Date.now() - a[1].lastAccessed);
      const scoreB = b[1].accessCount / (Date.now() - b[1].lastAccessed);
      return scoreA - scoreB;
    });

    // Remove entries until cache size is acceptable
    const targetSize = this.maxCacheSize * 0.8; // Remove 20% when over limit
    let currentSize = Array.from(this.cache.values())
      .reduce((sum, entry) => sum + entry.size, 0);

    for (const [uri] of entries) {
      if (currentSize <= targetSize) break;
      const entry = this.cache.get(uri);
      if (entry) {
        currentSize -= entry.size;
        await this.removeEntry(uri);
      }
    }
  }

  async preloadImages(uris: string[]): Promise<void> {
    const preloadPromises = uris.map(async (uri) => {
      const cached = await this.getCachedImage(uri);
      if (cached) return;

      try {
        // Download and cache image
        const response = await fetch(uri);
        const imageData = await response.text();
        await this.cacheImage(uri, imageData);
      } catch (error) {
        console.error('Failed to preload image:', uri, error);
      }
    });

    await Promise.allSettled(preloadPromises);
  }

  async clearCache(): Promise<void> {
    try {
      // Remove all cached files
      const files = await RNFS.readDir(this.cacheDir);
      for (const file of files) {
        await RNFS.unlink(file.path);
      }

      // Clear cache metadata
      this.cache.clear();
      await AsyncStorage.removeItem('imageCache');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  getCacheStats(): {
    totalSize: number;
    entryCount: number;
    hitRate: number;
  } {
    const totalSize = Array.from(this.cache.values())
      .reduce((sum, entry) => sum + entry.size, 0);
    const entryCount = this.cache.size;

    // Calculate hit rate (this would need additional tracking)
    const hitRate = 0; // Placeholder

    return {
      totalSize,
      entryCount,
      hitRate,
    };
  }
}

export const imageCacheManager = new ImageCacheManager();