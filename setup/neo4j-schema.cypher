// Neo4j Schema for DMlogn8n World State Management System
// This file defines the complete graph database schema for tracking
// relationships, world states, and cascading effects

// ============================================
// CONSTRAINTS - Ensure data integrity
// ============================================

// Campaign constraints
CREATE CONSTRAINT campaign_id_unique IF NOT EXISTS FOR (c:Campaign) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT campaign_id_exists IF NOT EXISTS FOR (c:Campaign) REQUIRE c.id IS NOT NULL;

// Node constraints
CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT npc_id_unique IF NOT EXISTS FOR (n:NPC) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT faction_id_unique IF NOT EXISTS FOR (f:Faction) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT quest_id_unique IF NOT EXISTS FOR (q:Quest) REQUIRE q.id IS UNIQUE;
CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT player_id_unique IF NOT EXISTS FOR (p:Player) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT item_id_unique IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE;

// Event and cascade constraints
CREATE CONSTRAINT cascade_id_unique IF NOT EXISTS FOR (c:Cascade) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT branch_id_unique IF NOT EXISTS FOR (b:Branch) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:Relationship) REQUIRE r.id IS UNIQUE;

// ============================================
// INDEXES - Optimize query performance
// ============================================

// Campaign indexes
CREATE INDEX campaign_status_index IF NOT EXISTS FOR (c:Campaign) ON (c.status);
CREATE INDEX campaign_created_index IF NOT EXISTS FOR (c:Campaign) ON (c.created_at);
CREATE INDEX campaign_last_update_index IF NOT EXISTS FOR (c:Campaign) ON (c.last_update);

// Location indexes
CREATE INDEX location_type_index IF NOT EXISTS FOR (l:Location) ON (l.type);
CREATE INDEX location_region_index IF NOT EXISTS FOR (l:Location) ON (l.region);
CREATE INDEX location_coordinates_index IF NOT EXISTS FOR (l:Location) ON (l.x, l.y, l.z);

// NPC indexes
CREATE INDEX npc_name_index IF NOT EXISTS FOR (n:NPC) ON (n.name);
CREATE INDEX npc_race_index IF NOT EXISTS FOR (n:NPC) ON (n.race);
CREATE INDEX npc_class_index IF NOT EXISTS FOR (n:NPC) ON (n.class);
CREATE INDEX npc_faction_index IF NOT EXISTS FOR (n:NPC) ON (n.faction_id);
CREATE INDEX npc_location_index IF NOT EXISTS FOR (n:NPC) ON (n.location_id);
CREATE INDEX npc_status_index IF NOT EXISTS FOR (n:NPC) ON (n.status);

// Faction indexes
CREATE INDEX faction_name_index IF NOT EXISTS FOR (f:Faction) ON (f.name);
CREATE INDEX faction_type_index IF NOT EXISTS FOR (f:Faction) ON (f.type);
CREATE INDEX faction_alignment_index IF NOT EXISTS FOR (f:Faction) ON (f.alignment);
CREATE INDEX faction_power_index IF NOT EXISTS FOR (f:Faction) ON (f.power_level);

// Quest indexes
CREATE INDEX quest_status_index IF NOT EXISTS FOR (q:Quest) ON (q.status);
CREATE INDEX quest_type_index IF NOT EXISTS FOR (q:Quest) ON (q.type);
CREATE INDEX quest_difficulty_index IF NOT EXISTS FOR (q:Quest) ON (q.difficulty);
CREATE INDEX quest_location_index IF NOT EXISTS FOR (q:Quest) ON (q.location_id);

// Event indexes
CREATE INDEX event_type_index IF NOT EXISTS FOR (e:Event) ON (e.type);
CREATE INDEX event_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX event_severity_index IF NOT EXISTS FOR (e:Event) ON (e.severity);
CREATE INDEX event_campaign_index IF NOT EXISTS FOR (e:Event) ON (e.campaign_id);

// Player indexes
CREATE INDEX player_name_index IF NOT EXISTS FOR (p:Player) ON (p.name);
CREATE INDEX player_level_index IF NOT EXISTS FOR (p:Player) ON (p.level);
CREATE INDEX player_class_index IF NOT EXISTS FOR (p:Player) ON (p.class);

// Item indexes
CREATE INDEX item_type_index IF NOT EXISTS FOR (i:Item) ON (i.type);
CREATE INDEX item_rarity_index IF NOT EXISTS FOR (i:Item) ON (i.rarity);
CREATE INDEX item_owner_index IF NOT EXISTS FOR (i:Item) ON (i.owner_id);

// Relationship indexes
CREATE INDEX relationship_type_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.type);
CREATE INDEX relationship_strength_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.strength);
CREATE INDEX relationship_since_index IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.since);

// Cascade indexes
CREATE INDEX cascade_depth_index IF NOT EXISTS FOR (c:Cascade) ON (c.current_depth);
CREATE INDEX cascade_max_depth_index IF NOT EXISTS FOR (c:Cascade) ON (c.max_depth);
CREATE INDEX cascade_active_index IF NOT EXISTS FOR (c:Cascade) ON (c.active);

// Time-based indexes
CREATE INDEX time_based_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX time_based_season_index IF NOT EXISTS FOR (e:Event) ON (e.season);

// Economic indexes
CREATE INDEX economic_category_index IF NOT EXISTS FOR (e:EconomicEntity) ON (e.category);
CREATE INDEX economic_value_index IF NOT EXISTS FOR (e:EconomicEntity) ON (e.value);

// ============================================
// NODE LABELS - Define entity types
// ============================================

// Core campaign structure
(:Campaign {
  id: String,           // Unique identifier
  name: String,          // Campaign name
  description: String,   // Campaign description
  status: String,        // active, paused, completed, archived
  created_at: DateTime,  // Creation timestamp
  last_update: DateTime, // Last update timestamp
  settings: Map,         // Campaign-specific settings
  world_state: Map,      // Current world state snapshot
  time_data: Map,        // Time tracking data
  economic_data: Map,    // Economic system data
  political_landscape: Map, // Political information
  metadata: Map         // Additional metadata
})

// Location nodes
(:Location {
  id: String,           // Unique identifier
  name: String,         // Location name
  description: String,  // Detailed description
  type: String,         // city, town, dungeon, forest, etc.
  region: String,       // Geographic region
  coordinates: Map,     // x, y, z coordinates
  size: String,         // small, medium, large, massive
  population: Integer,   // Population count
  importance: Integer,   // Strategic importance (1-10)
  resources: Map,       // Available resources
  dangers: Map,         // Environmental dangers
  secrets: Map,         // Hidden information
  discovered: Boolean,  // Player discovery status
  controlled_by: String, // Controlling faction
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// NPC nodes
(:NPC {
  id: String,           // Unique identifier
  name: String,         // Character name
  title: String,        // Title or honorific
  race: String,         // Race
  class: String,        // Class or profession
  level: Integer,       // Character level
  alignment: String,    // Alignment
  faction_id: String,   // Faction affiliation
  location_id: String,  // Current location
  status: String,       // alive, dead, missing, etc.
  personality: Map,     // Personality traits
  appearance: Map,      // Physical appearance
  background: String,   // Backstory
  motivations: Map,     // Goals and motivations
  relationships: Map,   // Relationship data
  inventory: Map,       // Items and equipment
  abilities: Map,       // Skills and abilities
  secrets: Map,         // Hidden information
  schedule: Map,        // Daily/weekly schedule
  importance: Integer,  // Plot importance (1-10)
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Faction nodes
(:Faction {
  id: String,           // Unique identifier
  name: String,         // Faction name
  description: String,  // Faction description
  type: String,         // government, guild, organization, etc.
  alignment: String,    // Overall alignment
  power_level: Integer, // Relative power (1-100)
  influence: Integer,   // Sphere of influence
  stability: String,    // stable, unstable, collapsing
  resources: Map,       // Available resources
  territories: List,    // Controlled territories
  members: List,        // Important members
  relationships: Map,   // Inter-faction relationships
  goals: List,          // Faction goals
  history: Map,         // Faction history
  secrets: Map,         // Hidden information
  reputation: Map,      // Reputation with various groups
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Quest nodes
(:Quest {
  id: String,           // Unique identifier
  name: String,         // Quest name
  description: String,  // Quest description
  type: String,         // main, side, personal, faction
  status: String,       // available, active, completed, failed
  difficulty: String,   // trivial, easy, normal, hard, deadly
  objectives: List,     // Quest objectives
  rewards: Map,         // Experience, gold, items
  prerequisites: List,  // Required quests or conditions
  location_id: String,  // Primary quest location
  giver_id: String,     // Quest giver (NPC/Faction)
  time_limit: Integer,  // Time limit in hours (0 = unlimited)
  importance: Integer,  // Story importance (1-10)
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Player nodes
(:Player {
  id: String,           // Unique identifier
  name: String,         // Character name
  player_name: String,  // Real player name
  race: String,         // Character race
  class: String,        // Character class
  level: Integer,       // Character level
  alignment: String,    // Character alignment
  experience: Integer,  // Current experience
  health: Integer,      // Current health
  max_health: Integer,  // Maximum health
  abilities: Map,       // Skills and abilities
  inventory: List,      // Item inventory
  gold: Integer,        // Current gold
  location_id: String,  // Current location
  faction_reputation: Map, // Reputation with factions
  quests_active: List,  // Active quests
  quests_completed: List, // Completed quests
  backstory: String,    // Character backstory
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Item nodes
(:Item {
  id: String,           // Unique identifier
  name: String,         // Item name
  description: String,  // Item description
  type: String,         // weapon, armor, consumable, etc.
  rarity: String,       // common, uncommon, rare, etc.
  value: Integer,       // Gold value
  weight: Float,        // Weight in pounds
  properties: Map,      // Item properties and stats
  requirements: Map,    // Requirements to use
  owner_id: String,     // Current owner
  location_id: String,  // Current location (if not owned)
  history: List,        // Ownership history
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Event nodes
(:Event {
  id: String,           // Unique identifier
  type: String,         // Event type
  subtype: String,      // Event subtype
  title: String,        // Event title
  description: String,  // Event description
  severity: String,     // trivial, minor, moderate, major, catastrophic
  impact_level: String, // Local, regional, global
  campaign_id: String,  // Associated campaign
  location_ids: List,   // Affected locations
  npc_ids: List,        // Affected NPCs
  faction_ids: List,    // Affected factions
  player_ids: List,     // Affected players
  consequences: List,   // Immediate consequences
  long_term_effects: List, // Long-term effects
  player_hooks: List,   // Player action opportunities
  timestamp: DateTime,  // When event occurred
  duration: String,     // How long event lasts
  resolved: Boolean,    // Event resolution status
  created_at: DateTime,
  metadata: Map
})

// Cascade nodes (for event cascading system)
(:Cascade {
  id: String,           // Unique identifier
  campaign_id: String,  // Associated campaign
  initial_event_id: String, // Triggering event
  current_depth: Integer, // Current cascade depth
  max_depth: Integer,   // Maximum cascade depth
  active: Boolean,      // Cascade is still propagating
  completed: Boolean,   // Cascade completed
  total_effects: Integer, // Total effects generated
  branches_created: Integer, // Number of branches created
  propagation_history: List, // History of propagation
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Branch nodes (cascade branches)
(:Branch {
  id: String,           // Unique identifier
  cascade_id: String,   // Parent cascade
  parent_effect_id: String, // Triggering effect
  branch_type: String,  // Type of branch
  priority: Integer,    // Processing priority (1-10)
  delay: Float,         // Delay before processing (hours)
  conditions: Map,      // Activation conditions
  processed: Boolean,   // Branch has been processed
  created_at: DateTime,
  metadata: Map
})

// Relationship nodes (explicit relationships)
(:Relationship {
  id: String,           // Unique identifier
  type: String,         // Relationship type
  strength: Float,      // Relationship strength (-100 to 100)
  description: String,  // Relationship description
  since: DateTime,      // When relationship established
  last_interaction: DateTime, // Last interaction
  trust_level: Float,   // Trust level (0-1)
  hostility_level: Float, // Hostility level (0-1)
  intimacy_level: Float, // Intimacy level (0-1)
  professional_level: Float, // Professional relationship level (0-1)
  history: List,        // Relationship history
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// Economic nodes
(:EconomicEntity {
  id: String,           // Unique identifier
  name: String,         // Entity name
  type: String,         // market, guild, merchant, etc.
  category: String,     // goods, services, magical, etc.
  value: Float,         // Economic value
  location_id: String,  // Primary location
  inventory: Map,       // Available goods/services
  prices: Map,          // Current prices
  supply: Map,          // Supply levels
  demand: Map,          // Demand levels
  reputation: Float,    // Business reputation
  created_at: DateTime,
  last_updated: DateTime,
  metadata: Map
})

// ============================================
// RELATIONSHIPS - Define connections
// ============================================

// Campaign contains other entities
()-[:CONTAINS]->() // Campaign contains locations, NPCs, quests, etc.

// Location relationships
(:Location)-[:CONNECTS_TO {type: String, distance: Float, difficulty: Integer, conditions: Map}]->(:Location)
(:Location)-[:CONTAINS]->(:NPC)
(:Location)-[:CONTAINS]->(:Item)
(:Location)-[:SITE_OF]->(:Quest)
(:Location)-[:SITE_OF]->(:Event)

// NPC relationships
(:NPC)-[:LIVES_IN]->(:Location)
(:NPC)-[:OWNS]->(:Item)
(:NPC)-[:MEMBER_OF]->(:Faction)
(:NPC)-[:OFFERS]->(:Quest)
(:NPC)-[:PARTICIPATES_IN]->(:Event)
(:NPC)-[:RELATES_TO]->(:NPC)
(:NPC)-[:RELATES_TO]->(:Faction)
(:NPC)-[:RELATES_TO]->(:Player)

// Faction relationships
(:Faction)-[:CONTROLS]->(:Location)
(:Faction)-[:HAS_MEMBER]->(:NPC)
(:Faction)-[:ALLIED_WITH]->(:Faction)
(:Faction)-[:HOSTILE_TO]->(:Faction)
(:Faction)-[:TRADES_WITH]->(:Faction)
(:Faction)-[:INFLUENCES]->(:Location)

// Quest relationships
(:Quest)-[:TAKES_PLACE_IN]->(:Location)
(:Quest)-[:GIVEN_BY]->(:NPC)
(:Quest)-[:GIVEN_BY]->(:Faction)
(:Quest)-[:REQUIRES]->(:NPC)
(:Quest)-[:REWARDS]->(:Item)
(:Quest)-[:TRIGGERS]->(:Event)

// Player relationships
(:Player)-[:LOCATED_AT]->(:Location)
(:Player)-[:OWNS]->(:Item)
(:Player)-[:PARTICIPATES_IN]->(:Quest)
(:Player)-[:KNOWS]->(:NPC)
(:Player)-[:MEMBER_OF]->(:Faction)
(:Player)-[:WITNESSED]->(:Event)

// Item relationships
(:Item)-[:LOCATED_AT]->(:Location)
(:Item)-[:OWNED_BY]->(:NPC)
(:Item)-[:OWNED_BY]->(:Player)
(:Item)-[:REQUIRED_FOR]->(:Quest)

// Event relationships
(:Event)-[:AFFECTS]->(:Location)
(:Event)-[:AFFECTS]->(:NPC)
(:Event)-[:AFFECTS]->(:Faction)
(:Event)-[:AFFECTS]->(:Player)
(:Event)-[:TRIGGERS]->(:Event)
(:Event)-[:LEADS_TO]->(:Quest)

// Cascade system relationships
(:Event)-[:TRIGGERS_CASCADE]->(:Cascade)
(:Cascade)-[:PRODUCES]->(:Event)
(:Cascade)-[:BRANCHES_INTO]->(:Branch)
(:Branch)-[:TRIGGERS]->(:Event)

// Economic relationships
(:EconomicEntity)-[:LOCATED_AT]->(:Location)
(:EconomicEntity)-[:TRADES_WITH]->(:EconomicEntity)
(:EconomicEntity)-[:SPECIALIZES_IN]->(:Item)

// Time-based relationships
(:Event)-[:OCCURS_DURING {season: String, time_of_day: String, day_of_week: Integer}]->(:Campaign)

// ============================================
// SAMPLE DATA CREATION (Optional)
// ============================================

// Create sample campaign (commented out for production use)
/*
CREATE (campaign:Campaign {
  id: 'campaign_001',
  name: 'The Chronicles of Arcanum',
  description: 'A epic fantasy adventure in a world of magic and intrigue',
  status: 'active',
  created_at: datetime(),
  last_update: datetime(),
  settings: {
    time_scale: 1.0,
    difficulty: 'normal',
    party_size: 4
  }
})
*/

// Create sample locations (commented out for production use)
/*
CREATE (capital:Location {
  id: 'location_001',
  name: 'Arcanum City',
  description: 'The magnificent capital of the Arcanum Empire',
  type: 'city',
  region: 'Central Plains',
  coordinates: {x: 0, y: 0, z: 0},
  size: 'large',
  population: 250000,
  importance: 10,
  resources: {trade: 'high', magic: 'medium', military: 'high'},
  discovered: true,
  created_at: datetime(),
  last_updated: datetime()
})

CREATE (campaign)-[:CONTAINS]->(capital)
*/

// ============================================
// FULL-TEXT SEARCH INDEXES
// ============================================

// Create full-text search indexes for important text fields
CREATE INDEX location_name_fulltext IF NOT EXISTS FOR (l:Location) ON (name, description);
CREATE INDEX npc_name_fulltext IF NOT EXISTS FOR (n:NPC) ON (name, title, background);
CREATE INDEX faction_name_fulltext IF NOT EXISTS FOR (f:Faction) ON (name, description);
CREATE INDEX quest_name_fulltext IF NOT EXISTS FOR (q:Quest) ON (name, description);
CREATE INDEX event_name_fulltext IF NOT EXISTS FOR (e:Event) ON (title, description);

// ============================================
// PROCEDURES AND FUNCTIONS
// ============================================

// Procedure to find shortest path between two locations
// CALL spatial.shortestPath('location_001', 'location_002') YIELD path, distance

// Procedure to find all entities affected by an event cascade
// CALL cascade.findAffectedEntities('cascade_001') YIELD entities, effects

// Procedure to calculate faction power dynamics
// CALL faction.calculatePowerDynamics('campaign_001') YIELD rankings, alliances

// Procedure to get player's current quest status
// CALL quest.getPlayerStatus('player_001') YIELD active_quests, completed_quests, available_quests

// Procedure to find economic opportunities
// CALL economic.findOpportunities('campaign_001') YIELD opportunities, markets

// ============================================
// TRIGGERS (if supported by Neo4j version)
// ============================================

// Auto-update timestamps on modification
// Note: Actual triggers would need to be implemented through APOC procedures or application logic

// ============================================
// VIEWS (if supported by Neo4j version)
// ============================================

// View for active quests by location
// CREATE VIEW active_quests_by_location AS
// MATCH (l:Location)<-[:TAKES_PLACE_IN]-(q:Quest {status: 'active'})
// RETURN l.name as location, collect(q) as active_quests

// View for faction relationships
// CREATE VIEW faction_relationships AS
// MATCH (f1:Faction)-[r]->(f2:Faction)
// RETURN f1.name as faction_1, type(r) as relationship_type, f2.name as faction_2, r.strength

// ============================================
// MAINTENANCE QUERIES
// ============================================

// Query to find orphaned nodes (nodes without relationships)
// MATCH (n) WHERE NOT (n)--() RETURN n

// Query to find duplicate relationships
// MATCH (a)-[r1]->(b)-[r2]->(a) WHERE id(r1) < id(r2) RETURN a, r1, r2, b

// Query to update relationship timestamps
// MATCH ()-[r:RELATES_TO]-() WHERE r.last_updated < datetime() - duration('P7D')
// SET r.last_updated = datetime()

// Query to clean up old events (older than 1 year)
// MATCH (e:Event) WHERE e.timestamp < datetime() - duration('P1Y')
// DETACH DELETE e

// ============================================
// SECURITY CONSIDERATIONS
// ============================================

// The schema should be used with appropriate user permissions:
// - read_only_user: Can only read data
// - read_write_user: Can read and write data
// - admin_user: Full access including schema modifications

// Example user creation (to be executed by admin):
// CREATE USER read_only_user SET PASSWORD 'secure_password' CHANGE NOT REQUIRED;
// GRANT READ ON GRAPH * TO read_only_user;
// GRANT ACCESS ON DATABASE * TO read_only_user;

// ============================================
// PERFORMANCE MONITORING QUERIES
// ============================================

// Query to check database size
// CALL db.info() YIELD name, dataOnDisk

// Query to check node count by label
// CALL db.labels() YIELD label
// CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
// YIELD value
// RETURN label, value.count

// Query to check relationship count by type
// CALL db.relationshipTypes() YIELD relationshipType
// CALL apoc.cypher.run('MATCH ()-[r:' + relationshipType + ']->() RETURN count(r) as count', {})
// YIELD value
// RETURN relationshipType, value.count

// Query to identify slow queries (requires APOC)
// CALL apoc.monitor.stores() YIELD *;