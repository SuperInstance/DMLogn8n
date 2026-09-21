#!/usr/bin/env python3
"""
Integration Tests for LoRA-based Strategic Adaptation System
Comprehensive testing suite for all components
"""

import asyncio
import json
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Import our modules
from agent_dnd_lora_trainer import LoRATrainer, CharacterExperience
from strategic_pattern_analyzer import StrategicPatternAnalyzer
from personalized_model_manager import PersonalizedModelManager
from adaptive_response_generator import AdaptiveResponseGenerator, ResponseContext, ResponseStyle
from error_handling import get_logger, HealthChecker
from performance_optimizer import ResourceManager

class TestLoRAAdaptationSystem:
    """Integration test suite for LoRA Adaptation System"""

    def __init__(self):
        self.logger = get_logger("integration_tests")
        self.test_results = []
        self.temp_dir = None

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.logger.info("Starting LoRA Adaptation System integration tests")

        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp(prefix="lora_test_")

        try:
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "test_suite": "LoRA Adaptation System",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_results": [],
                "performance_metrics": {},
                "system_health": {}
            }

            # Run individual test suites
            test_suites = [
                ("Model Manager Tests", self.test_model_manager),
                ("LoRA Trainer Tests", self.test_lora_trainer),
                ("Pattern Analyzer Tests", self.test_pattern_analyzer),
                ("Response Generator Tests", self.test_response_generator),
                ("Error Handling Tests", self.test_error_handling),
                ("Performance Optimization Tests", self.test_performance_optimizer),
                ("End-to-End Integration Tests", self.test_end_to_end_integration),
                ("Resource Management Tests", self.test_resource_management),
                ("System Health Tests", self.test_system_health)
            ]

            for suite_name, test_function in test_suites:
                suite_result = await self._run_test_suite(suite_name, test_function)
                test_results["test_results"].append(suite_result)
                test_results["total_tests"] += suite_result["total_tests"]
                test_results["passed_tests"] += suite_result["passed_tests"]
                test_results["failed_tests"] += suite_result["failed_tests"]

            # Get performance metrics
            test_results["performance_metrics"] = await self._collect_performance_metrics()

            # Get system health
            health_checker = HealthChecker()
            test_results["system_health"] = await health_checker.get_system_health()

            # Calculate overall success rate
            if test_results["total_tests"] > 0:
                test_results["success_rate"] = test_results["passed_tests"] / test_results["total_tests"]
            else:
                test_results["success_rate"] = 0.0

            self.logger.info(f"Integration tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")

            return test_results

        except Exception as e:
            self.logger.error(f"Integration test suite failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

        finally:
            # Cleanup temporary directory
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)

    async def _run_test_suite(self, suite_name: str, test_function) -> Dict[str, Any]:
        """Run a test suite and return results"""
        suite_result = {
            "suite_name": suite_name,
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_cases": []
        }

        try:
            self.logger.info(f"Running test suite: {suite_name}")

            # Run the test suite
            test_cases = await test_function()

            for test_case in test_cases:
                suite_result["total_tests"] += 1
                if test_case["passed"]:
                    suite_result["passed_tests"] += 1
                else:
                    suite_result["failed_tests"] += 1

                suite_result["test_cases"].append(test_case)

            self.logger.info(f"Test suite '{suite_name}' completed: {suite_result['passed_tests']}/{suite_result['total_tests']} passed")

        except Exception as e:
            self.logger.error(f"Test suite '{suite_name}' failed: {str(e)}")
            suite_result["error"] = str(e)

        return suite_result

    async def test_model_manager(self) -> List[Dict[str, Any]]:
        """Test Personalized Model Manager functionality"""
        test_cases = []

        # Test 1: Agent registration
        try:
            model_manager = PersonalizedModelManager()

            character_info = {
                "name": "Test Character",
                "class": "Wizard",
                "level": 5,
                "skills": ["arcana", "evocation"],
                "traits": ["intelligent", "wise"]
            }

            agent_id = "test_agent_001"
            success = await model_manager.register_agent(agent_id, character_info)

            test_cases.append({
                "test_name": "Agent Registration",
                "passed": success,
                "details": f"Agent {agent_id} registered successfully" if success else "Agent registration failed"
            })

            # Test 2: Agent profile retrieval
            profile = model_manager.agent_profiles.get(agent_id)
            profile_exists = profile is not None and profile.character_name == "Test Character"

            test_cases.append({
                "test_name": "Agent Profile Retrieval",
                "passed": profile_exists,
                "details": "Profile retrieved and verified" if profile_exists else "Profile retrieval failed"
            })

            # Test 3: Experience addition
            experience = CharacterExperience(
                agent_id=agent_id,
                session_id="test_session",
                timestamp=datetime.now(),
                situation="Test situation",
                action="Test action",
                outcome="Test outcome",
                success_score=0.8,
                reward=50.0,
                context={"test": True},
                skills_used=["arcana"],
                character_class="Wizard",
                level=5,
                emotional_valence=0.5,
                strategic_importance=0.7
            )

            exp_success = await model_manager.add_experience(experience)

            test_cases.append({
                "test_name": "Experience Addition",
                "passed": exp_success,
                "details": "Experience added successfully" if exp_success else "Experience addition failed"
            })

            # Test 4: System status
            status = model_manager.get_system_status()
            status_valid = "registered_agents" in status and status["registered_agents"] >= 1

            test_cases.append({
                "test_name": "System Status",
                "passed": status_valid,
                "details": "System status retrieved and valid" if status_valid else "System status invalid"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Model Manager Tests",
                "passed": False,
                "details": f"Model manager tests failed: {str(e)}"
            })

        return test_cases

    async def test_lora_trainer(self) -> List[Dict[str, Any]]:
        """Test LoRA Trainer functionality"""
        test_cases = []

        try:
            trainer = LoRATrainer()

            # Test 1: Trainer initialization
            trainer_valid = trainer.base_model_name is not None

            test_cases.append({
                "test_name": "LoRA Trainer Initialization",
                "passed": trainer_valid,
                "details": "Trainer initialized successfully" if trainer_valid else "Trainer initialization failed"
            })

            # Test 2: LoRA configuration creation
            character_info = {"class": "Wizard", "level": 5}
            config = trainer._create_character_specific_config(character_info)
            config_valid = config is not None and config.r > 0

            test_cases.append({
                "test_name": "LoRA Configuration Creation",
                "passed": config_valid,
                "details": "LoRA configuration created successfully" if config_valid else "LoRA configuration creation failed"
            })

            # Test 3: Experience formatting
            experience = CharacterExperience(
                agent_id="test",
                session_id="test",
                timestamp=datetime.now(),
                situation="Test",
                action="Test action",
                outcome="Success",
                success_score=0.9,
                reward=100.0,
                context={},
                skills_used=["test"],
                character_class="Wizard",
                level=5,
                emotional_valence=0.5,
                strategic_importance=0.8
            )

            formatted = trainer._format_experience_for_training(experience)
            format_valid = formatted is not None and len(formatted) > 0

            test_cases.append({
                "test_name": "Experience Formatting",
                "passed": format_valid,
                "details": "Experience formatted successfully" if format_valid else "Experience formatting failed"
            })

            # Test 4: Experience collection
            await trainer.collect_experience(experience)
            collection_valid = len(trainer.experience_buffer.get("test", [])) > 0

            test_cases.append({
                "test_name": "Experience Collection",
                "passed": collection_valid,
                "details": "Experience collected successfully" if collection_valid else "Experience collection failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "LoRA Trainer Tests",
                "passed": False,
                "details": f"LoRA trainer tests failed: {str(e)}"
            })

        return test_cases

    async def test_pattern_analyzer(self) -> List[Dict[str, Any]]:
        """Test Strategic Pattern Analyzer functionality"""
        test_cases = []

        try:
            analyzer = StrategicPatternAnalyzer()

            # Test 1: Analyzer initialization
            analyzer_valid = analyzer.vectorizer is not None

            test_cases.append({
                "test_name": "Pattern Analyzer Initialization",
                "passed": analyzer_valid,
                "details": "Analyzer initialized successfully" if analyzer_valid else "Analyzer initialization failed"
            })

            # Test 2: Pattern extraction
            experiences = [
                CharacterExperience(
                    agent_id="test",
                    session_id="test",
                    timestamp=datetime.now(),
                    situation="Combat situation",
                    action="Attack with sword",
                    outcome="Victory",
                    success_score=0.9,
                    reward=100.0,
                    context={},
                    skills_used=["combat"],
                    character_class="Fighter",
                    level=5,
                    emotional_valence=0.8,
                    strategic_importance=0.9
                )
            ]

            patterns = await analyzer.extract_patterns(experiences)
            patterns_valid = isinstance(patterns, dict) and "success_patterns" in patterns

            test_cases.append({
                "test_name": "Pattern Extraction",
                "passed": patterns_valid,
                "details": "Patterns extracted successfully" if patterns_valid else "Pattern extraction failed"
            })

            # Test 3: Situation categorization
            category = analyzer._categorize_situation("Combat with goblins in forest")
            category_valid = category in ["combat", "social", "exploration", "magical", "general"]

            test_cases.append({
                "test_name": "Situation Categorization",
                "passed": category_valid,
                "details": f"Situation categorized as: {category}" if category_valid else "Situation categorization failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Pattern Analyzer Tests",
                "passed": False,
                "details": f"Pattern analyzer tests failed: {str(e)}"
            })

        return test_cases

    async def test_response_generator(self) -> List[Dict[str, Any]]:
        """Test Adaptive Response Generator functionality"""
        test_cases = []

        try:
            # Setup
            model_manager = PersonalizedModelManager()
            generator = AdaptiveResponseGenerator(model_manager)

            # Test 1: Generator initialization
            generator_valid = generator.response_templates is not None

            test_cases.append({
                "test_name": "Response Generator Initialization",
                "passed": generator_valid,
                "details": "Generator initialized successfully" if generator_valid else "Generator initialization failed"
            })

            # Test 2: Response style determination
            profile = type('Profile', (), {
                'playstyle': 'strategic',
                'character_class': 'Wizard',
                'level': 5
            })()

            context = ResponseContext(
                agent_id="test",
                current_situation="Combat with dragon",
                game_state={},
                available_actions=["attack", "defend", "cast_spell"],
                nearby_characters=["ally1", "ally2"],
                environment={"terrain": "mountain"},
                urgency_level=8,
                stakes="critical"
            )

            style = generator._determine_response_style(context, profile)
            style_valid = style is not None

            test_cases.append({
                "test_name": "Response Style Determination",
                "passed": style_valid,
                "details": f"Style determined as: {style.value if style_valid else 'None'}"
            })

            # Test 3: Enhanced prompt building
            prompt = await generator._build_enhanced_prompt(context, profile, ResponseStyle.STRATEGIC)
            prompt_valid = prompt is not None and len(prompt) > 100

            test_cases.append({
                "test_name": "Enhanced Prompt Building",
                "passed": prompt_valid,
                "details": f"Prompt built with {len(prompt) if prompt_valid else 0} characters"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Response Generator Tests",
                "passed": False,
                "details": f"Response generator tests failed: {str(e)}"
            })

        return test_cases

    async def test_error_handling(self) -> List[Dict[str, Any]]:
        """Test Error Handling functionality"""
        test_cases = []

        try:
            from error_handling import LoRAAdaptationLogger, safe_execute

            # Test 1: Logger initialization
            logger = LoRAAdaptationLogger()
            logger_valid = logger.loggers is not None

            test_cases.append({
                "test_name": "Error Logger Initialization",
                "passed": logger_valid,
                "details": "Error logger initialized successfully" if logger_valid else "Error logger initialization failed"
            })

            # Test 2: Safe execution decorator
            @safe_execute(error_category="TEST_ERROR", default_return="fallback", component="test")
            async def test_function():
                return "success"

            result = await test_function()
            safe_exec_valid = result == "success"

            test_cases.append({
                "test_name": "Safe Execution Decorator",
                "passed": safe_exec_valid,
                "details": "Safe execution worked correctly" if safe_exec_valid else "Safe execution failed"
            })

            # Test 3: Error categorization
            test_error = ValueError("Test error")
            category = logger._categorize_error(test_error)
            category_valid = category is not None

            test_cases.append({
                "test_name": "Error Categorization",
                "passed": category_valid,
                "details": f"Error categorized as: {category.value if category_valid else 'None'}"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Error Handling Tests",
                "passed": False,
                "details": f"Error handling tests failed: {str(e)}"
            })

        return test_cases

    async def test_performance_optimizer(self) -> List[Dict[str, Any]]:
        """Test Performance Optimizer functionality"""
        test_cases = []

        try:
            from performance_optimizer import ResourceManager, ModelCache

            # Test 1: Resource manager initialization
            resource_manager = ResourceManager()
            manager_valid = resource_manager.model_cache is not None

            test_cases.append({
                "test_name": "Resource Manager Initialization",
                "passed": manager_valid,
                "details": "Resource manager initialized successfully" if manager_valid else "Resource manager initialization failed"
            })

            # Test 2: Model cache
            cache = ModelCache(max_size=3)
            cache.put("test_key", "test_value", 10.0)
            cached_value = cache.get("test_key")
            cache_valid = cached_value == "test_value"

            test_cases.append({
                "test_name": "Model Cache Operations",
                "passed": cache_valid,
                "details": "Model cache operations successful" if cache_valid else "Model cache operations failed"
            })

            # Test 3: Resource monitoring
            snapshot = await resource_manager.monitor_resources()
            monitoring_valid = "memory" in snapshot

            test_cases.append({
                "test_name": "Resource Monitoring",
                "passed": monitoring_valid,
                "details": "Resource monitoring successful" if monitoring_valid else "Resource monitoring failed"
            })

            # Test 4: Performance analysis
            analysis = resource_manager.get_performance_analysis(hours=1)
            analysis_valid = isinstance(analysis, dict)

            test_cases.append({
                "test_name": "Performance Analysis",
                "passed": analysis_valid,
                "details": "Performance analysis completed" if analysis_valid else "Performance analysis failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Performance Optimizer Tests",
                "passed": False,
                "details": f"Performance optimizer tests failed: {str(e)}"
            })

        return test_cases

    async def test_end_to_end_integration(self) -> List[Dict[str, Any]]:
        """Test end-to-end integration of all components"""
        test_cases = []

        try:
            # Initialize all components
            model_manager = PersonalizedModelManager()
            generator = AdaptiveResponseGenerator(model_manager)

            # Test 1: Complete agent lifecycle
            character_info = {
                "name": "Integration Test Character",
                "class": "Rogue",
                "level": 7,
                "skills": ["stealth", "perception", "deception"],
                "traits": ["cunning", "agile"]
            }

            agent_id = "integration_test_agent"
            registration_success = await model_manager.register_agent(agent_id, character_info)

            test_cases.append({
                "test_name": "Complete Agent Registration",
                "passed": registration_success,
                "details": "Agent registered successfully" if registration_success else "Agent registration failed"
            })

            # Test 2: Experience collection and learning
            experiences = [
                CharacterExperience(
                    agent_id=agent_id,
                    session_id="integration_test",
                    timestamp=datetime.now(),
                    situation="Discovered trapped treasure chest",
                    action="Carefully disarmed trap",
                    outcome="Successfully opened chest",
                    success_score=0.95,
                    reward=200.0,
                    context={"location": "dungeon", "trap_type": "poison"},
                    skills_used=["perception", "dexterity"],
                    character_class="Rogue",
                    level=7,
                    emotional_valence=0.8,
                    strategic_importance=0.9
                )
            ]

            for exp in experiences:
                await model_manager.add_experience(exp)

            experience_success = len(model_manager.experience_buffers.get(agent_id, [])) > 0

            test_cases.append({
                "test_name": "Experience Collection Integration",
                "passed": experience_success,
                "details": "Experiences collected and processed" if experience_success else "Experience collection failed"
            })

            # Test 3: Response generation integration
            context = ResponseContext(
                agent_id=agent_id,
                current_situation="You encounter a locked door with strange markings",
                game_state={"health": 85, "position": "corridor"},
                available_actions=["pick_lock", "search_for_key", "force_door", "examine_markings"],
                nearby_characters=["wizard_companion"],
                environment={"lighting": "dim", "material": "stone"},
                urgency_level=3,
                stakes="medium"
            )

            response = await generator.generate_response(context)
            response_valid = response.response_text is not None and len(response.response_text) > 0

            test_cases.append({
                "test_name": "Response Generation Integration",
                "passed": response_valid,
                "details": f"Response generated: {response.response_text[:50]}..." if response_valid else "Response generation failed"
            })

            # Test 4: Pattern analysis integration
            patterns = await generator.pattern_analyzer.analyze_agent_experiences(agent_id, experiences)
            patterns_valid = isinstance(patterns, list)

            test_cases.append({
                "test_name": "Pattern Analysis Integration",
                "passed": patterns_valid,
                "details": f"Pattern analysis found {len(patterns)} patterns" if patterns_valid else "Pattern analysis failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "End-to-End Integration Tests",
                "passed": False,
                "details": f"End-to-end integration tests failed: {str(e)}"
            })

        return test_cases

    async def test_resource_management(self) -> List[Dict[str, Any]]:
        """Test resource management capabilities"""
        test_cases = []

        try:
            from performance_optimizer import ResourceManager

            # Test 1: Resource limits enforcement
            resource_manager = ResourceManager()
            limits_valid = resource_manager.limits.max_memory_mb > 0

            test_cases.append({
                "test_name": "Resource Limits Configuration",
                "passed": limits_valid,
                "details": "Resource limits configured" if limits_valid else "Resource limits not configured"
            })

            # Test 2: Memory optimization
            initial_memory = psutil.virtual_memory().used
            await resource_manager._optimize_memory_usage()
            optimized_memory = psutil.virtual_memory().used
            memory_optimized = optimized_memory <= initial_memory * 1.05  # Allow 5% increase for overhead

            test_cases.append({
                "test_name": "Memory Optimization",
                "passed": memory_optimized,
                "details": "Memory optimization completed" if memory_optimized else "Memory optimization failed"
            })

            # Test 3: Cache management
            cache_stats_before = resource_manager.model_cache.get_stats()
            resource_manager.model_cache.clear()
            cache_stats_after = resource_manager.model_cache.get_stats()
            cache_cleared = cache_stats_after["size"] == 0

            test_cases.append({
                "test_name": "Cache Management",
                "passed": cache_cleared,
                "details": "Cache cleared successfully" if cache_cleared else "Cache clearing failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "Resource Management Tests",
                "passed": False,
                "details": f"Resource management tests failed: {str(e)}"
            })

        return test_cases

    async def test_system_health(self) -> List[Dict[str, Any]]:
        """Test system health monitoring"""
        test_cases = []

        try:
            health_checker = HealthChecker()

            # Test 1: Health checker initialization
            checker_valid = health_checker.logger is not None

            test_cases.append({
                "test_name": "Health Checker Initialization",
                "passed": checker_valid,
                "details": "Health checker initialized" if checker_valid else "Health checker initialization failed"
            })

            # Test 2: Component health check
            health_status = await health_checker.check_component_health("test_component")
            health_check_valid = isinstance(health_status, dict) and "status" in health_status

            test_cases.append({
                "test_name": "Component Health Check",
                "passed": health_check_valid,
                "details": f"Component health status: {health_status.get('status', 'unknown')}" if health_check_valid else "Health check failed"
            })

            # Test 3: System health overview
            system_health = await health_checker.get_system_health()
            system_health_valid = isinstance(system_health, dict) and "overall_status" in system_health

            test_cases.append({
                "test_name": "System Health Overview",
                "passed": system_health_valid,
                "details": f"System status: {system_health.get('overall_status', 'unknown')}" if system_health_valid else "System health check failed"
            })

        except Exception as e:
            test_cases.append({
                "test_name": "System Health Tests",
                "passed": False,
                "details": f"System health tests failed: {str(e)}"
            })

        return test_cases

    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics during tests"""
        try:
            import psutil

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "system_resources": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent
                },
                "test_duration_ms": 0,  # Would be calculated in real implementation
                "memory_peak_mb": psutil.virtual_memory().used / 1024 / 1024
            }

            return metrics

        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Main execution for running tests
async def run_integration_tests():
    """Run integration tests and save results"""
    test_runner = TestLoRAAdaptationSystem()
    results = await test_runner.run_all_tests()

    # Save results to file
    results_file = Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Integration tests completed. Results saved to {results_file}")
    print(f"Overall success rate: {results.get('success_rate', 0):.1%}")

    return results

if __name__ == "__main__":
    asyncio.run(run_integration_tests())