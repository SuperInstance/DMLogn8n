#!/usr/bin/env python3
"""
LoRA-based Strategic Adaptation System for D&D Agents
Implements personalized model fine-tuning based on character experiences
"""

import torch
import json
import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import sklearn.feature_extraction.text
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs/lora_trainer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CharacterExperience:
    """Data structure for character gameplay experiences"""
    agent_id: str
    session_id: str
    timestamp: datetime
    situation: str
    action: str
    outcome: str
    success_score: float  # 0.0 to 1.0
    reward: float
    context: Dict[str, Any]
    skills_used: List[str]
    character_class: str
    level: int
    emotional_valence: float  # -1.0 to 1.0
    strategic_importance: float  # 0.0 to 1.0

@dataclass
class LoRAConfig:
    """Configuration for LoRA fine-tuning"""
    rank: int = 8
    alpha: int = 32
    dropout: float = 0.1
    target_modules: List[str] = None
    task_type: str = "CAUSAL_LM"

class LoRATrainer:
    """
    Efficient LoRA fine-tuning system for D&D agent personalization
    """

    def __init__(self, base_model_name: str = "microsoft/DialoGPT-medium"):
        self.base_model_name = base_model_name
        self.agent_configs: Dict[str, Dict] = {}
        self.training_data: Dict[str, List[CharacterExperience]] = {}
        self.experience_buffer: Dict[str, List[CharacterExperience]] = {}
        self.model_cache: Dict[str, Tuple[Any, Any]] = {}  # agent_id -> (model, tokenizer)

        # Ensure directories exist
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/agents").mkdir(parents=True, exist_ok=True)
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models").mkdir(parents=True, exist_ok=True)
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs").mkdir(parents=True, exist_ok=True)

        logger.info(f"LoRA Trainer initialized with base model: {base_model_name}")

    async def initialize_agent_lora(self, agent_id: str, character_info: Dict[str, Any]) -> str:
        """
        Initialize a LoRA adapter for a specific agent character

        Args:
            agent_id: Unique identifier for the agent
            character_info: Character class, level, traits, etc.

        Returns:
            Path to the saved adapter
        """
        try:
            logger.info(f"Initializing LoRA adapter for agent {agent_id}")

            # Create LoRA configuration based on character class
            lora_config = self._create_character_specific_config(character_info)

            # Load base model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)

            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Apply LoRA configuration
            peft_model = get_peft_model(model, lora_config)

            # Save agent-specific adapter
            adapter_path = f"/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models/{agent_id}_adapter"
            peft_model.save_pretrained(adapter_path)
            tokenizer.save_pretrained(adapter_path)

            # Store configuration
            self.agent_configs[agent_id] = {
                "adapter_path": adapter_path,
                "character_info": character_info,
                "training_examples": 0,
                "last_trained": None,
                "performance_metrics": {
                    "avg_loss": 0.0,
                    "success_rate": 0.0,
                    "strategic_improvement": 0.0
                },
                "lora_config": asdict(lora_config),
                "created_at": datetime.now().isoformat()
            }

            # Initialize training data buffer
            self.training_data[agent_id] = []
            self.experience_buffer[agent_id] = []

            # Cache model for faster inference
            self.model_cache[agent_id] = (peft_model, tokenizer)

            logger.info(f"Successfully initialized LoRA adapter for agent {agent_id} at {adapter_path}")
            return adapter_path

        except Exception as e:
            logger.error(f"Failed to initialize LoRA adapter for agent {agent_id}: {str(e)}")
            raise

    def _create_character_specific_config(self, character_info: Dict[str, Any]) -> LoraConfig:
        """Create LoRA configuration tailored to character class and playstyle"""

        character_class = character_info.get("class", "fighter").lower()
        level = character_info.get("level", 1)

        # Adjust LoRA parameters based on character complexity
        if character_class in ["wizard", "sorcerer", "bard"]:
            # Magic users need more complex adaptation
            rank = min(16, 8 + level // 3)
            alpha = min(64, 32 + level // 2)
        elif character_class in ["fighter", "barbarian", "rogue"]:
            # Martial characters focus on tactical patterns
            rank = min(12, 6 + level // 4)
            alpha = min(48, 24 + level // 3)
        else:
            # Balanced approach for other classes
            rank = 8
            alpha = 32

        # Target modules may vary by model architecture
        target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]

        return LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=rank,
            lora_alpha=alpha,
            lora_dropout=0.1,
            target_modules=target_modules,
            bias="none"
        )

    async def collect_experience(self, experience: CharacterExperience):
        """
        Collect gameplay experience for training data

        Args:
            experience: Character experience data
        """
        try:
            agent_id = experience.agent_id

            if agent_id not in self.experience_buffer:
                self.experience_buffer[agent_id] = []

            # Store experience
            self.experience_buffer[agent_id].append(experience)

            # Check if we have enough data for training
            batch_size = max(50, 20 + experience.level * 5)  # Scale with character level

            if len(self.experience_buffer[agent_id]) >= batch_size:
                await self._process_experience_batch(agent_id)

        except Exception as e:
            logger.error(f"Failed to collect experience for agent {experience.agent_id}: {str(e)}")

    async def _process_experience_batch(self, agent_id: str):
        """Process a batch of experiences for training"""
        try:
            experiences = self.experience_buffer[agent_id]

            # Filter high-quality experiences
            quality_experiences = self._filter_quality_experiences(experiences)

            if len(quality_experiences) < 10:  # Minimum threshold
                return

            # Format for training
            training_examples = []
            for exp in quality_experiences:
                formatted = self._format_experience_for_training(exp)
                if formatted:
                    training_examples.append(formatted)

            # Add to training data
            self.training_data[agent_id].extend(training_examples)

            # Clear buffer
            self.experience_buffer[agent_id] = []

            # Check if we should trigger training
            if len(self.training_data[agent_id]) >= 100:
                await self.train_agent_lora(agent_id)

        except Exception as e:
            logger.error(f"Failed to process experience batch for agent {agent_id}: {str(e)}")

    def _filter_quality_experiences(self, experiences: List[CharacterExperience]) -> List[CharacterExperience]:
        """Filter experiences based on quality metrics"""

        filtered = []

        for exp in experiences:
            quality_score = 0.0

            # High success or failure (learning opportunities)
            if exp.success_score > 0.8 or exp.success_score < 0.2:
                quality_score += 0.3

            # Strategic importance
            quality_score += exp.strategic_importance * 0.3

            # Emotional intensity (memorable experiences)
            quality_score += abs(exp.emotional_valence) * 0.2

            # Recent experiences get slight boost
            days_old = (datetime.now() - exp.timestamp).days
            recency_boost = max(0, 1 - days_old / 30) * 0.2
            quality_score += recency_boost

            if quality_score >= 0.4:  # Quality threshold
                filtered.append(exp)

        # Sort by quality and keep top experiences
        filtered.sort(key=lambda x: x.strategic_importance + abs(x.emotional_valence), reverse=True)
        return filtered[:50]  # Limit batch size

    def _format_experience_for_training(self, experience: CharacterExperience) -> Optional[str]:
        """Format experience as training example"""
        try:
            # Create training prompt based on experience success
            if experience.success_score > 0.7:
                # Success case - learn from effective actions
                training_text = f"""
Character: {experience.character_class} Level {experience.level}
Situation: {experience.situation}
Context: {json.dumps(experience.context, indent=2)}
Available Skills: {', '.join(experience.skills_used)}

Q: What would be the most strategic action in this situation?
A: {experience.action}

This action led to: {experience.outcome}
Success Rate: {experience.success_score:.2f}
Reward: {experience.reward:.2f}
"""
            elif experience.success_score < 0.3:
                # Failure case - learn what to avoid
                training_text = f"""
Character: {experience.character_class} Level {experience.level}
Situation: {experience.situation}
Context: {json.dumps(experience.context, indent=2)}
Available Skills: {', '.join(experience.skills_used)}

Q: What action should be avoided in this situation?
A: {experience.action}

This action led to: {experience.outcome}
Success Rate: {experience.success_score:.2f}
A better approach would have been...
"""
            else:
                # Mixed results - provide context for decision-making
                training_text = f"""
Character: {experience.character_class} Level {experience.level}
Situation: {experience.situation}
Context: {json.dumps(experience.context, indent=2)}
Available Skills: {', '.join(experience.skills_used)}

Action Taken: {experience.action}
Result: {experience.outcome}
Success Rate: {experience.success_score:.2f}

Learning: Strategic assessment of risk vs reward in this scenario.
"""

            return training_text.strip()

        except Exception as e:
            logger.error(f"Failed to format experience for training: {str(e)}")
            return None

    async def train_agent_lora(self, agent_id: str):
        """
        Fine-tune the agent's LoRA adapter with collected experiences

        Args:
            agent_id: Agent identifier
        """
        try:
            logger.info(f"Starting LoRA training for agent {agent_id}")

            if agent_id not in self.agent_configs:
                raise ValueError(f"Agent {agent_id} not initialized")

            training_examples = self.training_data.get(agent_id, [])
            if len(training_examples) < 20:
                logger.warning(f"Insufficient training data for agent {agent_id}: {len(training_examples)} examples")
                return

            # Prepare dataset
            dataset = Dataset.from_dict({"text": training_examples})

            # Load base model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)

            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token

            # Load existing adapter
            adapter_path = self.agent_configs[agent_id]["adapter_path"]
            model = PeftModel.from_pretrained(model, adapter_path)

            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=512,
                    return_tensors="pt"
                )

            tokenized_dataset = dataset.map(tokenize_function, batched=True)

            # Training arguments optimized for efficiency
            training_args = TrainingArguments(
                output_dir=f"/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/models/{agent_id}_training",
                per_device_train_batch_size=2,
                gradient_accumulation_steps=4,
                learning_rate=5e-5,
                num_train_epochs=2,
                logging_dir=f"/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs/{agent_id}_training",
                logging_steps=10,
                save_steps=100,
                save_total_limit=2,
                fp16=True,
                dataloader_pin_memory=False,
                remove_unused_columns=False,
                report_to=None,  # Disable wandb/etc for production
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )

            # Create trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )

            # Train
            trainer.train()

            # Save updated adapter
            model.save_pretrained(adapter_path)

            # Update metrics
            final_loss = trainer.state.log_history[-1].get("train_loss", 0.0) if trainer.state.log_history else 0.0

            self.agent_configs[agent_id]["training_examples"] += len(training_examples)
            self.agent_configs[agent_id]["last_trained"] = datetime.now().isoformat()
            self.agent_configs[agent_id]["performance_metrics"]["avg_loss"] = final_loss

            # Clear training data for this batch
            self.training_data[agent_id] = []

            # Update cached model
            self.model_cache[agent_id] = (model, tokenizer)

            logger.info(f"Successfully trained LoRA adapter for agent {agent_id}. Final loss: {final_loss:.4f}")

        except Exception as e:
            logger.error(f"Failed to train LoRA adapter for agent {agent_id}: {str(e)}")
            raise

    async def generate_response(self, agent_id: str, prompt: str, max_length: int = 150) -> str:
        """
        Generate response using agent's personalized model

        Args:
            agent_id: Agent identifier
            prompt: Input prompt for generation
            max_length: Maximum response length

        Returns:
            Generated response text
        """
        try:
            if agent_id not in self.model_cache:
                if agent_id not in self.agent_configs:
                    raise ValueError(f"Agent {agent_id} not initialized")

                # Load model from disk
                adapter_path = self.agent_configs[agent_id]["adapter_path"]
                model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                model = PeftModel.from_pretrained(model, adapter_path)
                tokenizer = AutoTokenizer.from_pretrained(adapter_path)

                self.model_cache[agent_id] = (model, tokenizer)

            model, tokenizer = self.model_cache[agent_id]

            # Generate response
            inputs = tokenizer.encode(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = inputs.to(model.device)

            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.8,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Clean up response (remove input prompt)
            if response.startswith(prompt):
                response = response[len(prompt):].strip()

            return response

        except Exception as e:
            logger.error(f"Failed to generate response for agent {agent_id}: {str(e)}")
            return f"I need a moment to consider this situation..."  # Fallback response

    def get_agent_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get training and performance metrics for an agent"""
        if agent_id not in self.agent_configs:
            return {}

        config = self.agent_configs[agent_id]
        return {
            "agent_id": agent_id,
            "training_examples": config["training_examples"],
            "last_trained": config["last_trained"],
            "performance_metrics": config["performance_metrics"],
            "character_info": config["character_info"],
            "experience_buffer_size": len(self.experience_buffer.get(agent_id, [])),
            "training_data_size": len(self.training_data.get(agent_id, []))
        }

    async def cleanup_agent(self, agent_id: str):
        """Clean up agent resources and save final state"""
        try:
            # Train any remaining data
            if agent_id in self.training_data and len(self.training_data[agent_id]) > 0:
                await self.train_agent_lora(agent_id)

            # Clear model cache
            if agent_id in self.model_cache:
                del self.model_cache[agent_id]

            logger.info(f"Cleaned up resources for agent {agent_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup agent {agent_id}: {str(e)}")

class StrategicPatternExtractor:
    """
    Extracts strategic patterns from gameplay data for LoRA training optimization
    """

    def __init__(self):
        self.pattern_cache: Dict[str, List[Dict]] = {}
        self.vectorizer = sklearn.feature_extraction.text.TfidfVectorizer(max_features=100)

    async def extract_patterns(self, experiences: List[CharacterExperience]) -> Dict[str, List[Dict]]:
        """Extract strategic patterns from character experiences"""

        if not experiences:
            return {"success_patterns": [], "failure_patterns": [], "improvement_areas": []}

        # Separate successful and failed experiences
        successful = [exp for exp in experiences if exp.success_score > 0.7]
        failed = [exp for exp in experiences if exp.success_score < 0.3]

        # Extract patterns
        success_patterns = await self._analyze_success_patterns(successful)
        failure_patterns = await self._analyze_failure_patterns(failed)
        improvement_areas = await self._identify_improvement_areas(experiences)

        return {
            "success_patterns": success_patterns,
            "failure_patterns": failure_patterns,
            "improvement_areas": improvement_areas
        }

    async def _analyze_success_patterns(self, successful_experiences: List[CharacterExperience]) -> List[Dict]:
        """Analyze patterns in successful experiences"""
        patterns = []

        if not successful_experiences:
            return patterns

        # Group by character class
        by_class = {}
        for exp in successful_experiences:
            cls = exp.character_class
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(exp)

        # Analyze each class
        for cls, exps in by_class.items():
            if len(exps) < 3:  # Need minimum examples
                continue

            # Find common situations
            situations = [exp.situation for exp in exps]
            actions = [exp.action for exp in exps]

            pattern = {
                "character_class": cls,
                "situations": situations,
                "successful_actions": actions,
                "avg_success_rate": np.mean([exp.success_score for exp in exps]),
                "common_skills": self._find_common_skills(exps),
                "frequency": len(exps)
            }

            patterns.append(pattern)

        return patterns

    async def _analyze_failure_patterns(self, failed_experiences: List[CharacterExperience]) -> List[Dict]:
        """Analyze patterns in failed experiences"""
        patterns = []

        if not failed_experiences:
            return patterns

        # Group by common failure reasons
        by_situation_type = {}
        for exp in failed_experiences:
            # Simplify situation categorization
            situation_type = self._categorize_situation(exp.situation)
            if situation_type not in by_situation_type:
                by_situation_type[situation_type] = []
            by_situation_type[situation_type].append(exp)

        # Analyze failure patterns
        for situation_type, exps in by_situation_type.items():
            if len(exps) < 2:
                continue

            pattern = {
                "situation_type": situation_type,
                "failed_approaches": [exp.action for exp in exps],
                "avg_success_rate": np.mean([exp.success_score for exp in exps]),
                "common_mistakes": self._identify_common_mistakes(exps),
                "frequency": len(exps)
            }

            patterns.append(pattern)

        return patterns

    async def _identify_improvement_areas(self, experiences: List[CharacterExperience]) -> List[Dict]:
        """Identify areas where the agent can improve"""
        improvements = []

        # Analyze skill usage vs success
        skill_performance = {}
        for exp in experiences:
            for skill in exp.skills_used:
                if skill not in skill_performance:
                    skill_performance[skill] = []
                skill_performance[skill].append(exp.success_score)

        for skill, scores in skill_performance.items():
            if len(scores) >= 3:
                avg_score = np.mean(scores)
                if avg_score < 0.5:  # Needs improvement
                    improvements.append({
                        "skill": skill,
                        "current_performance": avg_score,
                        "recommended_focus": "practice and strategic study",
                        "priority": "high" if avg_score < 0.3 else "medium"
                    })

        return improvements

    def _find_common_skills(self, experiences: List[CharacterExperience]) -> List[str]:
        """Find skills commonly used in successful experiences"""
        skill_counts = {}
        for exp in experiences:
            for skill in exp.skills_used:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Return skills used in >50% of experiences
        threshold = len(experiences) * 0.5
        return [skill for skill, count in skill_counts.items() if count >= threshold]

    def _categorize_situation(self, situation: str) -> str:
        """Categorize situation type for pattern analysis"""
        situation_lower = situation.lower()

        if any(word in situation_lower for word in ["combat", "fight", "battle", "attack"]):
            return "combat"
        elif any(word in situation_lower for word in ["talk", "negotiate", "persuade", "social"]):
            return "social"
        elif any(word in situation_lower for word in ["trap", "puzzle", "mystery", "investigate"]):
            return "exploration"
        elif any(word in situation_lower for word in ["magic", "spell", "arcane", "ritual"]):
            return "magical"
        else:
            return "general"

    def _identify_common_mistakes(self, failed_experiences: List[CharacterExperience]) -> List[str]:
        """Identify common mistakes in failed experiences"""
        mistakes = []

        # Look for patterns in actions that led to failure
        actions = [exp.action for exp in failed_experiences]

        # Simple keyword-based mistake identification
        for action in actions:
            action_lower = action.lower()
            if any(word in action_lower for word in ["rush", "quickly", "without thinking"]):
                if "recklessness" not in mistakes:
                    mistakes.append("recklessness")
            elif any(word in action_lower for word in ["alone", "by myself"]):
                if "isolation" not in mistakes:
                    mistakes.append("isolation")
            elif any(word in action_lower for word in ["ignore", "disregard"]):
                if "ignoring_warnings" not in mistakes:
                    mistakes.append("ignoring_warnings")

        return mistakes

# Main execution for testing
if __name__ == "__main__":
    async def main():
        trainer = LoRATrainer()

        # Test with a sample character
        character_info = {
            "class": "Wizard",
            "level": 5,
            "traits": ["intelligent", "cautious", "curious"]
        }

        agent_id = "test_wizard_001"
        adapter_path = await trainer.initialize_agent_lora(agent_id, character_info)
        print(f"Initialized adapter at: {adapter_path}")

        # Create sample experience
        experience = CharacterExperience(
            agent_id=agent_id,
            session_id="session_001",
            timestamp=datetime.now(),
            situation="Encountered a group of goblins guarding a treasure chest",
            action="Cast sleep spell to disable the group peacefully",
            outcome="Successfully neutralized the goblins and acquired the treasure without combat",
            success_score=0.9,
            reward=100.0,
            context={"location": "dungeon", "allies": ["fighter", "rogue"]},
            skills_used=["arcana", "deception"],
            character_class="Wizard",
            level=5,
            emotional_valence=0.7,
            strategic_importance=0.8
        )

        await trainer.collect_experience(experience)
        metrics = trainer.get_agent_metrics(agent_id)
        print(f"Agent metrics: {json.dumps(metrics, indent=2, default=str)}")

    asyncio.run(main())