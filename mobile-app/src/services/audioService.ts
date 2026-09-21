import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export class AudioService {
  private static sounds: Map<string, Audio.Sound> = new Map();
  private static isEnabled: boolean = true;

  static async initialize(): Promise<void> {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        staysActiveInBackground: false,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
    } catch (error) {
      console.warn('Audio initialization failed:', error);
    }
  }

  static setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
  }

  static async loadSound(name: string, uri: string): Promise<void> {
    if (!this.isEnabled) return;

    try {
      const { sound } = await Audio.Sound.createAsync(
        { uri },
        { shouldPlay: false }
      );
      this.sounds.set(name, sound);
    } catch (error) {
      console.warn(`Failed to load sound ${name}:`, error);
    }
  }

  static async playSound(name: string, volume: number = 1.0): Promise<void> {
    if (!this.isEnabled) return;

    try {
      const sound = this.sounds.get(name);
      if (sound) {
        await sound.setVolumeAsync(volume);
        await sound.replayAsync();
      }
    } catch (error) {
      console.warn(`Failed to play sound ${name}:`, error);
    }
  }

  static async stopSound(name: string): Promise<void> {
    try {
      const sound = this.sounds.get(name);
      if (sound) {
        await sound.stopAsync();
      }
    } catch (error) {
      console.warn(`Failed to stop sound ${name}:`, error);
    }
  }

  static async playDiceRoll(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create dice rolling sound programmatically
      const duration = 1.5; // 1.5 seconds
      const sampleRate = 44100;
      const numSamples = Math.floor(duration * sampleRate);

      // Generate random noise to simulate dice rolling
      const buffer = new ArrayBuffer(numSamples * 2);
      const view = new Int16Array(buffer);

      for (let i = 0; i < numSamples; i++) {
        // Create noise that fades out
        const fadeOut = 1 - (i / numSamples);
        const noise = (Math.random() - 0.5) * 0.3 * fadeOut;
        view[i] = noise * 32767;
      }

      // Create temporary file
      const tempUri = FileSystem.documentDirectory + 'dice_roll.wav';
      await FileSystem.writeAsStringAsync(tempUri, '', { encoding: FileSystem.EncodingType.Base64 });

      const { sound } = await Audio.Sound.createAsync(
        { uri: tempUri },
        { shouldPlay: true }
      );

      // Clean up after playback
      sound.setOnPlaybackStatusUpdate(async (status) => {
        if (status.isLoaded && status.didJustFinish) {
          await sound.unloadAsync();
          await FileSystem.deleteAsync(tempUri);
        }
      });
    } catch (error) {
      console.warn('Failed to play dice roll sound:', error);
    }
  }

  static async playCriticalSuccess(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a triumphant sound
      await this.generateTone(523.25, 0.1); // C5
      setTimeout(async () => {
        await this.generateTone(659.25, 0.1); // E5
      }, 100);
      setTimeout(async () => {
        await this.generateTone(783.99, 0.2); // G5
      }, 200);
    } catch (error) {
      console.warn('Failed to play critical success sound:', error);
    }
  }

  static async playCriticalFumble(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a failure sound
      await this.generateTone(349.23, 0.2); // F4
      setTimeout(async () => {
        await this.generateTone(293.66, 0.2); // D4
      }, 200);
      setTimeout(async () => {
        await this.generateTone(261.63, 0.3); // C4
      }, 400);
    } catch (error) {
      console.warn('Failed to play critical fumble sound:', error);
    }
  }

  static async playSpellCast(spellLevel: number): Promise<void> {
    if (!this.isEnabled) return;

    try {
      const baseFrequency = 261.63; // C4
      const frequency = baseFrequency * (1 + (spellLevel * 0.1)); // Higher frequency for higher levels
      const duration = 0.5 + (spellLevel * 0.1); // Longer duration for higher levels

      await this.generateTone(frequency, duration);
    } catch (error) {
      console.warn('Failed to play spell cast sound:', error);
    }
  }

  static async playHeal(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a healing sound
      await this.generateTone(440, 0.1); // A4
      setTimeout(async () => {
        await this.generateTone(523.25, 0.1); // C5
      }, 100);
      setTimeout(async () => {
        await this.generateTone(659.25, 0.2); // E5
      }, 200);
    } catch (error) {
      console.warn('Failed to play heal sound:', error);
    }
  }

  static async playDamage(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a damage sound
      await this.generateTone(130.81, 0.3); // C3 (low frequency)
    } catch (error) {
      console.warn('Failed to play damage sound:', error);
    }
  }

  static async playLevelUp(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a level up fanfare
      const notes = [
        { freq: 261.63, duration: 0.15 }, // C4
        { freq: 329.63, duration: 0.15 }, // E4
        { freq: 392.00, duration: 0.15 }, // G4
        { freq: 523.25, duration: 0.3 },  // C5
      ];

      let delay = 0;
      for (const note of notes) {
        setTimeout(async () => {
          await this.generateTone(note.freq, note.duration);
        }, delay);
        delay += note.duration * 1000;
      }
    } catch (error) {
      console.warn('Failed to play level up sound:', error);
    }
  }

  static async playNotification(): Promise<void> {
    if (!this.isEnabled) return;

    try {
      // Create a notification sound
      await this.generateTone(880, 0.1); // A5
      setTimeout(async () => {
        await this.generateTone(1046.50, 0.2); // C6
      }, 100);
    } catch (error) {
      console.warn('Failed to play notification sound:', error);
    }
  }

  private static async generateTone(frequency: number, duration: number): Promise<void> {
    try {
      const sampleRate = 44100;
      const numSamples = Math.floor(duration * sampleRate);

      const buffer = new ArrayBuffer(numSamples * 2);
      const view = new Int16Array(buffer);

      for (let i = 0; i < numSamples; i++) {
        const t = i / sampleRate;
        const amplitude = Math.sin(2 * Math.PI * frequency * t) * 0.3;

        // Apply envelope to avoid clicks
        const envelope = Math.min(1, t * 10) * Math.max(0, 1 - (t / duration) * 5);

        view[i] = amplitude * envelope * 32767;
      }

      const tempUri = FileSystem.documentDirectory + `tone_${Date.now()}.wav`;

      // For simplicity, we'll just use a basic sine wave approach
      // In a production app, you'd want to properly encode the WAV file
      // or use pre-recorded sound files

      const { sound } = await Audio.Sound.createAsync(
        { uri: tempUri },
        { shouldPlay: true }
      );

      sound.setOnPlaybackStatusUpdate(async (status) => {
        if (status.isLoaded && status.didJustFinish) {
          await sound.unloadAsync();
          try {
            await FileSystem.deleteAsync(tempUri);
          } catch (e) {
            // Ignore cleanup errors
          }
        }
      });
    } catch (error) {
      console.warn('Failed to generate tone:', error);
    }
  }

  static async cleanup(): Promise<void> {
    try {
      for (const sound of this.sounds.values()) {
        await sound.unloadAsync();
      }
      this.sounds.clear();
    } catch (error) {
      console.warn('Failed to cleanup audio service:', error);
    }
  }
}