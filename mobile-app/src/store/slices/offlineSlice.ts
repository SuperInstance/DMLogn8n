import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { OfflineAction } from '../../types';
import { offlineService } from '../../services/offlineService';

interface OfflineState {
  actions: OfflineAction[];
  isConnected: boolean;
  isSyncing: boolean;
  lastSyncTime: string | null;
  syncError: string | null;
  pendingActionsCount: number;
}

const initialState: OfflineState = {
  actions: [],
  isConnected: true,
  isSyncing: false,
  lastSyncTime: null,
  syncError: null,
  pendingActionsCount: 0,
};

export const syncOfflineActions = createAsyncThunk(
  'offline/sync',
  async (_, { rejectWithValue }) => {
    try {
      const result = await offlineService.syncActions();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Sync failed');
    }
  },
);

export const addOfflineAction = createAsyncThunk(
  'offline/addAction',
  async (action: Omit<OfflineAction, 'id' | 'timestamp' | 'isSynced' | 'retryCount'>, { rejectWithValue }) => {
    try {
      const offlineAction = await offlineService.addAction(action);
      return offlineAction;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add offline action');
    }
  },
);

export const retryFailedAction = createAsyncThunk(
  'offline/retryAction',
  async (actionId: string, { rejectWithValue }) => {
    try {
      const result = await offlineService.retryAction(actionId);
      return { actionId, result };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Retry failed');
    }
  },
);

export const clearSyncedActions = createAsyncThunk(
  'offline/clearSynced',
  async (_, { rejectWithValue }) => {
    try {
      await offlineService.clearSyncedActions();
      return;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to clear synced actions');
    }
  },
);

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setConnectionStatus: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    setSyncing: (state, action: PayloadAction<boolean>) => {
      state.isSyncing = action.payload;
    },
    setLastSyncTime: (state, action: PayloadAction<string>) => {
      state.lastSyncTime = action.payload;
    },
    setSyncError: (state, action: PayloadAction<string | null>) => {
      state.syncError = action.payload;
    },
    removeAction: (state, action: PayloadAction<string>) => {
      state.actions = state.actions.filter(a => a.id !== action.payload);
    },
    clearSyncError: (state) => {
      state.syncError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Sync Actions
      .addCase(syncOfflineActions.pending, (state) => {
        state.isSyncing = true;
        state.syncError = null;
      })
      .addCase(syncOfflineActions.fulfilled, (state, action) => {
        state.isSyncing = false;
        state.lastSyncTime = new Date().toISOString();
        state.actions = action.payload.pendingActions;
        state.pendingActionsCount = action.payload.pendingActions.length;
        state.syncError = null;
      })
      .addCase(syncOfflineActions.rejected, (state, action) => {
        state.isSyncing = false;
        state.syncError = action.payload as string;
      })
      // Add Offline Action
      .addCase(addOfflineAction.fulfilled, (state, action) => {
        state.actions.push(action.payload);
        if (!action.payload.isSynced) {
          state.pendingActionsCount += 1;
        }
      })
      // Retry Failed Action
      .addCase(retryFailedAction.fulfilled, (state, action) => {
        const { actionId, result } = action.payload;
        const action = state.actions.find(a => a.id === actionId);
        if (action) {
          if (result.success) {
            action.isSynced = true;
            state.pendingActionsCount = Math.max(0, state.pendingActionsCount - 1);
          } else {
            action.retryCount += 1;
          }
        }
      })
      // Clear Synced Actions
      .addCase(clearSyncedActions.fulfilled, (state) => {
        state.actions = state.actions.filter(action => !action.isSynced);
      });
  },
});

export const {
  setConnectionStatus,
  setSyncing,
  setLastSyncTime,
  setSyncError,
  removeAction,
  clearSyncError,
} = offlineSlice.actions;

export default offlineSlice.reducer;