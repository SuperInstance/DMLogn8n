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

import { fetchActiveCombat } from '../../store/slices/combatSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const CombatScreen: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();

  const { activeCombat, isLoading } = useSelector((state: RootState) => state.combat);

  const handleStartCombat = () => {
    console.log('Start combat');
  };

  const handleJoinCombat = () => {
    console.log('Join combat');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Combat
        </Text>
        {activeCombat?.isActive && (
          <View style={[styles.activeIndicator, { backgroundColor: theme.colors.success }]} />
        )}
      </View>

      {isLoading ? (
        <LoadingSpinner />
      ) : activeCombat?.isActive ? (
        <ScrollView contentContainerStyle={styles.content}>
          <View style={[styles.combatCard, { backgroundColor: theme.colors.surface }]}>
            <Text style={[styles.combatTitle, { color: theme.colors.text }]}>
              Active Combat
            </Text>
            <Text style={[styles.roundText, { color: theme.colors.textSecondary }]}>
              Round {activeCombat.round}
            </Text>
            <View style={styles.participantsList}>
              {activeCombat.participants.map((participant) => (
                <View
                  key={participant.id}
                  style={[
                    styles.participantItem,
                    {
                      backgroundColor: participant.isCurrentTurn
                        ? theme.colors.primary + '20'
                        : 'transparent',
                      borderColor: theme.colors.border,
                    },
                  ]}
                >
                  <Text style={[styles.participantName, { color: theme.colors.text }]}>
                    {participant.name}
                  </Text>
                  <Text style={[styles.participantInitiative, { color: theme.colors.textSecondary }]}>
                    Init: {participant.initiative}
                  </Text>
                </View>
              ))}
            </View>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: theme.colors.primary }]}
              onPress={handleJoinCombat}
            >
              <Text style={styles.actionButtonText}>Join Combat</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      ) : (
        <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
          <Icon name="sports-kabaddi" size={64} color={theme.colors.textSecondary} />
          <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
            No active combat
          </Text>
          <TouchableOpacity
            style={[styles.startCombatButton, { backgroundColor: theme.colors.primary }]}
            onPress={handleStartCombat}
          >
            <Text style={styles.startCombatButtonText}>
              Start Combat
            </Text>
          </TouchableOpacity>
        </View>
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
  activeIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  content: {
    padding: 16,
  },
  combatCard: {
    borderRadius: 12,
    padding: 20,
  },
  combatTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  roundText: {
    fontSize: 16,
    marginBottom: 20,
  },
  participantsList: {
    marginBottom: 20,
  },
  participantItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 8,
  },
  participantName: {
    fontSize: 16,
    fontWeight: '500',
  },
  participantInitiative: {
    fontSize: 14,
  },
  actionButton: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    borderRadius: 12,
    margin: 16,
  },
  emptyStateText: {
    fontSize: 18,
    marginTop: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  startCombatButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  startCombatButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CombatScreen;