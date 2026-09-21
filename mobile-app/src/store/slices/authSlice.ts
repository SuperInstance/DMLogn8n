import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { User, APIResponse } from '../../types';
import { authService } from '../../services/authService';
import { storageService } from '../../services/storageService';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  isBiometricEnabled: boolean;
  loginAttempts: number;
  lastLoginAttempt: number | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  isLoading: false,
  error: null,
  isBiometricEnabled: false,
  loginAttempts: 0,
  lastLoginAttempt: null,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (
    credentials: { email: string; password: string; rememberMe?: boolean },
    { rejectWithValue }
  ) => {
    try {
      const response = await authService.login(credentials);

      if (response.success && response.data) {
        // Store credentials securely
        await storageService.storeAuthToken(response.data.token);
        if (credentials.rememberMe) {
          await storageService.storeUserData(response.data.user);
        }

        return response.data;
      } else {
        throw new Error(response.error || 'Login failed');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Login failed');
    }
  }
);

export const loginWithBiometric = createAsyncThunk(
  'auth/loginWithBiometric',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authService.authenticateWithBiometric();

      if (response.success && response.data) {
        await storageService.storeAuthToken(response.data.token);
        await storageService.storeUserData(response.data.user);

        return response.data;
      } else {
        throw new Error(response.error || 'Biometric authentication failed');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Biometric authentication failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    userData: {
      username: string;
      email: string;
      password: string;
      displayName: string;
    },
    { rejectWithValue }
  ) => {
    try {
      const response = await authService.register(userData);

      if (response.success && response.data) {
        await storageService.storeAuthToken(response.data.token);
        await storageService.storeUserData(response.data.user);

        return response.data;
      } else {
        throw new Error(response.error || 'Registration failed');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Registration failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      await storageService.clearAuthData();
      return true;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Logout failed');
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue, getState }) => {
    try {
      const state = getState() as { auth: AuthState };
      const currentToken = state.auth.token;

      if (!currentToken) {
        throw new Error('No token to refresh');
      }

      const response = await authService.refreshToken(currentToken);

      if (response.success && response.data) {
        await storageService.storeAuthToken(response.data.token);
        return response.data;
      } else {
        throw new Error(response.error || 'Token refresh failed');
      }
    } catch (error) {
      // If refresh fails, clear auth data
      await storageService.clearAuthData();
      return rejectWithValue(error instanceof Error ? error.message : 'Token refresh failed');
    }
  }
);

export const enableBiometric = createAsyncThunk(
  'auth/enableBiometric',
  async (credentials: { userId: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authService.enableBiometric(credentials);

      if (response.success) {
        await storageService.setBiometricEnabled(true);
        return true;
      } else {
        throw new Error(response.error || 'Failed to enable biometric authentication');
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to enable biometric authentication');
    }
  }
);

export const disableBiometric = createAsyncThunk(
  'auth/disableBiometric',
  async (_, { rejectWithValue }) => {
    try {
      await authService.disableBiometric();
      await storageService.setBiometricEnabled(false);
      return false;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to disable biometric authentication');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },

    resetLoginAttempts: (state) => {
      state.loginAttempts = 0;
      state.lastLoginAttempt = null;
    },

    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },

    setToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
    },

    restoreAuth: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.loginAttempts = 0;
        state.lastLoginAttempt = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.loginAttempts += 1;
        state.lastLoginAttempt = Date.now();
      })

      // Biometric login
      .addCase(loginWithBiometric.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithBiometric.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.loginAttempts = 0;
      })
      .addCase(loginWithBiometric.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Register
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })

      // Logout
      .addCase(logout.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(logout.fulfilled, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.isBiometricEnabled = false;
      })
      .addCase(logout.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        // Still clear auth data on failed logout attempt
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
      })

      // Refresh token
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.token;
        if (action.payload.user) {
          state.user = action.payload.user;
        }
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.error = action.payload as string;
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
      })

      // Enable biometric
      .addCase(enableBiometric.fulfilled, (state) => {
        state.isBiometricEnabled = true;
      })
      .addCase(enableBiometric.rejected, (state, action) => {
        state.error = action.payload as string;
      })

      // Disable biometric
      .addCase(disableBiometric.fulfilled, (state) => {
        state.isBiometricEnabled = false;
      })
      .addCase(disableBiometric.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  clearError,
  resetLoginAttempts,
  updateUser,
  setToken,
  restoreAuth,
} = authSlice.actions;

export default authSlice.reducer;