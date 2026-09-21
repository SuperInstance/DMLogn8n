#!/usr/bin/env python3
"""
Main integration script for LoRA-based Strategic Adaptation System
Demonstrates complete system functionality
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Import system components
from personalized_model_manager import PersonalizedModelManager
from adaptive_response_generator import AdaptiveResponseGenerator, ResponseContext, ResponseStyle
from agent_dnd_lora_trainer import CharacterExperience
from strategic_pattern_analyzer import StrategicPatternAnalyzer
from error_handling import get_logger, HealthChecker
from performance_optimizer import ResourceManager

# Configure logging
logger = get_logger("main")

class LoRAAdaptationSystem:
    """Main system integration class"""

    def __init__(self):
        self.model_manager = None
        self.response_generator = None
        self.resource_manager = None
        self.health_checker = None
        self.initialized = False

    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing LoRA Adaptation System...")

            # Initialize core components
            self.model_manager = PersonalizedModelManager()
            self.response_generator = AdaptiveResponseGenerator(self.model_manager)
            self.resource_manager = ResourceManager()
            self.health_checker = HealthChecker()

            # Perform initial system health check
            health_status = await self.health_checker.get_system_health()
            if health_status.get("overall_status") == "error":
                raise Exception("System health check failed")

            # Optimize system resources
            optimization_result = await self.resource_manager.optimize_system()
            logger.info(f"System optimization completed: {optimization_result}")

            self.initialized = True
            logger.info("LoRA Adaptation System initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize system: {str(e)}")
            return False

    async def create_sample_agents(self):
        """Create sample agents for demonstration"""
        try:
            sample_characters = [
                {
                    "agent_id": "wizard_elara_001",
                    "character_info": {
                        "name": "Elara Moonwhisper",
                        "class": "Wizard",
                        "level": 10,
                        "skills": ["arcana", "evocation", "illusion", "history"],
                        "traits": ["intelligent", "wise", "curious", "cautious"]
                    }
                },
                {
                    "agent_id": "fighter_thorin_001",
                    "character_info": {
                        "name": "Thorin Ironforge",
                        "class": "Fighter",
                        "level": 8,
                        "skills": ["athletics", "intimidation", "survival", "perception"],
                        "traits": ["brave", "strong", "honorable", "protective"]
                    }
                },
                {
                    "agent_id": "rogue_shadow_001",
                    "character_info": {
                        "name": "Shadow Swiftblade",
                        "class": "Rogue",
                        "level": 9,
                        "skills": ["stealth", "perception", "deception", "sleight_of_hand"],
                        "traits": ["cunning", "agile", "cautious", "opportunistic"]
                    }
                }
            ]

            created_agents = []
            for character in sample_characters:
                success = await self.model_manager.register_agent(
                    character["agent_id"],
                    character["character_info"]
                )
                if success:
                    created_agents.append(character["agent_id"])
                    logger.info(f"Created agent: {character['character_info']['name']}")
                else:
                    logger.error(f"Failed to create agent: {character['agent_id']}")

            return created_agents

        except Exception as e:
            logger.error(f"Failed to create sample agents: {str(e)}")
            return []

    async def simulate_gameplay_experiences(self, agent_ids: list):
        """Simulate gameplay experiences for agents"""
        try:
            sample_experiences = [
                {
                    "agent_id": "wizard_elara_001",
                    "experience": CharacterExperience(
                        agent_id="wizard_elara_001",
                        session_id="dungeon_crawl_001",
                        timestamp=datetime.now(),
                        situation="Encountered a group of goblins guarding a magical artifact",
                        action="Cast sleep spell to neutralize the group peacefully",
                        outcome="Successfully acquired the artifact without combat",
                        success_score=0.95,
                        reward=200.0,
                        context={"location": "ancient_ruins", "artifact_type": "magical_staff"},
                        skills_used=["arcana", "illusion"],
                        character_class="Wizard",
                        level=10,
                        emotional_valence=0.8,
                        strategic_importance=0.9
                    )
                },
                {
                    "agent_id": "fighter_thorin_001",
                    "experience": CharacterExperience(
                        agent_id="fighter_thorin_001",
                        session_id="dragon_encounter_001",
                        timestamp=datetime.now(),
                        situation="Young dragon attacks the party",
                        action="Used defensive stance to protect allies while looking for opening",
                        outcome="Successfully defended party and created opportunity for counterattack",
                        success_score=0.85,
                        reward=150.0,
                        context={"location": "mountain_pass", "dragon_type": "young_red"},
                        skills_used=["athletics", "intimidation"],
                        character_class="Fighter",
                        level=8,
                        emotional_valence=0.6,
                        strategic_importance=0.95
                    )
                },
                {
                    "agent_id": "rogue_shadow_001",
                    "experience": CharacterExperience(
                        agent_id="rogue_shadow_001",
                        session_id="heist_001",
                        timestamp=datetime.now(),
                        situation="Need to infiltrate noble's mansion to steal documents",
                        action="Used stealth and disguise to bypass guards and reach study",
                        outcome="Successfully acquired documents without detection",
                        success_score=0.90,
                        reward=300.0,
                        context={"location": "noble_mansion", "security_level": "high"},
                        skills_used=["stealth", "deception", "sleight_of_hand"],
                        character_class="Rogue",
                        level=9,
                        emotional_valence=0.9,
                        strategic_importance=0.85
                    )
                }
            ]

            added_experiences = []
            for exp_data in sample_experiences:
                if exp_data["agent_id"] in agent_ids:
                    success = await self.model_manager.add_experience(exp_data["experience"])
                    if success:
                        added_experiences.append(exp_data["agent_id"])
                        logger.info(f"Added experience for agent: {exp_data['agent_id']}")

            return added_experiences

        except Exception as e:
            logger.error(f"Failed to simulate gameplay experiences: {str(e)}")
            return []

    async def demonstrate_response_generation(self, agent_ids: list):
        """Demonstrate adaptive response generation"""
        try:
            sample_situations = [
                {
                    "agent_id": "wizard_elara_001",
                    "context": ResponseContext(
                        agent_id="wizard_elara_001",
                        current_situation="You discover an ancient magical library with floating books and mysterious runes",
                        game_state={"health": 90, "mana": 120, "position": "library"},
                        available_actions=["study_runes", "read_books", "cast_detect_magic", "search_for_traps"],
                        nearby_characters=["scholar_npc"],
                        environment={"lighting": "magical_glow", "magic_level": "high"},
                        urgency_level=2,
                        stakes="medium"
                    )
                },
                {
                    "agent_id": "fighter_thorin_001",
                    "context": ResponseContext(
                        agent_id="fighter_thorin_001",
                        current_situation="A bridge ahead has collapsed and the party needs to cross a deep chasm",
                        game_state={"health": 75, "position": "chasm_edge"},
                        available_actions["search_for_alternate_route", "attempt_jump", "use_rope", "call_for_help"],
                        nearby_characters=["party_members"],
                        environment={"terrain": "mountain", "weather": "windy"},
                        urgency_level=6,
                        stakes="high"
                    )
                },
                {
                    "agent_id": "rogue_shadow_001",
                    "context": ResponseContext(
                        agent_id="rogue_shadow_001",
                        current_situation="You overhear guards discussing a secret passage in the castle",
                        game_state={"health": 85, "position": "castle_corridor"},
                        available_actions=["follow_guards", "search_for_passage", "create_diversion", "wait_opportunity"],
                        nearby_characters=["guards", "nobles"],
                        environment={"lighting": "torches", "security": "high"},
                        urgency_level=4,
                        stakes="high"
                    )
                }
            ]

            responses = []
            for situation in sample_situations:
                if situation["agent_id"] in agent_ids:
                    response = await self.response_generator.generate_response(
                        situation["context"],
                        max_length=200
                    )
                    responses.append({
                        "agent_id": situation["agent_id"],
                        "response": response,
                        "situation": situation["context"].current_situation
                    })
                    logger.info(f"Generated response for {situation['agent_id']}: {response.response_text[:100]}...")

            return responses

        except Exception as e:
            logger.error(f"Failed to demonstrate response generation: {str(e)}")
            return []

    async def demonstrate_learning_cycle(self, agent_ids: list):
        """Demonstrate the complete learning cycle"""
        try:
            logger.info("Starting learning cycle demonstration...")

            # Step 1: Collect experiences
            logger.info("Step 1: Collecting gameplay experiences...")
            experienced_agents = await self.simulate_gameplay_experiences(agent_ids)

            # Step 2: Analyze patterns
            logger.info("Step 2: Analyzing strategic patterns...")
            for agent_id in experienced_agents:
                experiences = self.model_manager.experience_buffers.get(agent_id, [])
                if experiences:
                    patterns = await self.response_generator.pattern_analyzer.analyze_agent_experiences(
                        agent_id, experiences[-10:]  # Analyze last 10 experiences
                    )
                    logger.info(f"Agent {agent_id}: Found {len(patterns)} strategic patterns")

            # Step 3: Trigger training if enough data
            logger.info("Step 3: Triggering model training...")
            training_results = []
            for agent_id in experienced_agents:
                trained = await self.model_manager.train_agent_model(agent_id)
                if trained:
                    training_results.append(agent_id)
                    logger.info(f"Agent {agent_id}: Model training completed")

            # Step 4: Generate responses with learned patterns
            logger.info("Step 4: Generating responses with learned patterns...")
            responses = await self.demonstrate_response_generation(agent_ids)

            return {
                "experienced_agents": experienced_agents,
                "trained_agents": training_results,
                "generated_responses": len(responses)
            }

        except Exception as e:
            logger.error(f"Learning cycle demonstration failed: {str(e)}")
            return {"error": str(e)}

    async def run_system_diagnostics(self):
        """Run comprehensive system diagnostics"""
        try:
            logger.info("Running system diagnostics...")

            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "system_status": {},
                "resource_usage": {},
                "performance_metrics": {},
                "health_checks": {},
                "agent_statistics": {}
            }

            # System status
            diagnostics["system_status"] = self.model_manager.get_system_status()

            # Resource usage
            diagnostics["resource_usage"] = await self.resource_manager.monitor_resources()

            # Performance metrics
            diagnostics["performance_metrics"] = self.resource_manager.get_performance_analysis()

            # Health checks
            diagnostics["health_checks"] = await self.health_checker.get_system_health()

            # Agent statistics
            for agent_id in self.model_manager.agent_profiles.keys():
                diagnostics["agent_statistics"][agent_id] = self.model_manager.get_agent_summary(agent_id)

            return diagnostics

        except Exception as e:
            logger.error(f"System diagnostics failed: {str(e)}")
            return {"error": str(e)}

    async def cleanup(self):
        """Cleanup system resources"""
        try:
            logger.info("Cleaning up system resources...")

            # Cleanup all agents
            agent_ids = list(self.model_manager.agent_profiles.keys())
            for agent_id in agent_ids:
                await self.model_manager.cleanup_agent(agent_id, backup=True)

            # Optimize resources one final time
            await self.resource_manager.optimize_system()

            logger.info("System cleanup completed")

        except Exception as e:
            logger.error(f"System cleanup failed: {str(e)}")

async def main():
    """Main demonstration function"""
    print("=" * 60)
    print("LoRA-based Strategic Adaptation System Demo")
    print("=" * 60)

    # Initialize system
    system = LoRAAdaptationSystem()

    if not await system.initialize():
        print("❌ System initialization failed!")
        return

    print("✅ System initialized successfully")

    # Create sample agents
    print("\n📝 Creating sample agents...")
    agent_ids = await system.create_sample_agents()
    print(f"✅ Created {len(agent_ids)} sample agents")

    # Demonstrate response generation
    print("\n💬 Demonstrating response generation...")
    responses = await system.demonstrate_response_generation(agent_ids)
    print(f"✅ Generated {len(responses)} adaptive responses")

    # Show sample responses
    for response_data in responses[:2]:  # Show first 2 responses
        print(f"\n📖 Agent: {response_data['agent_id']}")
        print(f"Situation: {response_data['situation']}")
        print(f"Response: {response_data['response'].response_text}")
        print(f"Style: {response_data['response'].response_style.value}")
        print(f"Confidence: {response_data['response'].confidence:.2f}")

    # Demonstrate learning cycle
    print("\n🎓 Demonstrating learning cycle...")
    learning_results = await system.demonstrate_learning_cycle(agent_ids)
    if "error" not in learning_results:
        print(f"✅ Learning cycle completed:")
        print(f"   - Agents with experiences: {len(learning_results['experienced_agents'])}")
        print(f"   - Agents trained: {len(learning_results['trained_agents'])}")
        print(f"   - Responses generated: {learning_results['generated_responses']}")

    # Run system diagnostics
    print("\n🔍 Running system diagnostics...")
    diagnostics = await system.run_system_diagnostics()
    if "error" not in diagnostics:
        print("✅ System diagnostics completed")
        print(f"   - Registered agents: {diagnostics['system_status']['registered_agents']}")
        print(f"   - Total experiences: {diagnostics['system_status']['total_experiences']}")
        print(f"   - Memory usage: {diagnostics['resource_usage']['memory']['percent']:.1f}%")
        print(f"   - System health: {diagnostics['health_checks']['overall_status']}")

    # Save demonstration results
    results_file = Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/demo_results.json")
    demo_results = {
        "timestamp": datetime.now().isoformat(),
        "agents_created": len(agent_ids),
        "responses_generated": len(responses),
        "learning_results": learning_results,
        "system_diagnostics": diagnostics
    }

    with open(results_file, 'w') as f:
        json.dump(demo_results, f, indent=2, default=str)

    print(f"\n💾 Demo results saved to: {results_file}")

    # Cleanup
    print("\n🧹 Cleaning up system resources...")
    await system.cleanup()

    print("\n" + "=" * 60)
    print("🎉 LoRA Adaptation System Demo completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())