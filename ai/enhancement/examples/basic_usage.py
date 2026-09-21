#!/usr/bin/env python3
"""
Basic Usage Examples for AI Enhancement System

This file demonstrates how to use the AI Enhancement System in various scenarios.
"""

import json
import time
from enhancement_manager import EnhancementManager

def example_basic_enhancement():
    """Basic example of response enhancement."""
    print("=== Basic Enhancement Example ===")

    # Create enhancement manager
    manager = EnhancementManager("example_agent")

    # Input data
    user_input = "Can you help me understand what machine learning is?"
    initial_response = "Machine learning is a technology."
    context = {'user_id': 'user123', 'session_id': 'session456'}

    # Enhance response
    result = manager.enhance_response(user_input, initial_response, context)

    print(f"User Input: {user_input}")
    print(f"Initial Response: {initial_response}")
    print(f"Enhanced Response: {result.enhanced_content}")
    print(f"Quality Score: {result.quality_score:.2f}")
    print(f"Processing Time: {result.processing_time:.3f}s")
    print(f"Applied Enhancements: {', '.join(result.applied_enhancements)}")
    print()

def example_different_modes():
    """Example of different enhancement modes."""
    print("=== Enhancement Modes Example ===")

    user_input = "I'm feeling overwhelmed with work. Can you help me organize my tasks?"
    initial_response = "You should make a list of tasks."

    modes = ['BALANCED', 'SPEED_PRIORITY', 'QUALITY_PRIORITY', 'CREATIVE_PRIORITY']

    for mode in modes:
        print(f"--- Mode: {mode} ---")

        # Create manager with specific mode
        from enhancement_manager import EnhancementMode
        manager = EnhancementManager("example_agent")
        manager.set_enhancement_mode(EnhancementMode(mode))

        # Enhance response
        result = manager.enhance_response(user_input, initial_response)

        print(f"Enhanced: {result.enhanced_content}")
        print(f"Quality: {result.quality_score:.2f}")
        print(f"Time: {result.processing_time:.3f}s")
        print()

def example_learning_from_feedback():
    """Example of learning from user feedback."""
    print("=== Learning from Feedback Example ===")

    manager = EnhancementManager("learning_agent")

    # Multiple interactions with feedback
    interactions = [
        {
            'user_input': "Explain blockchain technology",
            'response': "Blockchain is a distributed ledger.",
            'feedback': {'clarity': 0.6, 'completeness': 0.5, 'helpfulness': 0.7}
        },
        {
            'user_input': "What are smart contracts?",
            'response': "Smart contracts are programs that run on blockchain.",
            'feedback': {'clarity': 0.8, 'completeness': 0.7, 'helpfulness': 0.9}
        },
        {
            'user_input': "How do I start investing in cryptocurrency?",
            'response': "You should buy Bitcoin from an exchange.",
            'feedback': {'clarity': 0.9, 'completeness': 0.4, 'helpfulness': 0.6}
        }
    ]

    for i, interaction in enumerate(interactions, 1):
        print(f"Interaction {i}:")
        print(f"  User: {interaction['user_input']}")
        print(f"  Response: {interaction['response']}")
        print(f"  Feedback: {interaction['feedback']}")

        # Learn from interaction
        manager.learn_from_interaction(
            interaction['user_input'],
            interaction['response'],
            interaction['feedback']
        )

        print("  ✓ Learned from feedback")
        print()

    # Show learning analytics
    analytics = manager.learning_accelerator.get_learning_analytics()
    print("Learning Analytics:")
    print(f"  Total Experiences: {analytics['total_experiences']}")
    print(f"  Average Quality: {analytics['average_idea_quality']:.2f}")
    print()

def example_quality_validation():
    """Example of quality validation."""
    print("=== Quality Validation Example ===")

    from quality_validator import QualityValidator, ContentCategory

    validator = QualityValidator("validation_agent")

    # Test different content qualities
    test_cases = [
        {
            'content': "AI is good technology that can help people.",
            'category': ContentCategory.INFORMATIONAL,
            'description': "Basic content"
        },
        {
            'content': "Artificial intelligence (AI) represents a transformative technology that leverages machine learning algorithms, neural networks, and advanced computational methods to process information, recognize patterns, and make decisions that traditionally required human intelligence.",
            'category': ContentCategory.TECHNICAL,
            'description': "High-quality technical content"
        },
        {
            'content': "AI AI AI technology machine learning neural networks AI is very good for everything because AI can do many things with data and algorithms that process information and help people solve problems and make decisions better than humans in many cases.",
            'category': ContentCategory.EDUCATIONAL,
            'description': "Repetitive, unclear content"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i} ({test_case['description']}):")
        print(f"  Content: {test_case['content'][:100]}...")

        result = validator.validate_content(
            test_case['content'],
            category=test_case['category']
        )

        print(f"  Overall Score: {result.overall_score:.2f}")
        print(f"  Outcome: {result.outcome.value}")
        print(f"  Issues: {len(result.issues)}")
        print(f"  Improvements: {len(result.improvements)}")

        if result.issues:
            print(f"  Top Issues: {result.issues[:2]}")
        if result.improvements:
            print(f"  Top Improvement: {result.improvements[0]}")
        print()

def example_emotional_intelligence():
    """Example of emotional intelligence enhancement."""
    print("=== Emotional Intelligence Example ===")

    from emotion_enhancer import EmotionEnhancer

    enhancer = EmotionEnhancer("emotional_agent")

    # Test cases with different emotional contexts
    emotional_cases = [
        {
            'user_input': "I just lost my job and I don't know what to do.",
            'ai_response': "You should update your resume and start applying.",
            'emotion': "distressed"
        },
        {
            'user_input': "I just got promoted! I'm so excited!",
            'ai_response': "That's nice. Congratulations on your promotion.",
            'emotion': "excited"
        },
        {
            'user_input': "I'm really confused about this technical concept.",
            'ai_response': "Let me explain it simply.",
            'emotion': "confused"
        }
    ]

    for i, case in enumerate(emotional_cases, 1):
        print(f"Emotional Case {i} ({case['emotion']}):")
        print(f"  User: {case['user_input']}")
        print(f"  Initial AI: {case['ai_response']}")

        # Enhance with emotional intelligence
        enhanced, emotional_response = enhancer.enhance_emotional_response(
            case['user_input'],
            case['ai_response'],
            {'user_emotion': case['emotion']}
        )

        print(f"  Enhanced: {enhanced}")
        print(f"  Emotional Tone: {emotional_response.emotional_tone.value}")
        print(f"  Empathy Level: {emotional_response.empathy_level:.2f}")
        print()

def example_creativity_boost():
    """Example of creativity enhancement for problem-solving."""
    print("=== Creativity Boost Example ===")

    from creativity_booster import CreativityBooster

    booster = CreativityBooster("creative_agent")

    # Problem-solving scenarios
    problems = [
        {
            'problem': "How can we reduce meeting fatigue in remote teams?",
            'context': {'team_size': 15, 'industry': 'technology'}
        },
        {
            'problem': "How might we make learning programming more accessible to beginners?",
            'context': {'target_audience': 'beginners', 'subject': 'programming'}
        },
        {
            'problem': "What are innovative ways to improve customer service?",
            'context': {'business_type': 'ecommerce', 'current_issues': ['slow_response']}
        }
    ]

    for i, problem_data in enumerate(problems, 1):
        print(f"Problem {i}: {problem_data['problem']}")

        # Generate creative solutions
        ideas, metrics = booster.boost_creativity(
            problem_data['problem'],
            problem_data['context']
        )

        print(f"  Generated {len(ideas)} creative ideas")
        print(f"  Average Quality: {metrics.idea_quality:.2f}")
        print(f"  Originality: {metrics.originality_score:.2f}")

        print("  Top 3 Ideas:")
        for j, idea in enumerate(ideas[:3], 1):
            print(f"    {j}. [{idea.technique.value}] {idea.content}")
            print(f"       Confidence: {idea.confidence:.2f}")
        print()

def example_system_monitoring():
    """Example of system monitoring and analytics."""
    print("=== System Monitoring Example ===")

    manager = EnhancementManager("monitoring_agent")

    # Simulate some interactions
    interactions = [
        ("What is AI?", "AI is artificial intelligence."),
        ("How does machine learning work?", "ML uses algorithms to learn from data."),
        ("Explain neural networks", "Neural networks mimic brain structure."),
        ("What are transformers?", "Transformers are attention-based models."),
        ("How to improve model accuracy?", "Use more data and better features.")
    ]

    print("Simulating interactions...")
    for user_input, response in interactions:
        result = manager.enhance_response(user_input, response, {'session_id': 'test'})
        time.sleep(0.1)  # Simulate processing time

    # Get system status
    status = manager.get_system_status()

    print("System Status:")
    print(f"  Agent ID: {status['agent_id']}")
    print(f"  Enhancement Mode: {status['enhancement_mode']}")
    print(f"  Total Enhancements: {status['total_enhancements_processed']}")
    print(f"  Average Processing Time: {status['average_processing_time']:.3f}s")
    print(f"  System Health: {status['system_health']['status']} ({status['system_health']['overall_score']:.2f})")

    print("\nModule Status:")
    for module, module_status in status['module_status'].items():
        if 'average_quality_score' in module_status:
            print(f"  {module}: Quality {module_status['average_quality_score']:.2f}")
        elif 'pass_rate' in module_status:
            print(f"  {module}: Pass Rate {module_status['pass_rate']:.2f}")
        else:
            print(f"  {module}: Active")

    print()

def example_configuration():
    """Example of configuration management."""
    print("=== Configuration Example ===")

    # Create custom configuration
    custom_config = {
        'conversation_style': 'PROFESSIONAL',
        'enhancement_mode': 'QUALITY_PRIORITY',
        'active_enhancements': [
            'conversation_optimizer',
            'emotion_enhancer',
            'quality_validator'
        ],
        'modules': {
            'quality_validator': {
                'validation_level': 'THOROUGH'
            },
            'response_accelerator': {
                'max_cache_size': 5000
            }
        }
    }

    # Create manager with custom config
    manager = EnhancementManager("config_agent", custom_config)

    print("Custom Configuration Applied:")
    print(f"  Conversation Style: {custom_config['conversation_style']}")
    print(f"  Enhancement Mode: {custom_config['enhancement_mode']}")
    print(f"  Active Enhancements: {custom_config['active_enhancements']}")

    # Test with custom configuration
    user_input = "Please provide a professional explanation of quantum computing"
    initial_response = "Quantum computing uses quantum mechanics."

    result = manager.enhance_response(user_input, initial_response)

    print(f"\nResult with Custom Config:")
    print(f"  Enhanced: {result.enhanced_content}")
    print(f"  Quality: {result.quality_score:.2f}")
    print(f"  Applied: {result.applied_enhancements}")

    # Export configuration
    exported_config = manager.export_configuration()
    print(f"\nExported Configuration:")
    print(json.dumps(exported_config, indent=2))
    print()

if __name__ == "__main__":
    print("AI Enhancement System - Basic Usage Examples")
    print("=" * 50)
    print()

    # Run all examples
    example_basic_enhancement()
    example_different_modes()
    example_learning_from_feedback()
    example_quality_validation()
    example_emotional_intelligence()
    example_creativity_boost()
    example_system_monitoring()
    example_configuration()

    print("All examples completed successfully!")
    print("Check the individual examples for more detailed usage patterns.")