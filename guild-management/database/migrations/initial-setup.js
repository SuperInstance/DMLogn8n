/**
 * Initial Database Setup Migration
 * Creates indexes and validates schemas for guild management system
 */

const collections = {
  // Guild collections
  guilds: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["id", "name", "tag", "leaderId", "status", "created"],
        properties: {
          id: { bsonType: "string", pattern: "^guild_[a-z0-9]{9,}$" },
          name: { bsonType: "string", minLength: 3, maxLength: 32 },
          tag: { bsonType: "string", minLength: 2, maxLength: 5, pattern: "^[A-Z0-9]{2,5}$" },
          leaderId: { bsonType: "string" },
          status: { bsonType: "string", enum: ["active", "inactive", "suspended", "dissolved"] },
          level: { bsonType: "int", minimum: 1, maximum: 100 },
          created: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { id: 1 }, unique: true, name: "guild_id_unique" },
      { key: { name: 1 }, unique: true, name: "guild_name_unique" },
      { key: { tag: 1 }, unique: true, name: "guild_tag_unique" },
      { key: { leaderId: 1 }, name: "guild_leader" },
      { key: { status: 1, level: -1 }, name: "guild_status_level" }
    ]
  },

  guild_members: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["guildId", "playerId", "rank", "status", "joined"],
        properties: {
          guildId: { bsonType: "string" },
          playerId: { bsonType: "string" },
          rank: { bsonType: "string", enum: ["Leader", "Officer", "Veteran", "Member", "Initiate"] },
          status: { bsonType: "string", enum: ["active", "inactive", "suspended", "left"] },
          joined: { bsonType: "date" },
          lastActivity: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1, playerId: 1 }, unique: true, name: "guild_member_unique" },
      { key: { guildId: 1, rank: 1 }, name: "guild_member_rank" },
      { key: { guildId: 1, status: 1 }, name: "guild_member_status" },
      { key: { playerId: 1 }, name: "member_player" },
      { key: { lastActivity: 1 }, name: "member_activity" }
    ]
  },

  guild_banks: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["guildId", "gold", "tabs", "created"],
        properties: {
          guildId: { bsonType: "string" },
          gold: { bsonType: "long", minimum: 0 },
          tabs: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["id", "name", "maxSlots"],
              properties: {
                id: { bsonType: "string" },
                name: { bsonType: "string", maxLength: 50 },
                maxSlots: { bsonType: "int", minimum: 1 }
              }
            }
          },
          created: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1 }, unique: true, name: "guild_bank_unique" }
    ]
  },

  // Alliance collections
  alliances: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["id", "name", "tag", "creatorGuildId", "leaderGuildId", "memberGuilds", "status", "created"],
        properties: {
          id: { bsonType: "string", pattern: "^alliance_[a-z0-9]{9,}$" },
          name: { bsonType: "string", minLength: 3, maxLength: 32 },
          tag: { bsonType: "string", minLength: 2, maxLength: 5, pattern: "^[A-Z0-9]{2,5}$" },
          creatorGuildId: { bsonType: "string" },
          leaderGuildId: { bsonType: "string" },
          memberGuilds: { bsonType: "array", items: { bsonType: "string" }, minItems: 1 },
          status: { bsonType: "string", enum: ["active", "inactive", "dissolved", "suspended"] },
          level: { bsonType: "int", minimum: 1, maximum: 50 },
          created: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { id: 1 }, unique: true, name: "alliance_id_unique" },
      { key: { name: 1 }, unique: true, name: "alliance_name_unique" },
      { key: { tag: 1 }, unique: true, name: "alliance_tag_unique" },
      { key: { leaderGuildId: 1 }, name: "alliance_leader" },
      { key: { memberGuilds: 1 }, name: "alliance_members" }
    ]
  },

  alliance_applications: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["allianceId", "guildId", "status", "submittedAt"],
        properties: {
          allianceId: { bsonType: "string" },
          guildId: { bsonType: "string" },
          status: { bsonType: "string", enum: ["pending", "accepted", "rejected", "withdrawn"] },
          submittedAt: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { allianceId: 1, status: 1 }, name: "alliance_app_alliance_status" },
      { key: { guildId: 1 }, name: "alliance_app_guild" },
      { key: { submittedAt: 1 }, name: "alliance_app_submitted" }
    ]
  },

  // Activity collections
  guild_events: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["guildId", "title", "creatorId", "startTime", "status", "created"],
        properties: {
          guildId: { bsonType: "string" },
          title: { bsonType: "string", maxLength: 100 },
          creatorId: { bsonType: "string" },
          startTime: { bsonType: "date" },
          status: { bsonType: "string", enum: ["scheduled", "active", "completed", "cancelled"] },
          created: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1, status: 1 }, name: "guild_event_guild_status" },
      { key: { startTime: 1 }, name: "guild_event_start_time" },
      { key: { creatorId: 1 }, name: "guild_event_creator" }
    ]
  },

  guild_quests: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["guildId", "title", "type", "status", "created"],
        properties: {
          guildId: { bsonType: "string" },
          title: { bsonType: "string", maxLength: 100 },
          type: { bsonType: "string", enum: ["collect", "defeat", "explore", "craft", "social", "raid", "pvp"] },
          status: { bsonType: "string", enum: ["active", "completed", "expired"] },
          created: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1, status: 1 }, name: "guild_quest_guild_status" },
      { key: { type: 1 }, name: "guild_quest_type" },
      { key: { created: -1 }, name: "guild_quest_created" }
    ]
  },

  // Communication collections
  guild_chat: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["guildId", "playerId", "content", "timestamp"],
        properties: {
          guildId: { bsonType: "string" },
          playerId: { bsonType: "string" },
          channel: { bsonType: "string", enum: ["general", "officers", "veterans", "recruitment"] },
          content: { bsonType: "string", maxLength: 500 },
          timestamp: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1, timestamp: -1 }, name: "guild_chat_guild_time" },
      { key: { channel: 1, timestamp: -1 }, name: "guild_chat_channel_time" },
      { key: { playerId: 1, timestamp: -1 }, name: "guild_chat_sender_time" },
      { key: { timestamp: 1 }, expireAfterSeconds: 2592000, name: "guild_chat_ttl" }
    ]
  },

  // Audit collections
  guild_audit_log: {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["action", "timestamp"],
        properties: {
          guildId: { bsonType: "string" },
          userId: { bsonType: "string" },
          action: { bsonType: "string" },
          targetId: { bsonType: "string" },
          metadata: { bsonType: "object" },
          timestamp: { bsonType: "date" }
        }
      }
    },
    indexes: [
      { key: { guildId: 1, timestamp: -1 }, name: "audit_guild_time" },
      { key: { userId: 1, timestamp: -1 }, name: "audit_user_time" },
      { key: { action: 1, timestamp: -1 }, name: "audit_action_time" },
      { key: { timestamp: 1 }, expireAfterSeconds: 31536000, name: "audit_ttl" }
    ]
  }
};

async function setupDatabase(db) {
  console.log('Setting up Guild Management Database...');

  try {
    // Create collections with validators and indexes
    for (const [collectionName, config] of Object.entries(collections)) {
      console.log(`Setting up collection: ${collectionName}`);

      // Check if collection exists
      const collections = await db.listCollections({ name: collectionName }).toArray();

      if (collections.length === 0) {
        // Create collection with validator
        await db.createCollection(collectionName, {
          validator: config.validator,
          validationLevel: 'moderate',
          validationAction: 'error'
        });
        console.log(`Created collection: ${collectionName}`);
      } else {
        // Update existing collection validator
        await db.command({
          collMod: collectionName,
          validator: config.validator,
          validationLevel: 'moderate',
          validationAction: 'error'
        });
        console.log(`Updated validator for collection: ${collectionName}`);
      }

      // Create indexes
      if (config.indexes && config.indexes.length > 0) {
        const collection = db.collection(collectionName);

        for (const indexSpec of config.indexes) {
          try {
            await collection.createIndex(indexSpec.key, {
              ...indexSpec,
              background: true
            });
            console.log(`Created index: ${indexSpec.name || JSON.stringify(indexSpec.key)} on ${collectionName}`);
          } catch (error) {
            if (error.code === 85) { // Index already exists
              console.log(`Index already exists: ${indexSpec.name || JSON.stringify(indexSpec.key)} on ${collectionName}`);
            } else {
              console.error(`Error creating index on ${collectionName}:`, error);
            }
          }
        }
      }
    }

    // Insert default data if needed
    await insertDefaultData(db);

    console.log('Database setup completed successfully!');
    return true;

  } catch (error) {
    console.error('Error setting up database:', error);
    return false;
  }
}

async function insertDefaultData(db) {
  console.log('Inserting default data...');

  try {
    // Create default ranks if they don't exist
    const defaultRanks = [
      {
        guildId: 'default',
        name: 'Leader',
        level: 100,
        permissions: [
          'invite_members', 'kick_members', 'promote_members', 'demote_members',
          'manage_ranks', 'manage_bank', 'manage_settings', 'disband_guild',
          'start_wars', 'accept_alliances'
        ],
        color: '#FFD700',
        icon: '👑',
        description: 'Guild Leader - Full control',
        isCustom: false,
        created: new Date()
      },
      {
        guildId: 'default',
        name: 'Officer',
        level: 75,
        permissions: [
          'invite_members', 'kick_members', 'promote_members', 'manage_bank',
          'start_events', 'accept_applications'
        ],
        color: '#C0C0C0',
        icon: '⭐',
        description: 'Guild Officer - Management role',
        isCustom: false,
        created: new Date()
      },
      {
        guildId: 'default',
        name: 'Veteran',
        level: 50,
        permissions: [
          'invite_members', 'access_bank', 'start_events', 'moderate_chat'
        ],
        color: '#CD7F32',
        icon: '🏆',
        description: 'Veteran Member - Trusted role',
        isCustom: false,
        created: new Date()
      },
      {
        guildId: 'default',
        name: 'Member',
        level: 25,
        permissions: [
          'access_bank', 'participate_events', 'guild_chat'
        ],
        color: '#00FF00',
        icon: '✓',
        description: 'Regular Guild Member',
        isCustom: false,
        created: new Date()
      },
      {
        guildId: 'default',
        name: 'Initiate',
        level: 10,
        permissions: [
          'guild_chat', 'participate_events'
        ],
        color: '#808080',
        icon: '🌱',
        description: 'New Member - Trial period',
        isCustom: false,
        created: new Date()
      }
    ];

    // Only insert default ranks if the guild_ranks collection is empty
    const ranksCount = await db.collection('guild_ranks').countDocuments();
    if (ranksCount === 0) {
      await db.collection('guild_ranks').insertMany(defaultRanks);
      console.log('Inserted default ranks');
    }

    // Create default guild chat channels
    const defaultChannels = [
      {
        name: 'General Chat Channel',
        type: 'text',
        permissions: 'all',
        description: 'General guild communication',
        created: new Date()
      },
      {
        name: 'Officer Channel',
        type: 'restricted',
        permissions: 'officers',
        description: 'Officer-only discussions',
        created: new Date()
      },
      {
        name: 'Events Channel',
        type: 'text',
        permissions: 'members',
        description: 'Event announcements and discussion',
        created: new Date()
      }
    ];

    // Store default channels in a system collection
    await db.collection('system_settings').updateOne(
      { key: 'default_chat_channels' },
      {
        $set: {
          key: 'default_chat_channels',
          value: defaultChannels,
          updated: new Date()
        }
      },
      { upsert: true }
    );

    console.log('Default data inserted successfully');

  } catch (error) {
    console.error('Error inserting default data:', error);
    throw error;
  }
}

async function validateSetup(db) {
  console.log('Validating database setup...');

  try {
    const validationResults = {};

    // Check collections exist
    for (const collectionName of Object.keys(collections)) {
      const collections = await db.listCollections({ name: collectionName }).toArray();
      validationResults[collectionName] = {
        exists: collections.length > 0,
        indexes: []
      };

      if (collections.length > 0) {
        const collection = db.collection(collectionName);
        const indexes = await collection.indexInformation({ full: true });
        validationResults[collectionName].indexes = indexes;
      }
    }

    // Test a simple query on each collection
    for (const collectionName of Object.keys(collections)) {
      try {
        const collection = db.collection(collectionName);
        await collection.findOne();
        validationResults[collectionName].queryTest = 'success';
      } catch (error) {
        validationResults[collectionName].queryTest = `error: ${error.message}`;
      }
    }

    console.log('Database validation completed');
    return validationResults;

  } catch (error) {
    console.error('Error validating database setup:', error);
    throw error;
  }
}

module.exports = {
  setupDatabase,
  validateSetup,
  collections
};