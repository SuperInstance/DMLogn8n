import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  Dimensions,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useDispatch } from 'react-redux';
import { sendDiceRoll } from '../../store/slices/messageSlice';
import { useTheme } from '../../hooks/useTheme';
import { useHaptic } from '../../contexts/HapticContext';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface DiceRollModalProps {
  visible: boolean;
  onClose: () => void;
  triggeredBy?: 'shake' | 'manual';
}

export const DiceRollModal: React.FC<DiceRollModalProps> = ({
  visible,
  onClose,
  triggeredBy = 'manual',
}) => {
  const theme = useTheme();
  const { diceRoll, success, criticalHit } = useHaptic();
  const dispatch = useDispatch();

  const [selectedDice, setSelectedDice] = useState('d20');
  const [modifier, setModifier] = useState('0');
  const [isRolling, setIsRolling] = useState(false);
  const [result, setResult] = useState<number | null>(null);
  const [rolls, setRolls] = useState<number[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [rollAnimation] = useState(new Animated.Value(0));

  const diceOptions = [
    { value: 'd4', label: 'd4' },
    { value: 'd6', label: 'd6' },
    { value: 'd8', label: 'd8' },
    { value: 'd10', label: 'd10' },
    { value: 'd12', label: 'd12' },
    { value: 'd20', label: 'd20' },
    { value: 'd100', label: 'd100' },
  ];

  useEffect(() => {
    if (visible && triggeredBy === 'shake') {
      setTimeout(() => handleRoll(), 500);
    }
  }, [visible, triggeredBy]);

  const handleRoll = () => {
    if (isRolling) return;

    setIsRolling(true);
    diceRoll();

    // Animate dice roll
    Animated.sequence([
      Animated.timing(rollAnimation, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.timing(rollAnimation, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();

    // Simulate rolling time
    setTimeout(() => {
      const sides = parseInt(selectedDice.substring(1));
      const numberOfDice = selectedDice === 'd100' ? 2 : 1;
      const newRolls = [];

      for (let i = 0; i < numberOfDice; i++) {
        newRolls.push(Math.floor(Math.random() * sides) + 1);
      }

      const rollResult = newRolls.reduce((sum, roll) => sum + roll, 0);
      const modifierValue = parseInt(modifier) || 0;
      const totalResult = rollResult + modifierValue;

      setResult(rollResult);
      setRolls(newRolls);
      setTotal(totalResult);

      // Special effects for critical rolls
      if (selectedDice === 'd20') {
        if (rollResult === 20) {
          criticalHit();
        } else if (rollResult === 1) {
          // Handle fumble effect
          diceRoll();
        } else {
          success();
        }
      } else {
        success();
      }

      setIsRolling(false);
    }, 1000);
  };

  const handleSendToChat = () => {
    if (total === null) return;

    // This would send the dice roll to the active chat
    const diceData = {
      campaignId: 'current-campaign-id', // Get from active campaign
      dice: selectedDice,
      result: result || 0,
      rolls,
      modifier: parseInt(modifier) || 0,
      total,
      reason: 'Manual roll',
    };

    dispatch(sendDiceRoll(diceData) as any);
    onClose();
  };

  const handleClose = () => {
    setResult(null);
    setRolls([]);
    setTotal(null);
    setModifier('0');
    onClose();
  };

  const getResultColor = () => {
    if (selectedDice !== 'd20' || result === null) return theme.colors.text;

    if (result === 20) return theme.colors.success;
    if (result === 1) return theme.colors.error;
    return theme.colors.text;
  };

  const getResultText = () => {
    if (selectedDice !== 'd20' || result === null) return null;

    if (result === 20) return 'CRITICAL HIT!';
    if (result === 1) return 'FUMBLE!';
    return null;
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose}>
            <Icon name="close" size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            Dice Roll
          </Text>
          <TouchableOpacity onPress={handleRoll} disabled={isRolling}>
            <Icon
              name="casino"
              size={24}
              color={isRolling ? theme.colors.textSecondary : theme.colors.primary}
            />
          </TouchableOpacity>
        </View>

        {/* Dice Selection */}
        <View style={styles.diceSelection}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Select Dice
          </Text>
          <View style={styles.diceGrid}>
            {diceOptions.map((dice) => (
              <TouchableOpacity
                key={dice.value}
                style={[
                  styles.diceOption,
                  {
                    backgroundColor:
                      selectedDice === dice.value
                        ? theme.colors.primary
                        : theme.colors.surface,
                    borderColor: theme.colors.border,
                  },
                ]}
                onPress={() => setSelectedDice(dice.value)}
              >
                <Text
                  style={[
                    styles.diceLabel,
                    {
                      color:
                        selectedDice === dice.value
                          ? 'white'
                          : theme.colors.text,
                    },
                  ]}
                >
                  {dice.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Modifier */}
        <View style={styles.modifierSection}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Modifier
          </Text>
          <View style={styles.modifierControls}>
            <TouchableOpacity
              style={[
                styles.modifierButton,
                { backgroundColor: theme.colors.surface },
              ]}
              onPress={() => setModifier((prev) => String(parseInt(prev) - 1))}
            >
              <Icon name="remove" size={20} color={theme.colors.text} />
            </TouchableOpacity>
            <View
              style={[
                styles.modifierDisplay,
                { backgroundColor: theme.colors.surface },
              ]}
            >
              <Text style={[styles.modifierText, { color: theme.colors.text }]}>
                {modifier}
              </Text>
            </View>
            <TouchableOpacity
              style={[
                styles.modifierButton,
                { backgroundColor: theme.colors.surface },
              ]}
              onPress={() => setModifier((prev) => String(parseInt(prev) + 1))}
            >
              <Icon name="add" size={20} color={theme.colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Result Display */}
        {isRolling && (
          <Animated.View
            style={[
              styles.rollingContainer,
              {
                transform: [
                  {
                    rotate: rollAnimation.interpolate({
                      inputRange: [0, 1],
                      outputRange: ['0deg', '360deg'],
                    }),
                  },
                ],
              },
            ]}
          >
            <Icon
              name="casino"
              size={80}
              color={theme.colors.primary}
            />
          </Animated.View>
        )}

        {!isRolling && result !== null && (
          <View style={styles.resultContainer}>
            <Text style={[styles.resultTitle, { color: theme.colors.textSecondary }]}>
              Roll Result
            </Text>
            <Text style={[styles.resultValue, { color: getResultColor() }]}>
              {rolls.join(' + ')}
            </Text>
            {parseInt(modifier) !== 0 && (
              <Text style={[styles.modifierResult, { color: theme.colors.textSecondary }]}>
                {modifier > 0 ? '+' : ''}{modifier}
              </Text>
            )}
            <View style={styles.totalContainer}>
              <Text style={[styles.totalLabel, { color: theme.colors.textSecondary }]}>
                Total
              </Text>
              <Text style={[styles.totalValue, { color: getResultColor() }]}>
                {total}
              </Text>
              {getResultText() && (
                <Text style={[styles.specialResult, { color: getResultColor() }]}>
                  {getResultText()}
                </Text>
              )}
            </View>
          </View>
        )}

        {/* Action Buttons */}
        {!isRolling && total !== null && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[
                styles.actionButton,
                { backgroundColor: theme.colors.surface },
              ]}
              onPress={handleRoll}
            >
              <Text style={[styles.actionButtonText, { color: theme.colors.text }]}>
                Roll Again
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.actionButton,
                { backgroundColor: theme.colors.primary },
              ]}
              onPress={handleSendToChat}
            >
              <Text style={styles.actionButtonText}>
                Send to Chat
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
  },
  diceSelection: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  diceGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  diceOption: {
    width: '30%',
    aspectRatio: 1,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    marginBottom: 10,
  },
  diceLabel: {
    fontSize: 16,
    fontWeight: '600',
  },
  modifierSection: {
    marginBottom: 30,
  },
  modifierControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modifierButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modifierDisplay: {
    width: 80,
    height: 50,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 20,
  },
  modifierText: {
    fontSize: 20,
    fontWeight: '600',
  },
  rollingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 40,
  },
  resultContainer: {
    alignItems: 'center',
    marginVertical: 40,
  },
  resultTitle: {
    fontSize: 16,
    marginBottom: 8,
  },
  resultValue: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  modifierResult: {
    fontSize: 20,
    marginBottom: 16,
  },
  totalContainer: {
    alignItems: 'center',
  },
  totalLabel: {
    fontSize: 14,
    marginBottom: 4,
  },
  totalValue: {
    fontSize: 48,
    fontWeight: 'bold',
  },
  specialResult: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 'auto',
  },
  actionButton: {
    flex: 1,
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 8,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});