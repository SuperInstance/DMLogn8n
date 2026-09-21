import { EventEmitter } from 'events';
import tmi from 'tmi.js';
import { DatabaseService, IViewer, IDonation } from './database';
import { logger } from '@/utils/logger';

interface ChatMessage {
  platform: string;
  username: string;
  message: string;
  timestamp: Date;
  userId?: string;
  displayName?: string;
  badges?: string[];
  emotes?: any[];
  isMod?: boolean;
  isSubscriber?: boolean;
  isVIP?: boolean;
}

interface Poll {
  id: string;
  question: string;
  options: string[];
  votes: { [option: string]: number };
  totalVotes: number;
  endTime: Date;
  isActive: boolean;
  platform: string;
}

interface ChatModeration {
  filterLinks: boolean;
  filterProfanity: boolean;
  capsLimit: number;
  messageLengthLimit: number;
  timeoutDuration: number;
  bannedWords: string[];
  allowedUsers: string[];
}

export class EngagementService extends EventEmitter {
  private static instance: EngagementService;
  private chatClients: Map<string, any> = new Map();
  private polls: Map<string, Poll> = new Map();
  private moderationSettings: ChatModeration;
  private profanityList: Set<string> = new Set();
  private isInitialized = false;

  private constructor() {
    super();
    this.moderationSettings = {
      filterLinks: true,
      filterProfanity: true,
      capsLimit: 0.7,
      messageLengthLimit: 500,
      timeoutDuration: 300,
      bannedWords: [],
      allowedUsers: []
    };
  }

  public static getInstance(): EngagementService {
    if (!EngagementService.instance) {
      EngagementService.instance = new EngagementService();
    }
    return EngagementService.instance;
  }

  public static async initialize(): Promise<void> {
    const service = EngagementService.getInstance();

    try {
      // Initialize profanity filter
      await service.loadProfanityList();

      // Initialize chat connections
      await service.initializeTwitchChat();

      service.isInitialized = true;
      logger.info('Engagement Service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Engagement Service:', error);
      throw error;
    }
  }

  private async loadProfanityList(): Promise<void> {
    // Basic profanity list - in production, this would be more comprehensive
    this.profanityList = new Set([
      'profanity1', 'profanity2', 'profanity3'
      // Add more words as needed
    ]);
  }

  private async initializeTwitchChat(): Promise<void> {
    if (!process.env.TWITCH_BROADCASTER_ID) {
      logger.warn('Twitch broadcaster ID not configured, skipping Twitch chat');
      return;
    }

    try {
      const client = tmi.Client({
        channels: [process.env.TWITCH_BROADCASTER_ID],
        connection: {
          reconnect: true,
          secure: true
        },
        options: {
          debug: false
        }
      });

      // Event handlers
      client.on('message', async (channel, tags, message, self) => {
        if (self) return;

        const chatMessage: ChatMessage = {
          platform: 'twitch',
          username: tags.username!,
          message: message,
          timestamp: new Date(),
          userId: tags['user-id'],
          displayName: tags['display-name'],
          badges: Object.keys(tags.badges || {}),
          emotes: tags.emotes ? Object.values(tags.emotes).flat() : [],
          isMod: tags.mod,
          isSubscriber: tags.subscriber,
          isVIP: tags.badges?.hasOwnProperty('vip')
        };

        await this.processMessage(chatMessage);
      });

      client.on('connected', (addr, port) => {
        logger.info(`Connected to Twitch chat at ${addr}:${port}`);
      });

      client.on('disconnected', (reason) => {
        logger.warn(`Disconnected from Twitch chat: ${reason}`);
      });

      // Connect to Twitch
      await client.connect();
      this.chatClients.set('twitch', client);

    } catch (error) {
      logger.error('Failed to initialize Twitch chat:', error);
      throw error;
    }
  }

  public static async processMessage(message: ChatMessage): Promise<ChatMessage> {
    const service = EngagementService.getInstance();

    try {
      // Update viewer information
      await service.updateViewer(message);

      // Check for moderation
      const moderationResult = await service.moderateMessage(message);
      if (!moderationResult.allowed) {
        service.emit('messageBlocked', { message, reason: moderationResult.reason });
        return message; // Still return the message but it's blocked
      }

      // Process commands
      if (message.message.startsWith('!')) {
        await service.processCommand(message);
      }

      // Check for keywords (polls, betting, etc.)
      await service.processKeywords(message);

      // Emit message to clients
      service.emit('newMessage', message);

      // Store message for analytics
      await service.storeMessage(message);

      return message;

    } catch (error) {
      logger.error('Error processing chat message:', error);
      return message;
    }
  }

  private async updateViewer(message: ChatMessage): Promise<void> {
    try {
      const viewerData: Partial<IViewer> = {
        username: message.username,
        platforms: [message.platform],
        lastSeen: message.timestamp,
        engagement: {
          chatMessages: 1,
          polls: 0,
          reactions: 0
        },
        isFollower: message.isSubscriber || false,
        isSubscriber: message.isSubscriber || false
      };

      await DatabaseService.createOrUpdateViewer(viewerData);
    } catch (error) {
      logger.error('Failed to update viewer:', error);
    }
  }

  private async moderateMessage(message: ChatMessage): Promise<{ allowed: boolean; reason?: string }> {
    const msg = message.message.toLowerCase();

    // Check if user is allowed
    if (this.moderationSettings.allowedUsers.includes(message.username)) {
      return { allowed: true };
    }

    // Filter profanity
    if (this.moderationSettings.filterProfanity) {
      const words = msg.split(' ');
      for (const word of words) {
        if (this.profanityList.has(word) || this.moderationSettings.bannedWords.includes(word)) {
          await this.timeoutUser(message.username, this.moderationSettings.timeoutDuration);
          return { allowed: false, reason: 'Profanity detected' };
        }
      }
    }

    // Filter links
    if (this.moderationSettings.filterLinks) {
      const linkRegex = /(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/g;
      if (linkRegex.test(message.message)) {
        await this.deleteMessage(message);
        return { allowed: false, reason: 'Links not allowed' };
      }
    }

    // Check excessive caps
    if (this.moderationSettings.capsLimit > 0) {
      const upperCaseCount = (message.message.match(/[A-Z]/g) || []).length;
      const letterCount = (message.message.match(/[a-zA-Z]/g) || []).length;
      const capsRatio = letterCount > 0 ? upperCaseCount / letterCount : 0;

      if (capsRatio > this.moderationSettings.capsLimit) {
        await this.deleteMessage(message);
        return { allowed: false, reason: 'Excessive caps' };
      }
    }

    // Check message length
    if (message.message.length > this.moderationSettings.messageLengthLimit) {
      await this.deleteMessage(message);
      return { allowed: false, reason: 'Message too long' };
    }

    return { allowed: true };
  }

  private async processCommand(message: ChatMessage): Promise<void> {
    const parts = message.message.slice(1).split(' ');
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    switch (command) {
      case 'roll':
        await this.processRollCommand(message, args);
        break;
      case 'poll':
        await this.processPollCommand(message, args);
        break;
      case 'vote':
        await this.processVoteCommand(message, args);
        break;
      case 'character':
        await this.processCharacterCommand(message, args);
        break;
      case 'tip':
      case 'donate':
        await this.processDonationCommand(message, args);
        break;
      case 'uptime':
        await this.processUptimeCommand(message);
        break;
      case 'commands':
        await this.processCommandsCommand(message);
        break;
    }
  }

  private async processRollCommand(message: ChatMessage, args: string[]): Promise<void> {
    if (args.length === 0) {
      const diceRoll = {
        playerName: message.displayName || message.username,
        diceType: 'd20',
        rolls: [Math.floor(Math.random() * 20) + 1],
        modifier: 0,
        total: Math.floor(Math.random() * 20) + 1,
        isCritical: false
      };

      if (diceRoll.rolls[0] === 20) {
        diceRoll.isCritical = 'success';
      } else if (diceRoll.rolls[0] === 1) {
        diceRoll.isCritical = 'failure';
      }

      this.emit('diceRoll', diceRoll);
      return;
    }

    // Parse dice notation (e.g., 2d6+3)
    const diceNotation = args[0];
    const match = diceNotation.match(/(\d*)d(\d+)([+-]\d+)?/);

    if (match) {
      const numDice = parseInt(match[1]) || 1;
      const diceSize = parseInt(match[2]);
      const modifier = parseInt(match[3]) || 0;

      const rolls = Array.from({ length: numDice }, () => Math.floor(Math.random() * diceSize) + 1);
      const total = rolls.reduce((sum, roll) => sum + roll, 0) + modifier;

      const diceRoll = {
        playerName: message.displayName || message.username,
        diceType: `${numDice}d${diceSize}`,
        rolls,
        modifier,
        total,
        isCritical: diceSize === 20 && (rolls[0] === 20 || rolls[0] === 1)
          ? (rolls[0] === 20 ? 'success' : 'failure')
          : false
      };

      this.emit('diceRoll', diceRoll);
    }
  }

  private async processPollCommand(message: ChatMessage, args: string[]): Promise<void> {
    if (!message.isMod) {
      this.emit('chatMessage', {
        platform: message.platform,
        username: 'System',
        message: 'Only moderators can create polls!',
        timestamp: new Date()
      });
      return;
    }

    if (args.length < 3) {
      this.emit('chatMessage', {
        platform: message.platform,
        username: 'System',
        message: 'Usage: !poll "Question" "Option 1" "Option 2" ...',
        timestamp: new Date()
      });
      return;
    }

    const question = args[0].replace(/['"]/g, '');
    const options = args.slice(1).map(opt => opt.replace(/['"]/g, ''));

    const poll: Poll = {
      id: Date.now().toString(),
      question,
      options,
      votes: {},
      totalVotes: 0,
      endTime: new Date(Date.now() + 60000), // 1 minute poll
      isActive: true,
      platform: message.platform
    };

    // Initialize votes for each option
    options.forEach(option => {
      poll.votes[option] = 0;
    });

    this.polls.set(poll.id, poll);

    this.emit('pollCreated', poll);

    // Schedule poll end
    setTimeout(() => {
      this.endPoll(poll.id);
    }, 60000);
  }

  private async processVoteCommand(message: ChatMessage, args: string[]): Promise<void> {
    if (args.length === 0) return;

    const activePoll = Array.from(this.polls.values()).find(poll => poll.isActive);
    if (!activePoll) return;

    const vote = args[0].toLowerCase();
    const option = activePoll.options.find(opt => opt.toLowerCase() === vote);

    if (option) {
      activePoll.votes[option]++;
      activePoll.totalVotes++;

      this.emit('pollUpdated', activePoll);
    }
  }

  private async processCharacterCommand(message: ChatMessage, args: string[]): Promise<void> {
    const characterName = args.join(' ') || message.displayName || message.username;

    this.emit('showCharacter', {
      name: characterName,
      platform: message.platform,
      requestedBy: message.username
    });
  }

  private async processDonationCommand(message: ChatMessage, args: string[]): Promise<void> {
    this.emit('donationRequested', {
      username: message.username,
      platform: message.platform
    });
  }

  private async processUptimeCommand(message: ChatMessage): Promise<void> {
    const startTime = new Date(); // This should come from actual stream start time
    const uptime = Date.now() - startTime.getTime();

    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);

    this.emit('chatMessage', {
      platform: message.platform,
      username: 'System',
      message: `Stream uptime: ${hours}h ${minutes}m ${seconds}s`,
      timestamp: new Date()
    });
  }

  private async processCommandsCommand(message: ChatMessage): Promise<void> {
    const commands = [
      '!roll [dice] - Roll dice (e.g., !roll 2d6+3)',
      '!poll "Question" "Option 1" "Option 2" - Create poll (mods only)',
      '!vote <option> - Vote in active poll',
      '!character [name] - Show character sheet',
      '!tip - Get donation information',
      '!uptime - Show stream uptime'
    ];

    this.emit('chatMessage', {
      platform: message.platform,
      username: 'System',
      message: 'Available commands: ' + commands.join(', '),
      timestamp: new Date()
    });
  }

  private async processKeywords(message: ChatMessage): Promise<void> {
    // Check for betting keywords
    if (message.message.toLowerCase().includes('bet') || message.message.toLowerCase().includes('wager')) {
      this.emit('bettingInterest', { message, platform: message.platform });
    }

    // Check for donation keywords
    if (message.message.toLowerCase().includes('donate') || message.message.toLowerCase().includes('tip')) {
      this.emit('donationInterest', { message, platform: message.platform });
    }

    // Check for subscription keywords
    if (message.message.toLowerCase().includes('subscribe') || message.message.toLowerCase().includes('sub')) {
      this.emit('subscriptionInterest', { message, platform: message.platform });
    }
  }

  private async storeMessage(message: ChatMessage): Promise<void> {
    // Store message in Redis for analytics and chat history
    try {
      const messageData = {
        ...message,
        timestamp: message.timestamp.toISOString()
      };

      // Store with TTL (e.g., 24 hours)
      await DatabaseService.cacheData(
        `chat:message:${message.platform}:${message.timestamp.getTime()}`,
        messageData,
        86400
      );
    } catch (error) {
      logger.error('Failed to store message:', error);
    }
  }

  private async timeoutUser(username: string, duration: number): Promise<void> {
    const twitchClient = this.chatClients.get('twitch');
    if (twitchClient) {
      try {
        await twitchClient.timeout(process.env.TWITCH_BROADCASTER_ID!, username, duration, 'Automated moderation');
        logger.info(`Timed out user ${username} for ${duration} seconds`);
      } catch (error) {
        logger.error('Failed to timeout user:', error);
      }
    }
  }

  private async deleteMessage(message: ChatMessage): Promise<void> {
    // This would require additional message ID information from the chat platform
    // Implementation depends on platform API capabilities
  }

  private endPoll(pollId: string): Promise<void> {
    return new Promise((resolve) => {
      const poll = this.polls.get(pollId);
      if (poll) {
        poll.isActive = false;
        this.emit('pollEnded', poll);
        this.polls.delete(pollId);
      }
      resolve();
    });
  }

  // Public API methods

  public static async createPoll(question: string, options: string[], duration: number = 60000): Promise<Poll> {
    const service = EngagementService.getInstance();

    const poll: Poll = {
      id: Date.now().toString(),
      question,
      options,
      votes: {},
      totalVotes: 0,
      endTime: new Date(Date.now() + duration),
      isActive: true,
      platform: 'system'
    };

    options.forEach(option => {
      poll.votes[option] = 0;
    });

    service.polls.set(poll.id, poll);

    // Schedule poll end
    setTimeout(() => {
      service.endPoll(poll.id);
    }, duration);

    service.emit('pollCreated', poll);
    return poll;
  }

  public static getActivePolls(): Poll[] {
    const service = EngagementService.getInstance();
    return Array.from(service.polls.values()).filter(poll => poll.isActive);
  }

  public static updateModerationSettings(settings: Partial<ChatModeration>): void {
    const service = EngagementService.getInstance();
    service.moderationSettings = { ...service.moderationSettings, ...settings };
  }

  public static async sendChatMessage(platform: string, message: string): Promise<void> {
    const service = EngagementService.getInstance();
    const client = service.chatClients.get(platform);

    if (client && platform === 'twitch') {
      try {
        await client.say(process.env.TWITCH_BROADCASTER_ID!, message);
      } catch (error) {
        logger.error('Failed to send chat message:', error);
      }
    }
  }

  public static async disconnectAll(): Promise<void> {
    const service = EngagementService.getInstance();

    for (const [platform, client] of service.chatClients) {
      try {
        if (platform === 'twitch') {
          await client.disconnect();
        }
      } catch (error) {
        logger.error(`Failed to disconnect from ${platform}:`, error);
      }
    }

    service.chatClients.clear();
  }
}

export default EngagementService;