import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AppState, User } from '../../types';
import { storageService } from '../../services/storageService';
import { syncService } from '../../services/syncService';

interface AppStateType extends AppState {
  permissions: {
    camera: boolean;
    microphone: boolean;
    location: boolean;
    notifications: boolean;
  };
  deviceInfo: {
    platform: string;
    version: string;
    model: string;
    isTablet: boolean;
  };
}

const initialState: AppStateType = {
  isLoading: false,
  isInitialized: false,
  isOnline: true,
  currentUser: null,
  activeCampaign: null,
  activeSession: null,
  error: null,
  syncStatus: 'synced',
  permissions: {
    camera: false,
    microphone: false,
    location: false,
    notifications: false,
  },
  deviceInfo: {
    platform: '',
    version: '',
    model: '',
    isTablet: false,
  },
};

// Async thunks
export const initializeApp = createAsyncThunk(
  'app/initialize',
  async (_, { rejectWithValue }) => {
    try {
      // Initialize storage
      await storageService.initialize();

      // Initialize sync service
      await syncService.initialize();

      // Load stored user data
      const userData = await storageService.getUserData();

      // Check network status
      const isOnline = await syncService.checkConnectivity();

      return {
        user: userData,
        isOnline,
      };
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to initialize app');
    }
  }
);

export const checkNetworkStatus = createAsyncThunk(
  'app/checkNetworkStatus',
  async (_, { rejectWithValue }) => {
    try {
      const isOnline = await syncService.checkConnectivity();
      return isOnline;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to check network status');
    }
  }
);

export const requestPermissions = createAsyncThunk(
  'app/requestPermissions',
  async (permissions: string[], { rejectWithValue }) => {
    try {
      // This would integrate with expo-permissions
      // For now, simulate permission requests
      const grantedPermissions: { [key: string]: boolean } = {};

      for (const permission of permissions) {
        // Simulate permission grant (in real app, use expo-permissions)
        grantedPermissions[permission] = true;
      }

      return grantedPermissions;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to request permissions');
    }
  }
);

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },

    clearError: (state) => {
      state.error = null;
    },

    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
      if (action.payload) {
        state.syncStatus = 'synced';
      }
    },

    setSyncStatus: (state, action: PayloadAction<'synced' | 'syncing' | 'offline' | 'error'>) => {
      state.syncStatus = action.payload;
    },

    setActiveCampaign: (state, action: PayloadAction<any>) => {
      state.activeCampaign = action.payload;
    },

    setActiveSession: (state, action: PayloadAction<any>) => {
      state.activeSession = action.payload;
    },

    updateDeviceInfo: (state, action: PayloadAction<Partial<AppStateType['deviceInfo']>>) => {
      state.deviceInfo = { ...state.deviceInfo, ...action.payload };
    },

    updatePermissions: (state, action: PayloadAction<Partial<AppStateType['permissions']>>) => {
      state.permissions = { ...state.permissions, ...action.payload };
    },

    logout: (state) => {
      state.currentUser = null;
      state.activeCampaign = null;
      state.activeSession = null;
      state.syncStatus = 'synced';
    },
  },
  extraReducers: (builder) => {
    builder
      // Initialize app
      .addCase(initializeApp.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(initializeApp.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isInitialized = true;
        state.currentUser = action.payload.user;
        state.isOnline = action.payload.isOnline;
      })
      .addCase(initializeApp.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isInitialized = true; // Still mark as initialized to show the app
      })

      // Check network status
      .addCase(checkNetworkStatus.fulfilled, (state, action) => {
        state.isOnline = action.payload;
        if (action.payload) {
          state.syncStatus = 'synced';
        } else {
          state.syncStatus = 'offline';
        }
      })
      .addCase(checkNetworkStatus.rejected, (state) => {
        state.isOnline = false;
        state.syncStatus = 'offline';
      })

      // Request permissions
      .addCase(requestPermissions.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(requestPermissions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.permissions = { ...state.permissions, ...action.payload };
      })
      .addCase(requestPermissions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  setLoading,
  setError,
  clearError,
  setOnlineStatus,
  setSyncStatus,
  setActiveCampaign,
  setActiveSession,
  updateDeviceInfo,
  updatePermissions,
  logout,
} = appSlice.actions;

export default appSlice.reducer;