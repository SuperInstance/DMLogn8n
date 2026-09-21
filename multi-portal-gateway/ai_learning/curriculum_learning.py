#!/usr/bin/env python3
"""
Curriculum Learning System for Structured Skill Acquisition
Implements progressive difficulty scaling and structured learning paths
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import math
import time
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurriculumType(Enum):
    """Types of curriculum learning strategies"""
    STATIC = "static"
    ADAPTIVE = "adaptive"
    SELF_PACED = "self_paced"
    COMPETENCY_BASED = "competency_based"
    REVERSE_CURRICULUM = "reverse_curriculum"

@dataclass
class CurriculumTask:
    """Represents a task in the curriculum"""
    task_id: str
    difficulty: float
    prerequisites: List[str] = field(default_factory=list)
    skills_learned: List[str] = field(default_factory=list)
    success_threshold: float = 0.8
    failure_threshold: float = 0.4
    max_attempts: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.completion_time = None
        self.skill_mastery = {skill: 0.0 for skill in self.skills_learned}

@dataclass
class CurriculumConfig:
    """Configuration for curriculum learning"""
    curriculum_type: CurriculumType = CurriculumType.ADAPTIVE
    difficulty_growth_rate: float = 0.1
    mastery_threshold: float = 0.9
    competency_decay_rate: float = 0.01
    adaptation_frequency: int = 100
    max_consecutive_failures: int = 3
    min_success_rate: float = 0.7
    exploration_rate: float = 0.1
    device: str = 'cuda'

class DifficultyScheduler(ABC):
    """Abstract base class for difficulty scheduling"""

    @abstractmethod
    def get_difficulty(self, step: int, performance: float) -> float:
        """Get difficulty level at given step"""
        pass

    @abstractmethod
    def update(self, performance: float, step: int):
        """Update scheduler based on performance"""
        pass

class LinearScheduler(DifficultyScheduler):
    """Linear difficulty progression"""

    def __init__(self, initial_difficulty: float = 0.1, max_difficulty: float = 1.0,
                 growth_rate: float = 0.01):
        self.initial_difficulty = initial_difficulty
        self.max_difficulty = max_difficulty
        self.growth_rate = growth_rate
        self.current_difficulty = initial_difficulty

    def get_difficulty(self, step: int, performance: float) -> float:
        """Linear increase in difficulty"""
        self.current_difficulty = min(
            self.max_difficulty,
            self.initial_difficulty + step * self.growth_rate
        )
        return self.current_difficulty

    def update(self, performance: float, step: int):
        """Update based on performance"""
        if performance > 0.8:
            self.growth_rate = min(0.05, self.growth_rate * 1.1)
        elif performance < 0.4:
            self.growth_rate = max(0.001, self.growth_rate * 0.9)

class ExponentialScheduler(DifficultyScheduler):
    """Exponential difficulty progression"""

    def __init__(self, initial_difficulty: float = 0.1, max_difficulty: float = 1.0,
                 growth_factor: float = 1.01):
        self.initial_difficulty = initial_difficulty
        self.max_difficulty = max_difficulty
        self.growth_factor = growth_factor
        self.current_difficulty = initial_difficulty

    def get_difficulty(self, step: int, performance: float) -> float:
        """Exponential increase in difficulty"""
        self.current_difficulty = min(
            self.max_difficulty,
            self.initial_difficulty * (self.growth_factor ** step)
        )
        return self.current_difficulty

    def update(self, performance: float, step: int):
        """Update based on performance"""
        if performance > 0.8:
            self.growth_factor = min(1.05, self.growth_factor * 1.02)
        elif performance < 0.4:
            self.growth_factor = max(1.001, self.growth_factor * 0.98)

class AdaptiveScheduler(DifficultyScheduler):
    """Adaptive difficulty based on performance"""

    def __init__(self, initial_difficulty: float = 0.3, adaptation_rate: float = 0.1):
        self.current_difficulty = initial_difficulty
        self.adaptation_rate = adaptation_rate
        self.performance_history = deque(maxlen=50)
        self.target_success_rate = 0.7

    def get_difficulty(self, step: int, performance: float) -> float:
        """Adaptive difficulty based on recent performance"""
        self.performance_history.append(performance)

        if len(self.performance_history) >= 10:
            recent_performance = np.mean(list(self.performance_history)[-10:])

            # Adjust difficulty based on performance
            if recent_performance > self.target_success_rate + 0.1:
                # Too easy, increase difficulty
                self.current_difficulty = min(1.0, self.current_difficulty + self.adaptation_rate)
            elif recent_performance < self.target_success_rate - 0.1:
                # Too hard, decrease difficulty
                self.current_difficulty = max(0.1, self.current_difficulty - self.adaptation_rate)

        return self.current_difficulty

    def update(self, performance: float, step: int):
        """Update with new performance data"""
        self.performance_history.append(performance)

class SelfPacedScheduler(DifficultyScheduler):
    """Self-paced learning scheduler"""

    def __init__(self, initial_difficulty: float = 0.1, pacing_rate: float = 0.05):
        self.current_difficulty = initial_difficulty
        self.pacing_rate = pacing_rate
        self.loss_history = deque(maxlen=100)
        self.min_loss_threshold = 0.1

    def get_difficulty(self, step: int, performance: float) -> float:
        """Self-paced difficulty based on loss"""
        # Convert performance to loss-like metric
        loss_metric = 1.0 - performance
        self.loss_history.append(loss_metric)

        if len(self.loss_history) >= 20:
            recent_loss = np.mean(list(self.loss_history)[-20:])

            if recent_loss < self.min_loss_threshold:
                # Learning well, increase difficulty
                self.current_difficulty = min(1.0, self.current_difficulty + self.pacing_rate)

        return self.current_difficulty

    def update(self, performance: float, step: int):
        """Update with performance data"""
        loss_metric = 1.0 - performance
        self.loss_history.append(loss_metric)

class CurriculumManager:
    """Manages curriculum learning progression"""

    def __init__(self, config: CurriculumConfig):
        self.config = config
        self.tasks = {}
        self.task_dependencies = defaultdict(list)
        self.completed_tasks = set()
        self.current_task = None
        self.skill_levels = defaultdict(float)
        self.performance_history = defaultdict(list)

        # Initialize difficulty scheduler
        self.scheduler = self._create_scheduler()

        # Learning metrics
        self.curriculum_progress = 0.0
        self.learning_efficiency = 0.0
        self.adaptation_events = []

    def _create_scheduler(self) -> DifficultyScheduler:
        """Create difficulty scheduler based on curriculum type"""
        if self.config.curriculum_type == CurriculumType.STATIC:
            return LinearScheduler()
        elif self.config.curriculum_type == CurriculumType.ADAPTIVE:
            return AdaptiveScheduler()
        elif self.config.curriculum_type == CurriculumType.SELF_PACED:
            return SelfPacedScheduler()
        elif self.config.curriculum_type == CurriculumType.COMPETENCY_BASED:
            return AdaptiveScheduler()  # Can be customized
        else:
            return LinearScheduler()

    def add_task(self, task: CurriculumTask):
        """Add a task to the curriculum"""
        self.tasks[task.task_id] = task

        # Update dependencies
        for prereq in task.prerequisites:
            self.task_dependencies[prereq].append(task.task_id)

        logger.info(f"Added task: {task.task_id} (difficulty: {task.difficulty})")

    def get_next_task(self, performance_history: Optional[List[float]] = None) -> Optional[CurriculumTask]:
        """Get the next appropriate task"""
        if self.config.curriculum_type == CurriculumType.ADAPTIVE:
            return self._get_adaptive_task(performance_history)
        elif self.config.curriculum_type == CurriculumType.SELF_PACED:
            return self._get_self_paced_task(performance_history)
        elif self.config.curriculum_type == CurriculumType.COMPETENCY_BASED:
            return self._get_competency_based_task()
        else:
            return self._get_static_task()

    def _get_adaptive_task(self, performance_history: Optional[List[float]] = None) -> Optional[CurriculumTask]:
        """Adaptive task selection based on performance"""
        available_tasks = []

        for task_id, task in self.tasks.items():
            if task_id in self.completed_tasks:
                continue

            # Check prerequisites
            if not all(prereq in self.completed_tasks for prereq in task.prerequisites):
                continue

            # Check if task is appropriate based on recent performance
            if performance_history:
                recent_performance = np.mean(performance_history[-5:]) if len(performance_history) >= 5 else 0.5

                # Adjust task difficulty threshold based on performance
                difficulty_threshold = 0.3 + 0.4 * recent_performance

                if task.difficulty <= difficulty_threshold:
                    available_tasks.append(task)
            else:
                available_tasks.append(task)

        if not available_tasks:
            return None

        # Select task based on difficulty and skill development needs
        return self._select_optimal_task(available_tasks)

    def _get_self_paced_task(self, performance_history: Optional[List[float]] = None) -> Optional[CurriculumTask]:
        """Self-paced task selection"""
        # Get current difficulty level
        current_difficulty = self.scheduler.current_difficulty

        # Find tasks close to current difficulty
        suitable_tasks = []
        for task_id, task in self.tasks.items():
            if task_id in self.completed_tasks:
                continue

            if not all(prereq in self.completed_tasks for prereq in task.prerequisites):
                continue

            # Select tasks within difficulty range
            if abs(task.difficulty - current_difficulty) < 0.2:
                suitable_tasks.append(task)

        if not suitable_tasks:
            # If no suitable tasks, adjust difficulty
            all_available = [t for t in self.tasks.values()
                           if t.task_id not in self.completed_tasks and
                           all(prereq in self.completed_tasks for prereq in t.prerequisites)]

            if all_available:
                suitable_tasks = all_available

        if suitable_tasks:
            return random.choice(suitable_tasks)
        return None

    def _get_competency_based_task(self) -> Optional[CurriculumTask]:
        """Competency-based task selection"""
        # Find tasks where the agent needs to improve specific skills
        for task_id, task in self.tasks.items():
            if task_id in self.completed_tasks:
                continue

            if not all(prereq in self.completed_tasks for prereq in task.prerequisites):
                continue

            # Check if agent needs improvement in task skills
            needs_improvement = any(
                self.skill_levels[skill] < task.success_threshold
                for skill in task.skills_learned
            )

            if needs_improvement:
                return task

        # If no specific improvement needed, choose easiest available task
        available_tasks = [t for t in self.tasks.values()
                          if t.task_id not in self.completed_tasks and
                          all(prereq in self.completed_tasks for prereq in t.prerequisites)]

        if available_tasks:
            return min(available_tasks, key=lambda t: t.difficulty)

        return None

    def _get_static_task(self) -> Optional[CurriculumTask]:
        """Static curriculum progression"""
        # Progress through tasks in order of difficulty
        available_tasks = [t for t in self.tasks.values()
                          if t.task_id not in self.completed_tasks and
                          all(prereq in self.completed_tasks for prereq in t.prerequisites)]

        if available_tasks:
            return min(available_tasks, key=lambda t: t.difficulty)
        return None

    def _select_optimal_task(self, available_tasks: List[CurriculumTask]) -> CurriculumTask:
        """Select the optimal task from available options"""
        # Score tasks based on multiple factors
        task_scores = []

        for task in available_tasks:
            score = 0.0

            # Difficulty appropriateness
            current_difficulty = self.scheduler.current_difficulty
            difficulty_match = 1.0 - abs(task.difficulty - current_difficulty)
            score += 0.4 * difficulty_match

            # Skill development value
            skill_value = 0.0
            for skill in task.skills_learned:
                current_level = self.skill_levels[skill]
                skill_value += (1.0 - current_level)  # Higher value for less developed skills
            skill_value /= max(1, len(task.skills_learned))
            score += 0.3 * skill_value

            # Success probability estimate
            estimated_success = min(0.9, max(0.1, 1.0 - task.difficulty))
            score += 0.2 * estimated_success

            # Novelty bonus (for less attempted tasks)
            novelty = 1.0 / (1.0 + task.attempts)
            score += 0.1 * novelty

            task_scores.append((task, score))

        # Select task with highest score (with some exploration)
        if random.random() < self.config.exploration_rate:
            return random.choice(available_tasks)
        else:
            return max(task_scores, key=lambda x: x[1])[0]

    def update_task_performance(self, task_id: str, performance: float, completion_time: Optional[float] = None):
        """Update performance metrics for a task"""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        task.attempts += 1

        if performance >= task.success_threshold:
            task.successes += 1
            self.completed_tasks.add(task_id)
            task.completion_time = completion_time or time.time()

            # Update skill mastery
            for skill in task.skills_learned:
                improvement = (performance - self.skill_levels[skill]) * 0.5
                self.skill_levels[skill] = min(1.0, self.skill_levels[skill] + improvement)

        elif performance < task.failure_threshold:
            task.failures += 1

        # Update performance history
        self.performance_history[task_id].append(performance)

        # Update scheduler
        self.scheduler.update(performance, len(self.performance_history[task_id]))

        # Log update
        logger.info(f"Task {task_id}: Performance={performance:.3f}, Attempts={task.attempts}, Completed={task_id in self.completed_tasks}")

    def get_curriculum_progress(self) -> Dict[str, Any]:
        """Get overall curriculum progress"""
        total_tasks = len(self.tasks)
        completed_tasks = len(self.completed_tasks)
        completion_rate = completed_tasks / max(1, total_tasks)

        # Average skill levels
        avg_skill_level = np.mean(list(self.skill_levels.values())) if self.skill_levels else 0.0

        # Recent performance
        all_recent_performances = []
        for performances in self.performance_history.values():
            if performances:
                all_recent_performances.append(performances[-1])

        recent_performance = np.mean(all_recent_performances) if all_recent_performances else 0.0

        return {
            'completion_rate': completion_rate,
            'completed_tasks': completed_tasks,
            'total_tasks': total_tasks,
            'average_skill_level': avg_skill_level,
            'recent_performance': recent_performance,
            'current_difficulty': self.scheduler.current_difficulty,
            'skill_levels': dict(self.skill_levels)
        }

    def get_learning_efficiency(self) -> float:
        """Calculate learning efficiency"""
        if not self.performance_history:
            return 0.0

        total_attempts = sum(len(perfs) for perfs in self.performance_history.values())
        successful_attempts = sum(len([p for p in perfs if p >= 0.7]) for perfs in self.performance_history.values())

        if total_attempts == 0:
            return 0.0

        return successful_attempts / total_attempts

    def adapt_curriculum(self):
        """Adapt curriculum based on learning progress"""
        progress = self.get_curriculum_progress()
        efficiency = self.get_learning_efficiency()

        # Adaptation strategies based on performance
        if efficiency < 0.3:
            # Low efficiency, simplify curriculum
            logger.info("Low learning efficiency detected, simplifying curriculum")
            self.config.adaptation_frequency = max(50, self.config.adaptation_frequency - 10)
            self.config.exploration_rate = min(0.3, self.config.exploration_rate + 0.05)

        elif efficiency > 0.8:
            # High efficiency, accelerate curriculum
            logger.info("High learning efficiency detected, accelerating curriculum")
            self.config.adaptation_frequency = max(200, self.config.adaptation_frequency + 20)
            self.config.exploration_rate = max(0.05, self.config.exploration_rate - 0.02)

        # Record adaptation event
        self.adaptation_events.append({
            'timestamp': time.time(),
            'efficiency': efficiency,
            'progress': progress,
            'adaptations': {
                'frequency': self.config.adaptation_frequency,
                'exploration_rate': self.config.exploration_rate
            }
        })

class CurriculumLearning:
    """Main curriculum learning system"""

    def __init__(self, config: CurriculumConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')
        self.curriculum_manager = CurriculumManager(config)

        # Training state
        self.current_step = 0
        self.episode_rewards = []
        self.task_rewards = defaultdict(list)
        self.learning_curves = defaultdict(list)

    def add_curriculum_task(self, task_id: str, difficulty: float,
                           prerequisites: List[str] = None,
                           skills_learned: List[str] = None,
                           **kwargs) -> CurriculumTask:
        """Add a task to the curriculum"""
        task = CurriculumTask(
            task_id=task_id,
            difficulty=difficulty,
            prerequisites=prerequisites or [],
            skills_learned=skills_learned or [],
            **kwargs
        )
        self.curriculum_manager.add_task(task)
        return task

    def train_episode(self, environment, model: nn.Module, optimizer: torch.optim.Optimizer,
                     max_steps: int = 1000) -> Dict[str, Any]:
        """Train one episode with curriculum learning"""
        # Get next task
        recent_performance = self.episode_rewards[-10:] if len(self.episode_rewards) >= 10 else None
        current_task = self.curriculum_manager.get_next_task(recent_performance)

        if current_task is None:
            logger.warning("No available tasks in curriculum")
            return {'task_id': None, 'reward': 0.0, 'steps': 0}

        # Configure environment for task
        task_env = self._configure_environment_for_task(environment, current_task)

        # Train on task
        start_time = time.time()
        episode_reward, steps = self._train_on_task(task_env, model, optimizer, current_task, max_steps)
        completion_time = time.time() - start_time

        # Calculate performance (normalized reward)
        performance = self._normalize_performance(episode_reward, current_task)

        # Update curriculum
        self.curriculum_manager.update_task_performance(current_task.task_id, performance, completion_time)

        # Store metrics
        self.episode_rewards.append(episode_reward)
        self.task_rewards[current_task.task_id].append(episode_reward)
        self.learning_curves[current_task.task_id].append(performance)

        # Log progress
        if self.current_step % self.config.adaptation_frequency == 0:
            self.curriculum_manager.adapt_curriculum()

        self.current_step += 1

        return {
            'task_id': current_task.task_id,
            'task_difficulty': current_task.difficulty,
            'reward': episode_reward,
            'performance': performance,
            'steps': steps,
            'completion_time': completion_time
        }

    def _configure_environment_for_task(self, environment, task: CurriculumTask):
        """Configure environment for specific task"""
        # This would be implemented based on specific environment and task requirements
        # For now, return the environment as-is
        return environment

    def _train_on_task(self, environment, model: nn.Module, optimizer: torch.optim.Optimizer,
                      task: CurriculumTask, max_steps: int) -> Tuple[float, int]:
        """Train model on specific task"""
        # Reset environment
        state = environment.reset()
        total_reward = 0.0

        for step in range(max_steps):
            # Get action from model
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            with torch.no_grad():
                if hasattr(model, 'select_action'):
                    action, _ = model.select_action(state_tensor)
                else:
                    action_output = model(state_tensor)
                    action = torch.argmax(action_output, dim=-1).item()

            # Take step
            next_state, reward, done, info = environment.step(action)
            total_reward += reward

            # Update model (this would be task-specific)
            # For now, just collect experience

            state = next_state
            if done:
                break

        return total_reward, step + 1

    def _normalize_performance(self, reward: float, task: CurriculumTask) -> float:
        """Normalize reward to performance score"""
        # Simple normalization - can be made more sophisticated
        max_expected_reward = 100.0  # This should be task-specific
        normalized = min(1.0, max(0.0, reward / max_expected_reward))
        return normalized

    def get_training_summary(self) -> Dict[str, Any]:
        """Get comprehensive training summary"""
        curriculum_progress = self.curriculum_manager.get_curriculum_progress()
        learning_efficiency = self.curriculum_manager.get_learning_efficiency()

        # Task-specific statistics
        task_stats = {}
        for task_id, rewards in self.task_rewards.items():
            if rewards:
                task_stats[task_id] = {
                    'episodes': len(rewards),
                    'avg_reward': np.mean(rewards),
                    'best_reward': np.max(rewards),
                    'recent_performance': np.mean(rewards[-5:]) if len(rewards) >= 5 else rewards[-1]
                }

        return {
            'curriculum_progress': curriculum_progress,
            'learning_efficiency': learning_efficiency,
            'total_episodes': len(self.episode_rewards),
            'current_step': self.current_step,
            'task_statistics': task_stats,
            'adaptation_events': len(self.curriculum_manager.adaptation_events)
        }

class ReverseCurriculum:
    """Reverse curriculum learning (start hard, get easier)"""

    def __init__(self, config: CurriculumConfig):
        self.config = config
        self.tasks = []
        self.current_difficulty = 1.0

    def create_reverse_sequence(self, base_tasks: List[CurriculumTask]) -> List[CurriculumTask]:
        """Create reverse curriculum sequence"""
        # Sort tasks by difficulty (descending)
        sorted_tasks = sorted(base_tasks, key=lambda t: t.difficulty, reverse=True)

        # Modify tasks for reverse curriculum
        reverse_tasks = []
        for i, task in enumerate(sorted_tasks):
            # Gradually reduce difficulty
            adjusted_difficulty = 1.0 - (i / len(sorted_tasks)) * 0.8

            reverse_task = CurriculumTask(
                task_id=f"reverse_{task.task_id}",
                difficulty=adjusted_difficulty,
                prerequisites=[],  # Remove prerequisites for reverse curriculum
                skills_learned=task.skills_learned.copy(),
                success_threshold=max(0.5, task.success_threshold - 0.1),
                failure_threshold=min(0.6, task.failure_threshold)
            )
            reverse_tasks.append(reverse_task)

        return reverse_tasks

# Utility functions
def create_curriculum_config(curriculum_type: str = 'adaptive') -> CurriculumConfig:
    """Create curriculum learning configuration"""
    return CurriculumConfig(
        curriculum_type=CurriculumType(curriculum_type),
        difficulty_growth_rate=0.1,
        mastery_threshold=0.9,
        competency_decay_rate=0.01,
        adaptation_frequency=100,
        max_consecutive_failures=3,
        min_success_rate=0.7,
        exploration_rate=0.1,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )

def create_sample_curriculum() -> List[CurriculumTask]:
    """Create a sample curriculum for demonstration"""
    tasks = [
        CurriculumTask(
            task_id="basic_movement",
            difficulty=0.1,
            skills_learned=["movement", "navigation"],
            success_threshold=0.7
        ),
        CurriculumTask(
            task_id="object_recognition",
            difficulty=0.3,
            prerequisites=["basic_movement"],
            skills_learned=["perception", "object_identification"],
            success_threshold=0.8
        ),
        CurriculumTask(
            task_id="simple_puzzles",
            difficulty=0.5,
            prerequisites=["object_recognition"],
            skills_learned=["problem_solving", "planning"],
            success_threshold=0.7
        ),
        CurriculumTask(
            task_id="complex_navigation",
            difficulty=0.7,
            prerequisites=["basic_movement", "simple_puzzles"],
            skills_learned=["pathfinding", "spatial_reasoning"],
            success_threshold=0.8
        ),
        CurriculumTask(
            task_id="social_interaction",
            difficulty=0.9,
            prerequisites=["object_recognition", "complex_navigation"],
            skills_learned=["communication", "cooperation"],
            success_threshold=0.8
        )
    ]
    return tasks

if __name__ == "__main__":
    # Example usage
    config = create_curriculum_config('adaptive')

    # Create curriculum learning system
    curriculum_system = CurriculumLearning(config)

    # Add sample curriculum
    sample_tasks = create_sample_curriculum()
    for task in sample_tasks:
        curriculum_system.add_curriculum_task(
            task_id=task.task_id,
            difficulty=task.difficulty,
            prerequisites=task.prerequisites,
            skills_learned=task.skills_learned
        )

    print("Curriculum Learning System initialized!")
    print(f"Curriculum type: {config.curriculum_type.value}")
    print(f"Number of tasks: {len(sample_tasks)}")
    print(f"Difficulty growth rate: {config.difficulty_growth_rate}")
    print(f"Mastery threshold: {config.mastery_threshold}")
    print(f"Available schedulers: Linear, Exponential, Adaptive, SelfPaced")
    print(f"Curriculum types: Static, Adaptive, SelfPaced, CompetencyBased, ReverseCurriculum")
    print(f"Task scheduling: Dynamic based on performance and prerequisites")
    print(f"Adaptation frequency: Every {config.adaptation_frequency} steps")