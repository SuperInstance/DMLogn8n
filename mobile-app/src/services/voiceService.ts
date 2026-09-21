import * as Speech from 'expo-speech';
import { Platform } from 'react-native';

export class VoiceService {
  private static isInitialized: boolean = false;
  private static isAvailable: boolean = false;
  private static defaultVoice: string | null = null;

  static async initialize(): Promise<void> {
    try {
      // Check if speech is available
      const voices = await Speech.getAvailableVoicesAsync();
      this.isAvailable = voices.length > 0;

      if (this.isAvailable) {
        // Find a suitable voice
        const englishVoices = voices.filter(voice =>
          voice.language.startsWith('en') && !voice.name.includes('legacy')
        );

        if (englishVoices.length > 0) {
          this.defaultVoice = englishVoices[0].identifier;
        }

        this.isInitialized = true;
      }
    } catch (error) {
      console.warn('Voice service initialization failed:', error);
      this.isAvailable = false;
    }
  }

  static async speak(
    text: string,
    options?: {
      voice?: string;
      pitch?: number;
      rate?: number;
      volume?: number;
      language?: string;
    }
  ): Promise<void> {
    if (!this.isAvailable || !text.trim()) return;

    try {
      const speechOptions = {
        voice: options?.voice || this.defaultVoice || undefined,
        pitch: options?.pitch || 1.0,
        rate: options?.rate || 0.9,
        volume: options?.volume || 1.0,
        language: options?.language || 'en-US',
      };

      await Speech.speak(text, speechOptions);
    } catch (error) {
      console.warn('Failed to speak text:', error);
    }
  }

  static async stop(): Promise<void> {
    try {
      await Speech.stop();
    } catch (error) {
      console.warn('Failed to stop speech:', error);
    }
  }

  static async pause(): Promise<void> {
    try {
      await Speech.pause();
    } catch (error) {
      console.warn('Failed to pause speech:', error);
    }
  }

  static async resume(): Promise<void> {
    try {
      await Speech.resume();
    } catch (error) {
      console.warn('Failed to resume speech:', error);
    }
  }

  static async isSpeaking(): Promise<boolean> {
    try {
      return await Speech.isSpeakingAsync();
    } catch (error) {
      console.warn('Failed to check if speaking:', error);
      return false;
    }
  }

  // D&D specific voice commands and responses
  static async announceDiceRoll(
    diceType: string,
    roll: number,
    modifier: number,
    total: number,
    characterName?: string
  ): Promise<void> {
    const prefix = characterName ? `${characterName} rolls` : 'You roll';
    let message = `${prefix} ${diceType}: ${roll}`;

    if (modifier !== 0) {
      const modStr = modifier >= 0 ? `+ ${modifier}` : `- ${Math.abs(modifier)}`;
      message += ` ${modStr}`;
    }

    message += ` = ${total}`;

    // Add emphasis for critical rolls
    if (diceType === 'd20') {
      if (roll === 20) {
        message = 'Critical success! ' + message;
      } else if (roll === 1) {
        message = 'Critical fumble! ' + message;
      }
    }

    await this.speak(message, {
      rate: 0.9,
      pitch: diceType === 'd20' && roll === 20 ? 1.2 : 1.0,
    });
  }

  static async announceSkillCheck(
    skillName: string,
    roll: number,
    modifier: number,
    total: number,
    success?: boolean
  ): Promise<void> {
    let message = `${skillName} check: ${roll}`;

    if (modifier !== 0) {
      const modStr = modifier >= 0 ? `+ ${modifier}` : `- ${Math.abs(modifier)}`;
      message += ` ${modStr}`;
    }

    message += ` = ${total}`;

    if (success !== undefined) {
      message += success ? ' Success!' : ' Failure!';
    }

    await this.speak(message, {
      rate: 0.9,
      pitch: success ? 1.1 : 0.9,
    });
  }

  static async announceCombatStart(characterNames: string[]): Promise<void> {
    const message = `Combat begins! Initiative order: ${characterNames.join(', ')}`;
    await this.speak(message, {
      rate: 1.0,
      pitch: 1.2,
      volume: 1.0,
    });
  }

  static async announceTurn(characterName: string): Promise<void> {
    const message = `${characterName}'s turn`;
    await this.speak(message, {
      rate: 1.0,
      pitch: 1.1,
    });
  }

  static async announceDamage(
    targetName: string,
    damage: number,
    damageType: string,
    isCritical: boolean = false
  ): Promise<void> {
    const prefix = isCritical ? 'Critical hit! ' : '';
    const message = `${prefix}${targetName} takes ${damage} ${damageType} damage`;

    await this.speak(message, {
      rate: 1.0,
      pitch: isCritical ? 1.3 : 1.0,
    });
  }

  static async announceHealing(
    targetName: string,
    amount: number
  ): Promise<void> {
    const message = `${targetName} heals for ${amount} hit points`;
    await this.speak(message, {
      rate: 0.9,
      pitch: 1.2,
    });
  }

  static async announceStatusEffect(
    targetName: string,
    effect: string,
    applied: boolean = true
  ): Promise<void> {
    const action = applied ? 'is now' : 'is no longer';
    const message = `${targetName} ${action} ${effect}`;

    await this.speak(message, {
      rate: 0.9,
    });
  }

  static async announceSpellCast(
    casterName: string,
    spellName: string,
    spellLevel: number
  ): Promise<void> {
    const levelText = spellLevel === 0 ? 'cantrip' : `level ${spellLevel} spell`;
    const message = `${casterName} casts ${spellName}, a ${levelText}`;

    await this.speak(message, {
      rate: 0.9,
      pitch: 1.0 + (spellLevel * 0.05),
    });
  }

  static async announceLevelUp(characterName: string, newLevel: number): Promise<void> {
    const message = `Congratulations! ${characterName} has reached level ${newLevel}!`;
    await this.speak(message, {
      rate: 1.0,
      pitch: 1.3,
      volume: 1.0,
    });
  }

  static async announceDeath(characterName: string): Promise<void> {
    const message = `${characterName} has fallen unconscious`;
    await this.speak(message, {
      rate: 0.8,
      pitch: 0.8,
      volume: 1.0,
    });
  }

  static async announceHealthStatus(
    characterName: string,
    current: number,
    maximum: number
  ): Promise<void> {
    const percentage = (current / maximum) * 100;
    let status = '';

    if (percentage <= 0) {
      status = 'is dead';
    } else if (percentage <= 25) {
      status = 'is critically wounded';
    } else if (percentage <= 50) {
      status = 'is wounded';
    } else if (percentage <= 75) {
      status = 'is injured';
    } else {
      status = 'is healthy';
    }

    const message = `${characterName} ${status} with ${current} of ${maximum} hit points`;
    await this.speak(message, {
      rate: 0.9,
    });
  }

  // Voice command processing
  static async processVoiceCommand(command: string): Promise<{
    action: string;
    params: Record<string, any>;
    confidence: number;
  } | null> {
    const lowerCommand = command.toLowerCase().trim();

    // Simple command matching - in a real app, this would use NLP
    const commandPatterns = [
      {
        pattern: /^(roll|throw)\s+(d\d+)(?:\s+([+-]\s*\d+))?/,
        action: 'roll',
        confidence: 0.9,
      },
      {
        pattern: /^(roll|throw)\s+(attack|skill|damage|heal)/,
        action: 'quick_roll',
        confidence: 0.8,
      },
      {
        pattern: /^(show|display)\s+(character|sheet|stats)/,
        action: 'show_character',
        confidence: 0.8,
      },
      {
        pattern: /^(next|end)\s+turn/,
        action: 'next_turn',
        confidence: 0.9,
      },
      {
        pattern: /^(cast|use)\s+(\w+)/,
        action: 'cast_spell',
        confidence: 0.7,
      },
      {
        pattern: /^(take|deal)\s+(\d+)\s+(damage|damage points)/,
        action: 'apply_damage',
        confidence: 0.8,
      },
      {
        pattern: /^(heal|restore)\s+(\d+)/,
        action: 'apply_healing',
        confidence: 0.8,
      },
    ];

    for (const pattern of commandPatterns) {
      const match = lowerCommand.match(pattern.pattern);
      if (match) {
        const params: Record<string, any> = {};

        if (pattern.action === 'roll') {
          params.dice = match[2];
          params.modifier = match[3] ? parseInt(match[3].replace(/\s/g, '')) : 0;
        } else if (pattern.action === 'quick_roll') {
          params.type = match[2];
        } else if (pattern.action === 'cast_spell') {
          params.spell = match[2];
        } else if (pattern.action === 'apply_damage') {
          params.amount = parseInt(match[2]);
        } else if (pattern.action === 'apply_healing') {
          params.amount = parseInt(match[2]);
        }

        return {
          action: pattern.action,
          params,
          confidence: pattern.confidence,
        };
      }
    }

    return null;
  }

  static async getAvailableVoices(): Promise<Speech.Voice[]> {
    try {
      return await Speech.getAvailableVoicesAsync();
    } catch (error) {
      console.warn('Failed to get available voices:', error);
      return [];
    }
  }

  static setDefaultVoice(voiceIdentifier: string): void {
    this.defaultVoice = voiceIdentifier;
  }

  static getIsAvailable(): boolean {
    return this.isAvailable;
  }

  static getIsInitialized(): boolean {
    return this.isInitialized;
  }
}