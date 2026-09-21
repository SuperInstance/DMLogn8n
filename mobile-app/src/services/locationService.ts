import Geolocation from '@react-native-community/geolocation';
import { Alert, PermissionsAndroid, Platform } from 'react-native';
import { Location } from '../types';
import { store } from '../store';

interface LocationOptions {
  enableHighAccuracy: boolean;
  timeout: number;
  maximumAge: number;
}

class LocationService {
  private watchId: number | null = null;
  private defaultOptions: LocationOptions = {
    enableHighAccuracy: true,
    timeout: 20000,
    maximumAge: 1000,
  };

  async requestLocationPermission(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      return true; // iOS handles location permissions through Geolocation
    }

    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
        {
          title: 'Location Permission',
          message: 'DMlogn8n needs access to your location for location-based campaigns.',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        },
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } catch (error) {
      console.error('Location permission error:', error);
      return false;
    }
  }

  async getCurrentLocation(options?: Partial<LocationOptions>): Promise<Location | null> {
    try {
      const hasPermission = await this.requestLocationPermission();
      if (!hasPermission) {
        Alert.alert(
          'Location Permission Required',
          'Please enable location access to use location-based features.',
        );
        return null;
      }

      const locationOptions = { ...this.defaultOptions, ...options };

      return new Promise((resolve, reject) => {
        Geolocation.getCurrentPosition(
          (position) => {
            const location: Location = {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy || 0,
              timestamp: new Date(position.timestamp).toISOString(),
            };
            resolve(location);
          },
          (error) => {
            console.error('Get location error:', error);
            let errorMessage = 'Failed to get location';

            switch (error.code) {
              case 1:
                errorMessage = 'Location permission denied';
                break;
              case 2:
                errorMessage = 'Location unavailable';
                break;
              case 3:
                errorMessage = 'Location request timeout';
                break;
            }

            Alert.alert('Location Error', errorMessage);
            resolve(null);
          },
          locationOptions,
        );
      });
    } catch (error) {
      console.error('Get current location error:', error);
      return null;
    }
  }

  async startLocationTracking(callback: (location: Location) => void, options?: Partial<LocationOptions>): Promise<boolean> {
    try {
      const hasPermission = await this.requestLocationPermission();
      if (!hasPermission) {
        return false;
      }

      const locationOptions = { ...this.defaultOptions, ...options };

      this.watchId = Geolocation.watchPosition(
        (position) => {
          const location: Location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy || 0,
            timestamp: new Date(position.timestamp).toISOString(),
          };
          callback(location);
        },
        (error) => {
          console.error('Location tracking error:', error);
        },
        locationOptions,
      );

      return true;
    } catch (error) {
      console.error('Start location tracking error:', error);
      return false;
    }
  }

  stopLocationTracking(): void {
    if (this.watchId !== null) {
      Geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  async checkLocationBasedCampaigns(location: Location): Promise<any[]> {
    try {
      const state = store.getState();
      const campaigns = state.campaigns.campaigns;

      // Filter campaigns that have location requirements
      const locationBasedCampaigns = campaigns.filter(campaign => {
        // This would be enhanced with actual location-based logic
        // For now, just return campaigns that might be location-based
        return campaign.location && campaign.location.length > 0;
      });

      // Here you would typically check if the user's location is within
      // the campaign's defined area (geofencing)
      return locationBasedCampaigns;
    } catch (error) {
      console.error('Check location-based campaigns error:', error);
      return [];
    }
  }

  async updateLocationForCampaign(campaignId: string, location: Location): Promise<void> {
    try {
      const state = store.getState();
      const accessToken = state.auth.user?.accessToken;

      if (!accessToken) return;

      await fetch(`${API_BASE_URL}/campaigns/${campaignId}/location`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          timestamp: location.timestamp,
        }),
      });
    } catch (error) {
      console.error('Update location for campaign error:', error);
    }
  }

  calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // Earth's radius in kilometers
    const dLat = this.toRadians(lat2 - lat1);
    const dLon = this.toRadians(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c * 1000; // Distance in meters
  }

  private toRadians(degrees: number): number {
    return degrees * (Math.PI / 180);
  }

  async isLocationEnabled(): Promise<boolean> {
    return new Promise((resolve) => {
      Geolocation.requestAuthorization(() => {
        resolve(true);
      });
    });
  }

  async openLocationSettings(): Promise<void> {
    // This would typically open the device location settings
    // Implementation would vary by platform
    if (Platform.OS === 'android') {
      // Use Linking to open Android location settings
      // Linking.openSettings();
    } else {
      // Use Linking to open iOS location settings
      // Linking.openURL('app-settings:');
    }
  }

  cleanup(): void {
    this.stopLocationTracking();
  }
}

export const locationService = new LocationService();