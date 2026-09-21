import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
  Animated,
  Vibration,
} from 'react-native';
import { Camera } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import {
  Card,
  Button,
  Icon,
  Chip,
  Badge,
  Slider,
} from '@rneui/themed';
import { useAppSelector } from '../../store/hooks';
import { colors, spacing } from '../../theme/theme';
import { HapticsService } from '../../services/hapticsService';
import { AudioService } from '../../services/audioService';
import { ARService, ARMarker, ARDetectionResult } from '../../services/arService';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface ARScannerScreenProps {
  // Props would include session ID, campaign context, etc.
}

const ARScannerScreen: React.FC<ARScannerScreenProps> = () => {
  const cameraRef = useRef<Camera>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [detectedMarkers, setDetectedMarkers] = useState<ARDetectionResult[]>([]);
  const [selectedMarker, setSelectedMarker] = useState<ARMarker | null>(null);
  const [arMode, setArMode] = useState<'scan' | 'place' | 'view'>('scan');
  const [zoom, setZoom] = useState(1.0);
  const [flashEnabled, setFlashEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  // Animation values
  const scanLineAnimation = useRef(new Animated.Value(0)).current;
  const markerHighlightAnimation = useRef(new Animated.Value(1)).current;

  const { activeCampaign } = useAppSelector(state => state.campaign);

  useEffect(() => {
    requestCameraPermission();
    startScanLineAnimation();

    return () => {
      stopScanLineAnimation();
    };
  }, []);

  const requestCameraPermission = async () => {
    const { status } = await Camera.requestCameraPermissionsAsync();
    setHasPermission(status === 'granted');
  };

  const startScanLineAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(scanLineAnimation, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(scanLineAnimation, {
          toValue: 0,
          duration: 0,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const stopScanLineAnimation = () => {
    scanLineAnimation.stopAnimation();
  };

  const startScanning = async () => {
    if (!hasPermission) {
      Alert.alert('Permission Required', 'Camera permission is required for AR features.');
      return;
    }

    setIsScanning(true);
    HapticsService.impactMedium();
    AudioService.playSound('scan_start');

    // Simulate AR scanning
    setTimeout(() => {
      performARScan();
    }, 1000);
  };

  const stopScanning = () => {
    setIsScanning(false);
    HapticsService.impactLight();
    stopScanLineAnimation();
  };

  const performARScan = async () => {
    try {
      // Simulate AR detection
      const mockMarkers: ARDetectionResult[] = [
        {
          marker: {
            id: 'marker_001',
            name: 'Dragon Miniature',
            type: 'miniature',
            model: 'dragon',
            position: { x: 0.5, y: 0.3, z: 0 },
            rotation: { x: 0, y: 45, z: 0 },
            scale: 1.0,
            size: { width: 50, height: 80, depth: 50 },
          },
          confidence: 0.95,
          boundingBox: {
            x: screenWidth * 0.4,
            y: screenHeight * 0.2,
            width: 100,
            height: 160,
          },
        },
        {
          marker: {
            id: 'marker_002',
            name: 'Treasure Chest',
            type: 'prop',
            model: 'chest',
            position: { x: 0.7, y: 0.5, z: 0.2 },
            rotation: { x: 0, y: 0, z: 0 },
            scale: 0.8,
            size: { width: 40, height: 30, depth: 40 },
          },
          confidence: 0.87,
          boundingBox: {
            x: screenWidth * 0.6,
            y: screenHeight * 0.4,
            width: 80,
            height: 60,
          },
        },
      ];

      setDetectedMarkers(mockMarkers);

      if (mockMarkers.length > 0) {
        HapticsService.notificationSuccess();
        AudioService.playSound('detection_complete');
        animateMarkerHighlight();
      }
    } catch (error) {
      console.error('AR scan failed:', error);
      HapticsService.notificationError();
    }
  };

  const animateMarkerHighlight = () => {
    Animated.sequence([
      Animated.timing(markerHighlightAnimation, {
        toValue: 1.2,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(markerHighlightAnimation, {
        toValue: 1.0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const capturePhoto = async () => {
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
      });

      HapticsService.impactLight();
      AudioService.playSound('camera_shutter');

      // Process the captured photo
      processCapturedImage(photo);
    } catch (error) {
      console.error('Failed to capture photo:', error);
      Alert.alert('Error', 'Failed to capture photo');
    }
  };

  const processCapturedImage = async (photo: any) => {
    try {
      // Here you would process the image to detect AR markers
      // For now, we'll simulate detection
      Alert.alert(
        'Photo Captured',
        'Image captured successfully. AR markers would be detected here.',
        [
          { text: 'OK' },
          {
            text: 'Save to Campaign',
            onPress: () => saveToCampaign(photo),
          },
        ]
      );
    } catch (error) {
      console.error('Failed to process image:', error);
    }
  };

  const saveToCampaign = async (photo: any) => {
    // Save the AR scene to the current campaign
    Alert.alert('Success', 'AR scene saved to campaign!');
  };

  const selectFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [16, 9],
        quality: 0.8,
      });

      if (!result.canceled) {
        HapticsService.selectionChanged();
        processCapturedImage(result.assets[0]);
      }
    } catch (error) {
      console.error('Failed to pick image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };

  const placeMarker = (marker: ARMarker) => {
    setSelectedMarker(marker);
    setArMode('place');
    HapticsService.impactMedium();
  };

  const confirmPlacement = () => {
    if (!selectedMarker) return;

    // Confirm AR marker placement
    Alert.alert(
      'Place Marker',
      `Place ${selectedMarker.name} at this location?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Place',
          onPress: () => {
            HapticsService.notificationSuccess();
            setArMode('view');
            // Here you would save the marker placement
          },
        },
      ]
    );
  };

  const toggleFlash = () => {
    setFlashEnabled(!flashEnabled);
    HapticsService.selectionChanged();
  };

  const startRecording = () => {
    setIsRecording(true);
    HapticsService.impactHeavy();
    // Here you would start video recording
  };

  const stopRecording = () => {
    setIsRecording(false);
    HapticsService.impactHeavy();
    // Here you would stop video recording
  };

  const renderCameraControls = () => (
    <View style={styles.cameraControls}>
      <TouchableOpacity
        style={styles.controlButton}
        onPress={toggleFlash}
      >
        <Icon
          name={flashEnabled ? 'flash-on' : 'flash-off'}
          size={24}
          color={colors.text}
        />
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={selectFromGallery}
      >
        <Icon name="photo-library" size={24} color={colors.text} />
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.controlButton, isRecording && styles.recordingButton]}
        onPress={isRecording ? stopRecording : startRecording}
      >
        <Icon
          name={isRecording ? 'stop' : 'videocam'}
          size={24}
          color={colors.text}
        />
      </TouchableOpacity>
    </View>
  );

  const renderAROverlay = () => {
    if (arMode === 'scan' && isScanning) {
      return (
        <View style={styles.scanOverlay}>
          <Animated.View
            style={[
              styles.scanLine,
              {
                transform: [
                  {
                    translateY: scanLineAnimation.interpolate({
                      inputRange: [0, 1],
                      outputRange: [0, screenHeight * 0.6],
                    }),
                  },
                ],
              },
            ]}
          />
          <View style={styles.scanCorners}>
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </View>
          <Text style={styles.scanText}>Scanning for AR markers...</Text>
        </View>
      );
    }

    if (arMode === 'view' && detectedMarkers.length > 0) {
      return (
        <View style={styles.arMarkers}>
          {detectedMarkers.map((detection, index) => (
            <TouchableOpacity
              key={detection.marker.id}
              style={[
                styles.markerOverlay,
                {
                  left: detection.boundingBox.x,
                  top: detection.boundingBox.y,
                  width: detection.boundingBox.width,
                  height: detection.boundingBox.height,
                },
              ]}
              onPress={() => placeMarker(detection.marker)}
              activeOpacity={0.8}
            >
              <Animated.View
                style={[
                  styles.markerHighlight,
                  {
                    transform: [{ scale: markerHighlightAnimation }],
                    borderColor: colors.primary,
                    borderWidth: 2,
                    borderRadius: 8,
                  },
                ]}
              >
                <View style={styles.markerInfo}>
                  <Text style={styles.markerName}>{detection.marker.name}</Text>
                  <Text style={styles.markerType}>{detection.marker.type}</Text>
                  <Badge
                    value={`${Math.round(detection.confidence * 100)}%`}
                    status={detection.confidence > 0.8 ? 'success' : 'warning'}
                    containerStyle={styles.confidenceBadge}
                  />
                </View>
              </Animated.View>
            </TouchableOpacity>
          ))}
        </View>
      );
    }

    if (arMode === 'place' && selectedMarker) {
      return (
        <View style={styles.placementOverlay}>
          <Card containerStyle={styles.placementCard}>
            <Text style={styles.placementTitle}>Place {selectedMarker.name}</Text>
            <Text style={styles.placementDescription}>
              Position the marker and confirm placement
            </Text>

            <View style={styles.placementControls}>
              <Slider
                value={selectedMarker.scale}
                onValueChange={(value) => {
                  setSelectedMarker({ ...selectedMarker, scale: value });
                }}
                minimumValue={0.5}
                maximumValue={2.0}
                step={0.1}
                thumbStyle={{ backgroundColor: colors.primary }}
                trackStyle={{ backgroundColor: colors.primary + '50' }}
              />
              <Text style={styles.scaleText}>
                Scale: {selectedMarker.scale.toFixed(1)}x
              </Text>
            </View>

            <View style={styles.placementButtons}>
              <Button
                title="Cancel"
                type="outline"
                onPress={() => setArMode('view')}
                containerStyle={styles.placementButton}
              />
              <Button
                title="Place"
                onPress={confirmPlacement}
                containerStyle={styles.placementButton}
              />
            </View>
          </Card>
        </View>
      );
    }

    return null;
  };

  const renderBottomControls = () => (
    <View style={styles.bottomControls}>
      <View style={styles.modeSelector}>
        <TouchableOpacity
          style={[styles.modeButton, arMode === 'scan' && styles.activeMode]}
          onPress={() => {
            setArMode('scan');
            HapticsService.selectionChanged();
          }}
        >
          <Icon name="qr-code-scanner" size={20} color={colors.text} />
          <Text style={styles.modeText}>Scan</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.modeButton, arMode === 'view' && styles.activeMode]}
          onPress={() => {
            setArMode('view');
            HapticsService.selectionChanged();
          }}
        >
          <Icon name="view-in-ar" size={20} color={colors.text} />
          <Text style={styles.modeText}>View</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.modeButton, arMode === 'place' && styles.activeMode]}
          onPress={() => {
            setArMode('place');
            HapticsService.selectionChanged();
          }}
        >
          <Icon name="add-location" size={20} color={colors.text} />
          <Text style={styles.modeText}>Place</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.actionButton, isScanning ? styles.stopButton : styles.startButton]}
          onPress={isScanning ? stopScanning : startScanning}
        >
          <Icon
            name={isScanning ? 'stop' : 'radar'}
            size={24}
            color={colors.text}
          />
          <Text style={styles.actionButtonText}>
            {isScanning ? 'Stop' : 'Scan'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.photoButton]}
          onPress={capturePhoto}
        >
          <Icon name="camera" size={24} color={colors.text} />
          <Text style={styles.actionButtonText}>Photo</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (hasPermission === null) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>Requesting camera permission...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.permissionContainer}>
        <Icon name="camera-off" size={64} color={colors.error} />
        <Text style={styles.permissionText}>No access to camera</Text>
        <Button
          title="Grant Permission"
          onPress={requestCameraPermission}
          containerStyle={styles.permissionButton}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={Camera.Constants.Type.back}
        zoom={zoom}
        flashMode={flashEnabled ? 'on' : 'off'}
        onCameraReady={() => console.log('Camera ready')}
      />

      {renderCameraControls()}
      {renderAROverlay()}
      {renderBottomControls()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  camera: {
    flex: 1,
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing.lg,
  },
  permissionText: {
    color: colors.text,
    fontSize: 18,
    textAlign: 'center',
    marginTop: spacing.md,
    fontFamily: 'Lato-Regular',
  },
  permissionButton: {
    marginTop: spacing.lg,
  },
  cameraControls: {
    position: 'absolute',
    top: 50,
    right: 20,
    flexDirection: 'row',
  },
  controlButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.surface + '80',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  recordingButton: {
    backgroundColor: colors.error,
  },
  scanOverlay: {
    position: 'absolute',
    top: '20%',
    left: '10%',
    width: '80%',
    height: '60%',
  },
  scanLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: colors.primary,
  },
  scanCorners: {
    flex: 1,
  },
  corner: {
    position: 'absolute',
    width: 20,
    height: 20,
    borderColor: colors.primary,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 3,
    borderLeftWidth: 3,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 3,
    borderRightWidth: 3,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 3,
    borderLeftWidth: 3,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 3,
    borderRightWidth: 3,
  },
  scanText: {
    position: 'absolute',
    bottom: -40,
    left: 0,
    right: 0,
    textAlign: 'center',
    color: colors.text,
    fontSize: 16,
    fontFamily: 'Lato-Regular',
  },
  arMarkers: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  markerOverlay: {
    position: 'absolute',
    backgroundColor: 'transparent',
  },
  markerHighlight: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.primary + '20',
  },
  markerInfo: {
    backgroundColor: colors.surface + '90',
    padding: spacing.sm,
    borderRadius: 8,
    minWidth: 120,
  },
  markerName: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    textAlign: 'center',
  },
  markerType: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    textAlign: 'center',
  },
  confidenceBadge: {
    marginTop: 4,
  },
  placementOverlay: {
    position: 'absolute',
    top: '50%',
    left: '10%',
    right: '10%',
    transform: [{ translateY: -100 }],
  },
  placementCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '50',
  },
  placementTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  placementDescription: {
    color: colors.textSecondary,
    fontSize: 14,
    textAlign: 'center',
    marginBottom: spacing.md,
    fontFamily: 'Lato-Regular',
  },
  placementControls: {
    marginBottom: spacing.md,
  },
  scaleText: {
    color: colors.text,
    fontSize: 12,
    textAlign: 'center',
    marginTop: spacing.sm,
    fontFamily: 'Lato-Regular',
  },
  placementButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  placementButton: {
    flex: 1,
    marginHorizontal: spacing.sm,
  },
  bottomControls: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.primary + '30',
    padding: spacing.md,
  },
  modeSelector: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: spacing.md,
  },
  modeButton: {
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 8,
  },
  activeMode: {
    backgroundColor: colors.primary + '30',
  },
  modeText: {
    color: colors.text,
    fontSize: 12,
    marginTop: 4,
    fontFamily: 'Lato-Regular',
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: 25,
    minWidth: 100,
    justifyContent: 'center',
  },
  startButton: {
    backgroundColor: colors.success,
  },
  stopButton: {
    backgroundColor: colors.error,
  },
  photoButton: {
    backgroundColor: colors.primary,
  },
  actionButtonText: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: spacing.sm,
    fontFamily: 'Lato-Bold',
  },
});

export default ARScannerScreen;