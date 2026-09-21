import { ShakeEventExpo } from 'expo';
import { store } from '../store';
import { showModal } from '../store/slices/uiSlice';
import { hapticService } from './hapticService';

class ShakeService {
  private subscription: any = null;
  private isEnabled = false;
  private lastShakeTime = 0;
  private shakeThreshold = 500; // milliseconds between shakes

  initialize(): void {
    this.setupShakeListener();
  }

  private setupShakeListener(): void {
    ShakeEventExpo.addListener(() => {
      this.handleShake();
    });
  }

  private async handleShake(): Promise<void> {
    const now = Date.now();

    // Prevent multiple rapid shakes
    if (now - this.lastShakeTime < this.shakeThreshold) {
      return;
    }

    this.lastShakeTime = now;

    // Check if shake to roll is enabled in settings
    const state = store.getState();
    const shakeToRollEnabled = state.settings?.settings?.gameplay?.shakeToRoll;

    if (!shakeToRollEnabled || !this.isEnabled) {
      return;
    }

    // Trigger haptic feedback
    hapticService.diceRoll();

    // Show dice roll modal
    store.dispatch(showModal({
      type: 'diceRoll',
      data: { triggeredBy: 'shake' },
    }));
  }

  enable(): void {
    this.isEnabled = true;
  }

  disable(): void {
    this.isEnabled = false;
  }

  toggle(): void {
    this.isEnabled = !this.isEnabled;
  }

  isShakeEnabled(): boolean {
    return this.isEnabled;
  }

  cleanup(): void {
    if (this.subscription) {
      this.subscription.remove();
      this.subscription = null;
    }
  }
}

export const shakeService = new ShakeService();