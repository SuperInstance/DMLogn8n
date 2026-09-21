import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Campaign } from '../../types';
import { useTheme } from '../../hooks/useTheme';

interface CampaignCardProps {
  campaign: Campaign;
  onPress: () => void;
}

export const CampaignCard: React.FC<CampaignCardProps> = ({
  campaign,
  onPress,
}) => {
  const theme = useTheme();

  const getStatusColor = () => {
    if (campaign.isActive) {
      return theme.colors.success;
    }
    return theme.colors.textSecondary;
  };

  const getStatusText = () => {
    if (campaign.isActive) {
      return 'Active';
    }
    return 'Inactive';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.border,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {/* Campaign Image */}
      <View style={styles.imageSection}>
        {campaign.imageUrl ? (
          <Image
            source={{ uri: campaign.imageUrl }}
            style={styles.campaignImage}
          />
        ) : (
          <View
            style={[
              styles.imagePlaceholder,
              { backgroundColor: theme.colors.primary + '20' },
            ]}
          >
            <Icon
              name="explore"
              size={32}
              color={theme.colors.primary}
            />
          </View>
        )}
      </View>

      {/* Campaign Info */}
      <View style={styles.infoSection}>
        <View style={styles.headerRow}>
          <Text
            style={[styles.campaignName, { color: theme.colors.text }]}
            numberOfLines={2}
          >
            {campaign.name}
          </Text>
          <View
            style={[
              styles.statusBadge,
              { backgroundColor: getStatusColor() + '20' },
            ]}
          >
            <Text
              style={[
                styles.statusText,
                { color: getStatusColor() },
              ]}
            >
              {getStatusText()}
            </Text>
          </View>
        </View>

        <Text
          style={[styles.campaignDescription, { color: theme.colors.textSecondary }]}
          numberOfLines={2}
        >
          {campaign.description}
        </Text>

        <View style={styles.detailsRow}>
          <View style={styles.detailItem}>
            <Icon
              name="person"
              size={16}
              color={theme.colors.textSecondary}
            />
            <Text
              style={[styles.detailText, { color: theme.colors.textSecondary }]}
            >
              {campaign.dmName}
            </Text>
          </View>

          <View style={styles.detailItem}>
            <Icon
              name="group"
              size={16}
              color={theme.colors.textSecondary}
            />
            <Text
              style={[styles.detailText, { color: theme.colors.textSecondary }]}
            >
              {campaign.currentPlayers}/{campaign.maxPlayers}
            </Text>
          </View>
        </View>

        {campaign.nextSession && (
          <View style={styles.sessionRow}>
            <Icon
              name="schedule"
              size={16}
              color={theme.colors.primary}
            />
            <Text
              style={[styles.sessionText, { color: theme.colors.primary }]}
            >
              Next: {formatDate(campaign.nextSession)}
            </Text>
          </View>
        )}

        {campaign.location && (
          <View style={styles.locationRow}>
            <Icon
              name="location-on"
              size={16}
              color={theme.colors.textSecondary}
            />
            <Text
              style={[styles.locationText, { color: theme.colors.textSecondary }]}
              numberOfLines={1}
            >
              {campaign.location}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginVertical: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  imageSection: {
    marginRight: 16,
  },
  campaignImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoSection: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  campaignName: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
    marginRight: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
  },
  campaignDescription: {
    fontSize: 14,
    marginBottom: 12,
    lineHeight: 20,
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailText: {
    fontSize: 12,
    marginLeft: 4,
  },
  sessionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  sessionText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
  locationRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  locationText: {
    fontSize: 12,
    marginLeft: 4,
    flex: 1,
  },
});