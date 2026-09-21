import * as Haptics from 'expo-haptics';

export class HapticsService {
  static async selectionChanged(): Promise<void> {
    try {
      await Haptics.selectionAsync();
    } catch (error) {
      console.warn('Haptics selection failed:', error);
    }
  }

  static async impactLight(): Promise<void> {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (error) {
      console.warn('Haptics light impact failed:', error);
    }
  }

  static async impactMedium(): Promise<void> {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (error) {
      console.warn('Haptics medium impact failed:', error);
    }
  }

  static async impactHeavy(): Promise<void> {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    } catch (error) {
      console.warn('Haptics heavy impact failed:', error);
    }
  }

  static async notificationSuccess(): Promise<void> {
    try {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      console.warn('Haptics success notification failed:', error);
    }
  }

  static async notificationError(): Promise<void> {
    try {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    } catch (error) {
      console.warn('Haptics error notification failed:', error);
    }
  }

  static async notificationWarning(): Promise<void> {
    try {
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    } catch (error) {
      console.warn('Haptics warning notification failed:', error);
    }
  }

  static async triggerDiceRoll(type: string): Promise<void> {
    try {
      // Different haptic patterns for different dice
      switch (type) {
        case 'd4':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'd6':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'd8':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'd10':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'd12':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'd20':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
        case 'd100':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
        default:
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      }
    } catch (error) {
      console.warn('Haptics dice roll failed:', error);
    }
  }

  static async triggerCriticalHit(): Promise<void> {
    try {
      // Custom sequence for critical hits
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      setTimeout(async () => {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }, 200);
    } catch (error) {
      console.warn('Haptics critical hit failed:', error);
    }
  }

  static async triggerCriticalFumble(): Promise<void> {
    try {
      // Custom sequence for critical fumbles
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      setTimeout(async () => {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      }, 200);
    } catch (error) {
      console.warn('Haptics critical fumble failed:', error);
    }
  }

  static async triggerLevelUp(): Promise<void> {
    try {
      // Celebration pattern for level up
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setTimeout(async () => {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      }, 300);
      setTimeout(async () => {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }, 600);
    } catch (error) {
      console.warn('Haptics level up failed:', error);
    }
  }

  static async triggerCombatTurn(): Promise<void> {
    try {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    } catch (error) {
      console.warn('Haptics combat turn failed:', error);
    }
  }

  static async triggerSpellCast(spellLevel: number): Promise<void> {
    try {
      // Different haptic intensity based on spell level
      if (spellLevel <= 2) {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } else if (spellLevel <= 5) {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      } else {
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
      }
    } catch (error) {
      console.warn('Haptics spell cast failed:', error);
    }
  }

  static async triggerHealthChange(type: 'damage' | 'heal'): Promise<void> {
    try {
      if (type === 'damage') {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      } else {
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (error) {
      console.warn('Haptics health change failed:', error);
    }
  }
}