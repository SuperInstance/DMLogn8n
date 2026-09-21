import AsyncStorage from '@react-native-async-storage/async-storage';
import { Alert } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { API_CONFIG, ApiResponse, PaginatedResponse } from '../constants/api';
import { OfflineService } from './offline';
import { store } from '../store';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: any;
  params?: Record<string, any>;
  timeout?: number;
  retries?: number;
  skipAuth?: boolean;
  skipOffline?: boolean;
  cache?: boolean;
}

class ApiService {
  private baseURL: string;
  private mobileBaseURL: string;
  private wsURL: string;
  private defaultTimeout: number;
  private maxRetries: number;
  private retryDelay: number;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.mobileBaseURL = API_CONFIG.MOBILE_BASE_URL;
    this.wsURL = API_CONFIG.WS_URL;
    this.defaultTimeout = API_CONFIG.TIMEOUT;
    this.maxRetries = API_CONFIG.RETRY_ATTEMPTS;
    this.retryDelay = API_CONFIG.RETRY_DELAY;
  }

  // Token Management
  private async getAuthToken(): Promise<string | null> {
    try {
      const token = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.AUTH_TOKEN);
      return token;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  private async setAuthToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
    } catch (error) {
      console.error('Failed to set auth token:', error);
    }
  }

  private async removeAuthToken(): Promise<void> {
    try {
      await AsyncStorage.removeItem(API_CONFIG.STORAGE_KEYS.AUTH_TOKEN);
      await AsyncStorage.removeItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Failed to remove auth tokens:', error);
    }
  }

  // Request/Response Helpers
  private async buildURL(endpoint: string, params?: Record<string, any>): Promise<string> {
    const baseURL = endpoint.includes('/mobile/') ? this.mobileBaseURL : this.baseURL;
    let url = `${baseURL}${endpoint}`;

    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const paramString = searchParams.toString();
      if (paramString) {
        url += `?${paramString}`;
      }
    }

    return url;
  }

  private async buildHeaders(
    customHeaders: Record<string, string> = {},
    skipAuth: boolean = false
  ): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-App-Version': await this.getAppVersion(),
      'X-Device-ID': await this.getDeviceId(),
      'X-Platform': this.getPlatform(),
      ...customHeaders,
    };

    if (!skipAuth) {
      const token = await this.getAuthToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  private async getAppVersion(): Promise<string> {
    try {
      const version = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.APP_VERSION);
      return version || '1.0.0';
    } catch (error) {
      return '1.0.0';
    }
  }

  private async getDeviceId(): Promise<string> {
    try {
      const deviceId = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.DEVICE_ID);
      if (deviceId) return deviceId;

      const newDeviceId = this.generateDeviceId();
      await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.DEVICE_ID, newDeviceId);
      return newDeviceId;
    } catch (error) {
      return 'unknown-device';
    }
  }

  private generateDeviceId(): string {
    return `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getPlatform(): string {
    // This would typically come from react-native-device-info
    return 'mobile';
  }

  // Network Check
  private async isOnline(): Promise<boolean> {
    try {
      const networkState = await NetInfo.fetch();
      return networkState.isConnected ?? false;
    } catch (error) {
      console.error('Failed to check network status:', error);
      return false;
    }
  }

  // Main Request Method
  async request<T = any>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      params,
      timeout = this.defaultTimeout,
      retries = this.maxRetries,
      skipAuth = false,
      skipOffline = false,
      cache = false,
    } = options;

    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        // Check network connectivity
        const isOnline = await this.isOnline();
        if (!isOnline && !skipOffline) {
          console.log('Device offline, attempting offline mode');
          return await this.handleOfflineRequest<T>(endpoint, options);
        }

        // Build request
        const url = await this.buildURL(endpoint, params);
        const requestHeaders = await this.buildHeaders(headers, skipAuth);

        // Prepare body
        let requestBody: string | undefined;
        if (body && method !== 'GET') {
          requestBody = typeof body === 'string' ? body : JSON.stringify(body);
        }

        console.log(`API Request: ${method} ${url}`, {
          headers: requestHeaders,
          body: requestBody,
        });

        // Make request with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          method,
          headers: requestHeaders,
          body: requestBody,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Handle response
        const responseData = await this.parseResponse<T>(response);

        // Cache successful GET requests
        if (method === 'GET' && cache && responseData.success) {
          await this.cacheResponse(endpoint, responseData);
        }

        return responseData;

      } catch (error) {
        lastError = error as Error;
        console.error(`Request failed (attempt ${attempt + 1}/${retries + 1}):`, error);

        // Don't retry on certain errors
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            // Timeout error
            continue;
          }
          if (error.message.includes('401') || error.message.includes('403')) {
            // Auth errors shouldn't be retried
            break;
          }
        }

        // Wait before retrying (except for the last attempt)
        if (attempt < retries) {
          await this.delay(this.retryDelay * Math.pow(2, attempt));
        }
      }
    }

    // Handle final error
    if (lastError) {
      if (lastError.name === 'AbortError') {
        return {
          success: false,
          error: 'Request timeout',
          timestamp: new Date().toISOString(),
        };
      }

      // Try offline mode if available
      if (!skipOffline) {
        try {
          return await this.handleOfflineRequest<T>(endpoint, options);
        } catch (offlineError) {
          console.error('Offline mode also failed:', offlineError);
        }
      }

      return {
        success: false,
        error: lastError.message || 'Request failed',
        timestamp: new Date().toISOString(),
      };
    }

    return {
      success: false,
      error: 'Unknown error occurred',
      timestamp: new Date().toISOString(),
    };
  }

  private async parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
    try {
      const responseText = await response.text();
      let data: any;

      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        // If response is not JSON, treat it as error message
        data = {
          success: false,
          error: responseText || 'Invalid response',
          timestamp: new Date().toISOString(),
        };
      }

      // Handle HTTP errors
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          await this.removeAuthToken();
          store.dispatch({ type: 'auth/logout' });
        }

        return {
          success: false,
          error: data.error || data.message || `HTTP ${response.status}`,
          timestamp: new Date().toISOString(),
        };
      }

      // Ensure response has required fields
      if (typeof data !== 'object' || data === null) {
        return {
          success: true,
          data: data as T,
          timestamp: new Date().toISOString(),
        };
      }

      return {
        success: data.success !== false,
        data: data.data || data,
        error: data.error,
        message: data.message,
        timestamp: data.timestamp || new Date().toISOString(),
      };

    } catch (error) {
      console.error('Failed to parse response:', error);
      return {
        success: false,
        error: 'Failed to parse response',
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Offline Handling
  private async handleOfflineRequest<T>(
    endpoint: string,
    options: RequestOptions
  ): Promise<ApiResponse<T>> {
    if (options.method !== 'GET') {
      // Queue non-GET requests for when we're back online
      await OfflineService.queueRequest(endpoint, options);
      return {
        success: false,
        error: 'Offline - request queued',
        timestamp: new Date().toISOString(),
      };
    }

    // Try to get cached response
    const cachedResponse = await this.getCachedResponse<T>(endpoint);
    if (cachedResponse) {
      return {
        ...cachedResponse,
        message: 'Offline - showing cached data',
      };
    }

    return {
      success: false,
      error: 'Offline - no cached data available',
      timestamp: new Date().toISOString(),
    };
  }

  private async cacheResponse<T>(endpoint: string, response: ApiResponse<T>): Promise<void> {
    try {
      const cacheKey = `cache_${endpoint}`;
      const cacheData = {
        ...response,
        cachedAt: new Date().toISOString(),
      };
      await AsyncStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Failed to cache response:', error);
    }
  }

  private async getCachedResponse<T>(endpoint: string): Promise<ApiResponse<T> | null> {
    try {
      const cacheKey = `cache_${endpoint}`;
      const cachedData = await AsyncStorage.getItem(cacheKey);
      if (!cachedData) return null;

      const parsed = JSON.parse(cachedData) as ApiResponse<T> & { cachedAt: string };
      const cacheAge = Date.now() - new Date(parsed.cachedAt).getTime();
      const maxCacheAge = 5 * 60 * 1000; // 5 minutes

      if (cacheAge > maxCacheAge) {
        await AsyncStorage.removeItem(cacheKey);
        return null;
      }

      return parsed;
    } catch (error) {
      console.error('Failed to get cached response:', error);
      return null;
    }
  }

  // Utility Methods
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // HTTP Method Wrappers
  async get<T = any>(endpoint: string, params?: Record<string, any>, options: Omit<RequestOptions, 'method' | 'params'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'GET', params });
  }

  async post<T = any>(endpoint: string, body?: any, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body });
  }

  async put<T = any>(endpoint: string, body?: any, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  async patch<T = any>(endpoint: string, body?: any, options: Omit<RequestOptions, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'PATCH', body });
  }

  async delete<T = any>(endpoint: string, options: Omit<RequestOptions, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  // Pagination Helper
  async getPaginated<T = any>(
    endpoint: string,
    params?: Record<string, any>,
    options: Omit<RequestOptions, 'method' | 'params'> = {}
  ): Promise<PaginatedResponse<T>> {
    const response = await this.get<T[]>(endpoint, params, options);

    if (!response.success || !Array.isArray(response.data)) {
      return {
        success: false,
        error: response.error || 'Invalid paginated response',
        timestamp: response.timestamp,
        pagination: {
          page: 1,
          limit: 20,
          total: 0,
          totalPages: 0,
          hasNext: false,
          hasPrev: false,
        },
      };
    }

    // Extract pagination info from response headers or data
    const pagination = {
      page: parseInt(params?.page || '1'),
      limit: parseInt(params?.limit || API_CONFIG.PAGINATION.DEFAULT_PAGE_SIZE.toString()),
      total: 0, // This would come from API headers
      totalPages: 0,
      hasNext: false,
      hasPrev: false,
    };

    return {
      ...response,
      pagination,
    };
  }

  // File Upload
  async uploadFile(
    endpoint: string,
    file: {
      uri: string;
      name: string;
      type: string;
    },
    options: Omit<RequestOptions, 'method' | 'body' | 'headers'> = {}
  ): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.type,
    } as any);

    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // WebSocket Connection
  createWebSocket(path: string = ''): WebSocket {
    const wsURL = `${this.wsURL.replace('http', 'ws')}${path}`;
    return new WebSocket(wsURL);
  }

  // Authentication Methods
  async login(email: string, password: string, rememberMe: boolean = false): Promise<ApiResponse<any>> {
    const response = await this.post('/auth/login', {
      email,
      password,
      rememberMe,
      deviceInfo: {
        deviceId: await this.getDeviceId(),
        platform: this.getPlatform(),
        appVersion: await this.getAppVersion(),
      },
    });

    if (response.success && response.data?.token) {
      await this.setAuthToken(response.data.token);
      if (response.data.refreshToken) {
        await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN, response.data.refreshToken);
      }
    }

    return response;
  }

  async logout(): Promise<ApiResponse<any>> {
    const response = await this.post('/auth/logout');
    await this.removeAuthToken();
    return response;
  }

  async refreshToken(): Promise<ApiResponse<any>> {
    const refreshToken = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.REFRESH_TOKEN);
    if (!refreshToken) {
      return {
        success: false,
        error: 'No refresh token available',
        timestamp: new Date().toISOString(),
      };
    }

    const response = await this.post('/auth/refresh', { refreshToken }, { skipAuth: true });

    if (response.success && response.data?.token) {
      await this.setAuthToken(response.data.token);
    }

    return response;
  }
}

// Create singleton instance
export const apiService = new ApiService();
export default apiService;