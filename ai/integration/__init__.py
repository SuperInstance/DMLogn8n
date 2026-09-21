#!/usr/bin/env python3
"""
Advanced AI Integration System - Complete AI orchestration platform
Integrates all AI components for ultra-fast, intelligent, and cost-effective AI interactions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .model_manager import ModelManager, ModelRequest, ModelResponse
from .inference_optimizer import InferenceOptimizer, InferenceRequest, InferenceResponse
from .model_cache import ModelCache, CacheConfig
from .ensemble_ai import AIEnsemble, EnsembleRequest, EnsembleResponse
from .custom_trainer import CustomTrainer, TrainingConfig
from .model_monitor import ModelMonitor, MonitoringConfig, AlertSeverity
from .prompt_optimizer import PromptOptimizer, OptimizationConfig
from .ai_load_balancer import AILoadBalancer, LoadBalancingConfig, Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIIntegrationConfig:
    """Configuration for the complete AI integration system"""
    # Component configurations
    cache_config: Optional[CacheConfig] = None
    monitoring_config: Optional[MonitoringConfig] = None
    load_balancer_config: Optional[LoadBalancingConfig] = None
    optimization_config: Optional[OptimizationConfig] = None

    # System settings
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_load_balancing: bool = True
    enable_ensemble: bool = True
    enable_optimization: bool = True

    # Performance targets
    target_response_time: float = 0.5  # 500ms
    target_quality_score: float = 0.8
    max_cost_per_request: float = 0.1

class AdvancedAIIntegration:
    """Complete AI integration system with all components"""

    def __init__(self, config: Optional[AIIntegrationConfig] = None):
        self.config = config or AIIntegrationConfig()

        # Initialize components
        self.model_manager = ModelManager()
        self.inference_optimizer = InferenceOptimizer()
        self.prompt_optimizer = PromptOptimizer()
        self.custom_trainer = CustomTrainer()
        self.ensemble_ai = AIEnsemble()

        # Conditionally initialize components
        self.cache: Optional[ModelCache] = None
        self.monitor: Optional[ModelMonitor] = None
        self.load_balancer: Optional[AILoadBalancer] = None

        if self.config.enable_caching:
            self.cache = ModelCache(self.config.cache_config)

        if self.config.enable_monitoring:
            self.monitor = ModelMonitor(self.config.monitoring_config or MonitoringConfig(
                models=["gpt-4", "claude-3", "gpt-3.5-turbo"]
            ))

        if self.config.enable_load_balancing:
            self.load_balancer = AILoadBalancer(
                self.config.load_balancer_config or LoadBalancingConfig(
                    providers=[]  # Will be populated from model manager
                )
            )

        # System state
        self.initialized = False
        self.startup_time = datetime.now()

        logger.info("Advanced AI Integration System initialized")

    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize model manager
            await self.model_manager.initialize()

            # Initialize cache
            if self.cache:
                logger.info("Cache system ready")

            # Start monitoring
            if self.monitor:
                await self.monitor.start_monitoring()
                logger.info("Monitoring system active")

            # Start load balancer
            if self.load_balancer:
                await self.load_balancer.start()
                logger.info("Load balancer active")

            self.initialized = True
            logger.info("AI Integration System fully initialized")

        except Exception as e:
            logger.error(f"Failed to initialize AI Integration System: {e}")
            raise

    async def process_request(self, prompt: str, model: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None,
                            optimize_prompt: bool = True,
                            use_ensemble: bool = False,
                            cache_result: bool = True) -> Dict[str, Any]:
        """
        Process an AI request with full optimization pipeline
        """
        if not self.initialized:
            await self.initialize()

        start_time = datetime.now()

        try:
            # Step 1: Optimize prompt
            if optimize_prompt and self.config.enable_optimization:
                optimized_prompt = await self.prompt_optimizer.optimize_prompt(
                    prompt, self._determine_task_type(prompt), context
                )
            else:
                optimized_prompt = prompt

            # Step 2: Check cache
            cache_key = None
            cached_response = None
            if self.cache and cache_result:
                cache_key = self.cache.generate_cache_key(model or "default", optimized_prompt)
                cached_response = await self.cache.get(cache_key)

            if cached_response:
                # Return cached result
                result = {
                    "content": cached_response,
                    "model": "cached",
                    "response_time": 0.001,
                    "cost": 0.0,
                    "quality_score": 0.9,
                    "cached": True,
                    "optimized_prompt": optimized_prompt if optimize_prompt else prompt
                }

                if self.monitor:
                    await self.monitor.record_request(
                        model=model or "cached",
                        response_time=result["response_time"],
                        quality_score=result["quality_score"],
                        success=True,
                        token_usage=len(optimized_prompt.split()),
                        cost=result["cost"]
                    )

                return result

            # Step 3: Determine processing strategy
            if use_ensemble and self.config.enable_ensemble:
                result = await self._process_with_ensemble(optimized_prompt, model, context)
            else:
                result = await self._process_single_model(optimized_prompt, model, context)

            # Step 4: Cache result
            if self.cache and cache_result and cache_key:
                await self.cache.set(cache_key, result["content"])

            # Step 5: Record metrics
            if self.monitor:
                await self.monitor.record_request(
                    model=result["model"],
                    response_time=result["response_time"],
                    quality_score=result["quality_score"],
                    success=result.get("success", True),
                    token_usage=result.get("token_usage", 0),
                    cost=result["cost"],
                    user_feedback=context.get("user_feedback") if context else None
                )

            # Add optimization metadata
            result["optimized_prompt"] = optimized_prompt if optimize_prompt else prompt
            result["processing_time"] = (datetime.now() - start_time).total_seconds()

            return result

        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return {
                "content": None,
                "model": model or "unknown",
                "error": str(e),
                "response_time": (datetime.now() - start_time).total_seconds(),
                "success": False
            }

    async def _process_single_model(self, prompt: str, model: Optional[str],
                                  context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Process request with single model"""
        # Select best model if not specified
        if not model:
            model = await self.model_manager.select_best_model(
                ModelRequest(prompt=prompt, model_type=self._determine_task_type(prompt))
            )

        # Create and execute request
        request = ModelRequest(
            prompt=prompt,
            model_type=self._determine_task_type(prompt),
            context=context
        )

        response = await self.model_manager.execute_request(request)

        return {
            "content": response.content,
            "model": response.model_name,
            "response_time": response.response_time,
            "cost": response.cost,
            "quality_score": response.quality_score or 0.8,
            "token_usage": response.token_usage.get("total", 0),
            "metadata": response.metadata
        }

    async def _process_with_ensemble(self, prompt: str, model: Optional[str],
                                   context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Process request with ensemble methods"""
        # Create ensemble request
        ensemble_request = EnsembleRequest(
            prompt=prompt,
            task_type=self._determine_task_type(prompt),
            max_responses=3,
            context=context
        )

        # Execute ensemble
        response = await self.ensemble_ai.process_request(ensemble_request)

        return {
            "content": response.content,
            "model": f"ensemble({response.method.value})",
            "response_time": response.processing_time,
            "cost": response.cost,
            "quality_score": response.confidence,
            "token_usage": sum(r.token_usage for r in response.individual_responses),
            "contributing_models": response.contributing_models,
            "consensus_score": response.consensus_score,
            "diversity_score": response.diversity_score,
            "metadata": response.metadata
        }

    def _determine_task_type(self, prompt: str):
        """Determine task type from prompt"""
        from .model_manager import ModelType
        from .ensemble_ai import TaskType

        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ["?", "what", "how", "why", "explain"]):
            if hasattr(ModelType, 'CHAT'):
                return ModelType.CHAT
            else:
                return TaskType.QUESTION_ANSWERING

        elif any(word in prompt_lower for word in ["summarize", "summary"]):
            if hasattr(ModelType, 'ANALYSIS'):
                return ModelType.ANALYSIS
            else:
                return TaskType.SUMMARIZATION

        elif any(word in prompt_lower for word in ["translate", "translation"]):
            if hasattr(ModelType, 'ANALYSIS'):
                return ModelType.ANALYSIS
            else:
                return TaskType.TRANSLATION

        elif any(word in prompt_lower for word in ["code", "function", "program"]):
            if hasattr(ModelType, 'CODE_GENERATION'):
                return ModelType.CODE_GENERATION
            else:
                return TaskType.CODE_GENERATION

        else:
            if hasattr(ModelType, 'CHAT'):
                return ModelType.CHAT
            else:
                return TaskType.TEXT_GENERATION

    async def batch_process(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple requests in parallel"""
        tasks = [
            self.process_request(
                prompt=req.get("prompt", ""),
                model=req.get("model"),
                context=req.get("context"),
                optimize_prompt=req.get("optimize_prompt", True),
                use_ensemble=req.get("use_ensemble", False),
                cache_result=req.get("cache_result", True)
            )
            for req in requests
        ]

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def train_custom_model(self, base_model: str, training_data: List[str],
                               task_type: str, output_dir: str) -> str:
        """Train a custom model"""
        if not self.initialized:
            await self.initialize()

        # Determine task type
        from .custom_trainer import TaskType
        task_enum = TaskType(task_type) if any(task_type == t.value for t in TaskType) else TaskType.CUSTOM_TASK

        # Use fine-tuning with examples
        examples = [
            {"prompt": training_data[i], "response": training_data[i + 1] if i + 1 < len(training_data) else ""}
            for i in range(0, len(training_data), 2)
        ]

        job_id = await self.custom_trainer.fine_tune_with_examples(
            base_model=base_model,
            examples=examples,
            task_type=task_enum,
            output_dir=output_dir
        )

        return job_id

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "initialized": self.initialized,
            "uptime": (datetime.now() - self.startup_time).total_seconds(),
            "components": {}
        }

        # Model manager status
        status["components"]["model_manager"] = {
            "models_available": len(self.model_manager.models),
            "model_stats": self.model_manager.get_model_stats()
        }

        # Cache status
        if self.cache:
            cache_stats = self.cache.get_stats()
            status["components"]["cache"] = {
                "enabled": True,
                "hit_rate": cache_stats.hit_rate,
                "entries_count": cache_stats.entries_count,
                "memory_usage_mb": cache_stats.memory_usage_mb
            }
        else:
            status["components"]["cache"] = {"enabled": False}

        # Monitor status
        if self.monitor:
            monitor_stats = self.monitor.get_statistics()
            status["components"]["monitor"] = {
                "enabled": True,
                "total_requests": monitor_stats["total_requests"],
                "average_response_time": monitor_stats["average_response_time"],
                "error_rate": monitor_stats["total_errors"] / monitor_stats["total_requests"] if monitor_stats["total_requests"] > 0 else 0,
                "active_alerts": monitor_stats["active_alerts"]
            }
        else:
            status["components"]["monitor"] = {"enabled": False}

        # Load balancer status
        if self.load_balancer:
            lb_stats = self.load_balancer.get_performance_stats()
            status["components"]["load_balancer"] = {
                "enabled": True,
                "total_requests": lb_stats["total_requests"],
                "success_rate": lb_stats["success_rate"],
                "healthy_providers": lb_stats["healthy_providers"]
            }
        else:
            status["components"]["load_balancer"] = {"enabled": False}

        # Ensemble status
        status["components"]["ensemble"] = {
            "enabled": self.config.enable_ensemble,
            "stats": self.ensemble_ai.get_ensemble_stats()
        }

        # Optimizer status
        status["components"]["optimizer"] = {
            "enabled": self.config.enable_optimization,
            "insights": self.prompt_optimizer.get_optimization_insights()
        }

        return status

    async def generate_report(self, include_recommendations: bool = True) -> Dict[str, Any]:
        """Generate comprehensive system report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_status": await self.get_system_status(),
            "performance_metrics": {}
        }

        # Add detailed metrics from monitoring
        if self.monitor:
            report["monitoring_report"] = await self.monitor.generate_report()

        # Add cost analysis from load balancer
        if self.load_balancer:
            report["cost_analysis"] = self.load_balancer.get_cost_analysis()

        # Add optimization insights
        if self.config.enable_optimization:
            report["optimization_report"] = await self.prompt_optimizer.generate_optimization_report()

        # Add training history
        report["training_history"] = self.custom_trainer.get_training_history()

        # Add recommendations
        if include_recommendations:
            report["recommendations"] = await self._generate_recommendations()

        return report

    async def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate system optimization recommendations"""
        recommendations = []

        # Performance recommendations
        system_status = await self.get_system_status()

        if system_status["components"]["model_manager"]["model_stats"]:
            avg_response_time = np.mean([
                stats.get("average_response_time", 0) for stats in
                system_status["components"]["model_manager"]["model_stats"].values()
            ])

            if avg_response_time > self.config.target_response_time:
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "High Response Time Detected",
                    "description": f"Average response time ({avg_response_time:.3f}s) exceeds target ({self.config.target_response_time:.3f}s)",
                    "suggestion": "Consider enabling more aggressive caching or using faster models"
                })

        # Cache recommendations
        if self.cache:
            cache_stats = self.cache.get_stats()
            if cache_stats.hit_rate < 0.5:
                recommendations.append({
                    "type": "caching",
                    "priority": "medium",
                    "title": "Low Cache Hit Rate",
                    "description": f"Cache hit rate ({cache_stats.hit_rate:.1%}) is below optimal",
                    "suggestion": "Consider increasing cache size or adjusting cache TTL settings"
                })

        # Cost recommendations
        if self.load_balancer:
            cost_analysis = self.load_balancer.get_cost_analysis()
            if cost_analysis.get("estimated_savings", 0) < 0.1:
                recommendations.append({
                    "type": "cost",
                    "priority": "medium",
                    "title": "Cost Optimization Opportunity",
                    "description": "Potential cost savings through better provider selection",
                    "suggestion": "Enable cost-optimized load balancing strategy"
                })

        # Quality recommendations
        if self.monitor:
            monitor_stats = self.monitor.get_statistics()
            if monitor_stats.get("average_confidence", 1.0) < self.config.target_quality_score:
                recommendations.append({
                    "type": "quality",
                    "priority": "high",
                    "title": "Quality Score Below Target",
                    "description": f"Average quality score ({monitor_stats.get('average_confidence', 0):.2f}) below target ({self.config.target_quality_score:.2f})",
                    "suggestion": "Consider using ensemble methods or higher quality models"
                })

        return recommendations

    async def health_check(self) -> Dict[str, bool]:
        """Perform comprehensive health check"""
        health_status = {
            "model_manager": True,
            "inference_optimizer": True,
            "cache": True,
            "monitor": True,
            "load_balancer": True,
            "ensemble": True,
            "trainer": True,
            "optimizer": True
        }

        # Check individual components
        if self.model_manager:
            try:
                model_health = await self.model_manager.health_check()
                health_status["model_manager"] = all(model_health.values())
            except:
                health_status["model_manager"] = False

        if self.cache:
            try:
                cache_health = await self.cache.health_check()
                health_status["cache"] = all(cache_health.values())
            except:
                health_status["cache"] = False

        if self.monitor:
            try:
                monitor_health = self.monitor.get_health_status()
                health_status["monitor"] = all(
                    status.status == "healthy" for status in monitor_health.values()
                )
            except:
                health_status["monitor"] = False

        return health_status

    async def shutdown(self):
        """Shutdown all components"""
        logger.info("Shutting down AI Integration System...")

        # Shutdown components
        if self.load_balancer:
            await self.load_balancer.stop()

        if self.monitor:
            await self.monitor.shutdown()

        if self.cache:
            await self.cache.shutdown()

        await self.model_manager.shutdown()
        await self.custom_trainer.shutdown()

        logger.info("AI Integration System shutdown complete")

# Convenience functions for easy usage
async def quick_ai_response(prompt: str, model: Optional[str] = None) -> str:
    """Quick AI response with default settings"""
    integration = AdvancedAIIntegration()
    await integration.initialize()

    try:
        result = await integration.process_request(prompt, model=model)
        return result.get("content", "No response generated")
    finally:
        await integration.shutdown()

async def batch_ai_responses(prompts: List[str], model: Optional[str] = None) -> List[str]:
    """Batch AI responses"""
    integration = AdvancedAIIntegration()
    await integration.initialize()

    try:
        requests = [{"prompt": prompt, "model": model} for prompt in prompts]
        results = await integration.batch_process(requests)
        return [result.get("content", "No response") for result in results]
    finally:
        await integration.shutdown()

# Export main classes
__all__ = [
    'AdvancedAIIntegration',
    'AIIntegrationConfig',
    'ModelManager',
    'InferenceOptimizer',
    'ModelCache',
    'AIEnsemble',
    'CustomTrainer',
    'ModelMonitor',
    'PromptOptimizer',
    'AILoadBalancer',
    'quick_ai_response',
    'batch_ai_responses'
]