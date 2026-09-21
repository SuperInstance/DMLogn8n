import React from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import {
  Card,
  Text,
  Avatar,
  Icon,
  Button,
  Badge,
} from 'react-native-elements';
import { useTheme } from '@react-navigation/native';
import { Character } from '../types';
import { getRarityColor } from '../utils/helpers';

interface CharacterCardProps {
  character: Character;
  onPress: (character: Character) => void;
  onLongPress?: (character: Character) => void;
  onEdit?: (character: Character) => void;
  onDelete?: (character: Character) => void;
  showActions?: boolean;
  compact?: boolean;
  isSelected?: boolean;
  showSelectionIndicator?: boolean;
}

const CharacterCard: React.FC<CharacterCardProps> = ({
  character,
  onPress,
  onLongPress,
  onEdit,
  onDelete,
  showActions = true,
  compact = false,
  isSelected = false,
  showSelectionIndicator = false,
}) => {
  const theme = useTheme();
  const scaleValue = React.useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.spring(scaleValue, {
      toValue: 0.98,
      useNativeDriver: true,
    }).start();
  };

  const handlePressOut = () => {
    Animated.spring(scaleValue, {
      toValue: 1,
      useNativeDriver: true,
    }).start();
  };

  const handlePress = () => {
    onPress(character);
  };

  const handleLongPress = () => {
    onLongPress?.(character);
  };

  const getHealthPercentage = () => {
    return (character.health / character.maxHealth) * 100;
  };

  const getManaPercentage = () => {
    return (character.mana / character.maxMana) * 100;
  };

  const getExperiencePercentage = () => {
    // This would need to be calculated based on level thresholds
    return (character.experience % 1000) / 1000 * 100;
  };

  const containerStyle = [
    styles.container,
    {
      backgroundColor: theme.colors.surface,
      borderColor: isSelected ? theme.colors.primary : theme.colors.border,
      borderWidth: isSelected ? 2 : 1,
    },
    compact && styles.compactContainer,
  ];

  const cardContent = (
    <Animated.View
      style={[
        containerStyle,
        {
          transform: [{ scale: scaleValue }],
        },
      ]}
    >
      {/* Selection Indicator */}
      {showSelectionIndicator && (
        <View style={[styles.selectionIndicator, isSelected && styles.selectionIndicatorSelected]}>
          {isSelected && (
            <Icon
              name="checkmark"
              type="ionicon"
              size={16}
              color="#FFFFFF"
            />
          )}
        </View>
      )}

      <TouchableOpacity
        style={styles.touchArea}
        onPress={handlePress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onLongPress={handleLongPress}
        activeOpacity={0.7}
      >
        <View style={styles.content}>
          {/* Character Avatar and Basic Info */}
          <View style={styles.header}>
            <Avatar
              size={compact ? 'medium' : 'large'}
              rounded
              source={
                character.appearance?.avatar
                  ? { uri: character.appearance.avatar }
                  : undefined
              }
              title={character.name.charAt(0)}
              containerStyle={[
                styles.avatar,
                { borderColor: getRarityColor(character.rarity || 'common') },
              ]}
              titleStyle={{ color: '#FFFFFF' }}
            />

            <View style={styles.basicInfo}>
              <Text
                h4
                style={[
                  styles.characterName,
                  { color: theme.colors.text },
                  compact && styles.characterNameCompact,
                ]}
                numberOfLines={1}
              >
                {character.name}
              </Text>

              <View style={styles.classInfo}>
                <Text
                  style={[
                    styles.className,
                    { color: theme.colors.textSecondary },
                  ]}
                  numberOfLines={1}
                >
                  {character.class.name}
                </Text>
                <Badge
                  value={`Lvl ${character.level}`}
                  badgeStyle={{
                    backgroundColor: theme.colors.experience,
                  }}
                  textStyle={{
                    fontSize: 10,
                    fontWeight: '600',
                  }}
                />
              </View>

              {!compact && (
                <Text
                  style={[
                    styles.characterRace,
                    { color: theme.colors.textSecondary },
                  ]}
                  numberOfLines={1}
                >
                  {character.appearance?.race} • {character.appearance?.gender}
                </Text>
              )}
            </View>

            {/* Status Badge */}
            <View style={styles.statusContainer}>
              {character.health > 0 ? (
                <Badge
                  status="success"
                  value="Active"
                  containerStyle={styles.statusBadge}
                />
              ) : (
                <Badge
                  status="error"
                  value="Inactive"
                  containerStyle={styles.statusBadge}
                />
              )}
            </View>
          </View>

          {/* Character Stats */}
          {!compact && (
            <View style={styles.statsContainer}>
              {/* Health Bar */}
              <View style={styles.statBar}>
                <Icon
                  name="heart"
                  type="ionicon"
                  size={16}
                  color={theme.colors.health}
                  style={styles.statIcon}
                />
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${getHealthPercentage()}%`,
                        backgroundColor: theme.colors.health,
                      },
                    ]}
                  />
                </View>
                <Text style={[styles.statText, { color: theme.colors.textSecondary }]}>
                  {character.health}/{character.maxHealth}
                </Text>
              </View>

              {/* Mana Bar */}
              <View style={styles.statBar}>
                <Icon
                  name="flash"
                  type="ionicon"
                  size={16}
                  color={theme.colors.mana}
                  style={styles.statIcon}
                />
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${getManaPercentage()}%`,
                        backgroundColor: theme.colors.mana,
                      },
                    ]}
                  />
                </View>
                <Text style={[styles.statText, { color: theme.colors.textSecondary }]}>
                  {character.mana}/{character.maxMana}
                </Text>
              </View>

              {/* Experience Bar */}
              <View style={styles.statBar}>
                <Icon
                  name="star"
                  type="ionicon"
                  size={16}
                  color={theme.colors.experience}
                  style={styles.statIcon}
                />
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      {
                        width: `${getExperiencePercentage()}%`,
                        backgroundColor: theme.colors.experience,
                      },
                    ]}
                  />
                </View>
                <Text style={[styles.statText, { color: theme.colors.textSecondary }]}>
                  {character.experience} XP
                </Text>
              </View>
            </View>
          )}

          {/* Equipment Preview */}
          {!compact && character.equipment && character.equipment.length > 0 && (
            <View style={styles.equipmentContainer}>
              <Text style={[styles.equipmentTitle, { color: theme.colors.textSecondary }]}>
                Equipment
              </Text>
              <View style={styles.equipmentItems}>
                {character.equipment.slice(0, 4).map((item, index) => (
                  <View
                    key={item.id}
                    style={[
                      styles.equipmentItem,
                      { borderColor: getRarityColor(item.rarity) },
                    ]}
                  >
                    <Icon
                      name={getEquipmentIcon(item.type)}
                      type="ionicon"
                      size={16}
                      color={getRarityColor(item.rarity)}
                    />
                  </View>
                ))}
                {character.equipment.length > 4 && (
                  <View style={styles.moreItems}>
                    <Text style={[styles.moreItemsText, { color: theme.colors.textSecondary }]}>
                      +{character.equipment.length - 4}
                    </Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Action Buttons */}
          {showActions && !compact && (
            <View style={styles.actionsContainer}>
              <Button
                type="outline"
                title="Edit"
                onPress={() => onEdit?.(character)}
                buttonStyle={[
                  styles.actionButton,
                  { borderColor: theme.colors.primary },
                ]}
                titleStyle={[styles.actionButtonText, { color: theme.colors.primary }]}
                size="sm"
              />
              <Button
                type="outline"
                title="Delete"
                onPress={() => onDelete?.(character)}
                buttonStyle={[
                  styles.actionButton,
                  { borderColor: theme.colors.error },
                ]}
                titleStyle={[styles.actionButtonText, { color: theme.colors.error }]}
                size="sm"
              />
            </View>
          )}
        </View>
      </TouchableOpacity>
    </Animated.View>
  );

  if (compact) {
    return cardContent;
  }

  return (
    <Card containerStyle={styles.cardContainer}>
      {cardContent}
    </Card>
  );
};

const getEquipmentIcon = (type: string): string => {
  switch (type) {
    case 'weapon': return 'sword';
    case 'armor': return 'shield';
    case 'helmet': return 'shield-checkmark';
    case 'accessory': return 'diamond';
    default: return 'cube';
  }
};

const styles = StyleSheet.create({
  cardContainer: {
    borderRadius: 16,
    padding: 0,
    marginHorizontal: 0,
    marginVertical: 8,
    backgroundColor: 'transparent',
    borderWidth: 0,
  },
  container: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    position: 'relative',
  },
  compactContainer: {
    padding: 12,
  },
  selectionIndicator: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#ddd',
    backgroundColor: '#FFFFFF',
    zIndex: 1,
  },
  selectionIndicatorSelected: {
    backgroundColor: '#6200EE',
    borderColor: '#6200EE',
  },
  touchArea: {
    width: '100%',
  },
  content: {
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  avatar: {
    borderWidth: 3,
    marginRight: 12,
  },
  basicInfo: {
    flex: 1,
  },
  characterName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  characterNameCompact: {
    fontSize: 16,
  },
  classInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 2,
  },
  className: {
    fontSize: 14,
    fontWeight: '500',
  },
  characterRace: {
    fontSize: 12,
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  statusBadge: {
    marginTop: 4,
  },
  statsContainer: {
    gap: 8,
  },
  statBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statIcon: {
    width: 20,
  },
  progressBar: {
    flex: 1,
    height: 6,
    backgroundColor: '#333',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  statText: {
    fontSize: 12,
    fontWeight: '500',
    minWidth: 60,
    textAlign: 'right',
  },
  equipmentContainer: {
    marginTop: 8,
  },
  equipmentTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  equipmentItems: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  equipmentItem: {
    width: 32,
    height: 32,
    borderRadius: 8,
    borderWidth: 2,
    backgroundColor: '#2C2C2C',
    justifyContent: 'center',
    alignItems: 'center',
  },
  moreItems: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: '#2C2C2C',
    justifyContent: 'center',
    alignItems: 'center',
  },
  moreItemsText: {
    fontSize: 10,
    fontWeight: '600',
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
    borderRadius: 8,
    paddingVertical: 8,
    borderWidth: 1,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
});

export default CharacterCard;