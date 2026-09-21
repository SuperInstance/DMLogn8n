import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check authentication status
  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get('/api/auth/me');
      if (response.data.success) {
        setUser(response.data.data);
        setIsAuthenticated(true);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  }, []);

  // Login
  const login = async (email, password) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/auth/login', { email, password });

      if (response.data.success) {
        const { token: newToken, user: userData } = response.data.data;

        setToken(newToken);
        setUser(userData);
        setIsAuthenticated(true);

        localStorage.setItem('token', newToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

        toast.success(`Welcome back, ${userData.name}!`);
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Login failed');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Login failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Register
  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/auth/register', userData);

      if (response.data.success) {
        const { token: newToken, user: newUser } = response.data.data;

        setToken(newToken);
        setUser(newUser);
        setIsAuthenticated(true);

        localStorage.setItem('token', newToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

        toast.success(`Welcome to DM World Builder, ${newUser.name}!`);
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Registration failed');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Registration failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Logout
  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);

    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];

    toast.success('Logged out successfully');
  }, []);

  // Update user profile
  const updateProfile = async (profileData) => {
    try {
      setLoading(true);
      const response = await axios.put('/api/auth/profile', profileData);

      if (response.data.success) {
        setUser(response.data.data);
        toast.success('Profile updated successfully');
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Profile update failed');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Profile update failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Change password
  const changePassword = async (currentPassword, newPassword) => {
    try {
      setLoading(true);
      const response = await axios.put('/api/auth/change-password', {
        currentPassword,
        newPassword
      });

      if (response.data.success) {
        toast.success('Password changed successfully');
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Password change failed');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Password change failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  // Request password reset
  const requestPasswordReset = async (email) => {
    try {
      const response = await axios.post('/api/auth/forgot-password', { email });

      if (response.data.success) {
        toast.success('Password reset email sent');
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Failed to send reset email');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to send reset email';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Reset password
  const resetPassword = async (token, newPassword) => {
    try {
      const response = await axios.post('/api/auth/reset-password', {
        token,
        newPassword
      });

      if (response.data.success) {
        toast.success('Password reset successful');
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Password reset failed');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Password reset failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Refresh token
  const refreshToken = async () => {
    try {
      const response = await axios.post('/api/auth/refresh');

      if (response.data.success) {
        const { token: newToken } = response.data.data;
        setToken(newToken);
        localStorage.setItem('token', newToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
        return { success: true };
      } else {
        logout();
        return { success: false };
      }
    } catch (error) {
      logout();
      return { success: false };
    }
  };

  // Check auth on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Setup token refresh interval
  useEffect(() => {
    if (isAuthenticated && token) {
      const refreshInterval = setInterval(async () => {
        const result = await refreshToken();
        if (!result.success) {
          console.log('Token refresh failed, logging out');
        }
      }, 50 * 60 * 1000); // Refresh every 50 minutes

      return () => clearInterval(refreshInterval);
    }
  }, [isAuthenticated, token]);

  // Axios response interceptor for token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const result = await refreshToken();
            if (result.success) {
              return axios(originalRequest);
            }
          } catch (refreshError) {
            logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [logout]);

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    refreshToken,
    checkAuth
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};