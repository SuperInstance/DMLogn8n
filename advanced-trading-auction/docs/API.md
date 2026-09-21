# DMlogn8n Trading System API Documentation

## Overview

The DMlogn8n Trading System provides a comprehensive RESTful API for managing auctions, marketplace listings, trades, and economic analytics. This document covers all available endpoints, request/response formats, and authentication requirements.

## Base URL

```
Development: http://localhost:3001/api
Production: https://your-domain.com/api
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Obtaining a Token

```http
POST /auth/login
Content-Type: application/json

{
  "username": "playername",
  "password": "password"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "uuid",
      "username": "playername",
      "email": "player@example.com"
    }
  }
}
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "pagination": {  // Optional for paginated responses
    "limit": 50,
    "offset": 0,
    "total": 150
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "errors": [  // Optional for validation errors
    {
      "field": "price",
      "message": "Price must be greater than 0"
    }
  ]
}
```

## Auction Endpoints

### Create Auction

Creates a new auction for an item.

```http
POST /api/auctions
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "itemId": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 1,
  "startingPrice": 1000.00,
  "reservePrice": 1500.00,
  "buyoutPrice": 2500.00,
  "duration": 86400000,
  "regionId": "global",
  "anonymous": false,
  "autoRelist": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "sellerId": "550e8400-e29b-41d4-a716-446655440002",
    "itemId": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 1,
    "startingPrice": "1000.00",
    "currentBid": "1000.00",
    "reservePrice": "1500.00",
    "buyoutPrice": "2500.00",
    "startTime": "2024-01-15T10:00:00.000Z",
    "endTime": "2024-01-16T10:00:00.000Z",
    "status": "active",
    "regionId": "global",
    "anonymous": false,
    "autoRelist": true,
    "minBidIncrement": 0.05,
    "bidCount": 0,
    "bidderId": null,
    "createdAt": "2024-01-15T10:00:00.000Z",
    "updatedAt": "2024-01-15T10:00:00.000Z"
  },
  "message": "Auction created successfully"
}
```

### Place Bid

Places a bid on an active auction.

```http
POST /api/auctions/:auctionId/bid
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 1200.00,
  "anonymous": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "auction": { ... },
    "bid": {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "auctionId": "550e8400-e29b-41d4-a716-446655440001",
      "bidderId": "550e8400-e29b-41d4-a716-446655440002",
      "amount": "1200.00",
      "timestamp": "2024-01-15T11:00:00.000Z"
    },
    "outbid": false
  },
  "message": "Bid placed successfully"
}
```

### Get Auction Details

Retrieves detailed information about a specific auction.

```http
GET /api/auctions/:auctionId?includeBids=true
```

**Response:**
```json
{
  "success": true,
  "data": {
    "auction": { ... },
    "bidHistory": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "auctionId": "550e8400-e29b-41d4-a716-446655440001",
        "bidderId": "550e8400-e29b-41d4-a716-446655440002",
        "amount": "1200.00",
        "timestamp": "2024-01-15T11:00:00.000Z"
      }
    ]
  }
}
```

### Search Auctions

Searches for auctions with various filters.

```http
GET /api/auctions?itemId=uuid&sellerId=uuid&regionId=global&minPrice=100&maxPrice=5000&sortBy=end_time&sortOrder=asc&limit=50&offset=0
```

**Query Parameters:**
- `itemId` (string, optional): Filter by item ID
- `sellerId` (string, optional): Filter by seller ID
- `regionId` (string, optional): Filter by region
- `minPrice` (number, optional): Minimum current bid
- `maxPrice` (number, optional): Maximum current bid
- `sortBy` (string, optional): Sort field (end_time, current_bid, starting_price, created_at)
- `sortOrder` (string, optional): Sort order (asc, desc)
- `limit` (number, optional): Results per page (max 100)
- `offset` (number, optional): Results offset

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "itemName": "Iron Sword",
      "itemRarity": "common",
      "itemIcon": "/api/items/550e8400-e29b-41d4-a716-446655440000/icon",
      "startingPrice": "1000.00",
      "currentBid": "1200.00",
      "buyoutPrice": "2500.00",
      "endTime": "2024-01-16T10:00:00.000Z",
      "status": "active",
      "bidCount": 3,
      "sellerId": "550e8400-e29b-41d4-a716-446655440002",
      "regionId": "global"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 150
  }
}
```

### Get Player's Auctions

Retrieves auctions for the authenticated player.

```http
GET /api/auctions/player/:type
Authorization: Bearer <token>
```

**Path Parameters:**
- `type` (string): Auction type (selling, bidding)

**Response:**
```json
{
  "success": true,
  "data": [
    { ... }
  ]
}
```

### Cancel Auction

Cancels an active auction (seller only).

```http
DELETE /api/auctions/:auctionId
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "reason": "seller_cancel"
}
```

### Get Auction Statistics

Retrieves statistical data about auctions.

```http
GET /api/auctions/stats?regionId=global&timeRange=7
```

**Query Parameters:**
- `regionId` (string, optional): Filter by region
- `timeRange` (number, optional): Time range in days (1-365)

**Response:**
```json
{
  "success": true,
  "data": {
    "totalAuctions": 1250,
    "soldAuctions": 875,
    "expiredAuctions": 300,
    "cancelledAuctions": 75,
    "successRate": 70.0,
    "totalVolume": "2500000.00",
    "avgFinalPrice": "2000.00",
    "avgBidsPerAuction": 4.5
  }
}
```

## Marketplace Endpoints

### Create Listing

Creates a new marketplace listing.

```http
POST /api/marketplace/listings
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "itemId": "550e8400-e29b-41d4-a716-446655440000",
  "quantity": 5,
  "price": 200.00,
  "listingType": "fixed",
  "regionId": "global",
  "duration": 604800000,
  "description": "High quality iron ingots",
  "tags": ["materials", "crafting", "iron"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "sellerId": "550e8400-e29b-41d4-a716-446655440002",
    "itemId": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 5,
    "price": "200.00",
    "regionId": "global",
    "listingType": "fixed",
    "status": "active",
    "createdAt": "2024-01-15T10:00:00.000Z",
    "expiresAt": "2024-01-22T10:00:00.000Z"
  },
  "message": "Listing created successfully"
}
```

### Purchase Listing

Purchases items from a marketplace listing.

```http
POST /api/marketplace/listings/:listingId/purchase
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "quantity": 2
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "listing": { ... },
    "buyerId": "550e8400-e29b-41d4-a716-446655440003",
    "quantity": 2,
    "totalPrice": "400.00"
  },
  "message": "Item purchased successfully"
}
```

### Make Offer

Makes an offer on a negotiable listing.

```http
POST /api/marketplace/listings/:listingId/offer
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 180.00,
  "message": "Is this price negotiable?"
}
```

### Search Listings

Searches for marketplace listings.

```http
GET /api/marketplace/listings?categoryIds=1,2,3&regionId=north&minPrice=50&maxPrice=1000&listingType=fixed&sortBy=price&sortOrder=asc&limit=50&offset=0
```

**Query Parameters:**
- `itemId` (string, optional): Filter by item ID
- `sellerId` (string, optional): Filter by seller ID
- `categoryIds` (string, optional): Comma-separated category IDs
- `regionId` (string, optional): Filter by region
- `minPrice` (number, optional): Minimum price
- `maxPrice` (number, optional): Maximum price
- `listingType` (string, optional): Listing type (fixed, negotiable)
- `tags` (string, optional): Comma-separated tags
- `sortBy` (string, optional): Sort field
- `sortOrder` (string, optional): Sort order
- `limit` (number, optional): Results per page
- `offset` (number, optional): Results offset
- `includeExpired` (boolean, optional): Include expired listings

### Get Market Trends

Retrieves market trend data.

```http
GET /api/marketplace/trends?regionId=global&timeRange=30&categoryId=uuid
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalCategories": 7,
      "avgPrice": 1250.50,
      "priceRange": {
        "min": 50.00,
        "max": 15000.00
      }
    },
    "categoryTrends": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440005",
        "name": "Weapons",
        "avgPrice": "2000.00",
        "minPrice": "100.00",
        "maxPrice": "15000.00",
        "dataPoints": 125
      }
    ]
  }
}
```

### Get Price History

Retrieves price history for an item.

```http
GET /api/marketplace/items/:itemId/price-history?regionId=global&timeRange=30
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "itemId": "550e8400-e29b-41d4-a716-446655440000",
      "price": "1200.00",
      "supply": "150.00",
      "demand": "200.00",
      "volatility": "0.05",
      "transactionCount": 25,
      "volume24h": "30000.00",
      "createdAt": "2024-01-15T10:00:00.000Z"
    }
  ]
}
```

## Analytics Endpoints

### Get Market Overview

Retrieves comprehensive market overview data.

```http
GET /api/analytics/market-overview?regionId=global&timeRange=7
```

**Response:**
```json
{
  "success": true,
  "data": {
    "region": "global",
    "timeRange": 7,
    "overview": {
      "volume": "5000000.00",
      "transactions": 2500,
      "uniqueItems": 150,
      "activeListings": 500,
      "sentiment": {
        "sentiment": "bullish",
        "score": 0.15,
        "confidence": 0.75
      },
      "topItems": [ ... ],
      "activityBreakdown": {
        "marketplace": 1800,
        "auctions": 500,
        "directTrades": 200
      }
    },
    "trends": { ... },
    "opportunities": [ ... ],
    "risks": [ ... ],
    "predictions": { ... },
    "recommendations": [ ... ],
    "marketHealth": {
      "overallScore": 0.75,
      "grade": "B+",
      "metrics": { ... }
    }
  }
}
```

### Get Investment Opportunities

Retrieves investment opportunities based on market analysis.

```http
GET /api/analytics/opportunities?regionId=global&riskTolerance=medium&limit=20
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "type": "undervalued",
      "itemId": "550e8400-e29b-41d4-a716-446655440007",
      "itemName": "Iron Ore",
      "currentPrice": "50.00",
      "predictedPrice": "75.00",
      "potentialGain": 50.0,
      "confidence": 0.8,
      "score": 0.75,
      "reasoning": "Item appears undervalued based on historical trends and current market conditions"
    }
  ]
}
```

### Get Market Risks

Retrieves identified market risks.

```http
GET /api/analytics/risks?regionId=global&severity=high
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "type": "price_volatility",
      "itemId": "550e8400-e29b-41d4-a716-446655440008",
      "severity": "high",
      "description": "Unusual price volatility detected for item Iron Ore",
      "data": {
        "avgPrice": "50.00",
        "variance": 0.4,
        "transactionCount": 150
      }
    }
  ]
}
```

### Get Player Portfolio

Retrieves portfolio analysis for a player.

```http
GET /api/analytics/portfolio/:playerId?regionId=global
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "portfolio": {
      "items": [ ... ],
      "currency": "10000.00",
      "lastUpdated": "2024-01-15T10:00:00.000Z"
    },
    "valuation": {
      "totalValue": "25000.00",
      "itemValues": [ ... ],
      "currency": "10000.00",
      "netWorth": "35000.00"
    },
    "performance": {
      "totalReturn": 15.5,
      "dailyChange": 2.3,
      "weeklyChange": 8.7
    },
    "recommendations": [ ... ],
    "riskAssessment": { ... }
  }
}
```

## WebSocket Events

### Connection

Connect to the WebSocket server for real-time updates:

```javascript
const socket = io('ws://localhost:3001', {
  auth: {
    token: 'your-jwt-token'
  }
});
```

### Auction Events

#### auction_updated
```javascript
socket.on('auction_updated', (data) => {
  console.log('Auction updated:', data);
  // data: { auctionId, currentBid, bidCount, status }
});
```

#### bid_placed
```javascript
socket.on('bid_placed', (data) => {
  console.log('New bid placed:', data);
  // data: { auctionId, bidderId, amount, timestamp }
});
```

#### auction_sold
```javascript
socket.on('auction_sold', (data) => {
  console.log('Auction sold:', data);
  // data: { auctionId, sellerId, buyerId, price, quantity }
});
```

#### outbid
```javascript
socket.on('outbid', (data) => {
  console.log('You were outbid:', data);
  // data: { auctionId, previousBidderId, newBidAmount }
});
```

### Marketplace Events

#### listing_sold
```javascript
socket.on('listing_sold', (data) => {
  console.log('Listing sold:', data);
  // data: { listingId, sellerId, buyerId, quantity, totalPrice }
});
```

#### offer_received
```javascript
socket.on('offer_received', (data) => {
  console.log('New offer received:', data);
  // data: { offerId, listingId, buyerId, amount, message }
});
```

### Market Events

#### price_alert
```javascript
socket.on('price_alert', (data) => {
  console.log('Price alert triggered:', data);
  // data: { alertId, itemId, currentPrice, alertType, threshold }
});
```

#### market_update
```javascript
socket.on('market_update', (data) => {
  console.log('Market update:', data);
  // data: { type, regionId, data }
});
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource conflict |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service temporarily down |

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Standard endpoints**: 100 requests per 15 minutes
- **Search endpoints**: 50 requests per 15 minutes
- **Analytics endpoints**: 25 requests per 15 minutes

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

- `limit`: Number of items per page (max 100)
- `offset`: Number of items to skip

Response includes pagination metadata:
```json
{
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 150,
    "hasMore": true
  }
}
```

## Filtering and Sorting

Most list endpoints support filtering and sorting:

### Filtering
- Use query parameters for specific fields
- Multiple values can be comma-separated
- Ranges can be specified with min/max prefixes

### Sorting
- `sortBy`: Field to sort by
- `sortOrder`: Sort direction (`asc` or `desc`)

## Versioning

API versioning is handled through URL paths:
- Current version: `/api/v1/`
- Previous versions: `/api/v0/`

Backward compatibility is maintained for at least one previous version.

## Testing

### Postman Collection

A Postman collection is available with pre-configured requests for all endpoints.

### Example cURL Commands

```bash
# Create auction
curl -X POST http://localhost:3001/api/auctions \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "itemId": "550e8400-e29b-41d4-a716-446655440000",
    "quantity": 1,
    "startingPrice": 1000,
    "duration": 86400000
  }'

# Search auctions
curl -X GET "http://localhost:3001/api/auctions?regionId=global&limit=10"

# Get market stats
curl -X GET "http://localhost:3001/api/auctions/stats?timeRange=7"
```

## Support

For API support and questions:
- Create an issue on GitHub
- Join our Discord server
- Check the documentation wiki