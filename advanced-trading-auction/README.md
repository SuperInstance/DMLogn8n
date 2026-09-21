# DMlogn8n Advanced Trading & Auction House System

A sophisticated, real-time global marketplace system for DMlogn8n that provides advanced trading, auction, and economic analytics capabilities.

## Features

### 🌍 Global Marketplace
- **Cross-server trading** with unified economy
- **Real-time price discovery** with supply/demand mechanics
- **Item categories** with advanced filtering and search
- **Trend analysis** and price predictions
- **Regional price variations** and arbitrage opportunities

### 🏪 Auction System
- **Timed auctions** with advanced bidding mechanics
- **Buyout options** and reserve prices
- **Anonymous bidding** and anti-sniping protection
- **Auction history** and comprehensive price tracking
- **Bulk auction creation** and management

### 💱 Trading Features
- **Direct player-to-player trades** with escrow system
- **Trade reputation system** for trustworthy trading
- **Bulk trading** and bartering capabilities
- **Rare item authentication** and verification

### 📊 Economic Mechanics
- **Dynamic pricing** based on real-time supply/demand
- **Tax and transaction fee** systems
- **Market manipulation detection** and prevention
- **Economic events** and regional influences
- **Currency exchange** for different regions

### 📈 Analytics & Insights
- **Market trends** and predictive analytics
- **Investment opportunities** identification
- **Price alerts** and notifications
- **Portfolio tracking** and performance metrics
- **Comprehensive trading statistics**

## Architecture

The system is built with a microservices architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Services      │
│   (React)       │◄──►│   (Express)     │◄──►│   (Node.js)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  WebSocket      │    │   Database      │
                       │  (Socket.io)    │    │   (PostgreSQL)  │
                       └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   n8n Workflows │    │      Redis      │
                       │  (Automation)   │    │    (Cache)      │
                       └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- n8n (for workflow automation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DMlogn8n/advanced-trading-auction
   ```

2. **Install dependencies**
   ```bash
   npm run setup
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up the database**
   ```bash
   npm run migrate
   npm run seed
   ```

5. **Start the services**
   ```bash
   # Start the main application
   npm run dev

   # In another terminal, start Redis
   redis-server

   # In another terminal, start n8n for workflows
   n8n start
   ```

6. **Import n8n workflows**
   - Navigate to the n8n interface (http://localhost:5678)
   - Import the workflow JSON files from `/n8n-workflows/`

### Environment Variables

Key environment variables to configure:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dmlogn8n_trading
DB_USER=postgres
DB_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Server
PORT=3001
NODE_ENV=development

# Security
JWT_SECRET=your-super-secret-jwt-key

# External APIs
N8N_WEBHOOK_URL=http://localhost:5678/webhook
DMLOGN8N_API_URL=http://localhost:3000/api

# Economic Parameters
BASE_TAX_RATE=0.05
AUCTION_FEE=0.02
TRADE_FEE=0.01
PRICE_UPDATE_INTERVAL=30000
```

## API Documentation

### Auction Endpoints

#### Create Auction
```http
POST /api/auctions
Content-Type: application/json
Authorization: Bearer <token>

{
  "itemId": "uuid",
  "quantity": 1,
  "startingPrice": 1000,
  "reservePrice": 1500,
  "buyoutPrice": 2500,
  "duration": 86400000,
  "regionId": "global",
  "anonymous": false
}
```

#### Place Bid
```http
POST /api/auctions/:auctionId/bid
Content-Type: application/json
Authorization: Bearer <token>

{
  "amount": 1200,
  "anonymous": false
}
```

#### Search Auctions
```http
GET /api/auctions?regionId=global&minPrice=100&maxPrice=5000&sortBy=end_time&sortOrder=asc&limit=50
```

### Marketplace Endpoints

#### Create Listing
```http
POST /api/marketplace/listings
Content-Type: application/json
Authorization: Bearer <token>

{
  "itemId": "uuid",
  "quantity": 5,
  "price": 200,
  "listingType": "fixed",
  "regionId": "global"
}
```

#### Search Listings
```http
GET /api/marketplace/listings?categoryIds=1,2,3&regionId=north&minPrice=50&maxPrice=1000
```

#### Make Offer
```http
POST /api/marketplace/listings/:listingId/offer
Content-Type: application/json
Authorization: Bearer <token>

{
  "amount": 180,
  "message": "Is this price negotiable?"
}
```

### Analytics Endpoints

#### Market Overview
```http
GET /api/marketplace/stats?regionId=global&timeRange=7
```

#### Market Trends
```http
GET /api/marketplace/trends?regionId=global&timeRange=30&categoryId=uuid
```

#### Investment Opportunities
```http
GET /api/analytics/opportunities?regionId=global&riskTolerance=medium
```

## Economic Engine

The economic engine is the core component that drives market dynamics:

### Supply/Demand Calculations

```javascript
// Price elasticity formula
priceModifier = 1 / (supply/demand)^elasticity

// Final price calculation
finalPrice = basePrice × priceModifier × trendFactor × volatilityFactor × regionalModifier
```

### Market Manipulation Detection

The system monitors for:
- Unusual volume spikes (>100,000 units)
- Price anomalies (>30% variance)
- Wash trading patterns
- Suspicious bidding activity

### Price Prediction

Uses time series analysis with:
- Linear regression for trend identification
- Exponential moving averages for smoothing
- Volatility adjustments for uncertainty
- Regional modifiers for local economics

## Real-time Features

### WebSocket Events

The system provides real-time updates through WebSocket connections:

```javascript
// Auction events
'auction_updated'    // Auction status or price changes
'bid_placed'         // New bid notification
'auction_sold'       // Auction completed
'outbid'             // Outbid notification

// Marketplace events
'listing_sold'       // Item purchased
'offer_received'     // New offer on listing
'trade_request'      // New trade request

// Market events
'price_alert'        // Price threshold alerts
'market_update'      // General market updates
```

### Real-time Price Updates

Prices are updated every 30 seconds based on:
- Current supply/demand ratios
- Recent transaction history
- Market sentiment analysis
- Regional economic factors

## n8n Workflows

The system includes three main automated workflows:

### 1. Auction Processing Workflow
- **Trigger**: Auction events (create, bid, complete)
- **Actions**: Process payments, transfer items, update analytics
- **Features**: Anti-manipulation detection, automated notifications

### 2. Price Updates Workflow
- **Trigger**: Scheduled every 30 minutes
- **Actions**: Recalculate prices, detect manipulation, send alerts
- **Features**: Dynamic pricing, market analysis, cache management

### 3. Market Analysis Workflow
- **Trigger**: Scheduled every 6 hours
- **Actions**: Generate insights, identify opportunities, assess risks
- **Features**: Comprehensive analytics, trend prediction, reporting

## Database Schema

### Core Tables

- **items**: Item definitions and properties
- **item_categories**: Category hierarchy
- **auctions**: Active and completed auctions
- **auction_bids**: Bid history
- **market_listings**: Marketplace listings
- **market_transactions**: Transaction records
- **market_prices**: Price history
- **players**: Player information
- **player_reputation**: Trading reputation scores

### Analytics Tables

- **price_alerts**: User-defined price alerts
- **trade_requests**: Direct trade proposals
- **regional_events**: Economic events affecting regions
- **market_analytics_cache**: Cached analysis results

## Frontend Components

### Key Components

- **AuctionCard**: Display auction information with real-time updates
- **MarketDashboard**: Comprehensive market analytics interface
- **TradingInterface**: Complete trading experience
- **PriceCharts**: Interactive price history visualization
- **OpportunityFinder**: Investment opportunity discovery

### State Management

Uses React Context and custom hooks for:
- Real-time socket connections
- Market data caching
- User authentication
- Shopping cart and watchlists

## Security Features

### Authentication & Authorization

- JWT-based authentication
- Role-based access control
- API rate limiting
- Input validation and sanitization

### Trading Security

- Escrow system for secure trades
- Reputation-based restrictions
- Transaction monitoring
- Fraud detection algorithms

### Data Protection

- Encrypted sensitive data
- SQL injection prevention
- XSS protection
- CSRF tokens

## Performance Optimization

### Caching Strategy

- Redis for real-time data
- Application-level caching
- Database query optimization
- CDN for static assets

### Database Optimization

- Indexed queries
- Connection pooling
- Read replicas for analytics
- Partitioned historical data

### Real-time Performance

- WebSocket connection management
- Efficient event broadcasting
- Load balancing for high traffic
- Graceful degradation

## Monitoring & Analytics

### Metrics Tracked

- Transaction volume and frequency
- Price volatility and trends
- User engagement patterns
- System performance metrics

### Alerting

- Price threshold alerts
- System health monitoring
- Anomaly detection
- Performance degradation alerts

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards

- ESLint for JavaScript/TypeScript
- Prettier for code formatting
- Conventional commit messages
- Comprehensive test coverage

### Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:coverage
```

## Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   NODE_ENV=production
   ```

2. **Database Migration**
   ```bash
   npm run migrate:prod
   ```

3. **Start Services**
   ```bash
   npm run build
   npm start
   ```

### Docker Deployment

```bash
# Build the image
docker build -t dmlogn8n-trading .

# Run with docker-compose
docker-compose up -d
```

## Support

### Documentation

- [API Reference](./docs/api.md)
- [Database Schema](./docs/database.md)
- [Frontend Components](./docs/frontend.md)
- [n8n Workflows](./docs/workflows.md)

### Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   - Check PostgreSQL service status
   - Verify connection string
   - Ensure proper permissions

2. **Redis Connection Issues**
   - Check Redis service status
   - Verify host and port configuration
   - Check firewall settings

3. **WebSocket Connection Issues**
   - Verify WebSocket server is running
   - Check CORS configuration
   - Ensure proper authentication

### Community

- GitHub Issues for bug reports
- Discord server for discussions
- Wiki for extended documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0 (Current)
- Initial release of advanced trading system
- Complete auction and marketplace functionality
- Real-time economic engine
- Analytics and insights system
- n8n workflow automation
- Comprehensive API and frontend

---

Built with ❤️ for the DMlogn8n community