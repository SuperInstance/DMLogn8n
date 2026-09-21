import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { combineReducers } from '@reduxjs/toolkit';

// Import slices
import appSlice from './slices/appSlice';
import authSlice from './slices/authSlice';
import campaignSlice from './slices/campaignSlice';
import characterSlice from './slices/characterSlice';
import sessionSlice from './slices/sessionSlice';
import diceSlice from './slices/diceSlice';
import voiceSlice from './slices/voiceSlice';
import arSlice from './slices/arSlice';
import notificationSlice from './slices/notificationSlice';
import syncSlice from './slices/syncSlice';

// Persist configuration
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'campaign', 'character', 'app'], // Only persist these slices
  blacklist: ['session', 'dice', 'voice', 'ar', 'notification', 'sync'], // Don't persist these
};

// Root reducer
const rootReducer = combineReducers({
  app: appSlice,
  auth: authSlice,
  campaign: campaignSlice,
  character: characterSlice,
  session: sessionSlice,
  dice: diceSlice,
  voice: voiceSlice,
  ar: arSlice,
  notification: notificationSlice,
  sync: syncSlice,
});

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/PAUSE',
          'persist/PURGE',
          'persist/REGISTER',
        ],
      },
    }),
  devTools: __DEV__,
});

// Create persistor
export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;