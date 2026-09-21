#!/usr/bin/env python3
"""
Sample Data Generator for DMLogn8n Demo
Creates realistic and impressive sample data for demonstrations
"""

import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger('DMLogn8n-SampleData')

@dataclass
class CharacterProfile:
    """Character profile for realistic data generation"""
    name: str
    class_type: str
    level: int
    faction: str
    personality_traits: List[str]
    background_story: str
    combat_style: str
    social_preferences: List[str]

class SampleDataGenerator:
    """Generate realistic sample data for DMLogn8n demonstrations"""

    def __init__(self):
        self.character_names = self._load_character_names()
        self.locations = self._load_location_templates()
        self.items = self._load_item_templates()
        self.factions = self._load_faction_data()
        self.dialogue_templates = self._load_dialogue_templates()
        self.generated_data = {}

    def _load_character_names(self) -> List[str]:
        """Load character name templates"""
        return [
            "Eldrin Shadowbane", "Lyra Moonwhisper", "Thorin Ironforge", "Aria Starweaver",
            "Kael Nightblade", "Mira Sunfire", "Gareth Stormrider", "Selena Winterwind",
            "Ragnar Blackheart", "Iris Lightbringer", "Zoltan Voidwalker", "Freya Stormcaller",
            "Marcus Ironhand", "Luna Silverleaf", "Darius Darkmere", "Celeste Dawnbreaker",
            "Victor Goldshield", "Nora Mistweaver", "Xander Nightfall", "Rose Summerwind"
        ]

    def _load_location_templates(self) -> List[Dict[str, Any]]:
        """Load location templates for world generation"""
        return [
            {
                "type": "city",
                "names": ["Stormwind", "Ironforge", "Darnassus", "Orgrimmar", "Undercity"],
                "features": ["market", "tavern", "forge", "temple", "guild_hall"],
                "population_range": (5000, 50000)
            },
            {
                "type": "dungeon",
                "names": ["Shadowfang Keep", "Deadmines", "Wailing Caverns", "Razorfen Kraul", "Uldaman"],
                "features": ["traps", "bosses", "treasure", "secrets", "puzzles"],
                "difficulty_range": (1, 10)
            },
            {
                "type": "wilderness",
                "names": ["Elwynn Forest", "Durotar", "Teldrassil", "Mulgore", "Tirisfal Glades"],
                "features": ["creatures", "resources", "landmarks", "weather", "ecology"],
                "size_range": (100, 1000)
            }
        ]

    def _load_item_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load item templates for equipment generation"""
        return {
            "weapons": [
                {"name": "Shadowstrike Dagger", "damage": (50, 80), "type": "dagger", "rarity": "rare"},
                {"name": "Flaming Sword", "damage": (80, 120), "type": "sword", "rarity": "epic"},
                {"name": "Frostbite Staff", "damage": (60, 90), "type": "staff", "rarity": "rare"},
                {"name": "Thunder Hammer", "damage": (100, 150), "type": "hammer", "rarity": "legendary"}
            ],
            "armor": [
                {"name": "Iron Plate Mail", "defense": 50, "type": "heavy", "rarity": "common"},
                {"name": "Shadow Leather Vest", "defense": 35, "type": "medium", "rarity": "rare"},
                {"name": "Mystic Robe", "defense": 25, "type": "light", "rarity": "epic"},
                {"name": "Dragon Scale Armor", "defense": 80, "type": "heavy", "rarity": "legendary"}
            ],
            "consumables": [
                {"name": "Health Potion", "effect": "heal", "power": 200, "duration": 0},
                {"name": "Mana Potion", "effect": "mana", "power": 150, "duration": 0},
                {"name": "Strength Elixir", "effect": "buff", "power": 25, "duration": 300},
                {"name": "Invisibility Potion", "effect": "stealth", "power": 100, "duration": 60}
            ]
        }

    def _load_faction_data(self) -> List[Dict[str, Any]]:
        """Load faction data for social systems"""
        return [
            {
                "name": "Alliance of Light",
                "alignment": "good",
                "values": ["honor", "justice", "cooperation"],
                "rivals": ["Shadow Legion"],
                "members": 15000,
                "influence": 85
            },
            {
                "name": "Shadow Legion",
                "alignment": "evil",
                "values": ["power", "dominance", "secrecy"],
                "rivals": ["Alliance of Light"],
                "members": 12000,
                "influence": 75
            },
            {
                "name": "Merchants Guild",
                "alignment": "neutral",
                "values": ["profit", "trade", "information"],
                "rivals": [],
                "members": 8000,
                "influence": 60
            },
            {
                "name": "Ancient Order",
                "alignment": "mysterious",
                "values": ["knowledge", "balance", "mystery"],
                "rivals": ["Shadow Legion"],
                "members": 3000,
                "influence": 70
            }
        ]

    def _load_dialogue_templates(self) -> Dict[str, List[str]]:
        """Load dialogue templates for AI conversations"""
        return {
            "greeting": [
                "Greetings, traveler. What brings you to these lands?",
                "Welcome! May your journey be safe and prosperous.",
                "Ah, a new face! I am {name}, pleased to meet you.",
                "The winds whisper of your arrival. How may I assist?"
            ],
            "quest": [
                "I have a task that requires courage and skill. Are you interested?",
                "Dark times have fallen upon us. We need heroes like you.",
                "There's a matter of great importance that needs your attention.",
                "Fortune favors the bold, and I have an opportunity for the bold."
            ],
            "combat": [
                "For the honor of {faction}!",
                "Your end comes now!",
                "Face the might of {name}!",
                "This battle will be legendary!"
            ],
            "social": [
                "The tavern atmosphere is lovely tonight, isn't it?",
                "Have you heard the news from the capital?",
                "Trading has been quite profitable this season.",
                "The festival next week should be amazing!"
            ],
            "emotional": [
                "I lost everything in that battle... but I won't give up.",
                "Thank you for your kindness. It means more than you know.",
                "Sometimes I wonder if all this fighting is worth it.",
                "Seeing young heroes like you gives me hope for the future."
            ]
        }

    async def generate_all_sample_data(self) -> Dict[str, Any]:
        """Generate all sample data for the demo"""
        logger.info("🎲 Generating comprehensive sample data...")

        self.generated_data = {
            'characters': await self.generate_characters(50),
            'worlds': await self.generate_worlds(5),
            'items': await self.generate_item_database(100),
            'guilds': await self.generate_guilds(10),
            'quests': await self.generate_quests(30),
            'dialogue_tree': await self.generate_dialogue_trees(20),
            'market_data': await self.generate_market_data(),
            'leaderboard': await self.generate_leaderboard_data()
        }

        logger.info("✅ Sample data generation complete")
        return self.generated_data

    async def generate_characters(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic character profiles"""
        characters = []
        classes = ["Warrior", "Mage", "Rogue", "Priest", "Hunter", "Paladin", "Warlock", "Druid"]

        for i in range(count):
            character = {
                'id': f"char_{i+1:04d}",
                'name': random.choice(self.character_names) if i < len(self.character_names) else f"Character_{i+1}",
                'class': random.choice(classes),
                'level': random.randint(1, 80),
                'faction': random.choice([f['name'] for f in self.factions]),
                'experience': random.randint(0, 1000000),
                'health': random.randint(1000, 50000),
                'mana': random.randint(500, 20000),
                'stats': {
                    'strength': random.randint(10, 100),
                    'agility': random.randint(10, 100),
                    'intelligence': random.randint(10, 100),
                    'wisdom': random.randint(10, 100),
                    'charisma': random.randint(10, 100)
                },
                'skills': random.sample([
                    "Sword Mastery", "Fire Magic", "Stealth", "Healing Light",
                    "Archery", "Holy Strike", "Shadow Bolt", "Nature's Grace"
                ], random.randint(3, 6)),
                'equipment': await self.generate_character_equipment(),
                'reputation': {
                    faction['name']: random.randint(-1000, 1000) for faction in random.sample(self.factions, 2)
                },
                'online_status': random.choice(['online', 'offline', 'away', 'busy']),
                'last_active': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
                'achievements': random.sample([
                    "Dragon Slayer", "Guild Master", "Explorer", "PvP Champion",
                    "Rich Merchant", "Master Crafter", "Hero of the People", "Shadow Walker"
                ], random.randint(2, 8)),
                'personality': {
                    'traits': random.sample([
                        "brave", "cautious", "aggressive", "defensive", "strategic",
                        "impulsive", "honorable", "cunning", "generous", "selfish"
                    ], random.randint(2, 4)),
                    'motivation': random.choice([
                        "Power and Glory", "Knowledge and Wisdom", "Wealth and Riches",
                        "Justice and Honor", "Freedom and Independence", "Revenge"
                    ])
                }
            }
            characters.append(character)

        return characters

    async def generate_character_equipment(self) -> Dict[str, Any]:
        """Generate equipment for a character"""
        weapon = random.choice(self.items['weapons'])
        armor = random.choice(self.items['armor'])

        return {
            'weapon': {
                'name': weapon['name'],
                'damage': random.randint(*weapon['damage']),
                'type': weapon['type'],
                'rarity': weapon['rarity'],
                'enchantments': random.sample([
                    "Fire Damage", "Ice Damage", "Lightning Damage", "Poison Damage",
                    "Life Steal", "Critical Strike", "Armor Penetration"
                ], random.randint(0, 2))
            },
            'armor': {
                'name': armor['name'],
                'defense': armor['defense'] + random.randint(-10, 20),
                'type': armor['type'],
                'rarity': armor['rarity'],
                'durability': random.randint(50, 100)
            },
            'accessories': random.sample([
                {"name": "Ring of Power", "type": "ring", "bonus": "+10 Intelligence"},
                {"name": "Amulet of Protection", "type": "amulet", "bonus": "+15 Defense"},
                {"name": "Boots of Speed", "type": "boots", "bonus": "+20% Movement Speed"},
                {"name": "Cloak of Shadows", "type": "cloak", "bonus": "+10 Stealth"}
            ], random.randint(1, 3))
        }

    async def generate_worlds(self, count: int) -> List[Dict[str, Any]]:
        """Generate detailed world data"""
        worlds = []

        for i in range(count):
            world = {
                'id': f"world_{i+1:04d}",
                'name': f"Realm of the {random.choice(['Ancients', 'Dragons', 'Mystics', 'Warriors', 'Sages'])}",
                'type': random.choice(['fantasy', 'sci_fi', 'post_apocalyptic', 'steampunk']),
                'size': random.choice(['small', 'medium', 'large', 'massive']),
                'locations': await self.generate_locations(random.randint(10, 50)),
                'population': random.randint(10000, 1000000),
                'governing_body': random.choice([
                    "Monarchy", "Republic", "Council of Elders", "Merchant Guild",
                    "Military Junta", "Magical Order", "Democratic Alliance"
                ]),
                'economy': {
                    'currency': random.choice(['Gold Coins', 'Credits', 'Essence', 'Shards']),
                    'main_industries': random.sample([
                        'Mining', 'Agriculture', 'Magic', 'Technology', 'Trade',
                        'Crafting', 'Military', 'Research', 'Tourism'
                    ], random.randint(2, 4)),
                    'trade_partners': random.randint(2, 8)
                },
                'climate': random.choice([
                    'Temperate', 'Tropical', 'Arctic', 'Desert', 'Volcanic',
                    'Mystical', 'Floating Islands', 'Underwater'
                ]),
                'threat_level': random.randint(1, 10),
                'resources': {
                    'magical_essence': random.randint(100, 10000),
                    'precious_metals': random.randint(500, 50000),
                    'ancient_artifacts': random.randint(10, 100),
                    'rare_herbs': random.randint(50, 5000)
                }
            }
            worlds.append(world)

        return worlds

    async def generate_locations(self, count: int) -> List[Dict[str, Any]]:
        """Generate locations within a world"""
        locations = []

        for i in range(count):
            location_template = random.choice(self.locations)
            location = {
                'id': f"loc_{i+1:04d}",
                'name': random.choice(location_template['names']) + f" {i+1}",
                'type': location_template['type'],
                'coordinates': {
                    'x': random.randint(-1000, 1000),
                    'y': random.randint(-1000, 1000),
                    'z': random.randint(-100, 100)
                },
                'features': random.sample(location_template['features'], random.randint(2, len(location_template['features']))),
                'population': random.randint(*location_template.get('population_range', (100, 1000))),
                'description': f"A {location_template['type']} with {random.choice(['peaceful', 'dangerous', 'mysterious', 'bustling', 'ancient'])} atmosphere.",
                'npcs': await self.generate_location_npcs(random.randint(5, 20)),
                'quests_available': random.randint(0, 5),
                'danger_level': random.randint(1, 10)
            }
            locations.append(location)

        return locations

    async def generate_location_npcs(self, count: int) -> List[Dict[str, Any]]:
        """Generate NPCs for a location"""
        npcs = []
        npc_roles = ["merchant", "guard", "innkeeper", "blacksmith", "alchemist", "trainer", "quest_giver"]

        for i in range(count):
            npc = {
                'id': f"npc_{i+1:04d}",
                'name': random.choice(self.character_names) + f" the {random.choice(['Smith', 'Merchant', 'Guard', 'Scholar', 'Healer'])}",
                'role': random.choice(npc_roles),
                'dialogue_options': random.sample([
                    "Welcome to our humble town!",
                    "I have goods to trade if you're interested.",
                    "Be careful out there, these lands can be dangerous.",
                    "The local lord has been looking for adventurers.",
                    "Have you heard the rumors about the ancient ruins?"
                ], random.randint(2, 4)),
                'services_offered': random.sample([
                    "item_trading", "repairs", "quests", "training", "information",
                    "crafting", "enchanting", "healing"
                ], random.randint(1, 3)),
                'personality': random.choice(['friendly', 'grumpy', 'mysterious', 'helpful', 'suspicious']),
                'reputation': random.randint(-100, 100)
            }
            npcs.append(npc)

        return npcs

    async def generate_item_database(self, count: int) -> List[Dict[str, Any]]:
        """Generate comprehensive item database"""
        items = []

        for i in range(count):
            category = random.choice(list(self.items.keys()))
            template = random.choice(self.items[category])

            item = {
                'id': f"item_{i+1:04d}",
                'name': template['name'],
                'category': category,
                'type': template.get('type', 'misc'),
                'rarity': template.get('rarity', random.choice(['common', 'uncommon', 'rare', 'epic', 'legendary'])),
                'value': random.randint(10, 10000),
                'level_requirement': random.randint(1, 80),
                'description': f"A {template.get('rarity', 'mysterious')} item of great power.",
                'stats': template
            }

            if category == "weapons":
                item['stats']['damage'] = random.randint(*template['damage'])
            elif category == "armor":
                item['stats']['defense'] = template['defense'] + random.randint(-5, 15)

            items.append(item)

        return items

    async def generate_guilds(self, count: int) -> List[Dict[str, Any]]:
        """Generate guild data"""
        guild_names = [
            "Dragon Slayers", "Shadow Syndicate", "Lightbringers", "Chaos Legion",
            "Ancient Guardians", "Merchant Kings", "Elite Warriors", "Mystic Circle"
        ]

        guilds = []

        for i in range(count):
            guild = {
                'id': f"guild_{i+1:04d}",
                'name': random.choice(guild_names) if i < len(guild_names) else f"Guild {i+1}",
                'tag': f"[{random.choice(['DS', 'SS', 'LB', 'CL', 'AG', 'MK', 'EW', 'MC'])}{i+1:02d}]",
                'level': random.randint(1, 25),
                'members': random.randint(10, 500),
                'founded_date': (datetime.now() - timedelta(days=random.randint(30, 1000))).isoformat(),
                'leader': random.choice(self.character_names),
                'type': random.choice(['pvp', 'pve', 'social', 'trading', 'raiding']),
                'achievements': random.randint(5, 50),
                'guild_hall': {
                    'location': random.choice(["Stormwind", "Ironforge", "Orgrimmar", "Undercity"]),
                    'level': random.randint(1, 10),
                    'amenities': random.sample([
                        'vault', 'repair_shop', 'training_dummies', 'portal',
                        'bar', 'officers_quarters', 'meeting_hall', 'trophy_room'
                    ], random.randint(3, 6))
                },
                'reputation': random.randint(-1000, 1000),
                'active': random.choice([True, False])
            }
            guilds.append(guild)

        return guilds

    async def generate_quests(self, count: int) -> List[Dict[str, Any]]:
        """Generate quest data"""
        quest_types = ['kill', 'collect', 'deliver', 'escort', 'explore', 'diplomatic', 'crafting']
        quest_difficulties = ['easy', 'medium', 'hard', 'epic', 'legendary']

        quests = []

        for i in range(count):
            quest = {
                'id': f"quest_{i+1:04d}",
                'title': f"The {random.choice(['Lost', 'Ancient', 'Cursed', 'Blessed', 'Hidden'])} {random.choice(['Sword', 'Crown', 'Amulet', 'Scroll', 'Artifact'])}",
                'description': f"A {random.choice(['dangerous', 'mysterious', 'urgent', 'important', 'legendary'])} quest that requires {random.choice(['courage', 'wisdom', 'strength', 'stealth', 'diplomacy'])}.",
                'type': random.choice(quest_types),
                'difficulty': random.choice(quest_difficulties),
                'level_requirement': random.randint(1, 80),
                'rewards': {
                    'experience': random.randint(100, 50000),
                    'gold': random.randint(50, 10000),
                    'items': random.randint(0, 3),
                    'reputation': random.randint(10, 500)
                },
                'objectives': await self.generate_quest_objectives(random.randint(1, 4)),
                'quest_giver': {
                    'name': random.choice(self.character_names),
                    'location': random.choice(["Stormwind", "Ironforge", "Orgrimmar", "Darnassus"]),
                    'faction': random.choice([f['name'] for f in self.factions])
                },
                'time_limit': random.choice([0, 3600, 7200, 14400, 86400]),  # 0 = unlimited, in seconds
                'repeatable': random.choice([True, False]),
                'prerequisites': random.sample([], random.randint(0, 2)),  # Quest IDs
                'active_players': random.randint(0, 50)
            }
            quests.append(quest)

        return quests

    async def generate_quest_objectives(self, count: int) -> List[Dict[str, Any]]:
        """Generate objectives for a quest"""
        objectives = []
        objective_types = ['kill', 'collect', 'deliver', 'talk_to', 'explore']

        for i in range(count):
            objective = {
                'id': f"obj_{i+1}",
                'type': random.choice(objective_types),
                'target': random.choice([
                    "Goblin Raiders", "Dark Wolves", "Ancient Golems", "Shadow Mages",
                    "Dragon Eggs", "Ancient Relics", "Magical Crystals", "Sacred Scrolls"
                ]),
                'current': 0,
                'required': random.randint(1, 20),
                'completed': False
            }
            objectives.append(objective)

        return objectives

    async def generate_dialogue_trees(self, count: int) -> List[Dict[str, Any]]:
        """Generate dialogue trees for NPCs"""
        dialogues = []

        for i in range(count):
            dialogue_tree = {
                'id': f"dialogue_{i+1:04d}",
                'npc_name': random.choice(self.character_names),
                'context': random.choice(['greeting', 'quest_offer', 'combat_taunt', 'merchant', 'storytelling']),
                'nodes': await self.generate_dialogue_nodes(random.randint(3, 8))
            }
            dialogues.append(dialogue_tree)

        return dialogues

    async def generate_dialogue_nodes(self, count: int) -> List[Dict[str, Any]]:
        """Generate nodes for a dialogue tree"""
        nodes = []

        for i in range(count):
            context = random.choice(list(self.dialogue_templates.keys()))
            template = random.choice(self.dialogue_templates[context])

            node = {
                'id': f"node_{i+1}",
                'text': template,
                'speaker': 'npc',
                'emotion': random.choice(['neutral', 'happy', 'sad', 'angry', 'excited', 'worried']),
                'responses': [
                    {
                        'id': f"resp_{i+1}_{j+1}",
                        'text': random.choice([
                            "Tell me more.", "I accept.", "Maybe later.", "What's in it for me?",
                            "I need to think about this.", "Where can I find this?",
                            "How dangerous is it?", "Who else is involved?"
                        ]),
                        'next_node': f"node_{random.randint(1, count)}" if random.random() > 0.3 else None
                    } for j in range(random.randint(2, 4))
                ],
                'conditions': random.sample([
                    {'type': 'level', 'value': random.randint(1, 80)},
                    {'type': 'faction', 'value': random.choice([f['name'] for f in self.factions])},
                    {'type': 'item', 'value': f"item_{random.randint(1, 100)}"},
                    {'type': 'quest', 'value': f"quest_{random.randint(1, 30)}"}
                ], random.randint(0, 2))
            }
            nodes.append(node)

        return nodes

    async def generate_market_data(self) -> Dict[str, Any]:
        """Generate dynamic market data"""
        return {
            'auctions': await self.generate_auctions(50),
            'trade_history': await self.generate_trade_history(200),
            'price_trends': await self.generate_price_trends(),
            'market_summary': {
                'total_volume': random.randint(100000, 10000000),
                'active_auctions': random.randint(100, 1000),
                'price_index': random.uniform(0.8, 1.2),
                'market_trend': random.choice(['rising', 'falling', 'stable'])
            }
        }

    async def generate_auctions(self, count: int) -> List[Dict[str, Any]]:
        """Generate auction listings"""
        auctions = []

        for i in range(count):
            auction = {
                'id': f"auction_{i+1:04d}",
                'item_id': f"item_{random.randint(1, 100)}",
                'seller': random.choice(self.character_names),
                'current_bid': random.randint(100, 10000),
                'buyout_price': random.randint(1000, 50000),
                'time_remaining': random.randint(3600, 172800),  # 1 hour to 48 hours
                'bid_count': random.randint(0, 20),
                'quality': random.choice(['common', 'uncommon', 'rare', 'epic', 'legendary'])
            }
            auctions.append(auction)

        return auctions

    async def generate_trade_history(self, count: int) -> List[Dict[str, Any]]:
        """Generate historical trade data"""
        history = []

        for i in range(count):
            trade = {
                'id': f"trade_{i+1:04d}",
                'item_name': f"Item {random.randint(1, 100)}",
                'price': random.randint(50, 20000),
                'quantity': random.randint(1, 20),
                'buyer': random.choice(self.character_names),
                'seller': random.choice(self.character_names),
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 720))).isoformat(),
                'location': random.choice(["Stormwind", "Ironforge", "Orgrimmar", "Undercity"])
            }
            history.append(trade)

        return history

    async def generate_price_trends(self) -> List[Dict[str, Any]]:
        """Generate price trend data"""
        trends = []
        items = ["Iron Ore", "Gold Bar", "Magic Crystal", "Dragon Scale", "Ancient Rune"]

        for item in items:
            trend = {
                'item_name': item,
                'prices': [random.randint(100, 1000) for _ in range(7)],  # Last 7 days
                'trend': random.choice(['up', 'down', 'stable']),
                'volatility': random.uniform(0.1, 0.5)
            }
            trends.append(trend)

        return trends

    async def generate_leaderboard_data(self) -> Dict[str, Any]:
        """Generate leaderboard data"""
        return {
            'pvp_rankings': await self.generate_pvp_rankings(50),
            'level_rankings': await self.generate_level_rankings(50),
            'wealth_rankings': await self.generate_wealth_rankings(50),
            'achievement_rankings': await self.generate_achievement_rankings(50),
            'guild_rankings': await self.generate_guild_rankings(20)
        }

    async def generate_pvp_rankings(self, count: int) -> List[Dict[str, Any]]:
        """Generate PvP rankings"""
        rankings = []

        for i in range(count):
            ranking = {
                'rank': i + 1,
                'character_name': random.choice(self.character_names),
                'rating': random.randint(1000, 3000) - (i * 20),
                'wins': random.randint(50, 500) - (i * 5),
                'losses': random.randint(10, 100),
                'win_rate': random.uniform(0.6, 0.95) - (i * 0.01),
                'class': random.choice(["Warrior", "Mage", "Rogue", "Priest", "Hunter"]),
                'faction': random.choice([f['name'] for f in self.factions])
            }
            rankings.append(ranking)

        return rankings

    async def generate_level_rankings(self, count: int) -> List[Dict[str, Any]]:
        """Generate level rankings"""
        rankings = []

        for i in range(count):
            ranking = {
                'rank': i + 1,
                'character_name': random.choice(self.character_names),
                'level': random.randint(80, 80) - (i // 5),
                'experience': random.randint(500000, 1000000) - (i * 5000),
                'play_time': random.randint(100, 1000) - (i * 10),
                'class': random.choice(["Warrior", "Mage", "Rogue", "Priest", "Hunter"]),
                'faction': random.choice([f['name'] for f in self.factions])
            }
            rankings.append(ranking)

        return rankings

    async def generate_wealth_rankings(self, count: int) -> List[Dict[str, Any]]:
        """Generate wealth rankings"""
        rankings = []

        for i in range(count):
            ranking = {
                'rank': i + 1,
                'character_name': random.choice(self.character_names),
                'total_wealth': random.randint(1000000, 10000000) - (i * 50000),
                'gold_coins': random.randint(500000, 5000000) - (i * 25000),
                'item_value': random.randint(200000, 2000000) - (i * 10000),
                'properties': random.randint(0, 10),
                'businesses': random.randint(0, 5)
            }
            rankings.append(ranking)

        return rankings

    async def generate_achievement_rankings(self, count: int) -> List[Dict[str, Any]]:
        """Generate achievement rankings"""
        rankings = []

        for i in range(count):
            ranking = {
                'rank': i + 1,
                'character_name': random.choice(self.character_names),
                'total_achievements': random.randint(100, 500) - (i * 5),
                'rare_achievements': random.randint(10, 50) - (i),
                'legendary_achievements': random.randint(1, 10),
                'achievement_points': random.randint(1000, 10000) - (i * 100),
                'completion_rate': random.uniform(0.5, 0.95) - (i * 0.01)
            }
            rankings.append(ranking)

        return rankings

    async def generate_guild_rankings(self, count: int) -> List[Dict[str, Any]]:
        """Generate guild rankings"""
        rankings = []

        for i in range(count):
            ranking = {
                'rank': i + 1,
                'guild_name': f"Guild {i+1}",
                'guild_level': random.randint(1, 25),
                'members': random.randint(50, 500) - (i * 10),
                'guild_points': random.randint(10000, 100000) - (i * 1000),
                'raid_progress': random.randint(0, 100) - (i * 2),
                'pvp_rating': random.randint(1000, 2500) - (i * 50)
            }
            rankings.append(ranking)

        return rankings

    def get_generated_data(self) -> Dict[str, Any]:
        """Get all generated sample data"""
        return self.generated_data

    def save_data_to_file(self, filename: str = "sample_data.json"):
        """Save generated data to file"""
        with open(filename, 'w') as f:
            json.dump(self.generated_data, f, indent=2, default=str)
        logger.info(f"Sample data saved to {filename}")