import { launchImageLibrary, launchCamera, MediaType, ImagePickerResponse, ImagePickerAsset } from 'react-native-image-picker';
import { Alert, Platform, PermissionsAndroid } from 'react-native';

interface CameraOptions {
  mediaType: MediaType;
  quality: number;
  maxWidth?: number;
  maxHeight?: number;
  includeBase64?: boolean;
  includeExtra?: boolean;
}

class CameraService {
  private defaultOptions: CameraOptions = {
    mediaType: 'photo',
    quality: 0.8,
    maxWidth: 1024,
    maxHeight: 1024,
    includeBase64: false,
    includeExtra: true,
  };

  async requestCameraPermission(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      return true; // iOS handles permission through launchCamera
    }

    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.CAMERA,
        {
          title: 'Camera Permission',
          message: 'DMlogn8n needs access to your camera to take character photos.',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        },
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } catch (error) {
      console.error('Camera permission error:', error);
      return false;
    }
  }

  async requestStoragePermission(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      return true; // iOS handles storage permissions differently
    }

    try {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
        {
          title: 'Storage Permission',
          message: 'DMlogn8n needs access to your storage to save photos.',
          buttonNeutral: 'Ask Me Later',
          buttonNegative: 'Cancel',
          buttonPositive: 'OK',
        },
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    } catch (error) {
      console.error('Storage permission error:', error);
      return false;
    }
  }

  async takePhoto(options?: Partial<CameraOptions>): Promise<string | null> {
    try {
      const hasPermission = await this.requestCameraPermission();
      if (!hasPermission) {
        Alert.alert('Permission Denied', 'Camera permission is required to take photos.');
        return null;
      }

      const photoOptions = { ...this.defaultOptions, ...options };

      return new Promise((resolve) => {
        launchCamera(photoOptions, (response: ImagePickerResponse) => {
          if (response.didCancel || response.errorMessage) {
            resolve(null);
            return;
          }

          const asset = response.assets?.[0];
          if (asset?.uri) {
            resolve(asset.uri);
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error('Take photo error:', error);
      return null;
    }
  }

  async selectFromLibrary(options?: Partial<CameraOptions>): Promise<string | null> {
    try {
      const photoOptions = { ...this.defaultOptions, ...options };

      return new Promise((resolve) => {
        launchImageLibrary(photoOptions, (response: ImagePickerResponse) => {
          if (response.didCancel || response.errorMessage) {
            resolve(null);
            return;
          }

          const asset = response.assets?.[0];
          if (asset?.uri) {
            resolve(asset.uri);
          } else {
            resolve(null);
          }
        });
      });
    } catch (error) {
      console.error('Select from library error:', error);
      return null;
    }
  }

  async takeCharacterSelfie(): Promise<string | null> {
    return this.takePhoto({
      quality: 0.9,
      maxWidth: 512,
      maxHeight: 512,
      mediaType: 'photo',
    });
  }

  async uploadCharacterAvatar(characterId: string, imageUri: string): Promise<string> {
    try {
      const formData = new FormData();

      // Get file info from URI
      const uriParts = imageUri.split('.');
      const fileType = uriParts[uriParts.length - 1];

      formData.append('avatar', {
        uri: imageUri,
        name: `character_${characterId}_avatar.${fileType}`,
        type: `image/${fileType}`,
      } as any);

      formData.append('characterId', characterId);

      const response = await fetch(`${API_BASE_URL}/characters/upload-avatar`, {
        method: 'POST',
        body: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to upload avatar');
      }

      const data = await response.json();
      return data.avatarUrl;
    } catch (error) {
      console.error('Upload avatar error:', error);
      throw error;
    }
  }

  async compressImage(imageUri: string, quality: number = 0.8): Promise<string> {
    // This would typically use a library like react-native-image-resizer
    // For now, return the original URI
    return imageUri;
  }

  async getImageDimensions(imageUri: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve, reject) => {
      Image.getSize(
        imageUri,
        (width, height) => resolve({ width, height }),
        (error) => reject(error),
      );
    });
  }

  showImagePicker(options?: {
    title?: string;
    message?: string;
    allowCamera?: boolean;
    allowLibrary?: boolean;
  }): Promise<string | null> {
    return new Promise((resolve) => {
      const buttons = [];

      if (options?.allowCamera !== false) {
        buttons.push({
          text: 'Take Photo',
          onPress: async () => {
            const photo = await this.takePhoto();
            resolve(photo);
          },
        });
      }

      if (options?.allowLibrary !== false) {
        buttons.push({
          text: 'Choose from Library',
          onPress: async () => {
            const photo = await this.selectFromLibrary();
            resolve(photo);
          },
        });
      }

      buttons.push({
        text: 'Cancel',
        style: 'cancel',
        onPress: () => resolve(null),
      });

      Alert.alert(
        options?.title || 'Select Photo',
        options?.message || 'Choose a photo for your character avatar',
        buttons,
      );
    });
  }
}

export const cameraService = new CameraService();