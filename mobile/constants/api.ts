export const API_CONFIG = {
  // Base URLs
  BASE_URL: __DEV__
    ? 'http://localhost:3000/api'
    : 'https://api.dmlogn8n.com',

  MOBILE_BASE_URL: __DEV__
    ? 'http://localhost:3001/api'
    : 'https://mobile.dmlogn8n.com/api',

  WS_URL: __DEV__
    ? 'ws://localhost:3000'
    : 'wss://ws.dmlogn8n.com',

  // Timeouts
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,

  // Endpoints
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/auth/login',
      REGISTER: '/auth/register',
      LOGOUT: '/auth/logout',
      REFRESH: '/auth/refresh',
      VERIFY: '/auth/verify',
      FORGOT_PASSWORD: '/auth/forgot-password',
      RESET_PASSWORD: '/auth/reset-password',
      BIOMETRIC_SETUP: '/auth/biometric/setup',
      BIOMETRIC_VERIFY: '/auth/biometric/verify',
    },

    // User Management
    USER: {
      PROFILE: '/user/profile',
      PREFERENCES: '/user/preferences',
      AVATAR: '/user/avatar',
      STATS: '/user/stats',
      ACHIEVEMENTS: '/user/achievements',
      FRIENDS: '/user/friends',
      FRIEND_REQUESTS: '/user/friends/requests',
      BLOCKED_USERS: '/user/blocked',
    },

    // Characters
    CHARACTERS: {
      LIST: '/characters',
      CREATE: '/characters',
      DETAIL: (id: string) => `/characters/${id}`,
      UPDATE: (id: string) => `/characters/${id}`,
      DELETE: (id: string) => `/characters/${id}`,
      EQUIPMENT: (id: string) => `/characters/${id}/equipment`,
      INVENTORY: (id: string) => `/characters/${id}/inventory`,
      SKILLS: (id: string) => `/characters/${id}/skills`,
      STATS: (id: string) => `/characters/${id}/stats`,
      APPEARANCE: (id: string) => `/characters/${id}/appearance`,
    },

    // Game Sessions
    SESSIONS: {
      LIST: '/sessions',
      CREATE: '/sessions',
      DETAIL: (id: string) => `/sessions/${id}`,
      UPDATE: (id: string) => `/sessions/${id}`,
      DELETE: (id: string) => `/sessions/${id}`,
      JOIN: (id: string) => `/sessions/${id}/join`,
      LEAVE: (id: string) => `/sessions/${id}/leave`,
      START: (id: string) => `/sessions/${id}/start`,
      PAUSE: (id: string) => `/sessions/${id}/pause`,
      RESUME: (id: string) => `/sessions/${id}/resume`,
      END: (id: string) => `/sessions/${id}/end`,
      PLAYERS: (id: string) => `/sessions/${id}/players`,
      SCENES: (id: string) => `/sessions/${id}/scenes`,
      CURRENT_SCENE: (id: string) => `/sessions/${id}/scenes/current`,
    },

    // Chat
    CHAT: {
      CHANNELS: '/chat/channels',
      MESSAGES: (channelId: string) => `/chat/channels/${channelId}/messages`,
      SEND_MESSAGE: (channelId: string) => `/chat/channels/${channelId}/messages`,
      TYPING: (channelId: string) => `/chat/channels/${channelId}/typing`,
      REACTIONS: (messageId: string) => `/chat/messages/${messageId}/reactions`,
    },

    // Notifications
    NOTIFICATIONS: {
      REGISTER: '/notifications/register',
      UNREGISTER: '/notifications/unregister',
      LIST: '/notifications',
      MARK_READ: (id: string) => `/notifications/${id}/read`,
      MARK_ALL_READ: '/notifications/read-all',
      SETTINGS: '/notifications/settings',
    },

    // Items and Equipment
    ITEMS: {
      LIST: '/items',
      DETAIL: (id: string) => `/items/${id}`,
      USE: (id: string) => `/items/${id}/use`,
      EQUIP: (id: string) => `/items/${id}/equip`,
      UNEQUIP: (id: string) => `/items/${id}/unequip`,
      TRADE: '/items/trade',
    },

    // Skills
    SKILLS: {
      LIST: '/skills',
      DETAIL: (id: string) => `/skills/${id}`,
      UPGRADE: (id: string) => `/skills/${id}/upgrade`,
      USE: (id: string) => `/skills/${id}/use`,
    },

    // Achievements
    ACHIEVEMENTS: {
      LIST: '/achievements',
      DETAIL: (id: string) => `/achievements/${id}`,
      PROGRESS: (id: string) => `/achievements/${id}/progress`,
      CLAIM_REWARD: (id: string) => `/achievements/${id}/claim`,
    },

    // Social
    SOCIAL: {
      FRIENDS: '/social/friends',
      FRIEND_REQUEST: '/social/friends/request',
      ACCEPT_REQUEST: (id: string) => `/social/friends/accept/${id}`,
      DECLINE_REQUEST: (id: string) => `/social/friends/decline/${id}`,
      BLOCK_USER: '/social/block',
      UNBLOCK_USER: (id: string) => `/social/unblock/${id}`,
      PROFILE: (userId: string) => `/social/profile/${userId}`,
    },

    // Media
    MEDIA: {
      UPLOAD: '/media/upload',
      AVATAR: '/media/avatar',
      CHARACTER_IMAGE: '/media/character',
      GAME_IMAGE: '/media/game',
    },

    // Analytics
    ANALYTICS: {
      EVENT: '/analytics/event',
      SESSION: '/analytics/session',
      PERFORMANCE: '/analytics/performance',
    },

    // Sync
    SYNC: {
      UPLOAD: '/sync/upload',
      DOWNLOAD: '/sync/download',
      STATUS: '/sync/status',
      CONFLICTS: '/sync/conflicts',
    },
  },

  // WebSocket Events
  WS_EVENTS: {
    CONNECTION: {
      CONNECT: 'connect',
      DISCONNECT: 'disconnect',
      ERROR: 'error',
      RECONNECT: 'reconnect',
    },

    AUTHENTICATION: {
      AUTHENTICATE: 'authenticate',
      AUTHENTICATED: 'authenticated',
      UNAUTHORIZED: 'unauthorized',
    },

    GAME: {
      SESSION_JOIN: 'session:join',
      SESSION_LEAVE: 'session:leave',
      SESSION_UPDATE: 'session:update',
      PLAYER_JOIN: 'player:join',
      PLAYER_LEAVE: 'player:leave',
      PLAYER_READY: 'player:ready',
      SCENE_CHANGE: 'scene:change',
      GAME_START: 'game:start',
      GAME_PAUSE: 'game:pause',
      GAME_END: 'game:end',
      ACTION: 'game:action',
      DICE_ROLL: 'game:dice',
    },

    CHAT: {
      MESSAGE: 'chat:message',
      TYPING: 'chat:typing',
      REACTION: 'chat:reaction',
      CHANNEL_JOIN: 'chat:channel:join',
      CHANNEL_LEAVE: 'chat:channel:leave',
    },

    NOTIFICATIONS: {
      PUSH: 'notification:push',
      READ: 'notification:read',
    },

    SYNC: {
      START: 'sync:start',
      PROGRESS: 'sync:progress',
      COMPLETE: 'sync:complete',
      ERROR: 'sync:error',
    },
  },

  // Error Codes
  ERROR_CODES: {
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
    AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
    AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    NOT_FOUND_ERROR: 'NOT_FOUND_ERROR',
    CONFLICT_ERROR: 'CONFLICT_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    OFFLINE_ERROR: 'OFFLINE_ERROR',
    SYNC_ERROR: 'SYNC_ERROR',
    BIOMETRIC_ERROR: 'BIOMETRIC_ERROR',
    PERMISSION_ERROR: 'PERMISSION_ERROR',
  },

  // HTTP Status Codes
  HTTP_STATUS: {
    OK: 200,
    CREATED: 201,
    ACCEPTED: 202,
    NO_CONTENT: 204,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    CONFLICT: 409,
    UNPROCESSABLE_ENTITY: 422,
    TOO_MANY_REQUESTS: 429,
    INTERNAL_SERVER_ERROR: 500,
    BAD_GATEWAY: 502,
    SERVICE_UNAVAILABLE: 503,
    GATEWAY_TIMEOUT: 504,
  },

  // Cache Keys
  CACHE_KEYS: {
    USER_PROFILE: 'user_profile',
    CHARACTERS: 'characters',
    GAME_SESSIONS: 'game_sessions',
    FRIENDS: 'friends',
    CHAT_CHANNELS: 'chat_channels',
    NOTIFICATIONS: 'notifications',
    ACHIEVEMENTS: 'achievements',
    OFFLINE_DATA: 'offline_data',
    BIOMETRIC_TOKEN: 'biometric_token',
    AUTH_TOKEN: 'auth_token',
    REFRESH_TOKEN: 'refresh_token',
  },

  // Local Storage Keys
  STORAGE_KEYS: {
    USER_PREFERENCES: '@user_preferences',
    OFFLINE_QUEUE: '@offline_queue',
    LAST_SYNC: '@last_sync',
    APP_VERSION: '@app_version',
    DEVICE_ID: '@device_id',
    PUSH_TOKEN: '@push_token',
    BIOMETRIC_ENABLED: '@biometric_enabled',
    THEME: '@theme',
    LANGUAGE: '@language',
  },

  // File Upload Limits
  UPLOAD_LIMITS: {
    AVATAR_MAX_SIZE: 5 * 1024 * 1024, // 5MB
    IMAGE_MAX_SIZE: 10 * 1024 * 1024, // 10MB
    AUDIO_MAX_SIZE: 20 * 1024 * 1024, // 20MB
    DOCUMENT_MAX_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    ALLOWED_AUDIO_TYPES: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a'],
    ALLOWED_DOCUMENT_TYPES: ['application/pdf', 'text/plain', 'application/json'],
  },

  // Rate Limiting
  RATE_LIMITS: {
    API_REQUESTS_PER_MINUTE: 60,
    MESSAGE_SEND_PER_MINUTE: 30,
    LOGIN_ATTEMPTS_PER_HOUR: 5,
    PASSWORD_RESET_PER_HOUR: 3,
    FILE_UPLOAD_PER_HOUR: 10,
  },

  // Pagination
  PAGINATION: {
    DEFAULT_PAGE_SIZE: 20,
    MAX_PAGE_SIZE: 100,
    MESSAGE_PAGE_SIZE: 50,
    SEARCH_PAGE_SIZE: 25,
  },
};

export default API_CONFIG;