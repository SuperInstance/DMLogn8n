import { EventEmitter } from 'events';
import OpenAI from 'openai';
import Replicate from 'replicate';
import puppeteer from 'puppeteer';
import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs/promises';
import path from 'path';
import { DatabaseService, IHighlight } from './database';
import { logger } from '@/utils/logger';

interface HighlightDetection {
  timestamp: number;
  type: 'combat' | 'roleplay' | 'dice-roll' | 'funny' | 'emotional' | 'important';
  confidence: number;
  description: string;
  audioLevel?: number;
  chatActivity?: number;
  visualCues?: string[];
}

interface ThumbnailConfig {
  style: 'fantasy' | 'realistic' | 'cartoon' | 'anime' | 'minimalist';
  textOverlay: boolean;
  showCharacters: boolean;
  showTitle: boolean;
  customPrompt?: string;
}

interface ClipGeneration {
  startTime: number;
  endTime: number;
  title: string;
  description: string;
  includeOverlay: boolean;
  quality: 'low' | 'medium' | 'high';
  format: 'mp4' | 'gif' | 'webm';
}

export class ContentService extends EventEmitter {
  private static instance: ContentService;
  private openai: OpenAI;
  private replicate: Replicate;
  private browser: puppeteer.Browser | null = null;
  private highlightDetectionQueue: HighlightDetection[] = [];
  private isProcessingHighlights = false;
  private isInitialized = false;

  private constructor() {
    super();
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
    this.replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN
    });
  }

  public static getInstance(): ContentService {
    if (!ContentService.instance) {
      ContentService.instance = new ContentService();
    }
    return ContentService.instance;
  }

  public static async initialize(): Promise<void> {
    const service = ContentService.getInstance();

    try {
      // Initialize Puppeteer for thumbnail generation
      service.browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
      });

      // Start highlight detection processing
      service.startHighlightProcessing();

      service.isInitialized = true;
      logger.info('Content Service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Content Service:', error);
      throw error;
    }
  }

  public static async generateAIThumbnail(
    title: string,
    description: string,
    config: ThumbnailConfig
  ): Promise<string> {
    const service = ContentService.getInstance();

    try {
      // Generate image with Replicate
      const prompt = service.buildThumbnailPrompt(title, description, config);

      const output = await service.replicate.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        {
          input: {
            prompt: prompt,
            width: 1280,
            height: 720,
            num_outputs: 1,
            num_inference_steps: 50,
            guidance_scale: 7.5,
            negative_prompt: "blurry, low quality, distorted, text, watermark, signature"
          }
        }
      );

      const imageUrl = Array.isArray(output) ? output[0] : output as string;

      // Add text overlay if requested
      if (config.textOverlay) {
        return await service.addTextOverlay(imageUrl, title, config);
      }

      // Download and save the image
      return await service.downloadImage(imageUrl, title);

    } catch (error) {
      logger.error('Failed to generate AI thumbnail:', error);
      throw error;
    }
  }

  private buildThumbnailPrompt(title: string, description: string, config: ThumbnailConfig): string {
    let prompt = '';

    switch (config.style) {
      case 'fantasy':
        prompt = `Epic fantasy artwork, Dungeons and Dragons theme, dramatic lighting, high quality digital painting, ${description}`;
        break;
      case 'realistic':
        prompt = `Photorealistic scene, cinematic lighting, high detail, professional photography style, ${description}`;
        break;
      case 'cartoon':
        prompt = `Colorful cartoon style, vibrant colors, fun and playful, digital illustration, ${description}`;
        break;
      case 'anime':
        prompt = `Anime style, dynamic pose, bright colors, manga art style, ${description}`;
        break;
      case 'minimalist':
        prompt = `Clean minimalist design, simple shapes, elegant composition, modern art style, ${description}`;
        break;
    }

    // Add specific elements based on content
    if (config.showCharacters) {
      prompt += ', detailed character designs, fantasy adventurers';
    }

    if (config.customPrompt) {
      prompt += `, ${config.customPrompt}`;
    }

    return prompt;
  }

  private async addTextOverlay(imageUrl: string, title: string, config: ThumbnailConfig): Promise<string> {
    if (!this.browser) {
      throw new Error('Browser not initialized');
    }

    const page = await this.browser.newPage();
    await page.setViewport({ width: 1280, height: 720 });

    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            width: 1280px;
            height: 720px;
            position: relative;
            overflow: hidden;
            background: url('${imageUrl}') no-repeat center center;
            background-size: cover;
          }
          .overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            padding: 40px;
            color: white;
            font-family: 'Cinzel', serif;
          }
          .title {
            font-size: 48px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            line-height: 1.2;
          }
          .subtitle {
            font-size: 24px;
            margin-top: 10px;
            opacity: 0.9;
          }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap" rel="stylesheet">
      </head>
      <body>
        <div class="overlay">
          <div class="title">${title}</div>
          <div class="subtitle">Live D&D Session</div>
        </div>
      </body>
      </html>
    `;

    await page.setContent(html);

    const screenshot = await page.screenshot({
      type: 'png',
      fullPage: false
    });

    await page.close();

    // Save screenshot
    const filename = `thumbnail_${Date.now()}.png`;
    const filepath = path.join('./uploads', filename);
    await fs.writeFile(filepath, screenshot);

    return `/uploads/${filename}`;
  }

  private async downloadImage(imageUrl: string, title: string): Promise<string> {
    const response = await fetch(imageUrl);
    const buffer = Buffer.from(await response.arrayBuffer());

    const filename = `thumbnail_${Date.now()}.png`;
    const filepath = path.join('./uploads', filename);
    await fs.writeFile(filepath, buffer);

    return `/uploads/${filename}`;
  }

  public static async detectHighlights(
    videoPath: string,
    sessionId: string,
    interval: number = 30
  ): Promise<IHighlight[]> {
    const service = ContentService.getInstance();
    const highlights: IHighlight[] = [];

    try {
      // Analyze video in chunks
      const duration = await service.getVideoDuration(videoPath);
      const chunkSize = interval; // seconds

      for (let timestamp = 0; timestamp < duration; timestamp += chunkSize) {
        const analysis = await service.analyzeVideoChunk(videoPath, timestamp, chunkSize);

        if (analysis.confidence > 0.7) {
          const highlight: IHighlight = {
            title: `${analysis.type.charAt(0).toUpperCase() + analysis.type.slice(1)} Moment`,
            description: analysis.description,
            timestamp,
            duration: Math.min(chunkSize, duration - timestamp),
            streamSession: sessionId,
            type: analysis.type,
            tags: service.generateTags(analysis),
            isAutoGenerated: true,
            confidence: analysis.confidence
          };

          highlights.push(highlight);

          // Save to database
          await DatabaseService.createHighlight(highlight);
        }
      }

      logger.info(`Detected ${highlights.length} highlights in session ${sessionId}`);
      service.emit('highlightsDetected', highlights);

      return highlights;

    } catch (error) {
      logger.error('Failed to detect highlights:', error);
      throw error;
    }
  }

  private async getVideoDuration(videoPath: string): Promise<number> {
    return new Promise((resolve, reject) => {
      ffmpeg.ffprobe(videoPath, (err, metadata) => {
        if (err) {
          reject(err);
        } else {
          resolve(metadata.format.duration || 0);
        }
      });
    });
  }

  private async analyzeVideoChunk(
    videoPath: string,
    startTime: number,
    duration: number
  ): Promise<HighlightDetection> {
    try {
      // Extract audio from chunk
      const audioPath = await this.extractAudioChunk(videoPath, startTime, duration);

      // Analyze audio for excitement levels
      const audioAnalysis = await this.analyzeAudio(audioPath);

      // Extract frame for visual analysis
      const framePath = await this.extractFrame(videoPath, startTime);
      const visualAnalysis = await this.analyzeFrame(framePath);

      // Get chat activity for this time period
      const chatActivity = await this.getChatActivity(startTime, startTime + duration);

      // Combine all signals
      const confidence = this.calculateConfidence(audioAnalysis, visualAnalysis, chatActivity);

      // Determine the type of moment
      const type = this.classifyMomentType(audioAnalysis, visualAnalysis, chatActivity);

      // Generate description
      const description = await this.generateHighlightDescription(type, confidence);

      return {
        timestamp: startTime,
        type,
        confidence,
        description,
        audioLevel: audioAnalysis.level,
        chatActivity: chatActivity.messages,
        visualCues: visualAnalysis.cues
      };

    } catch (error) {
      logger.error('Failed to analyze video chunk:', error);
      return {
        timestamp: startTime,
        type: 'important',
        confidence: 0,
        description: 'Analysis failed'
      };
    }
  }

  private async extractAudioChunk(videoPath: string, startTime: number, duration: number): Promise<string> {
    const outputPath = `temp_audio_${startTime}_${Date.now()}.wav`;

    return new Promise((resolve, reject) => {
      ffmpeg(videoPath)
        .seekInput(startTime)
        .duration(duration)
        .audioCodec('pcm_s16le')
        .audioFrequency(16000)
        .audioChannels(1)
        .format('wav')
        .output(outputPath)
        .on('end', () => resolve(outputPath))
        .on('error', reject)
        .run();
    });
  }

  private async extractFrame(videoPath: string, timestamp: number): Promise<string> {
    const outputPath = `temp_frame_${timestamp}_${Date.now()}.png`;

    return new Promise((resolve, reject) => {
      ffmpeg(videoPath)
        .seekInput(timestamp)
        .frames(1)
        .format('image2')
        .output(outputPath)
        .on('end', () => resolve(outputPath))
        .on('error', reject)
        .run();
    });
  }

  private async analyzeAudio(audioPath: string): Promise<{ level: number; hasSpeech: boolean; hasMusic: boolean }> {
    // This is a simplified implementation
    // In production, you'd use audio analysis libraries or APIs
    try {
      // For now, return random values as placeholder
      return {
        level: Math.random() * 100,
        hasSpeech: Math.random() > 0.5,
        hasMusic: Math.random() > 0.7
      };
    } catch (error) {
      logger.error('Audio analysis failed:', error);
      return { level: 0, hasSpeech: false, hasMusic: false };
    }
  }

  private async analyzeFrame(imagePath: string): Promise<{ cues: string[]; hasFaces: boolean; hasText: boolean }> {
    // This would use computer vision APIs in production
    try {
      // For now, return random analysis as placeholder
      return {
        cues: ['fantasy', 'adventure', 'magic'],
        hasFaces: Math.random() > 0.3,
        hasText: Math.random() > 0.6
      };
    } catch (error) {
      logger.error('Frame analysis failed:', error);
      return { cues: [], hasFaces: false, hasText: false };
    }
  }

  private async getChatActivity(startTime: number, endTime: number): Promise<{ messages: number; engagement: number }> {
    // This would query the database for chat messages in the time range
    try {
      // Placeholder implementation
      return {
        messages: Math.floor(Math.random() * 50),
        engagement: Math.random() * 100
      };
    } catch (error) {
      logger.error('Chat activity analysis failed:', error);
      return { messages: 0, engagement: 0 };
    }
  }

  private calculateConfidence(
    audio: any,
    visual: any,
    chat: any
  ): number {
    let confidence = 0;

    // Audio contributes 40%
    if (audio.level > 70) confidence += 0.4;
    else if (audio.level > 50) confidence += 0.3;
    else if (audio.level > 30) confidence += 0.2;

    // Visual contributes 30%
    if (visual.hasFaces) confidence += 0.2;
    if (visual.cues.length > 2) confidence += 0.1;

    // Chat contributes 30%
    if (chat.messages > 20) confidence += 0.3;
    else if (chat.messages > 10) confidence += 0.2;
    else if (chat.messages > 5) confidence += 0.1;

    return Math.min(confidence, 1);
  }

  private classifyMomentType(
    audio: any,
    visual: any,
    chat: any
  ): HighlightDetection['type'] {
    if (audio.level > 80 && chat.messages > 15) {
      return 'combat';
    } else if (visual.hasFaces && audio.hasSpeech) {
      return 'roleplay';
    } else if (audio.level > 70 && !audio.hasSpeech) {
      return 'funny';
    } else if (chat.engagement > 80) {
      return 'important';
    } else {
      return 'emotional';
    }
  }

  private async generateHighlightDescription(type: HighlightDetection['type'], confidence: number): Promise<string> {
    try {
      const prompt = `Generate a brief, exciting description for a Dungeons and Dragons stream highlight of type "${type}" with ${Math.round(confidence * 100)}% confidence. Keep it under 100 characters and make it sound exciting for viewers.`;

      const response = await this.openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          { role: "system", content: "You are a professional D&D stream editor creating highlight descriptions." },
          { role: "user", content: prompt }
        ],
        max_tokens: 50,
        temperature: 0.7
      });

      return response.choices[0]?.message?.content?.trim() || 'Exciting D&D moment!';

    } catch (error) {
      logger.error('Failed to generate highlight description:', error);
      return 'Exciting D&D moment!';
    }
  }

  private generateTags(analysis: HighlightDetection): string[] {
    const tags = [analysis.type];

    if (analysis.audioLevel > 70) tags.push('high-energy');
    if (analysis.chatActivity > 20) tags.push('chat-active');
    if (analysis.visualCues?.includes('fantasy')) tags.push('fantasy');
    if (analysis.visualCues?.includes('magic')) tags.push('magic');

    return tags;
  }

  private startHighlightProcessing(): void {
    setInterval(async () => {
      if (this.highlightDetectionQueue.length > 0 && !this.isProcessingHighlights) {
        this.isProcessingHighlights = true;

        while (this.highlightDetectionQueue.length > 0) {
          const detection = this.highlightDetectionQueue.shift()!;
          await this.processHighlightDetection(detection);
        }

        this.isProcessingHighlights = false;
      }
    }, 5000);
  }

  private async processHighlightDetection(detection: HighlightDetection): Promise<void> {
    try {
      // Process the detection and emit results
      this.emit('highlightDetected', detection);
    } catch (error) {
      logger.error('Failed to process highlight detection:', error);
    }
  }

  public static async createClip(config: ClipGeneration, inputVideo: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const outputPath = `clip_${Date.now()}.${config.format}`;

      let command = ffmpeg(inputVideo)
        .seekInput(config.startTime)
        .duration(config.endTime - config.startTime);

      if (config.quality === 'high') {
        command = command.videoBitrate('2000k').audioBitrate('192k');
      } else if (config.quality === 'medium') {
        command = command.videoBitrate('1000k').audioBitrate('128k');
      } else {
        command = command.videoBitrate('500k').audioBitrate('96k');
      }

      if (config.format === 'gif') {
        command = command
          .format('gif')
          .fps(15)
          .videoFilters('split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse');
      }

      command
        .output(path.join('./uploads', outputPath))
        .on('end', () => resolve(`/uploads/${outputPath}`))
        .on('error', reject)
        .run();
    });
  }

  public static async rollDice(diceNotation: string): Promise<any> {
    const service = ContentService.getInstance();

    // Parse dice notation (e.g., "2d6+3", "1d20", "4d8-2")
    const match = diceNotation.match(/(\d*)d(\d+)([+-]\d+)?/);

    if (!match) {
      throw new Error('Invalid dice notation');
    }

    const numDice = parseInt(match[1]) || 1;
    const diceSize = parseInt(match[2]);
    const modifier = parseInt(match[3]) || 0;

    const rolls = Array.from({ length: numDice }, () => Math.floor(Math.random() * diceSize) + 1);
    const total = rolls.reduce((sum, roll) => sum + roll, 0) + modifier;

    const result = {
      notation: diceNotation,
      rolls,
      modifier,
      total,
      diceSize,
      numDice,
      critical: diceSize === 20 ? (rolls[0] === 20 ? 'success' : rolls[0] === 1 ? 'failure' : null) : null
    };

    service.emit('diceRoll', result);
    return result;
  }

  public static async generateSessionSummary(sessionId: string): Promise<string> {
    const service = ContentService.getInstance();

    try {
      // Get session data and highlights
      const session = await DatabaseService.getStreamSession(sessionId);
      const highlights = await DatabaseService.getHighlightsBySession(sessionId);

      if (!session || highlights.length === 0) {
        return 'No highlights available for this session.';
      }

      const prompt = `
        Create an engaging summary of a Dungeons and Dragons streaming session with the following information:

        Session Title: ${session.title}
        Duration: ${session.duration ? Math.round(session.duration / 60) : 'Unknown'} minutes
        Number of Highlights: ${highlights.length}
        Highlight Types: ${highlights.map(h => h.type).join(', ')}

        Key Moments:
        ${highlights.slice(0, 5).map(h => `- ${h.title}: ${h.description}`).join('\n')}

        Create a compelling summary that would make viewers want to watch the VOD or highlights. Include the most exciting moments and keep it under 300 words.
      `;

      const response = await service.openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [
          { role: "system", content: "You are a professional D&D content creator writing engaging session summaries for viewers." },
          { role: "user", content: prompt }
        ],
        max_tokens: 400,
        temperature: 0.7
      });

      return response.choices[0]?.message?.content?.trim() || 'Session summary not available.';

    } catch (error) {
      logger.error('Failed to generate session summary:', error);
      return 'Failed to generate session summary.';
    }
  }

  public static async cleanup(): Promise<void> {
    const service = ContentService.getInstance();

    if (service.browser) {
      await service.browser.close();
      service.browser = null;
    }
  }
}

export default ContentService;