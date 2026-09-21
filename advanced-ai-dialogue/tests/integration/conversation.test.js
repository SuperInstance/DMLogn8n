const request = require('supertest');
const { app, server } = require('../../src/api/server');
const ContextAwareConversationManager = require('../../src/core/ContextAwareConversationManager');
const EmotionalIntelligenceEngine = require('../../src/core/EmotionalIntelligenceEngine');

describe('Conversation Integration Tests', () => {
  let conversationManager;
  let emotionalEngine;
  let conversationId;

  beforeAll(async () => {
    // Initialize test engines
    conversationManager = new ContextAwareConversationManager({
      maxConversations: 10,
      shortTermMemoryLimit: 20,
      longTermMemoryLimit: 100
    });

    emotionalEngine = new EmotionalIntelligenceEngine({
      emotionDecayRate: 0.01,
      memoryLimit: 100,
      empathyThreshold: 0.6
    });

    // Set up test environment
    app.set('conversationManager', conversationManager);
    app.set('emotionalEngine', emotionalEngine);
  });

  afterAll(async () => {
    // Clean up
    if (server) {
      server.close();
    }
    conversationManager.reset();
    emotionalEngine.reset();
  });

  describe('Conversation Lifecycle', () => {
    test('should initiate a new conversation', async () => {
      const participants = [
        {
          id: 'player_001',
          name: 'Aria',
          role: 'player',
          race: 'elf',
          class: 'ranger'
        },
        {
          id: 'npc_001',
          name: 'Elder Thorin',
          role: 'npc',
          race: 'dwarf',
          class: 'fighter'
        }
      ];

      const response = await request(app)
        .post('/api/conversation/initiate')
        .send({
          participants,
          context: {
            campaign: {
              id: 'campaign_001',
              name: 'The Dragon\'s Legacy'
            },
            environment: {
              location: {
                name: 'The Prancing Pony',
                type: 'tavern',
                description: 'A cozy inn in Bree'
              },
              time: {
                inGame: '20:30',
                season: 'spring'
              },
              atmosphere: 'peaceful'
            },
            objectives: ['Investigate strange happenings', 'Meet the local wizard']
          }
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.conversation.id).toBeDefined();
      expect(response.body.data.conversation.participants).toHaveLength(2);
      expect(response.body.data.context).toBeDefined();
      expect(response.body.data.suggestions).toBeDefined();

      conversationId = response.body.data.conversation.id;
    });

    test('should process messages in conversation', async () => {
      const messageData = {
        conversationId,
        message: 'Hello Elder Thorin! I heard you might have information about the dragon sightings in the region.',
        speakerId: 'player_001',
        additionalContext: {
          urgency: 'medium',
          emotionalState: {
            curiosity: 0.7,
            respect: 0.8
          }
        }
      };

      const response = await request(app)
        .post('/api/conversation/process-message')
        .send(messageData)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.message).toBeDefined();
      expect(response.body.data.context).toBeDefined();
      expect(response.body.data.suggestions).toBeDefined();
      expect(response.body.data.suggestions.length).toBeGreaterThan(0);

      // Verify context was updated
      expect(response.body.data.context.environmental).toBeDefined();
      expect(response.body.data.context.relational).toBeDefined();
    });

    test('should handle emotional context in responses', async () => {
      // Send an emotionally charged message
      const emotionalMessage = {
        conversationId,
        message: 'I\'m actually quite worried about these dragon sightings. My village was destroyed by a dragon years ago.',
        speakerId: 'player_001',
        additionalContext: {
          emotionalState: {
            fear: 0.6,
            sadness: 0.7,
            trust: 0.5
          },
          backstory: 'village_destroyed_by_dragon'
        }
      };

      const response = await request(app)
        .post('/api/conversation/process-message')
        .send(emotionalMessage)
        .expect(200);

      expect(response.body.success).toBe(true);

      // Check if empathy was detected
      const suggestions = response.body.data.suggestions;
      const empatheticResponse = suggestions.find(s =>
        s.type === 'empathetic' || s.emotionalTone === 'supportive'
      );
      expect(empatheticResponse).toBeDefined();
    });

    test('should track conversation topics', async () => {
      const topicMessage = {
        conversationId,
        message: 'Let\'s talk about the quest to find the ancient artifact. Do you know where it might be hidden?',
        speakerId: 'player_001'
      };

      const response = await request(app)
        .post('/api/conversation/process-message')
        .send(topicMessage)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.context.topics).toBeDefined();

      // Check if quest-related topics were extracted
      const topics = response.body.data.context.topics;
      expect(topics.some(t => t.includes('quest') || t.includes('artifact'))).toBe(true);
    });

    test('should conclude conversation properly', async () => {
      const concludeData = {
        conversationId,
        reason: 'natural',
        summary: 'The party met with Elder Thorin and gathered information about dragon sightings and an ancient artifact quest.'
      };

      const response = await request(app)
        .post('/api/conversation/conclude')
        .send(concludeData)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.conversation.state).toBe('concluded');
      expect(response.body.data.analytics).toBeDefined();
      expect(response.body.data.summary).toBeDefined();
    });
  });

  describe('Context Awareness', () => {
    test('should maintain environmental context', async () => {
      // Start new conversation with specific environment
      const participants = [
        { id: 'player_002', name: 'Grog', role: 'player', race: 'half-orc' },
        { id: 'npc_002', name: 'Elara', role: 'npc', race: 'elf' }
      ];

      const initiateResponse = await request(app)
        .post('/api/conversation/initiate')
        .send({
          participants,
          context: {
            environment: {
              location: {
                name: 'Darkmoon Forest',
                type: 'forest',
                description: 'An ancient, misty forest'
              },
              weather: {
                condition: 'foggy',
                visibility: 'poor'
              },
              atmosphere: 'mysterious'
            }
          }
        })
        .expect(200);

      const forestConversationId = initiateResponse.body.data.conversation.id;

      // Send a message that references the environment
      const messageResponse = await request(app)
        .post('/api/conversation/process-message')
        .send({
          conversationId: forestConversationId,
          message: 'This fog is so thick I can barely see the path ahead. Do you know these woods well?',
          speakerId: 'player_002'
        })
        .expect(200);

      // Verify environmental context was maintained
      const context = messageResponse.data.context;
      expect(context.environmental.location).toBeDefined();
      expect(context.environmental.weather).toBeDefined();
      expect(context.environmental.location.type).toBe('forest');
    });

    test('should track relationship dynamics', async () => {
      const participants = [
        { id: 'player_003', name: 'Lyra', role: 'player', race: 'human' },
        { id: 'npc_003', name: 'Captain Valerius', role: 'npc', race: 'human' }
      ];

      const initiateResponse = await request(app)
        .post('/api/conversation/initiate')
        .send({
          participants,
          context: {
            campaign: { id: 'campaign_002', name: 'The Pirate\'s Treasure' }
          }
        })
        .expect(200);

      const relationshipConversationId = initiateResponse.body.data.conversation.id;

      // Build relationship through positive interactions
      const messages = [
        'Captain Valerius, I\'ve heard you\'re the best sailor in these waters.',
        'Thank you for the compliment! I\'ve been sailing these seas for over 20 years.',
        'Perhaps you could help us find the legendary treasure? We would split it with you, of course.',
        'An interesting proposition. Your honesty is appreciated. Tell me more about your crew.'
      ];

      for (let i = 0; i < messages.length; i++) {
        const speakerId = i % 2 === 0 ? 'player_003' : 'npc_003';

        await request(app)
          .post('/api/conversation/process-message')
          .send({
            conversationId: relationshipConversationId,
            message: messages[i],
            speakerId
          })
          .expect(200);
      }

      // Check relationship metrics
      const relationshipResponse = await request(app)
        .get(`/api/conversation/relationships/player_003`)
        .expect(200);

      expect(relationshipResponse.body.success).toBe(true);
      expect(relationshipResponse.body.data.relationships).toBeDefined();

      // Should show improved relationship with Captain Valerius
      const valeriusRelationship = relationshipResponse.body.data.relationships['npc_003'];
      expect(valeriusRelationship).toBeDefined();
      expect(valeriusRelationship.trust).toBeGreaterThan(0.5);
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid conversation IDs', async () => {
      const response = await request(app)
        .post('/api/conversation/process-message')
        .send({
          conversationId: 'invalid_conversation_id',
          message: 'Hello',
          speakerId: 'player_001'
        })
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('not found');
    });

    test('should handle missing required fields', async () => {
      const response = await request(app)
        .post('/api/conversation/process-message')
        .send({
          conversationId,
          // Missing message and speakerId
        })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('Missing required fields');
    });

    test('should handle malformed participant data', async () => {
      const response = await request(app)
        .post('/api/conversation/initiate')
        .send({
          participants: [
            { id: '', name: '', role: 'invalid_role' } // Invalid data
          ]
        })
        .expect(400);

      expect(response.body.success).toBe(false);
    });

    test('should handle conversation state conflicts', async () => {
      // Try to send message to concluded conversation
      const response = await request(app)
        .post('/api/conversation/process-message')
        .send({
          conversationId, // This conversation was concluded earlier
          message: 'This should fail',
          speakerId: 'player_001'
        })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('concluded');
    });
  });

  describe('Performance Tests', () => {
    test('should handle concurrent conversation processing', async () => {
      const participants = [
        { id: 'player_perf_1', name: 'Test Player', role: 'player' },
        { id: 'npc_perf_1', name: 'Test NPC', role: 'npc' }
      ];

      // Create conversation
      const initiateResponse = await request(app)
        .post('/api/conversation/initiate')
        .send({ participants })
        .expect(200);

      const perfConversationId = initiateResponse.body.data.conversation.id;

      // Send multiple concurrent messages
      const messagePromises = [];
      const startTime = Date.now();

      for (let i = 0; i < 10; i++) {
        messagePromises.push(
          request(app)
            .post('/api/conversation/process-message')
            .send({
              conversationId: perfConversationId,
              message: `Test message ${i}`,
              speakerId: 'player_perf_1'
            })
        );
      }

      const results = await Promise.all(messagePromises);
      const endTime = Date.now();

      // All requests should succeed
      results.forEach(response => {
        expect(response.status).toBe(200);
        expect(response.body.success).toBe(true);
      });

      // Performance should be reasonable (less than 5 seconds for 10 concurrent requests)
      const totalTime = endTime - startTime;
      expect(totalTime).toBeLessThan(5000);
    });

    test('should handle memory usage efficiently', async () => {
      const initialMemory = process.memoryUsage();

      // Create and process multiple conversations
      for (let i = 0; i < 5; i++) {
        const participants = [
          { id: `player_mem_${i}`, name: `Player ${i}`, role: 'player' },
          { id: `npc_mem_${i}`, name: `NPC ${i}`, role: 'npc' }
        ];

        const initiateResponse = await request(app)
          .post('/api/conversation/initiate')
          .send({ participants })
          .expect(200);

        const memConversationId = initiateResponse.body.data.conversation.id;

        // Send several messages
        for (let j = 0; j < 5; j++) {
          await request(app)
            .post('/api/conversation/process-message')
            .send({
              conversationId: memConversationId,
              message: `Memory test message ${j}`,
              speakerId: `player_mem_${i}`
            })
            .expect(200);
        }

        // Conclude conversation
        await request(app)
          .post('/api/conversation/conclude')
          .send({
            conversationId: memConversationId,
            reason: 'test_completion'
          })
          .expect(200);
      }

      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;

      // Memory increase should be reasonable (less than 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });
  });
});

describe('Conversation Analytics Integration', () => {
  test('should track conversation analytics', async () => {
    const response = await request(app)
      .get('/api/analytics/conversation-metrics')
      .query({
        startDate: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        endDate: new Date().toISOString()
      })
      .expect(200);

    expect(response.body.success).toBe(true);
    expect(response.body.data).toBeDefined();
    expect(response.body.data.summary).toBeDefined();
    expect(response.body.data.performance).toBeDefined();
  });

  test('should generate conversation reports', async () => {
    const response = await request(app)
      .post('/api/analytics/generate-report')
      .send({
        type: 'conversation',
        period: 'daily',
        filters: {
          campaignIds: ['campaign_001', 'campaign_002']
        }
      })
      .expect(200);

    expect(response.body.success).toBe(true);
    expect(response.body.data.report).toBeDefined();
    expect(response.body.data.report.summary).toBeDefined();
    expect(response.body.data.report.recommendations).toBeDefined();
  });
});