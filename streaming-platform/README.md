# D&D Streaming Platform

A comprehensive streaming platform designed specifically for Dungeons & Dragons sessions, providing professional broadcasting tools, multi-platform integration, and audience engagement features similar to Critical Role.

## 🎭 Features

### 🎬 Multi-Platform Streaming
- **Twitch Integration**: Full chat, alerts, and channel management
- **YouTube Live Streaming**: Monetization, DVR, and community features
- **Facebook Gaming**: Social media integration and audience reach
- **TikTok Live**: Short-form streaming integration
- **Custom RTMP**: Support for any RTMP-compatible platform

### 🎥 Professional Broadcasting Tools
- **OBS Studio Plugin**: Native integration with scene management
- **Scene Switching**: Pre-configured D&D themed scenes
- **Custom Overlays**: Animated dice rollers, character sheets, combat trackers
- **Lower Thirds**: Professional graphics with smooth animations
- **Sound Board**: D&D themed sound effects and reactions

### 👥 Audience Engagement
- **Live Chat Integration**: Cross-platform chat aggregation
- **AI Moderation**: Smart filtering and automated moderation
- **Interactive Polls**: Real-time voting and audience participation
- **Donation Notifications**: Animated alerts with custom effects
- **Subscriber Perks**: Special commands, exclusive content, and rewards

### 🎨 Content Enhancement
- **AI-Generated Thumbnails**: Custom thumbnails for every stream
- **Automatic Highlight Detection**: AI-powered moment identification
- **Clip Creation Tools**: Easy highlight generation and sharing
- **VOD Management**: Automatic recording and organization
- **Social Media Auto-Posting**: Cross-platform content distribution

### 💰 Monetization Features
- **Multi-Platform Tips**: Integrated donation processing
- **Subscription Tiers**: Bronze, Silver, and Gold supporter levels
- **Merchandise Integration**: Print-on-demand and digital products
- **Patreon Integration**: Exclusive content and member benefits
- **Sponsorship Management**: Brand partnerships and sponsored content

### 🎛️ Stream Deck Integration
- **Physical Controls**: Dedicated Stream Deck plugin
- **One-Click Actions**: Start/stop streaming, scene switching, dice rolling
- **Custom Commands**: Pre-configured chat messages and sound effects
- **Real-time Feedback**: Visual indicators and status updates

### 📊 Revenue Analytics
- **Live Dashboard**: Real-time metrics and performance tracking
- **Revenue Breakdown**: Detailed analytics by source and platform
- **Audience Insights**: Viewer behavior and engagement metrics
- **Content Performance**: Most popular moments and highlights

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- OBS Studio 28+
- MongoDB 5.0+
- Redis 6.0+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/dnd-streaming-platform.git
   cd dnd-streaming-platform
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Start services with Docker**
   ```bash
   docker-compose up -d
   ```

5. **Run the application**
   ```bash
   npm run dev
   ```

6. **Access the dashboard**
   Open http://localhost:3000 in your browser

### OBS Studio Plugin Installation

1. **Build the plugin**
   ```bash
   cd obs-plugin
   cmake -S . -B build
   cmake --build build
   ```

2. **Install to OBS**
   - Windows: Plugin files are automatically copied to OBS plugins directory
   - macOS: Copy build products to `/Library/Application Support/obs-studio/plugins/`
   - Linux: Copy to `/usr/lib/obs-plugins/`

### Stream Deck Plugin Installation

1. **Build the plugin**
   ```bash
   cd stream-deck-plugin
   npm install
   npm run build
   ```

2. **Install to Stream Deck**
   - Copy the `com.dndstreaming.streamdeck` folder to your Stream Deck plugins directory

## 📁 Project Structure

```
dnd-streaming-platform/
├── src/                          # Main application source
│   ├── controllers/              # API route controllers
│   ├── services/                 # Core business logic
│   │   ├── database.ts           # Database management
│   │   ├── streaming.ts          # Multi-platform streaming
│   │   ├── obs.ts                # OBS Studio integration
│   │   ├── engagement.ts         # Chat and audience engagement
│   │   ├── content.ts            # AI content enhancement
│   │   └── monetization.ts       # Payment processing
│   ├── models/                   # Database models
│   ├── routes/                   # API routes
│   └── middleware/               # Express middleware
├── obs-plugin/                   # OBS Studio plugin
│   ├── src/                      # Plugin source code
│   ├── include/                  # Header files
│   └── data/                     # Plugin resources
├── stream-deck-plugin/           # Stream Deck plugin
│   ├── src/                      # Plugin source code
│   └── property-inspector/       # UI components
├── overlays/                     # Browser-based overlays
│   ├── dice/                     # Dice rolling overlay
│   ├── character/                # Character sheet display
│   ├── chat/                     # Chat overlay
│   └── donation/                 # Donation alerts
├── dashboard/                    # Web dashboard
│   └── public/                   # Static files
└── docker-compose.yml            # Development environment
```

## ⚙️ Configuration

### Environment Variables

Key environment variables to configure:

```env
# Server
PORT=3000
NODE_ENV=development

# Database
MONGODB_URI=mongodb://localhost:27017/dnd-streaming-platform
REDIS_URL=redis://localhost:6379

# Twitch
TWITCH_CLIENT_ID=your_twitch_client_id
TWITCH_CLIENT_SECRET=your_twitch_client_secret
TWITCH_BROADCASTER_ID=your_twitch_channel_id

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret

# OBS Studio
OBS_WEBSOCKET_URL=ws://localhost:4444
OBS_WEBSOCKET_PASSWORD=your_obs_password

# AI Services
OPENAI_API_KEY=your_openai_api_key
REPLICATE_API_TOKEN=your_replicate_api_token

# Payments
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
```

### Platform Setup

#### Twitch
1. Create a Twitch application at [dev.twitch.tv](https://dev.twitch.tv)
2. Get Client ID and Client Secret
3. Configure OAuth redirect URLs
4. Set up channel points rewards

#### YouTube
1. Create a project at [Google Cloud Console](https://console.cloud.google.com)
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Set up channel memberships

#### OBS Studio
1. Enable WebSocket server in OBS settings
2. Set port to 4444 (default)
3. Configure password for authentication
4. Install the D&D Streaming plugin

## 🎮 Usage

### Starting a Stream

1. **Configure Platforms**: Set up your streaming platforms in the dashboard
2. **Prepare Scenes**: Create and configure your D&D themed scenes in OBS
3. **Test Connections**: Verify OBS, chat, and platform connections
4. **Go Live**: Click "Start Stream" in the dashboard or Stream Deck

### During Stream

- **Scene Switching**: Use Stream Deck or dashboard to switch between scenes
- **Dice Rolling**: Trigger animated dice rolls with `!roll` commands
- **Character Display**: Show character sheets with `!character` commands
- **Polls**: Create quick polls for audience decisions
- **Sound Effects**: Play D&D themed sound effects from the sound board

### Post-Stream

- **Highlights**: AI automatically identifies and marks key moments
- **Thumbnails**: Generate custom thumbnails for VODs
- **Analytics**: Review revenue and engagement metrics
- **Social Media**: Share highlights and clips to social platforms

## 🔧 API Documentation

### Streaming Endpoints

- `POST /api/streaming/start` - Start streaming on configured platforms
- `POST /api/streaming/stop` - Stop all active streams
- `GET /api/streaming/status/:sessionId` - Get stream status
- `POST /api/streaming/scenes/switch` - Switch OBS scene

### Monetization Endpoints

- `POST /api/monetization/donations/process` - Process a donation
- `POST /api/monetization/payments/stripe/create-intent` - Create Stripe payment
- `GET /api/monetization/analytics/revenue` - Get revenue analytics

### Content Endpoints

- `POST /api/content/highlights/generate` - Generate AI highlights
- `POST /api/content/thumbnails/generate` - Create AI thumbnail
- `GET /api/content/highlights` - Get stream highlights

## 🛠️ Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
npm run build
npm start
```

### Docker Development
```bash
docker-compose up -d  # Start all services
docker-compose logs -f  # View logs
docker-compose down  # Stop all services
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [Full documentation](https://docs.dndstreaming.com)
- **Discord**: [Community Discord](https://discord.gg/dndstreaming)
- **Issues**: [GitHub Issues](https://github.com/your-username/dnd-streaming-platform/issues)
- **Email**: support@dndstreaming.com

## 🎉 Acknowledgments

- **Critical Role** - Inspiration for professional D&D streaming
- **OBS Project** - Open source broadcasting software
- **Elgato** - Stream Deck platform
- **Twitch** - Live streaming platform
- **D&D Beyond** - D&D resources and tools

---

Built with ❤️ for the D&D streaming community