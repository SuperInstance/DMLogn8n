#!/usr/bin/env python3
"""
Personalized Model Manager for D&D Agent LoRA Adapters
Manages character-specific LoRA adapters and model lifecycle
"""

import json
import logging
import asyncio
import psutil
import gc
import torch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from threading import Lock
from collections import defaultdict, OrderedDict
import hashlib
import pickle

# Import from our modules
from agent_dnd_lora_trainer import LoRATrainer, CharacterExperience, LoRAConfig
from strategic_pattern_analyzer import StrategicPatternAnalyzer, StrategicPattern

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs/model_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AgentProfile:
    """Profile information for an agent character"""
    agent_id: str
    character_name: str
    character_class: str
    level: int
    skills: List[str]
    personality_traits: List[str]
    playstyle: str  # "aggressive", "defensive", "strategic", "social"
    created_at: datetime
    last_active: datetime
    total_experiences: int
    adaptation_version: int

@dataclass
class ModelMetadata:
    """Metadata for a LoRA adapter"""
    adapter_path: str
    model_name: str
    created_at: datetime
    last_updated: datetime
    training_examples: int
    performance_score: float
    file_size_mb: float
    checksum: str
    version: int

@dataclass
class ResourceUsage:
    """System resource usage tracking"""
    memory_usage_mb: float
    gpu_memory_usage_mb: float
    cpu_usage_percent: float
    active_models: int
    cached_models: int
    disk_usage_mb: float

class PersonalizedModelManager:
    """
    Manages personalized LoRA adapters for D&D agents with efficient resource handling
    """

    def __init__(self, base_model_name: str = "microsoft/DialoGPT-medium",
                 max_cache_size: int = 5, max_memory_mb: int = 4096):
        self.base_model_name = base_model_name
        self.max_cache_size = max_cache_size
        self.max_memory_mb = max_memory_mb

        # Core components
        self.lora_trainer = LoRATrainer(base_model_name)
        self.pattern_analyzer = StrategicPatternAnalyzer()

        # Storage systems
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}
        self.active_models: OrderedDict = OrderedDict()  # LRU cache for active models
        self.model_cache: Dict[str, Tuple[Any, Any]] = {}  # agent_id -> (model, tokenizer)
        self.experience_buffers: Dict[str, List[CharacterExperience]] = defaultdict(list)

        # Resource management
        self.cache_lock = Lock()
        self.resource_monitor_active = False
        self.last_cleanup = datetime.now()

        # Performance tracking
        self.usage_stats: Dict[str, Dict] = defaultdict(lambda: {
            "requests": 0,
            "avg_response_time": 0.0,
            "last_used": None,
            "cache_hits": 0,
            "cache_misses": 0
        })

        # Ensure directories exist
        self._ensure_directories()

        # Load existing data
        self._load_existing_data()

        # Start resource monitoring
        self._start_resource_monitoring()

        logger.info("Personalized Model Manager initialized")

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents",
            "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models/adapters",
            "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models/cache",
            "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs",
            "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/backups"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _load_existing_data(self):
        """Load existing agent profiles and metadata"""
        try:
            # Load agent profiles
            profiles_file = "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents/agent_profiles.json"
            if Path(profiles_file).exists():
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    for agent_id, profile_data in data.items():
                        profile_data['created_at'] = datetime.fromisoformat(profile_data['created_at'])
                        profile_data['last_active'] = datetime.fromisoformat(profile_data['last_active'])
                        self.agent_profiles[agent_id] = AgentProfile(**profile_data)

            # Load model metadata
            metadata_file = "/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents/model_metadata.json"
            if Path(metadata_file).exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    for agent_id, metadata_data in data.items():
                        metadata_data['created_at'] = datetime.fromisoformat(metadata_data['created_at'])
                        metadata_data['last_updated'] = datetime.fromisoformat(metadata_data['last_updated'])
                        self.model_metadata[agent_id] = ModelMetadata(**metadata_data)

            logger.info(f"Loaded {len(self.agent_profiles)} agent profiles and {len(self.model_metadata)} model metadata")

        except Exception as e:
            logger.error(f"Failed to load existing data: {str(e)}")

    async def register_agent(self, agent_id: str, character_info: Dict[str, Any]) -> bool:
        """
        Register a new agent and initialize their personalized model

        Args:
            agent_id: Unique agent identifier
            character_info: Character details (class, level, skills, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Registering new agent: {agent_id}")

            # Check if agent already exists
            if agent_id in self.agent_profiles:
                logger.warning(f"Agent {agent_id} already exists, updating profile")
                await self.update_agent_profile(agent_id, character_info)
                return True

            # Create agent profile
            profile = AgentProfile(
                agent_id=agent_id,
                character_name=character_info.get("name", "Unknown"),
                character_class=character_info.get("class", "Fighter"),
                level=character_info.get("level", 1),
                skills=character_info.get("skills", []),
                personality_traits=character_info.get("traits", []),
                playstyle=self._determine_playstyle(character_info),
                created_at=datetime.now(),
                last_active=datetime.now(),
                total_experiences=0,
                adaptation_version=1
            )

            self.agent_profiles[agent_id] = profile

            # Initialize LoRA adapter
            adapter_path = await self.lora_trainer.initialize_agent_lora(agent_id, character_info)

            # Create model metadata
            metadata = ModelMetadata(
                adapter_path=adapter_path,
                model_name=self.base_model_name,
                created_at=datetime.now(),
                last_updated=datetime.now(),
                training_examples=0,
                performance_score=0.5,
                file_size_mb=self._calculate_directory_size(adapter_path),
                checksum=self._calculate_checksum(adapter_path),
                version=1
            )

            self.model_metadata[agent_id] = metadata

            # Save data
            await self._save_agent_data()

            logger.info(f"Successfully registered agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False

    async def update_agent_profile(self, agent_id: str, character_info: Dict[str, Any]) -> bool:
        """Update an existing agent's profile"""
        try:
            if agent_id not in self.agent_profiles:
                logger.error(f"Agent {agent_id} not found")
                return False

            profile = self.agent_profiles[agent_id]

            # Update fields
            profile.character_name = character_info.get("name", profile.character_name)
            profile.character_class = character_info.get("class", profile.character_class)
            profile.level = character_info.get("level", profile.level)
            profile.skills = character_info.get("skills", profile.skills)
            profile.personality_traits = character_info.get("traits", profile.personality_traits)
            profile.playstyle = self._determine_playstyle(character_info)
            profile.last_active = datetime.now()

            # Save updated profile
            await self._save_agent_data()

            logger.info(f"Updated profile for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update agent profile {agent_id}: {str(e)}")
            return False

    async def add_experience(self, experience: CharacterExperience) -> bool:
        """
        Add a new experience for an agent and trigger learning if needed

        Args:
            experience: Character experience data

        Returns:
            True if successful, False otherwise
        """
        try:
            agent_id = experience.agent_id

            if agent_id not in self.agent_profiles:
                logger.error(f"Agent {agent_id} not registered")
                return False

            # Add to experience buffer
            self.experience_buffers[agent_id].append(experience)

            # Update profile
            self.agent_profiles[agent_id].total_experiences += 1
            self.agent_profiles[agent_id].last_active = datetime.now()

            # Collect experience for LoRA training
            await self.lora_trainer.collect_experience(experience)

            # Check if we should trigger pattern analysis
            if len(self.experience_buffers[agent_id]) >= 20:
                await self._trigger_pattern_analysis(agent_id)

            # Save updated data
            await self._save_agent_data()

            logger.debug(f"Added experience for agent {agent_id}. Total: {self.agent_profiles[agent_id].total_experiences}")
            return True

        except Exception as e:
            logger.error(f"Failed to add experience for agent {experience.agent_id}: {str(e)}")
            return False

    async def generate_response(self, agent_id: str, prompt: str,
                              max_length: int = 150, use_patterns: bool = True) -> str:
        """
        Generate a response using the agent's personalized model

        Args:
            agent_id: Agent identifier
            prompt: Input prompt
            max_length: Maximum response length
            use_patterns: Whether to use strategic pattern enhancement

        Returns:
            Generated response
        """
        try:
            start_time = datetime.now()

            # Update usage stats
            self.usage_stats[agent_id]["requests"] += 1
            self.usage_stats[agent_id]["last_used"] = datetime.now()

            # Check if agent exists
            if agent_id not in self.agent_profiles:
                logger.error(f"Agent {agent_id} not found")
                return "I'm not ready to respond yet..."

            # Enhance prompt with strategic patterns if requested
            if use_patterns:
                enhanced_prompt = await self._enhance_prompt_with_patterns(agent_id, prompt)
            else:
                enhanced_prompt = prompt

            # Generate response using LoRA trainer
            response = await self.lora_trainer.generate_response(
                agent_id, enhanced_prompt, max_length
            )

            # Update performance metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_metrics(agent_id, response_time)

            return response

        except Exception as e:
            logger.error(f"Failed to generate response for agent {agent_id}: {str(e)}")
            return "I need a moment to think about this..."

    async def _enhance_prompt_with_patterns(self, agent_id: str, base_prompt: str) -> str:
        """Enhance prompt with strategic pattern insights"""
        try:
            # Get recent patterns for the agent
            patterns = self.pattern_analyzer.pattern_cache.get(agent_id, [])

            if not patterns:
                return base_prompt

            # Get agent profile
            profile = self.agent_profiles[agent_id]

            # Get strategy recommendations
            recommendations = await self.pattern_analyzer.get_strategy_recommendations(
                agent_id, base_prompt, {
                    "class": profile.character_class,
                    "level": profile.level,
                    "skills": profile.skills
                }
            )

            if recommendations:
                # Add top recommendation to prompt
                top_rec = recommendations[0]
                enhanced_prompt = f"""
                {base_prompt}

                Strategic context: {top_rec.recommended_strategy}
                Consider this approach based on past experience.
                """
                return enhanced_prompt.strip()

            return base_prompt

        except Exception as e:
            logger.error(f"Failed to enhance prompt with patterns: {str(e)}")
            return base_prompt

    async def _trigger_pattern_analysis(self, agent_id: str):
        """Trigger strategic pattern analysis for accumulated experiences"""
        try:
            experiences = self.experience_buffers[agent_id][-50:]  # Analyze last 50 experiences

            if len(experiences) >= 10:
                patterns = await self.pattern_analyzer.analyze_agent_experiences(agent_id, experiences)

                if patterns:
                    logger.info(f"Discovered {len(patterns)} new patterns for agent {agent_id}")

                    # Clear analyzed experiences from buffer
                    self.experience_buffers[agent_id] = self.experience_buffers[agent_id][25:]

        except Exception as e:
            logger.error(f"Failed to trigger pattern analysis for agent {agent_id}: {str(e)}")

    async def train_agent_model(self, agent_id: str, force: bool = False) -> bool:
        """
        Trigger LoRA training for an agent

        Args:
            agent_id: Agent identifier
            force: Force training even if conditions aren't met

        Returns:
            True if training was triggered, False otherwise
        """
        try:
            if agent_id not in self.agent_profiles:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Check training conditions
            training_data_size = len(self.lora_trainer.training_data.get(agent_id, []))

            if not force and training_data_size < 50:
                logger.info(f"Insufficient training data for agent {agent_id}: {training_data_size}")
                return False

            # Trigger training
            await self.lora_trainer.train_agent_lora(agent_id)

            # Update metadata
            if agent_id in self.model_metadata:
                self.model_metadata[agent_id].last_updated = datetime.now()
                self.model_metadata[agent_id].training_examples += training_data_size

            # Save updated metadata
            await self._save_agent_data()

            logger.info(f"Triggered LoRA training for agent {agent_id} with {training_data_size} examples")
            return True

        except Exception as e:
            logger.error(f"Failed to train agent model {agent_id}: {str(e)}")
            return False

    async def cleanup_agent(self, agent_id: str, backup: bool = True) -> bool:
        """
        Clean up agent resources and optionally create backup

        Args:
            agent_id: Agent identifier
            backup: Whether to create backup before cleanup

        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_id not in self.agent_profiles:
                logger.error(f"Agent {agent_id} not found")
                return False

            logger.info(f"Cleaning up agent {agent_id}")

            # Create backup if requested
            if backup:
                await self._create_agent_backup(agent_id)

            # Train any remaining data
            await self.train_agent_model(agent_id, force=True)

            # Clear model cache
            if agent_id in self.model_cache:
                with self.cache_lock:
                    del self.model_cache[agent_id]

            # Clear from active models
            if agent_id in self.active_models:
                del self.active_models[agent_id]

            # Cleanup LoRA trainer resources
            await self.lora_trainer.cleanup_agent(agent_id)

            # Clear experience buffer
            if agent_id in self.experience_buffers:
                del self.experience_buffers[agent_id]

            # Clear usage stats
            if agent_id in self.usage_stats:
                del self.usage_stats[agent_id]

            logger.info(f"Successfully cleaned up agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup agent {agent_id}: {str(e)}")
            return False

    async def _create_agent_backup(self, agent_id: str):
        """Create backup of agent data"""
        try:
            backup_dir = f"/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/backups/{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            Path(backup_dir).mkdir(parents=True, exist_ok=True)

            # Backup profile
            if agent_id in self.agent_profiles:
                with open(f"{backup_dir}/profile.json", 'w') as f:
                    json.dump(asdict(self.agent_profiles[agent_id]), f, indent=2, default=str)

            # Backup metadata
            if agent_id in self.model_metadata:
                with open(f"{backup_dir}/metadata.json", 'w') as f:
                    json.dump(asdict(self.model_metadata[agent_id]), f, indent=2, default=str)

            # Backup model adapter
            if agent_id in self.model_metadata:
                adapter_path = self.model_metadata[agent_id].adapter_path
                if Path(adapter_path).exists():
                    import shutil
                    shutil.copytree(adapter_path, f"{backup_dir}/adapter")

            # Backup experiences
            if agent_id in self.experience_buffers:
                experiences_data = [asdict(exp) for exp in self.experience_buffers[agent_id]]
                with open(f"{backup_dir}/experiences.json", 'w') as f:
                    json.dump(experiences_data, f, indent=2, default=str)

            logger.info(f"Created backup for agent {agent_id} at {backup_dir}")

        except Exception as e:
            logger.error(f"Failed to create backup for agent {agent_id}: {str(e)}")

    def _determine_playstyle(self, character_info: Dict[str, Any]) -> str:
        """Determine agent's playstyle from character information"""
        traits = [trait.lower() for trait in character_info.get("traits", [])]
        character_class = character_info.get("class", "").lower()

        # Analyze traits and class to determine playstyle
        if any(trait in traits for trait in ["aggressive", "brave", "reckless", "bold"]) or character_class in ["barbarian", "fighter"]:
            return "aggressive"
        elif any(trait in traits for trait in ["cautious", "defensive", "wise", "patient"]) or character_class in ["cleric", "paladin"]:
            return "defensive"
        elif any(trait in traits for trait in ["strategic", "intelligent", "cunning", "analytical"]) or character_class in ["wizard", "artificer"]:
            return "strategic"
        elif any(trait in traits for trait in ["charismatic", "friendly", "deceptive", "persuasive"]) or character_class in ["bard", "rogue"]:
            return "social"
        else:
            return "balanced"

    def _calculate_directory_size(self, path: str) -> float:
        """Calculate directory size in MB"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in Path(path).walk():
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0.0

    def _calculate_checksum(self, path: str) -> str:
        """Calculate checksum for directory contents"""
        try:
            hash_md5 = hashlib.md5()
            for file_path in sorted(Path(path).rglob('*')):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _update_performance_metrics(self, agent_id: str, response_time: float):
        """Update performance metrics for an agent"""
        stats = self.usage_stats[agent_id]

        # Update average response time
        current_avg = stats["avg_response_time"]
        requests = stats["requests"]
        stats["avg_response_time"] = ((current_avg * (requests - 1)) + response_time) / requests

    async def _save_agent_data(self):
        """Save agent profiles and metadata to disk"""
        try:
            # Save profiles
            profiles_data = {}
            for agent_id, profile in self.agent_profiles.items():
                profiles_data[agent_id] = asdict(profile)

            with open("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents/agent_profiles.json", 'w') as f:
                json.dump(profiles_data, f, indent=2, default=str)

            # Save metadata
            metadata_data = {}
            for agent_id, metadata in self.model_metadata.items():
                metadata_data[agent_id] = asdict(metadata)

            with open("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents/model_metadata.json", 'w') as f:
                json.dump(metadata_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save agent data: {str(e)}")

    def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        self.resource_monitor_active = True
        # In a real implementation, this would start a background thread
        # For now, we'll call it manually when needed

    async def get_resource_usage(self) -> ResourceUsage:
        """Get current system resource usage"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_mb = memory.used / (1024 * 1024)

            # GPU memory usage (if available)
            gpu_memory_usage_mb = 0
            if torch.cuda.is_available():
                gpu_memory_usage_mb = torch.cuda.memory_allocated() / (1024 * 1024)

            # CPU usage
            cpu_usage_percent = psutil.cpu_percent(interval=1)

            # Active and cached models
            active_models = len(self.active_models)
            cached_models = len(self.model_cache)

            # Disk usage
            disk_usage = psutil.disk_usage('/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation')
            disk_usage_mb = disk_usage.used / (1024 * 1024)

            return ResourceUsage(
                memory_usage_mb=memory_usage_mb,
                gpu_memory_usage_mb=gpu_memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                active_models=active_models,
                cached_models=cached_models,
                disk_usage_mb=disk_usage_mb
            )

        except Exception as e:
            logger.error(f"Failed to get resource usage: {str(e)}")
            return ResourceUsage(0, 0, 0, 0, 0, 0)

    async def perform_maintenance(self) -> Dict[str, Any]:
        """Perform routine maintenance tasks"""
        try:
            maintenance_results = {
                "timestamp": datetime.now().isoformat(),
                "actions_performed": [],
                "resources_freed": {},
                "errors": []
            }

            # Cleanup old backups
            await self._cleanup_old_backups(maintenance_results)

            # Clear inactive models from cache
            await self._cleanup_model_cache(maintenance_results)

            # Garbage collection
            collected = gc.collect()
            maintenance_results["actions_performed"].append(f"Garbage collection freed {collected} objects")

            # Update last cleanup time
            self.last_cleanup = datetime.now()

            return maintenance_results

        except Exception as e:
            logger.error(f"Maintenance failed: {str(e)}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _cleanup_old_backups(self, results: Dict[str, Any]):
        """Clean up old backup files"""
        try:
            backup_dir = Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/backups")
            if not backup_dir.exists():
                return

            # Remove backups older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            removed_count = 0

            for backup_path in backup_dir.iterdir():
                if backup_path.is_dir():
                    # Extract date from directory name
                    try:
                        date_str = backup_path.name.split('_')[-2] + '_' + backup_path.name.split('_')[-1]
                        backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')

                        if backup_date < cutoff_date:
                            import shutil
                            shutil.rmtree(backup_path)
                            removed_count += 1
                    except (ValueError, IndexError):
                        # If we can't parse the date, skip
                        continue

            results["actions_performed"].append(f"Removed {removed_count} old backups")
            results["resources_freed"]["backups"] = removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {str(e)}")
            results["errors"].append(f"Backup cleanup failed: {str(e)}")

    async def _cleanup_model_cache(self, results: Dict[str, Any]):
        """Clean up inactive models from cache"""
        try:
            with self.cache_lock:
                cutoff_time = datetime.now() - timedelta(hours=1)
                removed_count = 0

                # Remove models not used in the last hour
                to_remove = []
                for agent_id, stats in self.usage_stats.items():
                    if (stats["last_used"] and stats["last_used"] < cutoff_time
                        and agent_id in self.model_cache):
                        to_remove.append(agent_id)

                for agent_id in to_remove:
                    del self.model_cache[agent_id]
                    removed_count += 1

                results["actions_performed"].append(f"Removed {removed_count} inactive models from cache")
                results["resources_freed"]["cached_models"] = removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup model cache: {str(e)}")
            results["errors"].append(f"Model cache cleanup failed: {str(e)}")

    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive summary of an agent"""
        try:
            if agent_id not in self.agent_profiles:
                return {"error": "Agent not found"}

            profile = self.agent_profiles[agent_id]
            metadata = self.model_metadata.get(agent_id)
            usage_stats = self.usage_stats.get(agent_id, {})
            pattern_summary = self.pattern_analyzer.get_pattern_summary(agent_id)

            summary = {
                "profile": asdict(profile),
                "model_metadata": asdict(metadata) if metadata else None,
                "usage_stats": dict(usage_stats),
                "pattern_summary": pattern_summary,
                "experience_buffer_size": len(self.experience_buffers.get(agent_id, [])),
                "training_data_size": len(self.lora_trainer.training_data.get(agent_id, [])),
                "model_cached": agent_id in self.model_cache,
                "last_analyzed": datetime.now().isoformat()
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get agent summary for {agent_id}: {str(e)}")
            return {"error": str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "registered_agents": len(self.agent_profiles),
                "active_models": len(self.active_models),
                "cached_models": len(self.model_cache),
                "total_experiences": sum(profile.total_experiences for profile in self.agent_profiles.values()),
                "total_training_examples": sum(
                    metadata.training_examples for metadata in self.model_metadata.values()
                ),
                "last_maintenance": self.last_cleanup.isoformat(),
                "resource_monitoring": self.resource_monitor_active
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {"error": str(e)}

# Main execution for testing
if __name__ == "__main__":
    async def main():
        manager = PersonalizedModelManager()

        # Test agent registration
        character_info = {
            "name": "Gandalf the Wise",
            "class": "Wizard",
            "level": 10,
            "skills": ["arcana", "evocation", "illusion"],
            "traits": ["wise", "strategic", "cautious"]
        }

        success = await manager.register_agent("test_wizard_001", character_info)
        print(f"Agent registration: {success}")

        # Get system status
        status = manager.get_system_status()
        print(f"System status: {json.dumps(status, indent=2)}")

        # Get resource usage
        resources = await manager.get_resource_usage()
        print(f"Resource usage: {asdict(resources)}")

    asyncio.run(main())