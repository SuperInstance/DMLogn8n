import React, { createContext, useContext, useState, useEffect } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { locationService } from '../services/locationService';
import { Location } from '../types';

interface LocationContextType {
  currentLocation: Location | null;
  isTracking: boolean;
  hasPermission: boolean;
  error: string | null;
  requestPermission: () => Promise<boolean>;
  getCurrentLocation: () => Promise<Location | null>;
  startTracking: (callback: (location: Location) => void) => Promise<boolean>;
  stopTracking: () => void;
  clearError: () => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

interface LocationProviderProps {
  children: React.ReactNode;
}

export const LocationProvider: React.FC<LocationProviderProps> = ({ children }) => {
  const [currentLocation, setCurrentLocation] = useState<Location | null>(null);
  const [isTracking, setIsTracking] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Clean up tracking when app state changes
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (nextAppState === 'background' || nextAppState === 'inactive') {
        stopTracking();
      }
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => subscription.remove();
  }, []);

  const requestPermission = async (): Promise<boolean> => {
    try {
      setError(null);
      const granted = await locationService.requestLocationPermission();
      setHasPermission(granted);
      return granted;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to request location permission';
      setError(errorMessage);
      return false;
    }
  };

  const getCurrentLocation = async (): Promise<Location | null> => {
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) {
        return null;
      }
    }

    try {
      setError(null);
      const location = await locationService.getCurrentLocation();
      setCurrentLocation(location);
      return location;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get current location';
      setError(errorMessage);
      return null;
    }
  };

  const startTracking = async (callback: (location: Location) => void): Promise<boolean> => {
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) {
        return false;
      }
    }

    try {
      setError(null);
      const success = await locationService.startLocationTracking((location) => {
        setCurrentLocation(location);
        callback(location);
      });

      if (success) {
        setIsTracking(true);
      }
      return success;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start location tracking';
      setError(errorMessage);
      return false;
    }
  };

  const stopTracking = (): void => {
    locationService.stopLocationTracking();
    setIsTracking(false);
  };

  const clearError = (): void => {
    setError(null);
  };

  return (
    <LocationContext.Provider
      value={{
        currentLocation,
        isTracking,
        hasPermission,
        error,
        requestPermission,
        getCurrentLocation,
        startTracking,
        stopTracking,
        clearError,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
};

export const useLocation = () => {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocation must be used within a LocationProvider');
  }
  return context;
};