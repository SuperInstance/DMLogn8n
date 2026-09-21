import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AppSettings } from '../../types';

interface SettingsState {
  settings: AppSettings | null;
  isLoading: boolean;
  error: string | null;
}

const defaultSettings: AppSettings = {
  userId: '',
  theme: 'dark',
  notifications: {
    combatTurns: true,
    dmMessages: true,
    partyInvites: true,
    achievements: true,
    scriptDeployments: true,
  },
  privacy: {
    locationSharing: false,
    cameraAccess: true,
    biometricAuth: false,
  },
  gameplay: {
    autoRollDice: false,
    hapticFeedback: true,
    shakeToRoll: true,
    soundEffects: true,
  },
  sync: {
    wifiOnly: false,
    backgroundSync: true,
    autoBackup: true,
  },
};

const initialState: SettingsState = {
  settings: defaultSettings,
  isLoading: false,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setSettings: (state, action: PayloadAction<AppSettings>) => {
      state.settings = action.payload;
    },
    updateSettings: (state, action: PayloadAction<Partial<AppSettings>>) => {
      if (state.settings) {
        state.settings = { ...state.settings, ...action.payload };
      }
    },
    updateNotificationSettings: (state, action: PayloadAction<Partial<AppSettings['notifications']>>) => {
      if (state.settings) {
        state.settings.notifications = { ...state.settings.notifications, ...action.payload };
      }
    },
    updatePrivacySettings: (state, action: PayloadAction<Partial<AppSettings['privacy']>>) => {
      if (state.settings) {
        state.settings.privacy = { ...state.settings.privacy, ...action.payload };
      }
    },
    updateGameplaySettings: (state, action: PayloadAction<Partial<AppSettings['gameplay']>>) => {
      if (state.settings) {
        state.settings.gameplay = { ...state.settings.gameplay, ...action.payload };
      }
    },
    updateSyncSettings: (state, action: PayloadAction<Partial<AppSettings['sync']>>) => {
      if (state.settings) {
        state.settings.sync = { ...state.settings.sync, ...action.payload };
      }
    },
    setUserId: (state, action: PayloadAction<string>) => {
      if (state.settings) {
        state.settings.userId = action.payload;
      }
    },
    resetSettings: (state) => {
      state.settings = defaultSettings;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setSettings,
  updateSettings,
  updateNotificationSettings,
  updatePrivacySettings,
  updateGameplaySettings,
  updateSyncSettings,
  setUserId,
  resetSettings,
  clearError,
} = settingsSlice.actions;

export default settingsSlice.reducer;