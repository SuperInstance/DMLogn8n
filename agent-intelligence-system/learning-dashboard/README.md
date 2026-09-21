# Agent Intelligence Learning Dashboard

A comprehensive real-time dashboard for visualizing and monitoring the cognitive growth and learning progress of AI agents in the DMlogn8n system.

## 🚀 Features

### 📊 **Real-Time Intelligence Metrics**
- Live IQ progression tracking with trend analysis
- Learning velocity and retention rate monitoring
- Adaptive thinking score measurement
- Meta-learning capabilities assessment

### 🧠 **Memory System Visualization**
- Hierarchical memory usage across different types (episodic, semantic, procedural, social)
- Memory consolidation and retention statistics
- Access pattern analysis and optimization insights
- Capacity management alerts

### ⭐ **Skill Development Tracking**
- Radar charts for multi-dimensional skill analysis
- Progress tracking across combat, social, exploration, strategic, and technical skills
- Mastery level distribution and improvement rates
- Emerging skill identification

### 📈 **Strategic Improvement Analysis**
- Before/after performance comparisons
- Success pattern recognition
- Failure analysis and learning insights
- Adaptive strategy evolution tracking

### 🎯 **Performance Benchmarks**
- Baseline comparison with initial capabilities
- Peer comparison across the agent population
- Personal best achievements tracking
- Percentile ranking and performance grading

### 🏆 **Milestone Celebrations**
- Automated milestone detection and celebration
- Achievement rewards and unlocks
- Progress acknowledgment and motivation

### 📤 **Export & Reporting**
- Multiple export formats (PDF, CSV, JSON, XLSX)
- Customizable report generation
- Historical data analysis
- Scheduled report options

### 📱 **Mobile-Responsive Design**
- Fully responsive layout for all devices
- Touch-optimized interactions
- Progressive Web App capabilities
- Mobile navigation with quick access

### ♿ **Accessibility Features**
- WCAG 2.1 AA compliance
- Screen reader support
- Keyboard navigation
- High contrast mode support
- Reduced motion preferences
- Customizable font sizes

### ⚡ **Real-Time Updates**
- WebSocket integration for live data streaming
- Configurable refresh intervals
- Background data synchronization
- Offline capability with caching

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Socket.IO Client** for real-time communication

### Backend
- **Node.js** with Express
- **Socket.IO** for WebSocket connections
- **TypeScript** for type safety
- **JWT** authentication (mock implementation)

### Development Tools
- **ESLint** for code linting
- **Vitest** for testing
- **PostCSS** for CSS processing
- **TypeScript** for static typing

## 📦 Installation

### Prerequisites
- Node.js 16.0.0 or higher
- npm 8.0.0 or higher

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent-intelligence-learning-dashboard
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Start the backend server** (in a separate terminal)
   ```bash
   npm run start
   ```

6. **Access the dashboard**
   Open your browser and navigate to `http://localhost:3000`

## 🏗️ Architecture

### Frontend Structure
```
src/
├── components/          # React components
│   ├── charts/         # Chart components
│   ├── panels/         # Dashboard panels
│   └── ...             # Other UI components
├── hooks/              # Custom React hooks
├── services/           # API services
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── styles/             # Global styles
```

### Backend Structure
```
backend/
├── api/                # API routes
├── services/           # Business logic services
├── middleware/         # Express middleware
├── websocket/          # WebSocket handlers
└── models/             # Data models
```

## 🔧 Configuration

### Dashboard Configuration
The dashboard can be customized through the `DashboardConfig` interface:

```typescript
const config: DashboardConfig = {
  refreshInterval: 5000,           // Data refresh interval in ms
  timeframes: [                    // Available timeframes
    { id: 'session', label: 'Current Session', duration: 1, unit: 'hours' },
    { id: 'day', label: 'Last 24 Hours', duration: 1, unit: 'days' },
    // ...
  ],
  alertThresholds: [               // Custom alert thresholds
    { metric: 'learningVelocity', condition: 'below', value: 0.1, severity: 'warning' },
    // ...
  ],
  chartPreferences: {              // Chart appearance settings
    colorScheme: 'viridis',
    animationEnabled: true,
    showDataLabels: true
  }
};
```

### API Configuration
Configure the backend API endpoints and authentication:

```typescript
// API endpoints
GET    /api/v1/agents/:agentId/learning-metrics
GET    /api/v1/agents/:agentId/historical-data
GET    /api/v1/agents/:agentId/comparison
GET    /api/v1/agents/:agentId/export/:format
POST   /api/v1/agents/:agentId/learning-metrics
GET    /api/v1/agents/:agentId/milestones
POST   /api/v1/agents/:agentId/process-session
```

## 📊 Data Integration

### Agent Data Format
The dashboard expects agent learning data in the following format:

```typescript
interface AgentLearningMetrics {
  agentId: string;
  agentName: string;
  characterClass: string;
  level: number;
  intelligenceMetrics: {
    currentIQ: number;
    baselineIQ: number;
    iqProgression: IQDataPoint[];
    learningVelocity: number;
    retentionRate: number;
    adaptiveThinkingScore: number;
  };
  // ... other metrics
}
```

### WebSocket Events
Real-time updates are handled through WebSocket events:

- `metrics_update` - Learning metrics updated
- `milestone_achieved` - Agent reached a milestone
- `session_complete` - Learning session finished
- `alert` - Performance alert triggered

## 🎨 Customization

### Color Schemes
The dashboard supports multiple color schemes:
- `viridis` (default)
- `plasma`
- `warm`
- `cool`

### Chart Types
Available chart types:
- Line charts for progression tracking
- Radar charts for skill analysis
- Bar charts for comparisons
- Pie charts for distributions
- Scatter plots for correlations
- Heatmaps for patterns

### Mobile Optimization
The dashboard includes:
- Touch-friendly interface elements
- Swipeable charts on mobile
- Collapsible navigation
- Responsive grid layouts
- Optimized performance for mobile devices

## 🧪 Testing

### Run Tests
```bash
# Run all tests
npm run test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
# Run linter
npm run lint

# Fix linting issues
npm run lint:fix
```

## 📱 Accessibility

The dashboard is designed with accessibility in mind:

- **Screen Reader Support**: All interactive elements are properly labeled
- **Keyboard Navigation**: Full keyboard navigation support
- **High Contrast Mode**: Automatic detection and support
- **Reduced Motion**: Respects user's motion preferences
- **Focus Management**: Proper focus handling and visual indicators
- **ARIA Labels**: Comprehensive ARIA labeling for complex components

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Environment Variables
Create a `.env.production` file with:

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_WS_URL=wss://your-websocket-domain.com
VITE_FRONTEND_URL=https://your-dashboard-domain.com
```

### Docker Deployment
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY dist ./dist
COPY backend ./backend

EXPOSE 3000
CMD ["npm", "run", "serve"]
```

## 🔒 Security

- Authentication middleware (JWT-based)
- Role-based access control
- Rate limiting on API endpoints
- Input validation and sanitization
- CORS configuration
- WebSocket authentication

## 📈 Performance

- **Lazy Loading**: Components loaded on demand
- **Virtual Scrolling**: For large datasets
- **Memoization**: Optimized re-renders
- **Code Splitting**: Reduced bundle sizes
- **Caching**: Intelligent data caching
- **Optimized Charts**: Efficient rendering

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [documentation](docs/)
- Review the [API reference](docs/api.md)

## 🗺️ Roadmap

### Version 1.1
- [ ] Advanced filtering options
- [ ] Custom dashboard layouts
- [ ] Enhanced export features
- [ ] Integration with more learning systems

### Version 1.2
- [ ] Multi-agent comparison views
- [ ] Predictive analytics
- [ ] Advanced milestone system
- [ ] Team collaboration features

### Version 2.0
- [ ] AI-powered insights
- [ ] Custom visualization builder
- [ ] Advanced reporting suite
- [ ] Enterprise features

---

**Built with ❤️ for the DMlogn8n Agent Intelligence System**