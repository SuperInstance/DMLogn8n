# Advanced Crafting System API Documentation

## Overview

The Advanced Crafting System provides a comprehensive API for managing all aspects of crafting, from basic item creation to complex social interactions. This document details all available endpoints, methods, and data structures.

## Table of Contents

1. [Core Crafting API](#core-crafting-api)
2. [Material System API](#material-system-api)
3. [Social Features API](#social-features-api)
4. [Profession-specific APIs](#profession-specific-apis)
5. [Data Structures](#data-structures)
6. [Error Handling](#error-handling)
7. [Webhooks](#webhooks)

## Core Crafting API

### Crafting Methods

#### `craftItem(crafterId, recipeId, materials, options)`

Crafts an item using specified materials and options.

**Parameters:**
- `crafterId` (string, required): Unique identifier of the crafter
- `recipeId` (string, required): ID of the recipe to craft
- `materials` (array, required): Array of material objects
  - `id` (string): Material ID
  - `quantity` (number): Amount required
- `options` (object, optional): Additional crafting parameters
  - `useTechniques` (array): List of crafting techniques to apply
  - `qualityTarget` (number): Target quality (1-100)
  - `rushOrder` (boolean): Expedited crafting (reduces time, affects quality)
  - `experimentMode` (boolean): Enable recipe experimentation

**Returns:**
```javascript
{
  crafterId: string,
  recipeId: string,
  timestamp: string,
  success: boolean,
  criticalSuccess: boolean,
  criticalFailure: boolean,
  quality: number,
  experience: number,
  item?: {
    id: string,
    name: string,
    type: string,
    quality: number,
    properties: object,
    durability: number,
    value: number
  },
  failureType?: string,
  penalties?: object
}
```

**Example:**
```javascript
const result = await craftingSystem.craftItem(
    'player_001',
    'longsword_steel',
    [
        { id: 'steel_ingot', quantity: 3 },
        { id: 'leather_strip', quantity: 2 }
    ],
    {
        useTechniques: ['FOLDING'],
        qualityTarget: 85,
        experimentMode: false
    }
);
```

#### `discoverRecipe(crafterId, baseRecipeId, experimentMaterials)`

Attempts to discover a new recipe variant through experimentation.

**Parameters:**
- `crafterId` (string, required): Crafter's unique ID
- `baseRecipeId` (string, required): Base recipe to experiment with
- `experimentMaterials` (array, required): Materials for experimentation

**Returns:**
```javascript
{
  success: boolean,
  recipe?: object, // New recipe if discovery successful
  experience: number,
  cost: number
}
```

#### `getRecipe(recipeId)`

Retrieves recipe details by ID.

**Parameters:**
- `recipeId` (string, required): Recipe ID to retrieve

**Returns:** Recipe object or null if not found

#### `getRecipesByProfession(profession)`

Gets all recipes for a specific profession.

**Parameters:**
- `profession` (string, required): Profession name

**Returns:** Array of recipe objects

### Crafter Management

#### `getCrafter(crafterId)`

Retrieves crafter information and statistics.

**Parameters:**
- `crafterId` (string, required): Crafter's unique ID

**Returns:**
```javascript
{
  id: string,
  name: string,
  skills: {
    [profession]: number
  },
  stats: {
    totalCrafts: number,
    successfulCrafts: number,
    criticalSuccesses: number,
    [profession]: object
  },
  resources: {
    gold: number,
    [otherResources]: number
  },
  unlockedRecipes: array,
  achievements: array
}
```

#### `updateCrafterStats(crafterId, statsUpdate)`

Updates crafter statistics and achievements.

**Parameters:**
- `crafterId` (string, required): Crafter's unique ID
- `statsUpdate` (object, required): Statistics to update

## Material System API

### Material Management

#### `createMaterial(materialData)`

Creates a new material with specified properties.

**Parameters:**
- `materialData` (object, required): Material creation data
  - `name` (string): Material name
  - `type` (string): Material type (METAL, HERB, GEM, etc.)
  - `quality` (number): Material quality (1-100)
  - `quantity` (number): Initial quantity
  - `properties` (object): Material-specific properties

**Returns:** Material object

#### `harvestMaterial(harvesterId, location, materialType, toolId, skill)`

Harvests materials from a specified location.

**Parameters:**
- `harvesterId` (string, required): Harvester's ID
- `location` (string, required): Harvesting location/zone
- `materialType` (string, required): Type of material to harvest
- `toolId` (string, optional): Tool being used
- `skill` (number, required): Harvesting skill level

**Returns:**
```javascript
{
  success: boolean,
  materials: array,
  experience: number,
  location: string
}
```

#### `processMaterial(processorId, materialId, processType, targetQuality)`

Processes a material to improve its quality or change its properties.

**Parameters:**
- `processorId` (string, required): Processor's ID
- `materialId` (string, required): Material to process
- `processType` (string, required): Type of processing
- `targetQuality` (number, optional): Target quality level

**Returns:**
```javascript
{
  success: boolean,
  originalMaterial: object,
  processedMaterial?: object,
  experience: number
}
```

### Material Trading

#### `createMaterialListing(sellerId, materialId, quantity, price, listingType)`

Lists materials on the marketplace for trading.

**Parameters:**
- `sellerId` (string, required): Seller's ID
- `materialId` (string, required): Material ID to list
- `quantity` (number, required): Amount to sell
- `price` (number, required): Price per unit
- `listingType` (string, required): 'auction', 'fixed_price', or 'trade'

**Returns:** Listing object

#### `purchaseMaterial(buyerId, listingId, quantity)`

Purchases materials from a marketplace listing.

**Parameters:**
- `buyerId` (string, required): Buyer's ID
- `listingId` (string, required): Listing ID
- `quantity` (number, required): Amount to purchase

**Returns:** Purchase result object

## Social Features API

### Crafting Orders

#### `createCraftingOrder(clientId, orderDetails)`

Creates a new crafting order for other players to fulfill.

**Parameters:**
- `clientId` (string, required): Client's ID
- `orderDetails` (object, required): Order specifications
  - `type` (string): 'individual', 'bulk', or 'commission'
  - `priority` (string): 'low', 'normal', 'high', or 'urgent'
  - `items` (array): Items to be crafted
  - `quality` (string): Required quality level
  - `deadline` (string): Order deadline
  - `payment` (object): Payment details
  - `specialRequirements` (array): Additional requirements

**Returns:** Order object

#### `applyForOrder(crafterId, orderId, application)`

Applies to fulfill a crafting order.

**Parameters:**
- `crafterId` (string, required): Crafter's ID
- `orderId` (string, required): Order ID
- `application` (object, required): Application details
  - `estimatedTime` (number): Time to complete (in seconds)
  - `qualityGuarantee` (number): Guaranteed quality level
  - `totalCost` (number): Total cost
  - `approach` (string): Crafting approach description
  - `portfolio` (array): Previous work examples

**Returns:** Application object

#### `acceptApplication(orderId, applicationId, clientId)`

Accepts an application and assigns the crafter to the order.

**Parameters:**
- `orderId` (string, required): Order ID
- `applicationId` (string, required): Application ID
- `clientId` (string, required): Client's ID (for verification)

**Returns:** Updated order object

### Guild Workshops

#### `createGuildWorkshop(guildId, workshopDetails)`

Creates a new guild workshop.

**Parameters:**
- `guildId` (string, required): Guild's ID
- `workshopDetails` (object, required): Workshop configuration
  - `name` (string): Workshop name
  - `type` (string): Workshop type
  - `location` (string): Workshop location
  - `initialResources` (number): Starting resources
  - `foundingMembers` (array): Initial members

**Returns:** Workshop object

#### `upgradeWorkshop(workshopId, upgradeType, resources)`

Upgrades a workshop with new features or increased level.

**Parameters:**
- `workshopId` (string, required): Workshop ID
- `upgradeType` (string, required): Type of upgrade
- `resources` (number, required): Resources to spend

**Returns:** Updated workshop object

#### `manageWorkshopAccess(workshopId, memberId, accessLevel)`

Manages member access levels in a workshop.

**Parameters:**
- `workshopId` (string, required): Workshop ID
- `memberId` (string, required): Member's ID
- `accessLevel` (string): New access level

**Returns:** Updated workshop object

### Competitions

#### `createCompetition(organizerId, competitionDetails)`

Creates a new crafting competition.

**Parameters:**
- `organizerId` (string, required): Competition organizer's ID
- `competitionDetails` (object, required): Competition configuration
  - `name` (string): Competition name
  - `description` (string): Competition description
  - `type` (string): Competition type
  - `category` (string): Crafting category
  - `rules` (array): Competition rules
  - `timeline` (object): Important dates
  - `prizes` (array): Prize structure
  - `entryFee` (number): Cost to enter

**Returns:** Competition object

#### `registerForCompetition(competitionId, participantId, registrationData)`

Registers a participant for a competition.

**Parameters:**
- `competitionId` (string, required): Competition ID
- `participantId` (string, required): Participant's ID
- `registrationData` (object, required): Registration information

**Returns:** Registration object

#### `submitCompetitionEntry(competitionId, participantId, submission)`

Submits an entry for a competition.

**Parameters:**
- `competitionId` (string, required): Competition ID
- `participantId` (string, required): Participant's ID
- `submission` (object, required): Entry details

**Returns:** Entry object

### Master-Apprentice System

#### `createApprenticeship(masterId, apprenticeId, terms)`

Creates a new master-apprentice relationship.

**Parameters:**
- `masterId` (string, required): Master's ID
- `apprenticeId` (string, required): Apprentice's ID
- `terms` (object, required): Apprenticeship terms
  - `duration` (number): Duration in days
  - `specializations` (array): Areas of focus
  - `goals` (array): Learning objectives
  - `obligations` (object): Mutual obligations
  - `compensation` (object): Payment/terms

**Returns:** Apprenticeship object

#### `conductTrainingSession(apprenticeshipId, sessionDetails)`

Conducts a training session as part of an apprenticeship.

**Parameters:**
- `apprenticeshipId` (string, required): Apprenticeship ID
- `sessionDetails` (object, required): Session details
  - `type` (string): Session type
  - `topic` (string): Session topic
  - `duration` (number): Session duration
  - `objectives` (array): Learning objectives

**Returns:** Session object

## Profession-specific APIs

### Blacksmithing

#### `craftWithTechnique(crafterId, recipeId, materials, techniqueIds, options)`

Crafts an item using specific blacksmithing techniques.

**Parameters:**
- `crafterId` (string, required): Crafter's ID
- `recipeId` (string, required): Recipe ID
- `materials` (array, required): Required materials
- `techniqueIds` (array, required): Techniques to apply
- `options` (object, optional): Additional options

**Returns:** Enhanced crafting result

#### `createAlloy(crafterId, alloyId, components, quality)`

Creates a custom alloy from component materials.

**Parameters:**
- `crafterId` (string, required): Crafter's ID
- `alloyId` (string, required): Alloy recipe ID
- `components` (array, required): Material components
- `quality` (number, optional): Target quality

**Returns:** Alloy creation result

### Alchemy

#### `brewCustomPotion(alchemistId, formula, reagents, modifications)`

Brews a custom potion using specific formula and reagents.

**Parameters:**
- `alchemistId` (string, required): Alchemist's ID
- `formula` (string, required): Alchemical formula
- `reagents` (array, required): Required reagents
- `modifications` (object, optional): Formula modifications

**Returns:** Potion brewing result

#### `refinePotion(alchemistId, potionId, refinementType, catalysts)`

Refines an existing potion to improve its properties.

**Parameters:**
- `alchemistId` (string, required): Alchemist's ID
- `potionId` (string, required): Potion to refine
- `refinementType` (string, required): Type of refinement
- `catalysts` (array, required): Refinement catalysts

**Returns:** Refinement result

## Data Structures

### Recipe Object

```javascript
{
  id: string,
  name: string,
  type: string,
  tier: string, // SIMPLE, ADVANCED, MASTER, ARTIFACT, MAGICAL
  requiredSkill: number,
  materials: [
    {
      id: string,
      quantity: number,
      optional: boolean
    }
  ],
  tools: array,
  station: string,
  craftingTime: number,
  experience: number,
  baseProperties: object,
  specialEffects: array,
  questRequirements: array
}
```

### Material Object

```javascript
{
  id: string,
  name: string,
  type: string,
  quality: number,
  properties: {
    [property]: number
  },
  quantity: number,
  stackSize: number,
  harvestedAt: string,
  harvestedBy: string,
  location: string,
  durability: number,
  value: number,
  storageRequirements: array,
  specialEffects: array,
  tags: array
}
```

### Crafter Object

```javascript
{
  id: string,
  name: string,
  skills: {
    [profession]: number
  },
  stats: {
    totalCrafts: number,
    successfulCrafts: number,
    criticalSuccesses: number,
    [profession]: {
      itemsCrafted: number,
      averageQuality: number,
      masterworksCreated: number
    }
  },
  resources: {
    gold: number,
    [resource]: number
  },
  unlockedRecipes: array,
  achievements: array,
  reputation: {
    overall: number,
    reliability: number,
    quality: number
  }
}
```

### Order Object

```javascript
{
  id: string,
  clientId: string,
  type: string,
  priority: string,
  specifications: {
    items: array,
    quality: string,
    deadline: string,
    specialRequirements: array
  },
  payment: {
    amount: number,
    currency: string,
    method: string,
    escrow: boolean
  },
  status: string,
  applicants: array,
  selectedCrafter: string,
  timeline: {
    createdAt: string,
    deadline: string,
    estimatedCompletion: string
  },
  reputation: {
    clientRating: number,
    crafterRating: number,
    feedback: string
  }
}
```

## Error Handling

The API uses standard HTTP error codes and provides detailed error messages:

### Common Error Codes

- `400 Bad Request`: Invalid parameters or data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions or skill level
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource state conflict
- `422 Unprocessable Entity`: Validation failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```javascript
{
  error: {
    code: string,
    message: string,
    details: object,
    timestamp: string,
    requestId: string
  }
}
```

### Example Error Responses

```javascript
// Insufficient skill level
{
  error: {
    code: "INSUFFICIENT_SKILL",
    message: "Skill level too low for this recipe",
    details: {
      required: 300,
      current: 150,
      profession: "BLACKSMITHING"
    }
  }
}

// Missing materials
{
  error: {
    code: "INSUFFICIENT_MATERIALS",
    message: "Not enough materials for crafting",
    details: {
      missing: [
        { id: "steel_ingot", required: 5, available: 2 }
      ]
    }
  }
}
```

## Webhooks

The system supports webhooks for real-time notifications of important events.

### Available Webhook Events

- `crafting.completed`: Item crafting finished
- `crafting.failed`: Crafting attempt failed
- `material.harvested`: Material harvesting completed
- `order.created`: New crafting order created
- `order.completed`: Order fulfillment completed
- `competition.started`: Competition began
- `competition.ended`: Competition finished
- `apprenticeship.created`: New apprenticeship formed

### Webhook Payload Format

```javascript
{
  event: string,
  timestamp: string,
  data: {
    // Event-specific data
  },
  metadata: {
    version: string,
    source: string
  }
}
```

### Setting Up Webhooks

```javascript
// Register webhook
await craftingSystem.registerWebhook('https://your-domain.com/webhooks', [
  'crafting.completed',
  'order.created'
]);

// Webhook handler example
app.post('/webhooks', (req, res) => {
  const { event, data } = req.body;

  switch(event) {
    case 'crafting.completed':
      handleCraftingCompleted(data);
      break;
    case 'order.created':
      handleOrderCreated(data);
      break;
  }

  res.status(200).send('OK');
});
```

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Standard users**: 100 requests per minute
- **Premium users**: 500 requests per minute
- **API keys**: 1000 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per period
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time until reset (Unix timestamp)

## Authentication

API requests require authentication using one of the following methods:

### API Key Authentication

```javascript
headers: {
  'Authorization': 'Bearer your-api-key',
  'Content-Type': 'application/json'
}
```

### Session-based Authentication

```javascript
headers: {
  'Authorization': 'Session your-session-token',
  'Content-Type': 'application/json'
}
```

## SDKs and Libraries

### JavaScript/Node.js

```bash
npm install @dmlogn8n/crafting-api
```

```javascript
const CraftingAPI = require('@dmlogn8n/crafting-api');
const client = new CraftingAPI({
  apiKey: 'your-api-key',
  baseURL: 'https://api.dmlogn8n.com'
});

// Craft an item
const result = await client.crafting.craftItem('player_001', 'sword_steel', materials);
```

### Python

```bash
pip install dmlogn8n-crafting
```

```python
from dmlogn8n_crafting import CraftingClient

client = CraftingClient(api_key='your-api-key')
result = client.crafting.craft_item('player_001', 'sword_steel', materials)
```

## Support

For API support and documentation:

- **Documentation**: https://docs.dmlogn8n.com/crafting-api
- **API Status**: https://status.dmlogn8n.com
- **Support Email**: api-support@dmlogn8n.com
- **Discord Community**: https://discord.gg/dmlogn8n