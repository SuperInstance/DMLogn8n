import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Animated,
  PanGestureHandler,
  Dimensions,
  Vibration,
} from 'react-native';
import {
  Card,
  Button,
  Icon,
  Chip,
  Badge,
  Input,
  Slider,
  ListItem,
  Avatar,
  Divider,
} from '@rneui/themed';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { Combat, Combatant, CombatEffect } from '../../types';
import { colors, spacing, typography } from '../../theme/theme';
import { HapticsService } from '../../services/hapticsService';
import { AudioService } from '../../services/audioService';
import { VoiceService } from '../../services/voiceService';

const { width: screenWidth } = Dimensions.get('window');

interface CombatTrackerScreenProps {
  route?: {
    params?: {
      sessionId?: string;
      combatId?: string;
    };
  };
}

const CombatTrackerScreen: React.FC<CombatTrackerScreenProps> = ({ route }) => {
  const dispatch = useAppDispatch();
  const { activeSession, activeCampaign } = useAppSelector(state => state.session);
  const { characters } = useAppSelector(state => state.character);

  // State
  const [combat, setCombat] = useState<Combat | null>(null);
  const [selectedCombatant, setSelectedCombatant] = useState<Combatant | null>(null);
  const [isCombatActive, setIsCombatActive] = useState(false);
  const [currentRound, setCurrentRound] = useState(1);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [showAddCombatant, setShowAddCombatant] = useState(false);
  const [showDamageDialog, setShowDamageDialog] = useState(false);
  const [damageAmount, setDamageAmount] = useState('');
  const [damageType, setDamageType] = useState('bludgeoning');
  const [showEffectDialog, setShowEffectDialog] = useState(false);

  // Animation refs
  const turnAnimation = useRef(new Animated.Value(0)).current;
  const roundAnimation = useRef(new Animated.Value(1)).current;
  const initiativeAnimation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    initializeCombat();
  }, []);

  useEffect(() => {
    if (combat && combat.isActive) {
      startTurnAnimation();
    }
  }, [currentTurn, combat?.isActive]);

  const initializeCombat = () => {
    // Initialize a new combat or load existing one
    const newCombat: Combat = {
      isActive: false,
      round: 1,
      turn: 0,
      initiative: [
        {
          id: '1',
          name: 'Player Character',
          type: 'player',
          userId: 'user1',
          characterId: 'char1',
          initiative: 15,
          health: { current: 25, max: 25, temp: 0 },
          ac: 16,
          speed: 30,
          conditions: [],
          effects: [],
        },
        {
          id: '2',
          name: 'Goblin',
          type: 'monster',
          initiative: 12,
          health: { current: 7, max: 7, temp: 0 },
          ac: 15,
          speed: 30,
          conditions: [],
          effects: [],
        },
        {
          id: '3',
          name: 'Orc',
          type: 'monster',
          initiative: 8,
          health: { current: 15, max: 15, temp: 0 },
          ac: 13,
          speed: 30,
          conditions: [],
          effects: [],
        },
      ],
      effects: [],
      environment: {
        name: 'Forest Clearing',
        description: 'A small clearing in the dense forest',
        size: { width: 50, height: 50 },
        terrain: 'difficult',
        lighting: 'dim',
        effects: ['cover'],
      },
    };

    setCombat(newCombat);
    sortInitiative(newCombat.initiative);
  };

  const startTurnAnimation = () => {
    turnAnimation.setValue(0);
    Animated.timing(turnAnimation, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();
  };

  const startCombat = () => {
    if (!combat || combat.initiative.length === 0) {
      Alert.alert('No Combatants', 'Add combatants to start combat.');
      return;
    }

    setIsCombatActive(true);
    setCombat({ ...combat, isActive: true });
    setCurrentTurn(0);

    HapticsService.triggerCombatTurn();
    AudioService.playSound('combat_start');
    VoiceService.announceCombatStart(combat.initiative.map(c => c.name));

    // Animate round change
    Animated.sequence([
      Animated.timing(roundAnimation, { toValue: 1.2, duration: 200, useNativeDriver: true }),
      Animated.timing(roundAnimation, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start();
  };

  const endCombat = () => {
    if (!combat) return;

    setIsCombatActive(false);
    setCombat({ ...combat, isActive: false });

    HapticsService.notificationSuccess();
    VoiceService.speak('Combat has ended');
  };

  const nextTurn = () => {
    if (!combat) return;

    const nextTurnIndex = (currentTurn + 1) % combat.initiative.length;

    if (nextTurnIndex === 0) {
      // New round
      setCurrentRound(currentRound + 1);
      setCombat({ ...combat, round: currentRound + 1 });
    }

    setCurrentTurn(nextTurnIndex);
    setCurrentTurnIndex(nextTurnIndex);

    // Announce next turn
    const nextCombatant = combat.initiative[nextTurnIndex];
    VoiceService.announceTurn(nextCombatant.name);
    HapticsService.triggerCombatTurn();
  };

  const setCurrentTurnIndex = (index: number) => {
    setCurrentTurn(index);
    if (combat) {
      setCombat({ ...combat, turn: index });
    }
  };

  const sortInitiative = (combatants: Combatant[]) => {
    return combatants.sort((a, b) => b.initiative - a.initiative);
  };

  const rollInitiative = async () => {
    if (!combat) return;

    HapticsService.impactMedium();

    // Roll initiative for all combatants
    const updatedInitiative = combat.initiative.map(combatant => {
      const roll = Math.floor(Math.random() * 20) + 1;
      const bonus = combatant.type === 'player' ? 2 : 0; // Players get +2 bonus
      const total = roll + bonus;

      return {
        ...combatant,
        initiative: total,
      };
    });

    const sorted = sortInitiative(updatedInitiative);
    setCombat({ ...combat, initiative: sorted });

    // Animate initiative sorting
    Animated.timing(initiativeAnimation, {
      toValue: 1,
      duration: 500,
      useNativeDriver: true,
    }).start();

    AudioService.playSound('dice_roll');
  };

  const applyDamage = () => {
    if (!selectedCombatant || !damageAmount) return;

    const damage = parseInt(damageAmount);
    if (isNaN(damage) || damage < 0) {
      Alert.alert('Invalid Damage', 'Please enter a valid damage amount.');
      return;
    }

    const updatedCombatant = {
      ...selectedCombatant,
      health: {
        ...selectedCombatant.health,
        current: Math.max(0, selectedCombatant.health.current - damage),
      },
    };

    updateCombatant(updatedCombatant);

    HapticsService.triggerHealthChange('damage');
    VoiceService.announceDamage(selectedCombatant.name, damage, damageType);

    setShowDamageDialog(false);
    setDamageAmount('');
  };

  const applyHealing = () => {
    if (!selectedCombatant || !damageAmount) return;

    const healing = parseInt(damageAmount);
    if (isNaN(healing) || healing < 0) {
      Alert.alert('Invalid Healing', 'Please enter a valid healing amount.');
      return;
    }

    const updatedCombatant = {
      ...selectedCombatant,
      health: {
        ...selectedCombatant.health,
        current: Math.min(selectedCombatant.health.max, selectedCombatant.health.current + healing),
      },
    };

    updateCombatant(updatedCombatant);

    HapticsService.triggerHealthChange('heal');
    VoiceService.announceHealing(selectedCombatant.name, healing);

    setShowDamageDialog(false);
    setDamageAmount('');
  };

  const updateCombatant = (updatedCombatant: Combatant) => {
    if (!combat) return;

    const updatedInitiative = combat.initiative.map(combatant =>
      combatant.id === updatedCombatant.id ? updatedCombatant : combatant
    );

    setCombat({ ...combat, initiative: updatedInitiative });

    if (selectedCombatant?.id === updatedCombatant.id) {
      setSelectedCombatant(updatedCombatant);
    }
  };

  const addCombatant = (combatant: Omit<Combatant, 'id'>) => {
    if (!combat) return;

    const newCombatant: Combatant = {
      ...combatant,
      id: Math.random().toString(36).substr(2, 9),
    };

    const updatedInitiative = [...combat.initiative, newCombatant];
    const sorted = sortInitiative(updatedInitiative);

    setCombat({ ...combat, initiative: sorted });
    setShowAddCombatant(false);

    HapticsService.selectionChanged();
  };

  const removeCombatant = (combatantId: string) => {
    if (!combat) return;

    Alert.alert(
      'Remove Combatant',
      'Are you sure you want to remove this combatant from combat?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            const updatedInitiative = combat.initiative.filter(c => c.id !== combatantId);
            setCombat({ ...combat, initiative: updatedInitiative });

            if (selectedCombatant?.id === combatantId) {
              setSelectedCombatant(null);
            }

            HapticsService.notificationError();
          },
        },
      ]
    );
  };

  const toggleCondition = (combatantId: string, condition: string) => {
    if (!combat) return;

    const updatedInitiative = combat.initiative.map(combatant => {
      if (combatant.id === combatantId) {
        const conditions = combatant.conditions.includes(condition)
          ? combatant.conditions.filter(c => c !== condition)
          : [...combatant.conditions, condition];

        return { ...combatant, conditions };
      }
      return combatant;
    });

    setCombat({ ...combat, initiative: updatedInitiative });
    HapticsService.selectionChanged();
  };

  const getHealthBarColor = (current: number, max: number) => {
    const percentage = (current / max) * 100;
    if (percentage > 50) return colors.success;
    if (percentage > 25) return colors.warning;
    return colors.error;
  };

  const getConditionColor = (condition: string) => {
    const conditionColors: Record<string, string> = {
      'blinded': colors.error,
      'charmed': colors.warning,
      'deafened': colors.textSecondary,
      'frightened': colors.error,
      'grappled': colors.warning,
      'incapacitated': colors.error,
      'invisible': colors.info,
      'paralyzed': colors.error,
      'petrified': colors.error,
      'poisoned': colors.warning,
      'prone': colors.textSecondary,
      'restrained': colors.warning,
      'stunned': colors.error,
      'unconscious': colors.error,
    };
    return conditionColors[condition] || colors.textSecondary;
  };

  const renderCombatantCard = (combatant: Combatant, index: number) => {
    const isCurrentTurn = isCombatActive && index === currentTurn;
    const isSelected = selectedCombatant?.id === combatant.id;

    return (
      <Animated.View
        key={combatant.id}
        style={[
          styles.combatantCard,
          isCurrentTurn && styles.currentTurnCard,
          isSelected && styles.selectedCard,
          {
            transform: [
              {
                translateX: isCurrentTurn ? turnAnimation.interpolate({
                  inputRange: [0, 1],
                  outputRange: [10, 0],
                }) : 0,
              },
            ],
          },
        ]}
      >
        <TouchableOpacity
          style={styles.combatantHeader}
          onPress={() => {
            setSelectedCombatant(combatant);
            HapticsService.selectionChanged();
          }}
          activeOpacity={0.7}
        >
          <View style={styles.combatantInfo}>
            <Avatar
              size="small"
              rounded
              title={combatant.name.substring(0, 2).toUpperCase()}
              containerStyle={[
                styles.avatar,
                { backgroundColor: combatant.type === 'player' ? colors.primary : colors.error }
              ]}
            />
            <View style={styles.combatantDetails}>
              <Text style={styles.combatantName}>{combatant.name}</Text>
              <View style={styles.combatantStats}>
                <Text style={styles.initiativeText}>
                  Init: {combatant.initiative}
                </Text>
                <Text style={styles.acText}>
                  AC: {combatant.ac}
                </Text>
                <Text style={styles.speedText}>
                  Speed: {combatant.speed}
                </Text>
              </View>
            </View>
          </View>

          {isCurrentTurn && (
            <View style={styles.currentTurnIndicator}>
              <Icon name="play-arrow" size={24} color={colors.success} />
              <Text style={styles.currentTurnText}>Current Turn</Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.removeButton}
            onPress={() => removeCombatant(combatant.id)}
          >
            <Icon name="close" size={20} color={colors.error} />
          </TouchableOpacity>
        </TouchableOpacity>

        <View style={styles.healthBar}>
          <View style={styles.healthInfo}>
            <Text style={styles.healthText}>
              {combatant.health.current}/{combatant.health.max}
            </Text>
            {combatant.health.temp > 0 && (
              <Text style={styles.tempHealthText}>
                +{combatant.health.temp} Temp
              </Text>
            )}
          </View>
          <View style={styles.healthBarBackground}>
            <View
              style={[
                styles.healthBarFill,
                {
                  width: `${(combatant.health.current / combatant.health.max) * 100}%`,
                  backgroundColor: getHealthBarColor(combatant.health.current, combatant.health.max),
                },
              ]}
            />
          </View>
        </View>

        {combatant.conditions.length > 0 && (
          <View style={styles.conditionsContainer}>
            {combatant.conditions.map((condition) => (
              <Chip
                key={condition}
                title={condition}
                type="outline"
                buttonStyle={{
                  backgroundColor: getConditionColor(condition) + '20',
                  borderColor: getConditionColor(condition),
                }}
                titleStyle={{
                  color: getConditionColor(condition),
                  fontSize: 10,
                }}
                containerStyle={styles.conditionChip}
                onPress={() => toggleCondition(combatant.id, condition)}
              />
            ))}
          </View>
        )}

        <View style={styles.actionButtons}>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: colors.error }]}
            onPress={() => {
              setSelectedCombatant(combatant);
              setShowDamageDialog(true);
              HapticsService.impactLight();
            }}
          >
            <Icon name="heart-broken" size={16} color={colors.text} />
            <Text style={styles.actionButtonText}>Damage</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: colors.success }]}
            onPress={() => {
              setSelectedCombatant(combatant);
              setShowDamageDialog(true);
              HapticsService.impactLight();
            }}
          >
            <Icon name="favorite" size={16} color={colors.text} />
            <Text style={styles.actionButtonText}>Heal</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: colors.info }]}
            onPress={() => {
              setSelectedCombatant(combatant);
              setShowEffectDialog(true);
              HapticsService.impactLight();
            }}
          >
            <Icon name="auto-fix-high" size={16} color={colors.text} />
            <Text style={styles.actionButtonText}>Effect</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    );
  };

  const renderCombatHeader = () => (
    <Card containerStyle={styles.headerCard}>
      <View style={styles.combatHeader}>
        <View style={styles.combatTitle}>
          <Animated.Text
            style={[
              styles.combatTitleText,
              {
                transform: [{ scale: roundAnimation }],
              },
            ]}
          >
            {combat?.environment.name || 'Combat'} - Round {currentRound}
          </Animated.Text>
          <View style={styles.combatStatus}>
            <Badge
              value={isCombatActive ? 'Active' : 'Paused'}
              status={isCombatActive ? 'success' : 'warning'}
            />
            {combat && (
              <Text style={styles.combatantCount}>
                {combat.initiative.length} Combatants
              </Text>
            )}
          </View>
        </View>

        <View style={styles.combatControls}>
          {!isCombatActive ? (
            <Button
              title="Start Combat"
              onPress={startCombat}
              icon={<Icon name="play-arrow" size={20} color={colors.text} />}
              buttonStyle={styles.startButton}
            />
          ) : (
            <View style={styles.activeControls}>
              <Button
                title="Next Turn"
                onPress={nextTurn}
                icon={<Icon name="skip-next" size={20} color={colors.text} />}
                buttonStyle={styles.nextTurnButton}
                containerStyle={styles.controlButton}
              />
              <Button
                title="End Combat"
                onPress={endCombat}
                icon={<Icon name="stop" size={20} color={colors.text} />}
                buttonStyle={styles.endButton}
                containerStyle={styles.controlButton}
              />
            </View>
          )}

          <TouchableOpacity
            style={styles.initiativeButton}
            onPress={rollInitiative}
            disabled={isCombatActive}
          >
            <Icon name="casino" size={20} color={colors.text} />
            <Text style={styles.initiativeButtonText}>Roll Init</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowAddCombatant(true)}
          >
            <Icon name="person-add" size={20} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>
    </Card>
  );

  const renderDamageDialog = () => (
    <Card containerStyle={styles.dialogCard}>
      <Text style={styles.dialogTitle}>
        {selectedCombatant?.name} - Apply {damageType.charAt(0).toUpperCase() + damageType.slice(1)}
      </Text>

      <Input
        placeholder="Amount"
        value={damageAmount}
        onChangeText={setDamageAmount}
        keyboardType="numeric"
        containerStyle={styles.dialogInput}
        inputStyle={styles.dialogInputText}
      />

      <View style={styles.damageTypeSelector}>
        {['bludgeoning', 'piercing', 'slashing', 'fire', 'cold', 'lightning', 'poison', 'psychic'].map((type) => (
          <TouchableOpacity
            key={type}
            style={[
              styles.damageTypeButton,
              damageType === type && styles.selectedDamageType,
            ]}
            onPress={() => {
              setDamageType(type);
              HapticsService.selectionChanged();
            }}
          >
            <Text style={[
              styles.damageTypeText,
              damageType === type && styles.selectedDamageTypeText,
            ]}>
              {type}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.dialogButtons}>
        <Button
          title="Cancel"
          type="outline"
          onPress={() => setShowDamageDialog(false)}
          containerStyle={styles.dialogButton}
        />
        <Button
          title="Apply Damage"
          onPress={applyDamage}
          containerStyle={styles.dialogButton}
        />
        <Button
          title="Apply Healing"
          onPress={applyHealing}
          buttonStyle={{ backgroundColor: colors.success }}
          containerStyle={styles.dialogButton}
        />
      </View>
    </Card>
  );

  return (
    <View style={styles.container}>
      {renderCombatHeader()}

      <ScrollView style={styles.combatantList} showsVerticalScrollIndicator={false}>
        {combat?.initiative.map((combatant, index) =>
          renderCombatantCard(combatant, index)
        )}
      </ScrollView>

      {showDamageDialog && selectedCombatant && renderDamageDialog()}

      {showAddCombatant && (
        <Card containerStyle={styles.dialogCard}>
          <Text style={styles.dialogTitle}>Add Combatant</Text>
          <Input
            placeholder="Name"
            // Handle input state
            containerStyle={styles.dialogInput}
          />
          <View style={styles.dialogButtons}>
            <Button
              title="Cancel"
              type="outline"
              onPress={() => setShowAddCombatant(false)}
              containerStyle={styles.dialogButton}
            />
            <Button
              title="Add"
              onPress={() => {
                // Handle adding combatant
                setShowAddCombatant(false);
              }}
              containerStyle={styles.dialogButton}
            />
          </View>
        </Card>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  headerCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    margin: spacing.md,
    marginBottom: spacing.sm,
  },
  combatHeader: {
    marginBottom: spacing.md,
  },
  combatTitle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  combatTitleText: {
    color: colors.text,
    fontSize: 20,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
  },
  combatStatus: {
    alignItems: 'flex-end',
  },
  combatantCount: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginTop: 4,
  },
  combatControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: colors.success,
    borderRadius: 25,
  },
  activeControls: {
    flexDirection: 'row',
    flex: 1,
  },
  controlButton: {
    flex: 1,
    marginHorizontal: 2,
  },
  nextTurnButton: {
    backgroundColor: colors.primary,
    borderRadius: 20,
  },
  endButton: {
    backgroundColor: colors.error,
    borderRadius: 20,
  },
  initiativeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.warning,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 20,
  },
  initiativeButtonText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginLeft: 4,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  combatantList: {
    flex: 1,
    paddingHorizontal: spacing.md,
  },
  combatantCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    borderRadius: 12,
    marginBottom: spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  currentTurnCard: {
    borderColor: colors.success,
    borderWidth: 2,
    shadowColor: colors.success,
    shadowOpacity: 0.3,
  },
  selectedCard: {
    borderColor: colors.primary,
    borderWidth: 2,
  },
  combatantHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
  },
  combatantInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    marginRight: spacing.md,
  },
  combatantDetails: {
    flex: 1,
  },
  combatantName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  combatantStats: {
    flexDirection: 'row',
    marginTop: 4,
  },
  initiativeText: {
    color: colors.primary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginRight: spacing.md,
  },
  acText: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginRight: spacing.md,
  },
  speedText: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  currentTurnIndicator: {
    alignItems: 'center',
  },
  currentTurnText: {
    color: colors.success,
    fontSize: 10,
    fontFamily: 'Lato-Regular',
  },
  removeButton: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: colors.error + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  healthBar: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  healthInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  healthText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  tempHealthText: {
    color: colors.info,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  healthBarBackground: {
    height: 8,
    backgroundColor: colors.background,
    borderRadius: 4,
    overflow: 'hidden',
  },
  healthBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  conditionsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  conditionChip: {
    marginRight: spacing.xs,
    marginBottom: spacing.xs,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 15,
    minWidth: 60,
    justifyContent: 'center',
  },
  actionButtonText: {
    color: colors.text,
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginLeft: 4,
  },
  dialogCard: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    borderRadius: 12,
    margin: spacing.md,
  },
  dialogTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  dialogInput: {
    marginBottom: spacing.md,
  },
  dialogInputText: {
    color: colors.text,
  },
  damageTypeSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  damageTypeButton: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    margin: 2,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: colors.primary + '50',
  },
  selectedDamageType: {
    backgroundColor: colors.primary,
  },
  damageTypeText: {
    color: colors.text,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  selectedDamageTypeText: {
    color: colors.background,
  },
  dialogButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: spacing.md,
  },
  dialogButton: {
    flex: 1,
    marginHorizontal: spacing.xs,
  },
});

export default CombatTrackerScreen;