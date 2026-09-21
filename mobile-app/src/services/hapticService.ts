import ReactNativeHapticFeedback, {
  HapticFeedbackTypes,
} from 'react-native-haptic-feedback';

class HapticService {
  private options = {
    enableVibrateFallback: true,
    ignoreAndroidSystemSettings: false,
  };

  // Light haptic for subtle feedback
  light(): void {
    ReactNativeHapticFeedback.trigger('impactLight', this.options);
  }

  // Medium haptic for standard feedback
  medium(): void {
    ReactNativeHapticFeedback.trigger('impactMedium', this.options);
  }

  // Heavy haptic for important feedback
  heavy(): void {
    ReactNativeHapticFeedback.trigger('impactHeavy', this.options);
  }

  // Success haptic for completed actions
  success(): void {
    ReactNativeHapticFeedback.trigger('notificationSuccess', this.options);
  }

  // Warning haptic for warnings
  warning(): void {
    ReactNativeHapticFeedback.trigger('notificationWarning', this.options);
  }

  // Error haptic for errors
  error(): void {
    ReactNativeHapticFeedback.trigger('notificationError', this.options);
  }

  // Selection haptic for UI selections
  selection(): void {
    ReactNativeHapticFeedback.trigger('selection', this.options);
  }

  // Notification haptic for incoming notifications
  notification(): void {
    ReactNativeHapticFeedback.trigger('notification', this.options);
  }

  // Dice roll haptic - sequence of haptics for rolling dice
  diceRoll(): void {
    // Simulate dice rolling with multiple haptics
    this.light();
    setTimeout(() => this.light(), 100);
    setTimeout(() => this.medium(), 200);
    setTimeout(() => this.heavy(), 300);
  }

  // Combat haptic - intense feedback for combat actions
  combat(): void {
    this.heavy();
    setTimeout(() => this.medium(), 150);
  }

  // Achievement unlock haptic - celebration pattern
  achievement(): void {
    this.success();
    setTimeout(() => this.light(), 200);
    setTimeout(() => this.light(), 400);
    setTimeout(() => this.success(), 600);
  }

  // Critical hit haptic - special feedback for critical successes
  criticalHit(): void {
    this.heavy();
    setTimeout(() => this.success(), 100);
    setTimeout(() => this.light(), 300);
  }

  // Level up haptic - progression feedback
  levelUp(): void {
    this.medium();
    setTimeout(() => this.heavy(), 200);
    setTimeout(() => this.success(), 400);
  }

  // Custom haptic with specified type
  custom(type: HapticFeedbackTypes): void {
    ReactNativeHapticFeedback.trigger(type, this.options);
  }

  // Check if haptic feedback is available
  async isAvailable(): Promise<boolean> {
    try {
      // On most devices haptic feedback is available
      // This could be enhanced with platform-specific checks
      return true;
    } catch (error) {
      return false;
    }
  }
}

export const hapticService = new HapticService();