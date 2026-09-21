import axios from 'axios';
import { EventEmitter } from 'events';
import { logger } from '@/utils/logger';
import { DatabaseService, IStreamSession } from './database';

interface StreamConfig {
  platform: 'twitch' | 'youtube' | 'facebook' | 'tiktok' | 'rtmp';
  title: string;
  description: string;
  tags: string[];
  category: string;
  latency: 'low' | 'normal' | 'high';
  quality: '720p' | '1080p' | '4k';
  bitrate: number;
  fps: number;
}

interface PlatformCredentials {
  twitch?: {
    clientId: string;
    clientSecret: string;
    broadcasterId: string;
    accessToken: string;
    refreshToken: string;
  };
  youtube?: {
    apiKey: string;
    clientId: string;
    clientSecret: string;
    accessToken: string;
    refreshToken: string;
    channelId: string;
  };
  facebook?: {
    appId: string;
    appSecret: string;
    pageId: string;
    accessToken: string;
  };
  tiktok?: {
    clientId: string;
    clientSecret: string;
    accessToken: string;
  };
  rtmp?: {
    serverUrl: string;
    streamKey: string;
  };
}

export class StreamingService extends EventEmitter {
  private static instance: StreamingService;
  private activeStreams: Map<string, any> = new Map();
  private credentials: PlatformCredentials = {};
  private isInitialized = false;

  private constructor() {
    super();
  }

  public static getInstance(): StreamingService {
    if (!StreamingService.instance) {
      StreamingService.instance = new StreamingService();
    }
    return StreamingService.instance;
  }

  public static async initialize(): Promise<void> {
    const service = StreamingService.getInstance();

    try {
      // Load credentials from environment
      service.credentials = {
        twitch: {
          clientId: process.env.TWITCH_CLIENT_ID!,
          clientSecret: process.env.TWITCH_CLIENT_SECRET!,
          broadcasterId: process.env.TWITCH_BROADCASTER_ID!,
          accessToken: '',
          refreshToken: ''
        },
        youtube: {
          apiKey: process.env.YOUTUBE_API_KEY!,
          clientId: process.env.YOUTUBE_CLIENT_ID!,
          clientSecret: process.env.YOUTUBE_CLIENT_SECRET!,
          accessToken: '',
          refreshToken: '',
          channelId: process.env.YOUTUBE_CHANNEL_ID!
        },
        facebook: {
          appId: process.env.FACEBOOK_APP_ID!,
          appSecret: process.env.FACEBOOK_APP_SECRET!,
          pageId: process.env.FACEBOOK_PAGE_ID!,
          accessToken: ''
        },
        tiktok: {
          clientId: process.env.TIKTOK_CLIENT_ID!,
          clientSecret: process.env.TIKTOK_CLIENT_SECRET!,
          accessToken: ''
        },
        rtmp: {
          serverUrl: process.env.RTMP_SERVER_URL!,
          streamKey: process.env.RTMP_STREAM_KEY!
        }
      };

      service.isInitialized = true;
      logger.info('Streaming Service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Streaming Service:', error);
      throw error;
    }
  }

  public static isReady(): boolean {
    return StreamingService.getInstance().isInitialized;
  }

  public static async startStream(config: StreamConfig[]): Promise<any> {
    const service = StreamingService.getInstance();
    const results = [];

    // Create stream session in database
    const sessionData: Partial<IStreamSession> = {
      title: config[0]?.title || 'D&D Session',
      description: config[0]?.description || 'Live D&D session streaming',
      platforms: config.map(c => c.platform),
      startTime: new Date(),
      status: 'live',
      metadata: {
        campaign: 'Unknown Campaign',
        sessionNumber: await service.getNextSessionNumber(),
        tags: config[0]?.tags || [],
        characters: []
      }
    };

    const session = await DatabaseService.createStreamSession(sessionData);

    // Start streaming on each platform
    for (const platformConfig of config) {
      try {
        let result;

        switch (platformConfig.platform) {
          case 'twitch':
            result = await service.startTwitchStream(platformConfig, session._id);
            break;
          case 'youtube':
            result = await service.startYouTubeStream(platformConfig, session._id);
            break;
          case 'facebook':
            result = await service.startFacebookStream(platformConfig, session._id);
            break;
          case 'tiktok':
            result = await service.startTikTokStream(platformConfig, session._id);
            break;
          case 'rtmp':
            result = await service.startRTMPStream(platformConfig, session._id);
            break;
          default:
            throw new Error(`Unsupported platform: ${platformConfig.platform}`);
        }

        service.activeStreams.set(`${platformConfig.platform}-${session._id}`, result);
        results.push(result);

        service.emit('streamStarted', { platform: platformConfig.platform, session, result });

      } catch (error) {
        logger.error(`Failed to start ${platformConfig.platform} stream:`, error);
        results.push({ platform: platformConfig.platform, error: error.message });
      }
    }

    return { session, streams: results };
  }

  public static async stopStream(sessionId?: string): Promise<any> {
    const service = StreamingService.getInstance();
    const results = [];

    if (!sessionId) {
      // Stop all active streams
      for (const [key, stream] of service.activeStreams) {
        try {
          const [platform, streamSessionId] = key.split('-');
          await service.stopPlatformStream(platform, streamSessionId);
          results.push({ platform, success: true });
        } catch (error) {
          results.push({ platform: key.split('-')[0], error: error.message });
        }
      }
      service.activeStreams.clear();
    } else {
      // Stop specific session
      for (const [key, stream] of service.activeStreams) {
        if (key.endsWith(sessionId)) {
          try {
            const [platform] = key.split('-');
            await service.stopPlatformStream(platform, sessionId);
            service.activeStreams.delete(key);
            results.push({ platform, success: true });
          } catch (error) {
            results.push({ platform: key.split('-')[0], error: error.message });
          }
        }
      }
    }

    // Update session in database
    if (sessionId) {
      await DatabaseService.updateStreamSession(sessionId, {
        endTime: new Date(),
        status: 'ended',
        duration: Math.floor((Date.now() - new Date().getTime()) / 1000)
      });
    }

    service.emit('streamStopped', { sessionId, results });
    return results;
  }

  private async startTwitchStream(config: StreamConfig, sessionId: string): Promise<any> {
    const credentials = this.credentials.twitch;

    try {
      // Get access token if needed
      if (!credentials.accessToken) {
        await this.refreshTwitchToken();
      }

      // Get channel info
      const channelResponse = await axios.get(`https://api.twitch.tv/helix/channels?broadcaster_id=${credentials.broadcasterId}`, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Client-Id': credentials.clientId
        }
      });

      // Update channel info
      await axios.patch(`https://api.twitch.tv/helix/channels?broadcaster_id=${credentials.broadcasterId}`, {
        game_id: '509658', // Dungeons & Dragons category ID
        title: config.title,
        tags: config.tags.slice(0, 10) // Twitch allows max 10 tags
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Client-Id': credentials.clientId,
          'Content-Type': 'application/json'
        }
      });

      // Start commercial (optional)
      // await axios.post(`https://api.twitch.tv/helix/channels/commercial`, {
      //   broadcaster_id: credentials.broadcasterId,
      //   length: 60
      // }, {
      //   headers: {
      //     'Authorization': `Bearer ${credentials.accessToken}`,
      //     'Client-Id': credentials.clientId
      //   }
      // });

      return {
        platform: 'twitch',
        streamUrl: `https://www.twitch.tv/${channelResponse.data.data[0].broadcaster_login}`,
        streamKey: credentials.broadcasterId,
        ingestUrl: 'rtmp://live.twitch.tv/app',
        status: 'live'
      };

    } catch (error) {
      logger.error('Twitch streaming error:', error);
      throw error;
    }
  }

  private async startYouTubeStream(config: StreamConfig, sessionId: string): Promise<any> {
    const credentials = this.credentials.youtube;

    try {
      if (!credentials.accessToken) {
        await this.refreshYouTubeToken();
      }

      // Create live broadcast
      const broadcastResponse = await axios.post('https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails', {
        snippet: {
          title: config.title,
          description: config.description,
          scheduledStartTime: new Date().toISOString()
        },
        status: {
          privacyStatus: 'public'
        },
        contentDetails: {
          enableAutoStart: true,
          enableAutoStop: true,
          enableDvr: true,
          enableEmbed: true
        }
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Content-Type': 'application/json'
        },
        params: {
          key: credentials.apiKey
        }
      });

      const broadcast = broadcastResponse.data;

      // Create live stream
      const streamResponse = await axios.post('https://www.googleapis.com/youtube/v3/liveStreams?part=id,snippet,cdn,status', {
        snippet: {
          title: `${config.title} - Stream`,
          description: config.description
        },
        cdn: {
          format: '1080p',
          ingestionType: 'rtmp',
          resolution: 'variable',
          frameRate: 'variable'
        }
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Content-Type': 'application/json'
        },
        params: {
          key: credentials.apiKey
        }
      });

      const stream = streamResponse.data;

      // Bind broadcast to stream
      await axios.post(`https://www.googleapis.com/youtube/v3/liveBroadcasts/bind?id=${broadcast.id}&streamId=${stream.id}`, {}, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Content-Type': 'application/json'
        },
        params: {
          key: credentials.apiKey
        }
      });

      return {
        platform: 'youtube',
        streamUrl: `https://www.youtube.com/watch?v=${broadcast.id}`,
        streamKey: stream.cdn.ingestionInfo.streamName,
        ingestUrl: stream.cdn.ingestionInfo.ingestionAddress,
        broadcastId: broadcast.id,
        status: 'live'
      };

    } catch (error) {
      logger.error('YouTube streaming error:', error);
      throw error;
    }
  }

  private async startFacebookStream(config: StreamConfig, sessionId: string): Promise<any> {
    const credentials = this.credentials.facebook;

    try {
      // Create live video
      const response = await axios.post(`https://graph.facebook.com/v18.0/${credentials.pageId}/live_videos`, {
        title: config.title,
        description: config.description,
        status: 'LIVE'
      }, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      const liveVideo = response.data;

      return {
        platform: 'facebook',
        streamUrl: `https://www.facebook.com/${credentials.pageId}/videos/${liveVideo.id}/`,
        streamKey: liveVideo.stream_key,
        ingestUrl: liveVideo.ingest_streams[0].stream_url,
        videoId: liveVideo.id,
        status: 'live'
      };

    } catch (error) {
      logger.error('Facebook streaming error:', error);
      throw error;
    }
  }

  private async startTikTokStream(config: StreamConfig, sessionId: string): Promise<any> {
    // Note: TikTok live API access is limited and requires special approval
    // This is a placeholder implementation

    return {
      platform: 'tiktok',
      streamUrl: 'https://www.tiktok.com/@username/live',
      streamKey: 'tiktok-stream-key-placeholder',
      ingestUrl: 'rtmp://live-push.tiktok.com/live',
      status: 'live',
      note: 'TikTok API access requires special approval'
    };
  }

  private async startRTMPStream(config: StreamConfig, sessionId: string): Promise<any> {
    const credentials = this.credentials.rtmp;

    return {
      platform: 'rtmp',
      streamUrl: `${credentials.serverUrl}/${credentials.streamKey}`,
      streamKey: credentials.streamKey,
      ingestUrl: credentials.serverUrl,
      status: 'live'
    };
  }

  private async stopPlatformStream(platform: string, sessionId: string): Promise<void> {
    switch (platform) {
      case 'twitch':
        await this.stopTwitchStream(sessionId);
        break;
      case 'youtube':
        await this.stopYouTubeStream(sessionId);
        break;
      case 'facebook':
        await this.stopFacebookStream(sessionId);
        break;
      case 'tiktok':
        await this.stopTikTokStream(sessionId);
        break;
      case 'rtmp':
        await this.stopRTMPStream(sessionId);
        break;
    }
  }

  private async stopTwitchStream(sessionId: string): Promise<void> {
    // Twitch automatically stops when RTMP stream ends
    // Could optionally run commercial or update channel info
  }

  private async stopYouTubeStream(sessionId: string): Promise<void> {
    const credentials = this.credentials.youtube;

    // Transition broadcast to complete
    await axios.post(`https://www.googleapis.com/youtube/v3/liveBroadcasts/transition`, {
      id: sessionId,
      broadcastStatus: 'complete'
    }, {
      headers: {
        'Authorization': `Bearer ${credentials.accessToken}`,
        'Content-Type': 'application/json'
      },
      params: {
        key: credentials.apiKey
      }
    });
  }

  private async stopFacebookStream(sessionId: string): Promise<void> {
    const credentials = this.credentials.facebook;

    await axios.post(`https://graph.facebook.com/v18.0/${sessionId}`, {
      end_live_video: true
    }, {
      headers: {
        'Authorization': `Bearer ${credentials.accessToken}`,
        'Content-Type': 'application/json'
      }
    });
  }

  private async stopTikTokStream(sessionId: string): Promise<void> {
    // TikTok stream management API
  }

  private async stopRTMPStream(sessionId: string): Promise<void> {
    // RTMP stream stops when connection is closed
  }

  private async refreshTwitchToken(): Promise<void> {
    const credentials = this.credentials.twitch!;

    try {
      const response = await axios.post('https://id.twitch.tv/oauth2/token', {
        grant_type: 'client_credentials',
        client_id: credentials.clientId,
        client_secret: credentials.clientSecret
      });

      credentials.accessToken = response.data.access_token;

    } catch (error) {
      logger.error('Failed to refresh Twitch token:', error);
      throw error;
    }
  }

  private async refreshYouTubeToken(): Promise<void> {
    const credentials = this.credentials.youtube!;

    try {
      const response = await axios.post('https://oauth2.googleapis.com/token', {
        grant_type: 'refresh_token',
        refresh_token: credentials.refreshToken,
        client_id: credentials.clientId,
        client_secret: credentials.clientSecret
      });

      credentials.accessToken = response.data.access_token;

    } catch (error) {
      logger.error('Failed to refresh YouTube token:', error);
      throw error;
    }
  }

  private async getNextSessionNumber(): Promise<number> {
    // This would typically query the database for the highest session number
    // For now, return a placeholder
    return 1;
  }

  public static async stopAllStreams(): Promise<void> {
    await StreamingService.stopStream();
  }

  public static async getStreamStatus(sessionId: string): Promise<any> {
    const service = StreamingService.getInstance();
    const streamStatuses = [];

    for (const [key, stream] of service.activeStreams) {
      if (key.endsWith(sessionId)) {
        const [platform] = key.split('-');

        try {
          let status;
          switch (platform) {
            case 'twitch':
              status = await service.getTwitchStreamStatus();
              break;
            case 'youtube':
              status = await service.getYouTubeStreamStatus(stream.broadcastId);
              break;
            case 'facebook':
              status = await service.getFacebookStreamStatus(stream.videoId);
              break;
            default:
              status = { platform, status: 'unknown' };
          }
          streamStatuses.push(status);
        } catch (error) {
          streamStatuses.push({ platform, error: error.message });
        }
      }
    }

    return streamStatuses;
  }

  private async getTwitchStreamStatus(): Promise<any> {
    const credentials = this.credentials.twitch!;

    try {
      const response = await axios.get(`https://api.twitch.tv/helix/streams?user_id=${credentials.broadcasterId}`, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`,
          'Client-Id': credentials.clientId
        }
      });

      if (response.data.data.length > 0) {
        const stream = response.data.data[0];
        return {
          platform: 'twitch',
          isLive: true,
          viewerCount: stream.viewer_count,
          startedAt: stream.started_at,
          gameName: stream.game_name,
          title: stream.title
        };
      } else {
        return {
          platform: 'twitch',
          isLive: false
        };
      }
    } catch (error) {
      logger.error('Failed to get Twitch stream status:', error);
      throw error;
    }
  }

  private async getYouTubeStreamStatus(broadcastId: string): Promise<any> {
    const credentials = this.credentials.youtube!;

    try {
      const response = await axios.get(`https://www.googleapis.com/youtube/v3/liveBroadcasts?part=id,snippet,status,contentDetails&id=${broadcastId}`, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`
        },
        params: {
          key: credentials.apiKey
        }
      });

      if (response.data.items.length > 0) {
        const broadcast = response.data.items[0];
        return {
          platform: 'youtube',
          isLive: broadcast.status.lifeCycleStatus === 'live',
          title: broadcast.snippet.title,
          viewerCount: 0, // YouTube doesn't provide viewer count in this endpoint
          startedAt: broadcast.snippet.actualStartTime
        };
      } else {
        return {
          platform: 'youtube',
          isLive: false
        };
      }
    } catch (error) {
      logger.error('Failed to get YouTube stream status:', error);
      throw error;
    }
  }

  private async getFacebookStreamStatus(videoId: string): Promise<any> {
    const credentials = this.credentials.facebook!;

    try {
      const response = await axios.get(`https://graph.facebook.com/v18.0/${videoId}?fields=live_views,status`, {
        headers: {
          'Authorization': `Bearer ${credentials.accessToken}`
        }
      });

      return {
        platform: 'facebook',
        isLive: response.data.status === 'LIVE',
        viewerCount: response.data.live_views || 0
      };
    } catch (error) {
      logger.error('Failed to get Facebook stream status:', error);
      throw error;
    }
  }
}

export default StreamingService;