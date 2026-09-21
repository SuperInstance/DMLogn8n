import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Icon } from '@rneui/themed';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { setOnlineStatus, setSyncStatus } from '../../store/slices/appSlice';
import { SyncService } from '../../services/syncService';
import { colors, spacing } from '../../theme/theme';

const NetworkStatus: React.FC = () => {
  const dispatch = useDispatch();
  const { isOnline, syncStatus } = useAppSelector(state => state.app);
  const [syncQueueLength, setSyncQueueLength] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const slideAnimation = new Animated.Value(-100);

  const syncService = SyncService.getInstance();

  useEffect(() => {
    // Initialize sync service
    syncService.initialize();

    // Add network status listener
    const unsubscribe = syncService.addNetworkStatusListener((online) => {
      dispatch(setOnlineStatus(online));
      if (!online) {
        setIsVisible(true);
        animateIn();
      } else {
        animateOut();
      }
    });

    return () => {
      unsubscribe();
    };
  }, [dispatch]);

  useEffect(() => {
    // Update sync queue length
    const interval = setInterval(() => {
      setSyncQueueLength(syncService.getSyncQueueLength());
      setIsSyncing(syncService.getIsSyncing());

      if (syncQueueLength > 0 && isOnline) {
        dispatch(setSyncStatus('syncing'));
      } else if (syncQueueLength === 0 && isOnline) {
        dispatch(setSyncStatus('synced'));
      } else if (!isOnline) {
        dispatch(setSyncStatus('offline'));
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [syncQueueLength, isOnline, dispatch]);

  const animateIn = () => {
    Animated.timing(slideAnimation, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  const animateOut = () => {
    Animated.timing(slideAnimation, {
      toValue: -100,
      duration: 300,
      useNativeDriver: true,
    }).start(() => setIsVisible(false));
  };

  const handleRetrySync = async () => {
    if (!isOnline) {
      Alert.alert(
        'Offline',
        'Cannot sync while offline. Please check your internet connection.',
        [{ text: 'OK' }]
      );
      return;
    }

    try {
      await syncService.forceSyncNow();
    } catch (error) {
      Alert.alert(
        'Sync Failed',
        error instanceof Error ? error.message : 'Failed to sync data',
        [{ text: 'OK' }]
      );
    }
  };

  const handleRetryFailed = async () => {
    try {
      await syncService.retryFailedItems();
    } catch (error) {
      Alert.alert(
        'Retry Failed',
        error instanceof Error ? error.message : 'Failed to retry sync items',
        [{ text: 'OK' }]
      );
    }
  };

  const handleClearQueue = () => {
    Alert.alert(
      'Clear Sync Queue',
      'Are you sure you want to clear all pending sync items? This will discard any unsynchronized changes.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            try {
              await syncService.clearSyncQueue();
            } catch (error) {
              Alert.alert('Error', 'Failed to clear sync queue');
            }
          },
        },
      ]
    );
  };

  const getStatusColor = () => {
    if (!isOnline) return colors.error;
    if (syncStatus === 'syncing') return colors.warning;
    if (syncStatus === 'error') return colors.error;
    return colors.success;
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline';
    if (syncStatus === 'syncing') return 'Syncing...';
    if (syncStatus === 'error') return 'Sync Error';
    if (syncStatus === 'synced') return 'Synced';
    return 'Unknown';
  };

  const getStatusIcon = () => {
    if (!isOnline) return 'wifi-off';
    if (syncStatus === 'syncing') return 'sync';
    if (syncStatus === 'error') return 'error';
    return 'wifi';
  };

  // Don't render if online and no sync issues
  if (isOnline && syncQueueLength === 0 && !isVisible) {
    return null;
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: colors.surface,
          transform: [{ translateY: slideAnimation }],
        },
      ]}
    >
      <View style={styles.content}>
        <View style={styles.statusContainer}>
          <Icon
            name={getStatusIcon()}
            size={20}
            color={getStatusColor()}
            style={styles.statusIcon}
          />
          <View style={styles.statusTextContainer}>
            <Text style={[styles.statusText, { color: getStatusColor() }]}>
              {getStatusText()}
            </Text>
            {syncQueueLength > 0 && (
              <Text style={styles.queueText}>
                {syncQueueLength} item{syncQueueLength !== 1 ? 's' : ''} pending
              </Text>
            )}
          </View>
        </View>

        <View style={styles.actionsContainer}>
          {!isOnline && (
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.warning }]}
              onPress={() => syncService.checkConnectivity()}
            >
              <Icon name="refresh" size={16} color={colors.text} />
            </TouchableOpacity>
          )}

          {isOnline && syncQueueLength > 0 && (
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.primary }]}
              onPress={handleRetrySync}
              disabled={isSyncing}
            >
              <Icon
                name={isSyncing ? 'hourglass-empty' : 'sync'}
                size={16}
                color={colors.text}
              />
            </TouchableOpacity>
          )}

          {syncQueueLength > 0 && (
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.error }]}
              onPress={handleClearQueue}
            >
              <Icon name="clear" size={16} color={colors.text} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Sync progress bar */}
      {isSyncing && (
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <Animated.View
              style={[
                styles.progressFill,
                {
                  backgroundColor: colors.primary,
                  width: '60%', // Placeholder - would be calculated from actual progress
                },
              ]}
            />
          </View>
        </View>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.primary + '30',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusIcon: {
    marginRight: spacing.sm,
  },
  statusTextContainer: {
    flex: 1,
  },
  statusText: {
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  queueText: {
    fontSize: 12,
    color: colors.textSecondary,
    fontFamily: 'Lato-Regular',
    marginTop: 2,
  },
  actionsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  progressContainer: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  progressBar: {
    height: 3,
    backgroundColor: colors.background,
    borderRadius: 1.5,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 1.5,
  },
});

export default NetworkStatus;