import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Character } from '../../types';
import { useTheme } from '../../hooks/useTheme';

interface CharacterCardProps {
  character: Character;
  onPress: () => void;
  size?: 'small' | 'medium' | 'large';
}

export const CharacterCard: React.FC<CharacterCardProps> = ({
  character,
  onPress,
  size = 'medium',
}) => {
  const theme = useTheme();

  const cardWidth = size === 'small' ? 140 : size === 'large' ? 200 : 160;
  const avatarSize = size === 'small' ? 60 : size === 'large' ? 80 : 70;

  const getHealthBarColor = () => {
    const healthPercentage = (character.hp / character.maxHp) * 100;
    if (healthPercentage > 50) return theme.colors.success;
    if (healthPercentage > 25) return theme.colors.warning;
    return theme.colors.error;
  };

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: theme.colors.surface,
          width: cardWidth,
          borderColor: theme.colors.border,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {/* Character Avatar */}
      <View style={styles.avatarSection}>
        {character.avatar ? (
          <Image
            source={{ uri: character.avatar }}
            style={[
              styles.avatar,
              {
                width: avatarSize,
                height: avatarSize,
                borderRadius: avatarSize / 2,
              },
            ]}
          />
        ) : (
          <View
            style={[
              styles.avatarPlaceholder,
              {
                width: avatarSize,
                height: avatarSize,
                borderRadius: avatarSize / 2,
                backgroundColor: theme.colors.primary + '20',
              },
            ]}
          >
            <Icon
              name="person"
              size={avatarSize * 0.5}
              color={theme.colors.primary}
            />
          </View>
        )}
      </View>

      {/* Character Info */}
      <View style={styles.infoSection}>
        <Text
          style={[
            styles.characterName,
            { color: theme.colors.text },
            size === 'small' && styles.smallText,
          ]}
          numberOfLines={1}
        >
          {character.name}
        </Text>

        <Text
          style={[
            styles.characterClass,
            { color: theme.colors.textSecondary },
            size === 'small' && styles.smallText,
          ]}
          numberOfLines={1}
        >
          Level {character.level} {character.class}
        </Text>

        <Text
          style={[
            styles.characterRace,
            { color: theme.colors.textSecondary },
            size === 'small' && styles.smallText,
          ]}
          numberOfLines={1}
        >
          {character.race}
        </Text>
      </View>

      {/* Health Bar */}
      <View style={styles.healthSection}>
        <View style={styles.healthBarContainer}>
          <View
            style={[
              styles.healthBar,
              {
                width: `${(character.hp / character.maxHp) * 100}%`,
                backgroundColor: getHealthBarColor(),
              },
            ]}
          />
        </View>
        <Text
          style={[
            styles.healthText,
            { color: theme.colors.textSecondary },
            size === 'small' && styles.smallText,
          ]}
        >
          {character.hp}/{character.maxHp}
        </Text>
      </View>

      {/* Status Indicators */}
      <View style={styles.statusSection}>
        <View style={styles.statusContainer}>
          <Text style={[styles.acText, { color: theme.colors.text }]}>
            AC {character.ac}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    marginVertical: 4,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  avatarSection: {
    alignItems: 'center',
    marginBottom: 8,
  },
  avatar: {
    resizeMode: 'cover',
  },
  avatarPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoSection: {
    alignItems: 'center',
    marginBottom: 8,
  },
  characterName: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  characterClass: {
    fontSize: 12,
    textAlign: 'center',
  },
  characterRace: {
    fontSize: 11,
    textAlign: 'center',
  },
  smallText: {
    fontSize: 10,
  },
  healthSection: {
    marginBottom: 8,
  },
  healthBarContainer: {
    height: 4,
    backgroundColor: '#e0e0e0',
    borderRadius: 2,
    marginBottom: 4,
  },
  healthBar: {
    height: '100%',
    borderRadius: 2,
  },
  healthText: {
    fontSize: 11,
    textAlign: 'center',
  },
  statusSection: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  statusContainer: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  acText: {
    fontSize: 11,
    fontWeight: '600',
  },
});