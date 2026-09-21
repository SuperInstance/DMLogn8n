#!/usr/bin/env python3
"""
Quick Start Script for LoRA-based Strategic Adaptation System
Simple demonstration of core functionality
"""

import asyncio
import json
from datetime import datetime

# Import required components
from personalized_model_manager import PersonalizedModelManager
from adaptive_response_generator import AdaptiveResponseGenerator, ResponseContext

async def quick_start_demo():
    """Quick start demonstration"""
    print("🚀 LoRA Adaptation System - Quick Start Demo")
    print("=" * 50)

    # Step 1: Initialize the system
    print("\n1️⃣ Initializing system...")
    model_manager = PersonalizedModelManager()
    response_generator = AdaptiveResponseGenerator(model_manager)

    # Step 2: Create a sample agent
    print("\n2️⃣ Creating a sample agent...")
    character_info = {
        "name": "Zara Firebrand",
        "class": "Sorcerer",
        "level": 6,
        "skills": ["arcana", "deception", "persuasion"],
        "traits": ["ambitious", "charismatic", "impulsive"]
    }

    agent_id = "zara_001"
    success = await model_manager.register_agent(agent_id, character_info)
    print(f"   ✅ Agent registered: {success}")

    # Step 3: Create a gameplay situation
    print("\n3️⃣ Creating gameplay situation...")
    context = ResponseContext(
        agent_id=agent_id,
        current_situation="You arrive at a crossroads in the enchanted forest. One path leads to a mysterious tower, another to a village in need, and a third to unknown dangers.",
        game_state={"health": 80, "mana": 60, "position": "forest_crossroads"},
        available_actions=["investigate_tower", "go_to_village", "explore_unknown_path", "cast_scrying_spell"],
        nearby_characters=["fellow_adventurers"],
        environment={"terrain": "forest", "time": "dusk", "weather": "calm"},
        urgency_level=5,
        stakes="medium"
    )

    # Step 4: Generate agent response
    print("\n4️⃣ Generating agent response...")
    response = await response_generator.generate_response(context, max_length=150)

    print(f"\n📖 Agent Response:")
    print(f"   Name: {character_info['name']}")
    print(f"   Class: {character_info['class']} Level {character_info['level']}")
    print(f"   Response: {response.response_text}")
    print(f"   Style: {response.response_style.value}")
    print(f"   Confidence: {response.confidence:.2f}")
    print(f"   Risk Assessment: {response.risk_assessment}")

    # Step 5: Show strategic considerations
    print(f"\n🧠 Strategic Considerations:")
    for consideration in response.strategic_considerations:
        print(f"   • {consideration}")

    # Step 6: Show system status
    print(f"\n📊 System Status:")
    system_status = model_manager.get_system_status()
    print(f"   • Registered agents: {system_status['registered_agents']}")
    print(f"   • Total experiences: {system_status['total_experiences']}")
    print(f"   • Active models: {system_status['active_models']}")

    print(f"\n✨ Quick start demo completed!")
    print(f"💡 The agent '{character_info['name']}' has made a strategic decision based on their personality and the situation!")
    print(f"🔧 Check the full documentation in README.md for advanced features!")

if __name__ == "__main__":
    asyncio.run(quick_start_demo())