# DMlogn8n Real-Time Components Deployment Guide

This guide provides comprehensive instructions for deploying the n8n workflows for the real-time components of DMlogn8n.

## Prerequisites

### 1. n8n Instance Setup

Ensure you have a running n8n instance with the following configuration:

```yaml
# docker-compose.yml (excerpt)
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your-secure-password
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - N8N_METRICS=true
      - N8N_LOG_LEVEL=info
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
```

### 2. Required Services

Ensure the following services are running and accessible:

- **Google Firestore**: For session and event storage
- **Voice Processing API**: For audio transcription and processing
- **AI Service API**: For AI agent interactions
- **WebSocket Server**: For real-time communication
- **Email Service** (optional): For alerts
- **Slack Webhook** (optional): For notifications

### 3. API Keys and Credentials

You'll need the following API keys:

- OpenAI API Key (for Whisper transcription)
- Google Cloud credentials (for Firestore)
- Voice Processing API key
- AI Service API key
- Email service credentials (optional)
- Slack webhook URL (optional)

## Deployment Steps

### 1. Environment Configuration

Create a `.env` file in the DMLogn8n directory:

```bash
# n8n Configuration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your-n8n-api-key

# Workflow Directory
WORKFLOWS_DIR=/home/activeloguser/DMLogn8n/workflows

# API Keys
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VOICE_PROCESSING_API_KEY=your-voice-api-key
AI_SERVICE_API_KEY=your-ai-service-key

# Optional Services
EMAIL_SERVICE_API_KEY=your-email-api-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 2. Install Dependencies

```bash
# Install Python client
pip install requests

# Make the client executable
chmod +x n8n-api-client.py
```

### 3. Deploy Workflows

Run the deployment script:

```bash
cd /home/activeloguser/DMLogn8n
python n8n-api-client.py
```

This will:
- Test connection to your n8n instance
- Deploy all 6 workflow files
- Activate the workflows
- Configure webhook endpoints
- Generate a deployment report

## Workflow Overview

### 1. Voice Chat Integration (2 workflows)

**Voice Chat Integration - WebRTC Signaling**
- Handles WebRTC connection setup and signaling
- Manages session participants and connection state
- Routes signaling messages between participants

**Voice Chat Integration - Audio Processing & Transcription**
- Processes audio uploads for transcription
- Implements voice activity detection
- Applies character voice profiles and effects
- Integrates with Whisper API for transcription

### 2. WebSocket Real-Time System

**WebSocket Real-Time System - Live Game Communication**
- Manages WebSocket connections for real-time communication
- Handles message routing between participants
- Supports direct messages and session broadcasts
- Tracks connection health and participant state

### 3. Multi-Session Management

**Multi-Session Management - Concurrent Game Sessions**
- Creates and manages game sessions
- Allocates system resources per session
- Handles player joining/leaving
- Supports session migration between servers
- Monitors resource usage and health

### 4. Event Bus System

**Event Bus System - Game Event Orchestration**
- Central event routing and filtering
- Event subscription management
- Event persistence and replay
- Cross-service event communication

### 5. Monitoring and Health Check

**Monitoring and Health Check System**
- Periodic health checks for all sessions
- Resource usage monitoring
- Service health verification
- Alert generation for critical issues
- Integration with Slack and email notifications

## Webhook Endpoints

The workflows create the following webhook endpoints:

### Voice Chat Endpoints
- `POST /webhook/voice/webrtc-signaling` - WebRTC signaling
- `POST /webhook/voice/audio-process` - Audio processing

### WebSocket Endpoints
- `POST /webhook/websocket/connect` - Connection establishment
- `POST /webhook/websocket/message` - Message handling
- `POST /webhook/websocket/disconnect` - Connection cleanup

### Session Management Endpoints
- `POST /webhook/session/create` - Session creation
- `POST /webhook/session/join` - Player joining
- `POST /webhook/session/migrate` - Session migration

### Event Bus Endpoints
- `POST /webhook/event/publish` - Event publishing
- `POST /webhook/event/subscribe` - Event subscription
- `POST /webhook/event/replay` - Event replay

## Configuration

### Voice Processing Configuration

Voice processing can be configured through the workflow:

```javascript
// Audio processing settings
const audioConfig = {
  maxFileSize: 25 * 1024 * 1024, // 25MB
  supportedFormats: ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/mp3', 'audio/m4a'],
  compressionSettings: {
    sampleRate: 16000,
    channels: 1,
    bitrate: 64000
  }
};
```

### Session Resource Limits

Default resource allocation per session:

```javascript
const resourceLimits = {
  maxPlayers: 6,
  memory: '512MB',
  cpu: '0.5',
  bandwidth: '1Mbps',
  aiAgentSlots: 2,
  voiceChannels: 1
};
```

### Health Check Configuration

Health checks run every 5 minutes and monitor:

- Connection health (latency, active connections)
- Resource usage (memory, CPU, bandwidth)
- Service health (voice service, AI service, event bus, database)

## Monitoring and Alerting

### Metrics Collected

- Session count and participant counts
- WebSocket connection health
- Resource utilization per session
- Event processing latency
- Error rates and types

### Alert Thresholds

- **Critical**: Health score < 60% or service down
- **Warning**: Health score 60-80% or resource usage > 80%
- **Info**: Normal operation updates

### Alert Channels

- **Slack**: Real-time notifications for critical issues
- **Email**: Detailed alerts for administrators
- **Dashboard**: Live metrics in n8n monitoring

## Troubleshooting

### Common Issues

1. **Workflows not activating**
   - Check n8n API key permissions
   - Verify webhook URLs are accessible
   - Ensure all required credentials are configured

2. **Audio processing failures**
   - Verify OpenAI API key and quota
   - Check audio file format and size limits
   - Ensure voice processing API is accessible

3. **WebSocket connection issues**
   - Check firewall rules for WebSocket ports
   - Verify SSL certificates if using HTTPS
   - Monitor connection health in logs

4. **Session resource exhaustion**
   - Monitor resource usage in health checks
   - Adjust resource allocation limits
   - Implement session migration if needed

### Log Locations

- n8n execution logs: Available in n8n UI
- Workflow errors: Check individual workflow executions
- System logs: `/var/log/n8n/` (if using Docker volumes)

### Performance Tuning

1. **Database Optimization**
   - Add appropriate indexes for Firestore queries
   - Implement connection pooling
   - Cache frequently accessed data

2. **Resource Management**
   - Monitor resource usage patterns
   - Implement auto-scaling for high load
   - Use resource quotas effectively

3. **Network Optimization**
   - Implement CDN for static assets
   - Optimize WebSocket message batching
   - Use compression for large payloads

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple n8n workers in queue mode
- Use load balancer for webhook distribution
- Implement session affinity where needed

### Database Scaling

- Consider sharding for high-volume sessions
- Implement read replicas for analytics queries
- Use caching layer for frequently accessed data

### Service Scaling

- Deploy voice processing service with auto-scaling
- Use CDN for audio file distribution
- Implement API rate limiting and quotas

## Security Considerations

1. **API Security**
   - Use HTTPS for all webhook endpoints
   - Implement API key rotation
   - Validate all incoming requests

2. **Data Protection**
   - Encrypt sensitive data at rest
   - Implement data retention policies
   - Sanitize user inputs

3. **Access Control**
   - Implement role-based permissions
   - Use session-based authentication
   - Audit all administrative actions

## Maintenance

### Regular Tasks

- Review and rotate API keys
- Monitor resource usage trends
- Update workflow configurations
- Backup critical data

### Updates

- Test workflow updates in staging
- Use blue-green deployment for critical workflows
- Monitor rollback procedures

## Support

For issues with these workflows:

1. Check the n8n execution logs
2. Review the deployment report
3. Verify all service connections
4. Monitor system resource usage

For additional support, refer to the n8n documentation and the specific service documentation for integrated APIs.