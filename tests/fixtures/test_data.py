"""
Test data fixtures and factories for DMLogn8n testing.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import faker

# Initialize faker for generating realistic test data
fake = faker.Faker()

class AgentDataFactory:
    """Factory for creating agent test data."""

    @staticmethod
    def create_basic_agent(agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create basic agent data."""
        return {
            'agent_id': agent_id or str(uuid.uuid4()),
            'name': fake.name(),
            'type': random.choice(['npc', 'player', 'monster']),
            'class': random.choice(['warrior', 'mage', 'rogue', 'cleric', 'ranger']),
            'level': random.randint(1, 20),
            'attributes': {
                'strength': random.randint(8, 18),
                'dexterity': random.randint(8, 18),
                'constitution': random.randint(8, 18),
                'intelligence': random.randint(8, 18),
                'wisdom': random.randint(8, 18),
                'charisma': random.randint(8, 18)
            },
            'skills': random.sample([
                'athletics', 'acrobatics', 'sleight_of_hand', 'stealth',
                'arcana', 'history', 'investigation', 'nature', 'religion',
                'animal_handling', 'insight', 'medicine', 'perception', 'survival',
                'deception', 'intimidation', 'performance', 'persuasion'
            ], k=random.randint(3, 8)),
            'equipment': [
                random.choice(['longsword', 'dagger', 'bow', 'staff', 'wand']),
                random.choice(['leather_armor', 'chain_mail', 'robe', 'shield'])
            ],
            'health': random.randint(20, 100),
            'max_health': random.randint(20, 100),
            'mana': random.randint(10, 50),
            'max_mana': random.randint(10, 50),
            'experience': random.randint(0, 10000),
            'status': random.choice(['active', 'idle', 'in_combat', 'resting']),
            'location': {
                'zone': fake.word(),
                'x': random.randint(0, 100),
                'y': random.randint(0, 100),
                'z': 0
            },
            'personality': {
                'traits': random.sample(['brave', 'cautious', 'curious', 'aggressive', 'friendly'], k=2),
                'ideals': [fake.word() for _ in range(2)],
                'bonds': [fake.word() for _ in range(2)],
                'flaws': [fake.word() for _ in range(1)]
            },
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

    @staticmethod
    def create_npc_agent(agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create NPC-specific agent data."""
        agent = AgentDataFactory.create_basic_agent(agent_id)
        agent.update({
            'type': 'npc',
            'behavior_patterns': [
                random.choice(['aggressive', 'defensive', 'neutral', 'friendly']),
                random.choice(['patrol', 'guard', 'wander', 'stationary'])
            ],
            'dialogue_options': [
                fake.sentence() for _ in range(random.randint(3, 8))
            ],
            'quests_available': random.randint(0, 3),
            'shop_inventory': random.choice([None, [
                {'item': fake.word(), 'price': random.randint(10, 100)}
                for _ in range(random.randint(5, 15))
            ]])
        })
        return agent

    @staticmethod
    def create_player_agent(agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create player-specific agent data."""
        agent = AgentDataFactory.create_basic_agent(agent_id)
        agent.update({
            'type': 'player',
            'user_id': str(uuid.uuid4()),
            'character_name': fake.name(),
            'background': random.choice(['soldier', 'scholar', 'merchant', 'noble', 'commoner']),
            'alignment': random.choice(['lawful_good', 'neutral_good', 'chaotic_good',
                                      'lawful_neutral', 'true_neutral', 'chaotic_neutral',
                                      'lawful_evil', 'neutral_evil', 'chaotic_evil']),
            'deity': fake.word() if random.random() > 0.3 else None,
            'inventory': [
                {'name': fake.word(), 'quantity': random.randint(1, 5), 'type': 'item'}
                for _ in range(random.randint(5, 20))
            ],
            'gold': random.randint(0, 1000),
            'level_progress': {
                'current_level': random.randint(1, 20),
                'experience': random.randint(0, 350000),
                'experience_to_next': random.randint(0, 30000)
            }
        })
        return agent

    @staticmethod
    def create_monster_agent(agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create monster-specific agent data."""
        agent = AgentDataFactory.create_basic_agent(agent_id)
        agent.update({
            'type': 'monster',
            'species': random.choice(['goblin', 'orc', 'dragon', 'undead', 'elemental', 'beast']),
            'challenge_rating': random.uniform(0.125, 25.0),
            'abilities': [
                {
                    'name': fake.word(),
                    'type': random.choice(['attack', 'spell', 'special']),
                    'damage': random.randint(5, 50),
                    'description': fake.sentence()
                }
                for _ in range(random.randint(2, 6))
            ],
            'loot_table': [
                {'item': fake.word(), 'chance': random.uniform(0.1, 1.0)}
                for _ in range(random.randint(3, 10))
            ],
            'behavior': {
                'aggression_level': random.randint(1, 10),
                'territorial': random.choice([True, False]),
                'pack_mentality': random.choice([True, False])
            }
        })
        return agent

class SessionDataFactory:
    """Factory for creating game session test data."""

    @staticmethod
    def create_basic_session(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create basic session data."""
        return {
            'session_id': session_id or str(uuid.uuid4()),
            'name': fake.catch_phrase(),
            'description': fake.paragraph(nb_sentences=3),
            'dungeon_master_id': str(uuid.uuid4()),
            'players': [str(uuid.uuid4()) for _ in range(random.randint(2, 6))],
            'npcs': [str(uuid.uuid4()) for _ in range(random.randint(5, 20))],
            'status': random.choice(['waiting', 'active', 'paused', 'completed']),
            'created_at': datetime.utcnow().isoformat(),
            'started_at': (datetime.utcnow() + timedelta(minutes=random.randint(-60, 0))).isoformat(),
            'settings': {
                'difficulty': random.choice(['easy', 'medium', 'hard', 'deadly']),
                'max_players': random.randint(4, 8),
                'allow_pvp': random.choice([True, False]),
                'respawn_enabled': random.choice([True, False]),
                'save_frequency': random.randint(5, 30) * 60,  # seconds
                'level_range': {
                    'min': random.randint(1, 10),
                    'max': random.randint(11, 20)
                }
            },
            'current_scene': {
                'scene_id': str(uuid.uuid4()),
                'name': fake.word(),
                'description': fake.paragraph(),
                'environment': random.choice(['dungeon', 'forest', 'city', 'mountain', 'desert']),
                'lighting': random.choice(['bright', 'dim', 'dark']),
                'weather': random.choice(['clear', 'rain', 'storm', 'fog', 'snow'])
            },
            'ruleset': 'dnd5e',
            'house_rules': [
                fake.sentence() for _ in range(random.randint(0, 5))
            ]
        }

    @staticmethod
    def create_campaign_session(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create campaign-style session data."""
        session = SessionDataFactory.create_basic_session(session_id)
        session.update({
            'type': 'campaign',
            'campaign_id': str(uuid.uuid4()),
            'session_number': random.randint(1, 50),
            'estimated_duration_hours': random.randint(2, 8),
            'previous_sessions': [str(uuid.uuid4()) for _ in range(random.randint(0, 20))],
            'story_arcs': [
                {
                    'arc_id': str(uuid.uuid4()),
                    'name': fake.catch_phrase(),
                    'progress': random.uniform(0.0, 1.0),
                    'objectives': [fake.sentence() for _ in range(random.randint(3, 8))]
                }
                for _ in range(random.randint(1, 4))
            ]
        })
        return session

    @staticmethod
    def create_one_shot_session(session_id: Optional[str] = None) -> Dict[str, Any]:
        """Create one-shot session data."""
        session = SessionDataFactory.create_basic_session(session_id)
        session.update({
            'type': 'one_shot',
            'estimated_duration_hours': random.randint(1, 4),
            'adventure_type': random.choice(['dungeon_crawl', 'mystery', 'investigation', 'social']),
            'main_objective': fake.sentence(),
            'time_limit_hours': random.choice([None, random.randint(2, 6)])
        })
        return session

class EventDataFactory:
    """Factory for creating game event test data."""

    @staticmethod
    def create_combat_event(session_id: str, agent_id: str) -> Dict[str, Any]:
        """Create combat event data."""
        return {
            'event_id': str(uuid.uuid4()),
            'session_id': session_id,
            'agent_id': agent_id,
            'event_type': 'combat_action',
            'event_data': {
                'action_type': random.choice(['attack', 'cast_spell', 'use_item', 'defend']),
                'target_id': str(uuid.uuid4()),
                'damage': random.randint(0, 50),
                'weapon': random.choice(['longsword', 'fireball', 'healing_potion']),
                'success': random.choice([True, False]),
                'critical_hit': random.random() > 0.95,
                'description': fake.sentence()
            },
            'timestamp': datetime.utcnow().isoformat(),
            'location': {
                'zone': fake.word(),
                'coordinates': {'x': random.randint(0, 100), 'y': random.randint(0, 100)}
            }
        }

    @staticmethod
    def create_dialogue_event(session_id: str, agent_id: str) -> Dict[str, Any]:
        """Create dialogue event data."""
        return {
            'event_id': str(uuid.uuid4()),
            'session_id': session_id,
            'agent_id': agent_id,
            'event_type': 'dialogue',
            'event_data': {
                'speaker': agent_id,
                'text': fake.sentence(),
                'language': 'common',
                'tone': random.choice(['friendly', 'hostile', 'neutral', 'mysterious', 'urgent']),
                'listeners': [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
                'emotion': random.choice(['happy', 'sad', 'angry', 'scared', 'surprised']),
                'checks': {
                    'persuasion': random.randint(1, 20) if random.random() > 0.5 else None,
                    'intimidation': random.randint(1, 20) if random.random() > 0.5 else None,
                    'deception': random.randint(1, 20) if random.random() > 0.5 else None
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def create_movement_event(session_id: str, agent_id: str) -> Dict[str, Any]:
        """Create movement event data."""
        return {
            'event_id': str(uuid.uuid4()),
            'session_id': session_id,
            'agent_id': agent_id,
            'event_type': 'movement',
            'event_data': {
                'from_location': {
                    'zone': fake.word(),
                    'x': random.randint(0, 100),
                    'y': random.randint(0, 100)
                },
                'to_location': {
                    'zone': fake.word(),
                    'x': random.randint(0, 100),
                    'y': random.randint(0, 100)
                },
                'speed': random.choice(['walk', 'run', 'sneak']),
                'distance': random.randint(5, 60),
                'terrain': random.choice(['difficult', 'normal', 'easy']),
                'obstacles': random.choice([None, fake.word()])
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def create_skill_check_event(session_id: str, agent_id: str) -> Dict[str, Any]:
        """Create skill check event data."""
        return {
            'event_id': str(uuid.uuid4()),
            'session_id': session_id,
            'agent_id': agent_id,
            'event_type': 'skill_check',
            'event_data': {
                'skill': random.choice(['perception', 'investigation', 'athletics', 'stealth', 'persuasion']),
                'difficulty_class': random.randint(5, 25),
                'roll': random.randint(1, 20),
                'modifier': random.randint(-5, 10),
                'total_score': random.randint(1, 30),
                'success': random.choice([True, False]),
                'critical_success': random.random() > 0.95,
                'critical_failure': random.random() > 0.95,
                'description': fake.sentence()
            },
            'timestamp': datetime.utcnow().isoformat()
        }

class WorldDataFactory:
    """Factory for creating world/location test data."""

    @staticmethod
    def create_location(location_id: Optional[str] = None) -> Dict[str, Any]:
        """Create location data."""
        return {
            'location_id': location_id or str(uuid.uuid4()),
            'name': fake.city(),
            'description': fake.paragraph(),
            'type': random.choice(['city', 'town', 'village', 'dungeon', 'forest', 'mountain', 'ruins']),
            'size': random.choice(['tiny', 'small', 'medium', 'large', 'huge']),
            'population': random.randint(0, 100000),
            'government': random.choice(['monarchy', 'democracy', 'republic', 'anarchy', 'theocracy']),
            'economy': {
                'primary_industry': random.choice(['agriculture', 'mining', 'trade', 'manufacturing', 'magic']),
                'wealth_level': random.choice(['poor', 'modest', 'comfortable', 'wealthy', 'aristocratic']),
                'trade_goods': [fake.word() for _ in range(random.randint(3, 8))]
            },
            'locations': [
                {
                    'name': fake.company(),
                    'type': random.choice(['tavern', 'shop', 'temple', 'guild', 'house']),
                    'description': fake.sentence()
                }
                for _ in range(random.randint(3, 10))
            ],
            'npcs': [str(uuid.uuid4()) for _ in range(random.randint(5, 20))],
            'quests': [str(uuid.uuid4()) for _ in range(random.randint(1, 5))],
            'dangers': [
                {
                    'type': random.choice(['monster', 'trap', 'hazard', 'political']),
                    'severity': random.randint(1, 10),
                    'description': fake.sentence()
                }
                for _ in range(random.randint(0, 5))
            ]
        }

    @staticmethod
    def create_quest(quest_id: Optional[str] = None) -> Dict[str, Any]:
        """Create quest data."""
        return {
            'quest_id': quest_id or str(uuid.uuid4()),
            'name': fake.catch_phrase(),
            'description': fake.paragraph(nb_sentences=5),
            'type': random.choice(['main_story', 'side_quest', 'fetch_quest', 'kill_quest', 'escort_quest']),
            'difficulty': random.choice(['trivial', 'easy', 'medium', 'hard', 'deadly']),
            'level_requirement': random.randint(1, 20),
            'objectives': [
                {
                    'objective_id': str(uuid.uuid4()),
                    'description': fake.sentence(),
                    'completed': random.choice([True, False]),
                    'optional': random.random() > 0.8
                }
                for _ in range(random.randint(2, 8))
            ],
            'rewards': {
                'experience': random.randint(50, 5000),
                'gold': random.randint(10, 1000),
                'items': [
                    {'name': fake.word(), 'quantity': random.randint(1, 5)}
                    for _ in range(random.randint(0, 3))
                ]
            },
            'giver': str(uuid.uuid4()),
            'location': str(uuid.uuid4()),
            'time_limit_hours': random.choice([None, random.randint(1, 72)]),
            'repeatable': random.choice([True, False]),
            'prerequisites': [str(uuid.uuid4()) for _ in range(random.randint(0, 3))],
            'status': random.choice(['available', 'in_progress', 'completed', 'failed'])
        }

class SystemDataFactory:
    """Factory for creating system-level test data."""

    @staticmethod
    def create_api_request() -> Dict[str, Any]:
        """Create API request data."""
        return {
            'request_id': str(uuid.uuid4()),
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'endpoint': random.choice([
                '/api/agents',
                '/api/sessions',
                '/api/events',
                '/api/quests',
                '/api/locations'
            ]),
            'headers': {
                'authorization': f'Bearer {fake.sha256()}',
                'content-type': 'application/json',
                'user-agent': fake.user_agent()
            },
            'body': {
                'data': fake.pydict(3, True, 'str')
            },
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': fake.ipv4()
        }

    @staticmethod
    def create_websocket_message() -> Dict[str, Any]:
        """Create WebSocket message data."""
        return {
            'message_id': str(uuid.uuid4()),
            'event': random.choice([
                'player_action',
                'game_update',
                'agent_update',
                'session_event',
                'system_notification'
            ]),
            'data': fake.pydict(3, True, 'str'),
            'room': random.choice([None, f'session_{uuid.uuid4()}']),
            'user_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def create_error_log() -> Dict[str, Any]:
        """Create error log data."""
        return {
            'error_id': str(uuid.uuid4()),
            'error_type': random.choice([
                'ValidationError',
                'DatabaseError',
                'NetworkError',
                'AuthenticationError',
                'AuthorizationError',
                'NotFoundError',
                'InternalServerError'
            ]),
            'message': fake.sentence(),
            'stack_trace': fake.paragraph(nb_sentences=5),
            'user_id': random.choice([None, str(uuid.uuid4())]),
            'session_id': random.choice([None, str(uuid.uuid4())]),
            'request_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'severity': random.choice(['low', 'medium', 'high', 'critical']),
            'resolved': random.choice([True, False]),
            'resolution_notes': fake.sentence() if random.random() > 0.5 else None
        }

class PerformanceDataFactory:
    """Factory for creating performance test data."""

    @staticmethod
    def create_load_test_scenario() -> Dict[str, Any]:
        """Create load test scenario data."""
        return {
            'scenario_id': str(uuid.uuid4()),
            'name': fake.catch_phrase(),
            'description': fake.paragraph(),
            'concurrent_users': random.randint(10, 1000),
            'duration_seconds': random.randint(60, 3600),
            'ramp_up_time': random.randint(10, 300),
            'think_time': random.uniform(0.5, 5.0),
            'requests_per_second': random.randint(1, 100),
            'endpoints': [
                {
                    'path': random.choice(['/api/agents', '/api/sessions', '/api/events']),
                    'method': random.choice(['GET', 'POST']),
                    'weight': random.uniform(0.1, 1.0),
                    'expected_response_time': random.uniform(0.1, 2.0)
                }
                for _ in range(random.randint(2, 6))
            ],
            'success_criteria': {
                'max_error_rate': random.uniform(0.01, 0.05),
                'max_response_time_p95': random.uniform(0.5, 3.0),
                'min_throughput': random.randint(10, 500)
            },
            'created_at': datetime.utcnow().isoformat()
        }

# Predefined test data sets
class TestDataSets:
    """Predefined test data sets for common scenarios."""

    @staticmethod
    def get_typical_party() -> List[Dict[str, Any]]:
        """Get a typical D&D party of 4-6 adventurers."""
        party = [
            AgentDataFactory.create_player_agent(),
            AgentDataFactory.create_player_agent(),
            AgentDataFactory.create_player_agent(),
            AgentDataFactory.create_player_agent()
        ]

        # Ensure varied classes
        classes = ['fighter', 'wizard', 'cleric', 'rogue', 'ranger', 'paladin']
        for i, agent in enumerate(party):
            agent['class'] = classes[i % len(classes)]
            agent['level'] = random.randint(3, 8)  # Typical starting level

        return party

    @staticmethod
    def get_dungeon_encounter() -> Dict[str, Any]:
        """Get a typical dungeon encounter setup."""
        return {
            'location': WorldDataFactory.create_location(),
            'monsters': [
                AgentDataFactory.create_monster_agent() for _ in range(random.randint(2, 8))
            ],
            'treasure': [
                {
                    'item': fake.word(),
                    'value': random.randint(10, 500),
                    'type': random.choice(['weapon', 'armor', 'magic_item', 'gold'])
                }
                for _ in range(random.randint(3, 12))
            ],
            'traps': [
                {
                    'type': random.choice(['pit', 'poison_dart', 'pressure_plate', 'magical_ward']),
                    'difficulty_class': random.randint(10, 20),
                    'damage': random.randint(5, 30),
                    'description': fake.sentence()
                }
                for _ in range(random.randint(0, 5))
            ],
            'clues': [
                fake.sentence() for _ in range(random.randint(1, 4))
            ]
        }

    @staticmethod
    def get_social_encounter() -> Dict[str, Any]:
        """Get a typical social encounter setup."""
        return {
            'location': WorldDataFactory.create_location(),
            'npcs': [
                AgentDataFactory.create_npc_agent() for _ in range(random.randint(2, 6))
            ],
            'faction': {
                'name': fake.company(),
                'attitude': random.choice(['friendly', 'neutral', 'hostile', 'suspicious']),
                'goals': [fake.sentence() for _ in range(random.randint(2, 5))],
                'secrets': [fake.sentence() for _ in range(random.randint(1, 3))]
            },
            'dialogue_options': [
                {
                    'option': fake.sentence(),
                    'skill_check': random.choice([None, 'persuasion', 'intimidation', 'deception']),
                    'difficulty_class': random.randint(10, 20),
                    'outcomes': [fake.sentence() for _ in range(3)]
                }
                for _ in range(random.randint(4, 10))
            ]
        }

    @staticmethod
    def get_campaign_story_arc() -> Dict[str, Any]:
        """Get a campaign story arc structure."""
        return {
            'arc_id': str(uuid.uuid4()),
            'title': fake.catch_phrase(),
            'description': fake.paragraph(nb_sentences=10),
            'main_villain': AgentDataFactory.create_npc_agent(),
            'plot_hooks': [
                {
                    'hook_id': str(uuid.uuid4()),
                    'description': fake.sentence(),
                    'trigger': fake.word(),
                    'location': str(uuid.uuid4())
                }
                for _ in range(random.randint(3, 8))
            ],
            'key_events': [
                {
                    'event_id': str(uuid.uuid4()),
                    'title': fake.catch_phrase(),
                    'description': fake.paragraph(),
                    'location': str(uuid.uuid4()),
                    'required_level': random.randint(1, 20),
                    'consequences': [fake.sentence() for _ in range(random.randint(2, 5))]
                }
                for _ in range(random.randint(5, 15))
            ],
            'climax': {
                'location': WorldDataFactory.create_location(),
                'final_boss': AgentDataFactory.create_monster_agent(),
                'objectives': [fake.sentence() for _ in range(random.randint(3, 6))],
                'outcomes': {
                    'victory': fake.paragraph(),
                    'defeat': fake.paragraph(),
                    'partial_success': fake.paragraph()
                }
            }
        }