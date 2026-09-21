import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';

import authSlice from './slices/authSlice';
import characterSlice from './slices/characterSlice';
import campaignSlice from './slices/campaignSlice';
import combatSlice from './slices/combatSlice';
import messageSlice from './slices/messageSlice';
import notificationSlice from './slices/notificationSlice';
import settingsSlice from './slices/settingsSlice';
import offlineSlice from './slices/offlineSlice';
import uiSlice from './slices/uiSlice';

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'characters', 'campaigns', 'settings', 'offline'],
  blacklist: ['ui'],
};

const rootReducer = combineReducers({
  auth: authSlice,
  characters: characterSlice,
  campaigns: campaignSlice,
  combat: combatSlice,
  messages: messageSlice,
  notifications: notificationSlice,
  settings: settingsSlice,
  offline: offlineSlice,
  ui: uiSlice,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }),
  devTools: __DEV__,
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;