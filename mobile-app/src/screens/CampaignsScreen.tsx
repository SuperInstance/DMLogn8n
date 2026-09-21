import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { fetchCampaigns } from '../../store/slices/campaignSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { CampaignCard } from '../../components/CampaignCard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const CampaignsScreen: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();

  const { campaigns, isLoading } = useSelector((state: RootState) => state.campaigns);

  const handleCampaignPress = (campaignId: string) => {
    console.log('Campaign pressed:', campaignId);
  };

  const handleBrowseCampaigns = () => {
    console.log('Browse campaigns');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Campaigns
        </Text>
        <TouchableOpacity
          style={[styles.browseButton, { backgroundColor: theme.colors.primary }]}
          onPress={handleBrowseCampaigns}
        >
          <Icon name="search" size={24} color="white" />
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {campaigns.length > 0 ? (
            campaigns.map((campaign) => (
              <CampaignCard
                key={campaign.id}
                campaign={campaign}
                onPress={() => handleCampaignPress(campaign.id)}
              />
            ))
          ) : (
            <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
              <Icon name="explore-outline" size={64} color={theme.colors.textSecondary} />
              <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
                No campaigns yet
              </Text>
              <TouchableOpacity
                style={[styles.browseCampaignsButton, { backgroundColor: theme.colors.primary }]}
                onPress={handleBrowseCampaigns}
              >
                <Text style={styles.browseCampaignsButtonText}>
                  Browse Campaigns
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  browseButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    borderRadius: 12,
    marginTop: 50,
  },
  emptyStateText: {
    fontSize: 18,
    marginTop: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  browseCampaignsButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  browseCampaignsButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CampaignsScreen;