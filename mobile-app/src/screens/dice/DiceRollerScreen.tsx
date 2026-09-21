import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  PanGestureHandler,
  State,
  Dimensions,
  TouchableOpacity,
  Vibration,
} from 'react-native';
import {
  Card,
  Button,
  Icon,
  Slider,
  Chip,
  Badge,
} from '@rneui/themed';
import { useAppSelector } from '../../store/hooks';
import { colors, spacing } from '../../theme/theme';
import { HapticsService } from '../../services/hapticsService';
import { AudioService } from '../../services/audioService';
import { DiceService, DiceRoll } from '../../services/diceService';
import { VoiceService } from '../../services/voiceService';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface DiceAnimation {
  id: string;
  type: string;
  value: number;
  x: Animated.Value;
  y: Animated.Value;
  rotation: Animated.Value;
  scale: Animated.Value;
  opacity: Animated.Value;
}

const DiceRollerScreen: React.FC = () => {
  const { activeCharacter } = useAppSelector(state => state.character);
  const { soundEnabled, hapticFeedbackEnabled } = useAppSelector(state => state.app);

  // State
  const [selectedDice, setSelectedDice] = useState<string[]>(['d20']);
  const [modifier, setModifier] = useState(0);
  const [numDice, setNumDice] = useState(1);
  const [isRolling, setIsRolling] = useState(false);
  const [rollHistory, setRollHistory] = useState<DiceRoll[]>([]);
  const [diceAnimations, setDiceAnimations] = useState<DiceAnimation[]>([]);
  const [currentTotal, setCurrentTotal] = useState<number | null>(null);

  // Animation refs
  const panRef = useRef<Animated.Value>(new Animated.Value(0));
  const shakeAnimation = useRef(new Animated.Value(1)).current;

  // Dice configuration
  const diceTypes = [
    { type: 'd4', sides: 4, color: colors.dice.d4, icon: 'change-history' },
    { type: 'd6', sides: 6, color: colors.dice.d6, icon: 'crop-square' },
    { type: 'd8', sides: 8, color: colors.dice.d8, icon: 'stop' },
    { type: 'd10', sides: 10, color: colors.dice.d10, icon: 'crop-16-9' },
    { type: 'd12', sides: 12, color: colors.dice.d12, icon: 'radio-button-checked' },
    { type: 'd20', sides: 20, color: colors.dice.d20, icon: 'help-outline' },
    { type: 'd100', sides: 100, color: colors.dice.d100, icon: 'grain' },
  ];

  // Quick roll presets
  const quickRolls = [
    { name: 'Attack', dice: ['d20'], mod: 'strength' },
    { name: 'Skill Check', dice: ['d20'], mod: 'custom' },
    { name: 'Damage', dice: ['d6'], mod: 'strength' },
    { name: 'Healing', dice: ['d8'], mod: 'wisdom' },
    { name: 'Advantage', dice: ['d20', 'd20'], mod: 'custom' },
    { name: 'Disadvantage', dice: ['d20', 'd20'], mod: 'custom' },
  ];

  useEffect(() => {
    // Setup shake animation
    const shakeSequence = Animated.sequence([
      Animated.timing(shakeAnimation, { toValue: 1.1, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 0.9, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 1.05, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 0.95, duration: 100, useNativeDriver: true }),
      Animated.timing(shakeAnimation, { toValue: 1, duration: 100, useNativeDriver: true }),
    ]);

    // Listen for shake gestures
    if (hapticFeedbackEnabled) {
      shakeAnimation.addListener(({ value }) => {
        if (value === 1.1) {
          HapticsService.impactHeavy();
        }
      });
    }

    return () => {
      shakeAnimation.removeAllListeners();
    };
  }, [hapticFeedbackEnabled, shakeAnimation]);

  const toggleDiceSelection = (diceType: string) => {
    HapticsService.selectionChanged();

    setSelectedDice(prev => {
      if (prev.includes(diceType)) {
        return prev.filter(d => d !== diceType);
      } else {
        return [...prev, diceType];
      }
    });
  };

  const createDiceAnimation = (type: string, value: number): DiceAnimation => {
    const id = Math.random().toString(36).substr(2, 9);

    return {
      id,
      type,
      value,
      x: new Animated.Value(Math.random() * 200 - 100),
      y: new Animated.Value(Math.random() * 200 - 100),
      rotation: new Animated.Value(0),
      scale: new Animated.Value(0.5),
      opacity: new Animated.Value(1),
    };
  };

  const animateDice = (animation: DiceAnimation) => {
    const duration = 1500 + Math.random() * 1000;

    // Scale animation
    Animated.timing(animation.scale, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();

    // Rotation animation
    Animated.loop(
      Animated.timing(animation.rotation, {
        toValue: 360,
        duration: 300,
        useNativeDriver: true,
      })
    ).start();

    // Position animation (rolling effect)
    const rollPath = Animated.sequence([
      Animated.timing(animation.x, {
        toValue: Math.random() * 100 - 50,
        duration: duration / 4,
        useNativeDriver: true,
      }),
      Animated.timing(animation.y, {
        toValue: Math.random() * 100 - 50,
        duration: duration / 4,
        useNativeDriver: true,
      }),
      Animated.timing(animation.x, {
        toValue: Math.random() * 100 - 50,
        duration: duration / 4,
        useNativeDriver: true,
      }),
      Animated.timing(animation.y, {
        toValue: 0,
        duration: duration / 4,
        useNativeDriver: true,
      }),
    ]);

    rollPath.start(() => {
      // Stop rotation and settle
      animation.rotation.stopAnimation();
      Animated.timing(animation.rotation, {
        toValue: Math.random() * 360,
        duration: 200,
        useNativeDriver: true,
      }).start();
    });
  };

  const performDiceRoll = async () => {
    if (selectedDice.length === 0 || isRolling) return;

    setIsRolling(true);
    setCurrentTotal(null);

    // Trigger haptic feedback
    if (hapticFeedbackEnabled) {
      HapticsService.impactHeavy();
      Vibration.vibrate(200);
    }

    // Play dice sound
    if (soundEnabled) {
      AudioService.playDiceRoll();
    }

    // Create animations for each die
    const animations: DiceAnimation[] = [];
    const rolls: { type: string; value: number; rolled: number }[] = [];

    for (let i = 0; i < numDice; i++) {
      for (const diceType of selectedDice) {
        const sides = parseInt(diceType.substring(1));
        const value = Math.floor(Math.random() * sides) + 1;
        const animation = createDiceAnimation(diceType, value);

        animations.push(animation);
        rolls.push({ type: diceType, value, rolled: value });
      }
    }

    setDiceAnimations(animations);

    // Animate all dice
    animations.forEach(animation => animateDice(animation));

    // Calculate total after animation
    setTimeout(() => {
      const total = rolls.reduce((sum, roll) => sum + roll.value, 0) + modifier;
      setCurrentTotal(total);

      // Create roll record
      const newRoll: DiceRoll = {
        id: Math.random().toString(36).substr(2, 9),
        userId: 'current-user', // Would come from auth
        characterId: activeCharacter?.id,
        type: selectedDice.join(' + '),
        formula: `${numDice > 1 ? numDice + 'x' : ''}${selectedDice.join(' + ')}${modifier >= 0 ? ' + ' : ' '}${modifier}`,
        rolls,
        total,
        modifier,
        reason: 'Manual Roll',
        timestamp: new Date().toISOString(),
        isCritical: selectedDice.includes('d20') && rolls.some(r => r.type === 'd20' && r.value === 20),
        isFumble: selectedDice.includes('d20') && rolls.some(r => r.type === 'd20' && r.value === 1),
      };

      setRollHistory(prev => [newRoll, ...prev.slice(0, 9)]);

      // Voice announcement
      if (soundEnabled) {
        let announcement = `You rolled ${total}`;
        if (newRoll.isCritical) announcement = 'Critical success! ' + announcement;
        if (newRoll.isFumble) announcement = 'Critical fumble! ' + announcement;
        VoiceService.speak(announcement);
      }

      // Final haptic feedback
      if (hapticFeedbackEnabled) {
        if (newRoll.isCritical) {
          HapticsService.notificationSuccess();
        } else if (newRoll.isFumble) {
          HapticsService.notificationError();
        } else {
          HapticsService.impactMedium();
        }
      }

      setIsRolling(false);

      // Clear animations after delay
      setTimeout(() => {
        setDiceAnimations([]);
      }, 3000);
    }, 2000);
  };

  const handleShakeGesture = (event: any) => {
    if (event.nativeEvent.state === State.ACTIVE && !isRolling) {
      // Shake detected - perform quick roll
      setSelectedDice(['d20']);
      setModifier(0);
      setNumDice(1);
      performDiceRoll();
    }
  };

  const clearHistory = () => {
    setRollHistory([]);
    HapticsService.impactLight();
  };

  const renderDiceSelector = () => (
    <Card containerStyle={styles.card}>
      <Text style={styles.sectionTitle}>Select Dice</Text>

      <View style={styles.diceGrid}>
        {diceTypes.map((dice) => (
          <TouchableOpacity
            key={dice.type}
            style={[
              styles.diceButton,
              selectedDice.includes(dice.type) && styles.selectedDiceButton,
              { borderColor: dice.color }
            ]}
            onPress={() => toggleDiceSelection(dice.type)}
            disabled={isRolling}
          >
            <Icon
              name={dice.icon}
              size={24}
              color={selectedDice.includes(dice.type) ? colors.text : dice.color}
            />
            <Text style={[
              styles.diceButtonText,
              selectedDice.includes(dice.type) && styles.selectedDiceButtonText
            ]}>
              {dice.type}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.diceControls}>
        <View style={styles.controlRow}>
          <Text style={styles.controlLabel}>Number of Dice:</Text>
          <View style={styles.numberControls}>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setNumDice(Math.max(1, numDice - 1))}
              disabled={isRolling}
            >
              <Icon name="remove" size={20} color={colors.text} />
            </TouchableOpacity>
            <Text style={styles.numberText}>{numDice}</Text>
            <TouchableOpacity
              style={styles.numberButton}
              onPress={() => setNumDice(Math.min(10, numDice + 1))}
              disabled={isRolling}
            >
              <Icon name="add" size={20} color={colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.controlRow}>
          <Text style={styles.controlLabel}>Modifier:</Text>
          <Slider
            value={modifier}
            onValueChange={setModifier}
            minimumValue={-10}
            maximumValue={20}
            step={1}
            thumbStyle={{ backgroundColor: colors.primary }}
            trackStyle={{ backgroundColor: colors.primary + '50' }}
            disabled={isRolling}
          />
          <Text style={styles.modifierText}>
            {modifier >= 0 ? '+' : ''}{modifier}
          </Text>
        </View>
      </View>
    </Card>
  );

  const renderRollArea = () => (
    <Card containerStyle={styles.rollCard}>
      <PanGestureHandler onGestureEvent={handleShakeGesture}>
        <Animated.View
          style={[
            styles.rollArea,
            { transform: [{ scale: shakeAnimation }] }
          ]}
        >
          {diceAnimations.length > 0 ? (
            <View style={styles.diceContainer}>
              {diceAnimations.map((animation) => (
                <Animated.View
                  key={animation.id}
                  style={[
                    styles.diceDisplay,
                    {
                      transform: [
                        { translateX: animation.x },
                        { translateY: animation.y },
                        { rotate: animation.rotation.interpolate({
                          inputRange: [0, 360],
                          outputRange: ['0deg', '360deg'],
                        })},
                        { scale: animation.scale },
                      ],
                      opacity: animation.opacity,
                    },
                  ]}
                >
                  <Text style={styles.diceValue}>{animation.value}</Text>
                  <Text style={styles.diceType}>{animation.type}</Text>
                </Animated.View>
              ))}
            </View>
          ) : (
            <View style={styles.rollPrompt}>
              <Icon name="casino" size={64} color={colors.primary} />
              <Text style={styles.rollPromptText}>
                Tap roll or shake device
              </Text>
            </View>
          )}

          {currentTotal !== null && (
            <View style={styles.totalDisplay}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={[
                styles.totalValue,
                rollHistory[0]?.isCritical && styles.criticalTotal,
                rollHistory[0]?.isFumble && styles.fumbleTotal,
              ]}>
                {currentTotal}
              </Text>
              {rollHistory[0]?.isCritical && (
                <Badge value="CRITICAL!" status="success" />
              )}
              {rollHistory[0]?.isFumble && (
                <Badge value="FUMBLE!" status="error" />
              )}
            </View>
          )}
        </Animated.View>
      </PanGestureHandler>

      <Button
        title={isRolling ? 'Rolling...' : 'Roll Dice'}
        onPress={performDiceRoll}
        disabled={isRolling || selectedDice.length === 0}
        buttonStyle={[styles.rollButton, isRolling && styles.rollButtonDisabled]}
        titleStyle={styles.rollButtonText}
        icon={<Icon name="casino" size={20} color={colors.text} />}
      />
    </Card>
  );

  const renderQuickRolls = () => (
    <Card containerStyle={styles.card}>
      <Text style={styles.sectionTitle}>Quick Rolls</Text>

      <View style={styles.quickRollGrid}>
        {quickRolls.map((quickRoll) => (
          <TouchableOpacity
            key={quickRoll.name}
            style={styles.quickRollButton}
            onPress={() => {
              setSelectedDice(quickRoll.dice);
              if (quickRoll.mod === 'strength' && activeCharacter) {
                setModifier(activeCharacter.stats.strengthMod);
              } else if (quickRoll.mod === 'dexterity' && activeCharacter) {
                setModifier(activeCharacter.stats.dexterityMod);
              } else if (quickRoll.mod === 'wisdom' && activeCharacter) {
                setModifier(activeCharacter.stats.wisdomMod);
              }
              performDiceRoll();
            }}
            disabled={isRolling}
          >
            <Text style={styles.quickRollText}>{quickRoll.name}</Text>
            <Text style={styles.quickRollDice}>{quickRoll.dice.join(' + ')}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </Card>
  );

  const renderHistory = () => (
    <Card containerStyle={styles.card}>
      <View style={styles.historyHeader}>
        <Text style={styles.sectionTitle}>Recent Rolls</Text>
        {rollHistory.length > 0 && (
          <TouchableOpacity onPress={clearHistory}>
            <Icon name="clear" size={20} color={colors.error} />
          </TouchableOpacity>
        )}
      </View>

      {rollHistory.length === 0 ? (
        <Text style={styles.emptyHistoryText}>No rolls yet</Text>
      ) : (
        <View style={styles.historyList}>
          {rollHistory.map((roll) => (
            <TouchableOpacity
              key={roll.id}
              style={styles.historyItem}
              onPress={() => {
                setSelectedDice(roll.type.split(' + '));
                setModifier(roll.modifier);
                setNumDice(roll.rolls.length);
              }}
            >
              <View style={styles.historyInfo}>
                <Text style={styles.historyFormula}>{roll.formula}</Text>
                <Text style={styles.historyReason}>{roll.reason}</Text>
              </View>
              <View style={styles.historyResult}>
                <Text style={[
                  styles.historyTotal,
                  roll.isCritical && styles.criticalTotal,
                  roll.isFumble && styles.fumbleTotal,
                ]}>
                  {roll.total}
                </Text>
                {roll.isCritical && (
                  <Icon name="star" size={16} color={colors.success} />
                )}
                {roll.isFumble && (
                  <Icon name="close" size={16} color={colors.error} />
                )}
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </Card>
  );

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {renderQuickRolls()}
        {renderDiceSelector()}
        {renderRollArea()}
        {renderHistory()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    borderRadius: 12,
    marginBottom: spacing.md,
  },
  rollCard: {
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.primary + '50',
    borderRadius: 16,
    marginBottom: spacing.md,
    minHeight: 300,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
    marginBottom: spacing.md,
  },
  diceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  diceButton: {
    width: '30%',
    aspectRatio: 1,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  selectedDiceButton: {
    backgroundColor: colors.primary,
  },
  diceButtonText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginTop: 4,
  },
  selectedDiceButtonText: {
    color: colors.background,
  },
  diceControls: {
    marginTop: spacing.md,
  },
  controlRow: {
    marginBottom: spacing.md,
  },
  controlLabel: {
    color: colors.text,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    marginBottom: spacing.sm,
  },
  numberControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: spacing.md,
  },
  numberText: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginHorizontal: spacing.lg,
  },
  modifierText: {
    color: colors.primary,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  rollArea: {
    minHeight: 200,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  diceContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 60,
  },
  diceDisplay: {
    width: 60,
    height: 60,
    backgroundColor: colors.primary,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    margin: spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4.65,
    elevation: 8,
  },
  diceValue: {
    color: colors.text,
    fontSize: 24,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  diceType: {
    color: colors.text,
    fontSize: 10,
    fontFamily: 'Lato-Regular',
  },
  rollPrompt: {
    alignItems: 'center',
  },
  rollPromptText: {
    color: colors.textSecondary,
    fontSize: 16,
    fontFamily: 'Lato-Regular',
    marginTop: spacing.sm,
  },
  totalDisplay: {
    position: 'absolute',
    bottom: 70,
    alignItems: 'center',
  },
  totalLabel: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
  },
  totalValue: {
    color: colors.text,
    fontSize: 48,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
  },
  criticalTotal: {
    color: colors.success,
  },
  fumbleTotal: {
    color: colors.error,
  },
  rollButton: {
    backgroundColor: colors.primary,
    borderRadius: 25,
    height: 50,
    marginTop: spacing.md,
  },
  rollButtonDisabled: {
    backgroundColor: colors.textSecondary,
  },
  rollButtonText: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
  },
  quickRollGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickRollButton: {
    width: '48%',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    borderRadius: 8,
    padding: spacing.sm,
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  quickRollText: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  quickRollDice: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  emptyHistoryText: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  historyList: {
    maxHeight: 200,
  },
  historyItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.background,
    padding: spacing.sm,
    borderRadius: 8,
    marginBottom: spacing.sm,
  },
  historyInfo: {
    flex: 1,
  },
  historyFormula: {
    color: colors.text,
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  historyReason: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  historyResult: {
    alignItems: 'flex-end',
  },
  historyTotal: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
});

export default DiceRollerScreen;