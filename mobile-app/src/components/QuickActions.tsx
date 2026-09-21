import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useTheme } from '../../hooks/useTheme';
import { useHaptic } from '../../contexts/HapticContext';
import { shakeService } from '../../services/shakeService';

export const QuickActions: React.FC = () => {
  const navigation = useNavigation();
  const theme = useTheme();
  const { diceRoll, medium } = useHaptic();

  const handleDiceRoll = () => {
    diceRoll();
    navigation.navigate('DiceRollModal' as never);
  };

  const handleCombat = () => {
    medium();
    navigation.navigate('Combat' as never);
  };

  const handleMessages = () => {
    medium();
    navigation.navigate('Messages' as never);
  };

  const handleCharacters = () => {
    medium();
    navigation.navigate('Characters' as never);
  };

  const handleShakeInfo = () => {
    medium();
    // Show info about shake to roll feature
  };

  const quickActions = [
    {
      id: 'dice',
      icon: 'casino',
      label: 'Roll Dice',
      color: theme.colors.primary,
      onPress: handleDiceRoll,
    },
    {
      id: 'combat',
      icon: 'sports-kabaddi',
      label: 'Combat',
      color: theme.colors.warning,
      onPress: handleCombat,
    },
    {
      id: 'messages',
      icon: 'chat',
      label: 'Messages',
      color: theme.colors.info,
      onPress: handleMessages,
    },
    {
      id: 'characters',
      icon: 'people',
      label: 'Characters',
      color: theme.colors.secondary,
      onPress: handleCharacters,
    },
  ];

  return (
    <View style={styles.container}>
      <View style={styles.actionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[
              styles.actionButton,
              { backgroundColor: action.color + '20' },
            ]}
            onPress={action.onPress}
            activeOpacity={0.7}
          >
            <View
              style={[
                styles.actionIcon,
                { backgroundColor: action.color },
              ]}
            >
              <Icon
                name={action.icon}
                size={24}
                color="white"
              />
            </View>
            <Text
              style={[
                styles.actionLabel,
                { color: theme.colors.text },
              ]}
            >
              {action.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Shake to Roll Hint */}
      <TouchableOpacity
        style={[
          styles.shakeHint,
          { backgroundColor: theme.colors.surface },
        ]}
        onPress={handleShakeInfo}
      >
        <Icon
          name="phone-iphone"
          size={20}
          color={theme.colors.primary}
        />
        <Text
          style={[
            styles.shakeHintText,
            { color: theme.colors.textSecondary },
          ]}
        >
          Shake to roll dice
        </Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 24,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  actionButton: {
    width: '48%',
    aspectRatio: 1.5,
    borderRadius: 12,
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  shakeHint: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  shakeHintText: {
    fontSize: 14,
    marginLeft: 8,
    fontStyle: 'italic',
  },
});