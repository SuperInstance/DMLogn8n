"""
Advanced Procedural World Generation System Demo
Demonstrates all components of the world generation system working together
to create complete, diverse, and engaging game worlds.
"""

import numpy as np
import random
import time
from typing import Dict, List, Tuple

# Import all world generation modules
from terrain_generator import TerrainGenerator, BiomeType
from city_builder import CityBuilder
from dungeon_crafter import DungeonCrafter, DungeonTheme
from ecosystem_simulator import EcosystemSimulator, create_sample_biome_map
from culture_generator import CultureGenerator, generate_world_cultures
from quest_weaver import QuestWeaver, create_sample_context, QuestType
from resource_distributor import ResourceDistributor
from world_history import WorldHistory, format_timeline_summary

class WorldGenerator:
    """Main world generation coordinator"""

    def __init__(self, width: int = 256, height: int = 256, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)

        print(f"Initializing World Generator...")
        print(f"World dimensions: {width}x{height}")
        print(f"Seed: {self.seed}")

        # Initialize all generators
        self.terrain_generator = TerrainGenerator(width, height, self.seed)
        self.city_builder = CityBuilder(width, height, self.seed + 1)
        self.dungeon_crafter = DungeonCrafter(self.seed + 2)
        self.ecosystem_simulator = None  # Will be initialized after terrain
        self.culture_generator = CultureGenerator(self.seed + 3)
        self.quest_weaver = QuestWeaver(self.seed + 4)
        self.resource_distributor = ResourceDistributor(width, height, self.seed + 5)
        self.world_history = WorldHistory(width, height, self.seed + 6)

        # Generated world data
        self.world_data = {}

    def generate_complete_world(self, include_dungeons: bool = True,
                              include_ecology: bool = True,
                              include_history: bool = True,
                              include_cultures: bool = True,
                              include_quests: bool = True) -> Dict:
        """Generate complete world with all components"""
        print(f"\n=== Starting World Generation ===")
        start_time = time.time()

        # 1. Generate terrain and biomes
        print("\n1. Generating Terrain...")
        self.world_data['terrain'] = self.terrain_generator.generate_complete_world()

        # 2. Generate resources
        print("\n2. Distributing Resources...")
        cities = [(128, 64), (64, 128), (192, 192)]  # Sample city locations
        self.resource_distributor.distribute_resources(
            self.world_data['terrain']['heightmap'],
            self.world_data['terrain']['biome_map'],
            cities
        )

        # 3. Generate cities
        print("\n3. Building Cities...")
        self.world_data['cities'] = []
        for city_location in cities:
            y, x = city_location
            # Get terrain height at city location
            terrain_height = self.world_data['terrain']['heightmap'][y, x]
            # Create water mask
            water_mask = self.world_data['terrain']['heightmap'] < 0.4

            city = self.city_builder.generate_city(
                city_center=(y, x),
                terrain_height=self.world_data['terrain']['heightmap'],
                water_mask=water_mask,
                city_size="medium",
                city_type="town"
            )
            self.world_data['cities'].append(city)

        # 4. Generate dungeons
        if include_dungeons:
            print("\n4. Crafting Dungeons...")
            self.world_data['dungeons'] = []
            # Generate dungeons of different themes
            themes = [DungeonTheme.CLASSIC, DungeonTheme.CAVE, DungeonTheme.TEMPLE,
                     DungeonTheme.FORTRESS, DungeonTheme.TOMB]

            for i, theme in enumerate(themes):
                dungeon = self.dungeon_crafter.generate_multi_level_dungeon(
                    width=80, height=60,
                    num_levels=random.randint(3, 7),
                    theme=theme,
                    name=f"{theme.value.title()} Dungeon #{i+1}"
                )
                self.world_data['dungeons'].append(dungeon)

        # 5. Generate ecosystems
        if include_ecology:
            print("\n5. Simulating Ecosystems...")
            biome_map = self.world_data['terrain']['biome_map']
            self.ecosystem_simulator = EcosystemSimulator(
                self.width, self.height, biome_map, self.seed + 7
            )

            # Run simulation steps
            for step in range(10):
                self.ecosystem_simulator.simulate_step()

            self.world_data['ecosystem'] = self.ecosystem_simulator

        # 6. Generate cultures
        if include_cultures:
            print("\n6. Generating Cultures...")
            biome_map = self.world_data['terrain']['biome_map']
            self.world_data['cultures'] = generate_world_cultures(
                self.width, self.height, 8, biome_map, self.seed + 8
            )

        # 7. Generate quests
        if include_quests:
            print("\n7. Weaving Quests...")
            self.world_data['quests'] = []
            self.world_data['quest_givers'] = []

            # Create quest givers from cultures
            if include_cultures and self.world_data['cultures']:
                for culture in self.world_data['cultures']:
                    for i in range(random.randint(2, 4)):
                        quest_giver = self.quest_weaver.generate_quest_giver(
                            location=culture.homeland,
                            context=create_sample_context()
                        )
                        self.world_data['quest_givers'].append(quest_giver)

                        # Generate quests for this giver
                        for quest_type in random.sample(
                            list(QuestType), random.randint(1, 3)
                        ):
                            quest = self.quest_weaver.generate_quest(
                                quest_type, quest_giver, create_sample_context()
                            )
                            self.world_data['quests'].append(quest)

        # 8. Generate world history
        if include_history:
            print("\n8. Simulating World History...")
            timeline = self.world_history.generate_world_history(num_steps=150)
            self.world_data['history'] = timeline

        # Calculate generation time
        end_time = time.time()
        generation_time = end_time - start_time

        print(f"\n=== World Generation Complete ===")
        print(f"Generation time: {generation_time:.2f} seconds")

        # Generate summary
        self._generate_world_summary()

        return self.world_data

    def _generate_world_summary(self) -> None:
        """Generate and display world summary"""
        print(f"\n=== World Summary ===")

        # Terrain summary
        terrain = self.world_data['terrain']
        print(f"\nTerrain Features:")
        print(f"  - Rivers: {len(terrain['rivers'])}")
        print(f"  - Special features: {len(terrain['features'])}")
        print(f"  - Biome types: {len(set(np.unique(terrain['biome_map'])))}")

        # Cities summary
        if 'cities' in self.world_data:
            print(f"\nCities: {len(self.world_data['cities'])}")
            total_population = sum(city.population for city in self.world_data['cities'])
            print(f"  - Total population: {total_population:,}")
            print(f"  - Districts: {sum(len(city.districts) for city in self.world_data['cities'])}")

        # Dungeons summary
        if 'dungeons' in self.world_data:
            print(f"\nDungeons: {len(self.world_data['dungeons'])}")
            total_levels = sum(len(dungeon.levels) for dungeon in self.world_data['dungeons'])
            print(f"  - Total levels: {total_levels}")

        # Ecosystem summary
        if 'ecosystem' in self.world_data:
            ecosystem = self.world_data['ecosystem']
            stats = ecosystem.get_ecosystem_statistics()
            print(f"\nEcosystem:")
            print(f"  - Total animals: {stats['total_animals']}")
            print(f"  - Total plants: {stats['total_plants']}")
            print(f"  - Species diversity: {stats['biodiversity_index']}")

        # Cultures summary
        if 'cultures' in self.world_data:
            cultures = self.world_data['cultures']
            print(f"\nCultures: {len(cultures)}")
            total_culture_population = sum(culture.population for culture in cultures)
            print(f"  - Total population: {total_culture_population:,}")
            print(f"  - Languages: {len(set(culture.language.name for culture in cultures))}")

        # Quests summary
        if 'quests' in self.world_data:
            quests = self.world_data['quests']
            print(f"\nQuests: {len(quests)}")
            quest_types = {}
            for quest in quests:
                quest_types[quest.quest_type.value] = quest_types.get(quest.quest_type.value, 0) + 1
            for qtype, count in quest_types.items():
                print(f"  - {qtype}: {count}")

        # Resources summary
        resources_analysis = self.resource_distributor.analyze_resource_distribution()
        print(f"\nResources:")
        print(f"  - Total resource nodes: {resources_analysis['total_resource_nodes']}")
        print(f"  - Trade routes: {resources_analysis['total_trade_routes']}")
        print(f"  - Markets: {resources_analysis['total_markets']}")

        # History summary
        if 'history' in self.world_data:
            timeline = self.world_data['history']
            print(f"\nHistory:")
            print(f"  - Timespan: {timeline.start_year} to {timeline.current_year}")
            print(f"  - Events: {len(timeline.events)}")
            print(f"  - Civilizations: {len(timeline.civilizations)}")

    def get_world_overview(self) -> str:
        """Get formatted world overview"""
        overview = []
        overview.append(f"Generated World Overview")
        overview.append(f"========================")
        overview.append(f"Dimensions: {self.width}x{self.height}")
        overview.append(f"Seed: {self.seed}")
        overview.append("")

        # Key locations
        overview.append("Key Locations:")
        if 'cities' in self.world_data:
            for i, city in enumerate(self.world_data['cities'][:5]):
                overview.append(f"  {i+1}. {city.name} - Population: {city.population:,}")

        if 'dungeons' in self.world_data:
            for i, dungeon in enumerate(self.world_data['dungeons'][:3]):
                overview.append(f"  {i+1}. {dungeon.name} - {len(dungeon.levels)} levels")

        # Sample quest
        if 'quests' in self.world_data and self.world_data['quests']:
            quest = random.choice(self.world_data['quests'])
            overview.append(f"\nSample Quest: {quest.title}")
            overview.append(f"  Type: {quest.quest_type.value}")
            overview.append(f"  Difficulty: {quest.difficulty.value}")
            overview.append(f"  Objectives: {len(quest.objectives)}")

        # Sample culture
        if 'cultures' in self.world_data and self.world_data['cultures']:
            culture = random.choice(self.world_data['cultures'])
            overview.append(f"\nSample Culture: {culture.name}")
            overview.append(f"  Population: {culture.population:,}")
            overview.append(f"  Government: {culture.government_type.value}")
            overview.append(f"  Technology: {culture.technology_level.value}")

        # Historical event
        if 'history' in self.world_data:
            major_events = self.world_history.get_major_events(min_significance=0.8)
            if major_events:
                event = random.choice(major_events)
                overview.append(f"\nHistorical Event: {event.name}")
                overview.append(f"  Year: {event.year}")
                overview.append(f"  Type: {event.event_type.value}")

        return "\n".join(overview)

def demo_world_generation():
    """Demonstrate the complete world generation system"""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     ADVANCED PROCEDURAL WORLD GENERATION SYSTEM DEMO          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    # Create world generator
    generator = WorldGenerator(width=128, height=128, seed=42)

    # Generate complete world
    world = generator.generate_complete_world(
        include_dungeons=True,
        include_ecology=True,
        include_history=True,
        include_cultures=True,
        include_quests=True
    )

    # Display world overview
    print("\n" + "="*60)
    print("WORLD OVERVIEW")
    print("="*60)
    print(generator.get_world_overview())

    # Show some interesting details
    print("\n" + "="*60)
    print("INTERESTING WORLD DETAILS")
    print("="*60)

    # Show a sample city
    if world['cities']:
        city = world['cities'][0]
        print(f"\nSample City: {city.name}")
        print(f"  Population: {city.population:,}")
        print(f"  Type: {city.city_type}")
        print(f"  Districts: {len(city.districts)}")
        print(f"  Buildings: {len(city.buildings)}")
        print(f"  Roads: {len(city.roads)}")

    # Show a sample dungeon
    if world['dungeons']:
        dungeon = world['dungeons'][0]
        print(f"\nSample Dungeon: {dungeon.name}")
        print(f"  Theme: {dungeon.theme.value}")
        print(f"  Levels: {len(dungeon.levels)}")
        print(f"  Total rooms: {sum(len(level.rooms) for level in dungeon.levels)}")
        print(f"  Lore: {dungeon.lore_description[:100]}...")

    # Show sample quest
    if world['quests']:
        quest = random.choice(world['quests'])
        print(f"\nSample Quest: {quest.title}")
        print(f"  Giver: {quest.quest_giver.name}")
        print(f"  Type: {quest.quest_type.value}")
        print(f"  Difficulty: {quest.difficulty.value}")
        print(f"  Description: {quest.description[:150]}...")

    # Show world history snippet
    if 'history' in world:
        timeline = world['history']
        print(f"\nWorld History Snippet:")
        print(format_timeline_summary(timeline)[:500] + "...")

    print(f"\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print("The world generation system has successfully created a rich,")
    print("diverse, and engaging world with:")
    print("✓ Realistic terrain with erosion simulation")
    print("✓ Intelligent cities with logical layouts")
    print("✓ Complex dungeons with multi-level structures")
    print("✓ Living ecosystems with wildlife simulation")
    print("✓ Rich cultures with unique traditions")
    print("✓ Dynamic quests with story integration")
    print("✓ Strategic resource distribution")
    print("✓ Historical simulation with timeline")
    print("\nThis world provides endless possibilities for adventure!")

if __name__ == "__main__":
    demo_world_generation()