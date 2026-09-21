#!/usr/bin/env python3
"""
Advanced Custom AI Model Trainer - Domain-specific fine-tuning and optimization
Provides comprehensive training pipelines for custom AI model development
"""

import asyncio
import time
import json
import logging
import pickle
import hashlib
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import psutil
from collections import defaultdict
import transformers
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer,
    DataCollatorForLanguageModeling, EarlyStoppingCallback
)

logger = logging.getLogger(__name__)

class TrainingMethod(Enum):
    """Training methods supported"""
    FINE_TUNING = "fine_tuning"
    FEW_SHOT_LEARNING = "few_shot_learning"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    DISTILLATION = "distillation"
    ADAPTER_TRAINING = "adapter_training"
    LORA_TRAINING = "lora_training"
    PROMPT_TUNING = "prompt_tuning"
    CONTINUED_PRETRAINING = "continued_pretraining"

class TaskType(Enum):
    """Task types for training"""
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    INSTRUCTION_FOLLOWING = "instruction_following"
    CUSTOM_TASK = "custom_task"

@dataclass
class TrainingConfig:
    """Configuration for model training"""
    base_model: str
    task_type: TaskType
    training_method: TrainingMethod
    output_dir: str
    train_data_path: Optional[str] = None
    val_data_path: Optional[str] = None
    test_data_path: Optional[str] = None

    # Training hyperparameters
    num_train_epochs: int = 3
    learning_rate: float = 5e-5
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    warmup_steps: int = 500
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    # Model configuration
    max_seq_length: int = 512
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100

    # Optimization settings
    fp16: bool = True
    dataloader_num_workers: int = 4
    save_total_limit: int = 3
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False

    # Early stopping
    early_stopping_patience: int = 5
    early_stopping_threshold: float = 0.001

@dataclass
class TrainingMetrics:
    """Training performance metrics"""
    train_loss: float
    eval_loss: float
    perplexity: float
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    bleu_score: Optional[float] = None
    rouge_score: Optional[Dict[str, float]] = None
    training_time: float = 0.0
    samples_per_second: float = 0.0
    gpu_memory_usage: float = 0.0
    convergence_epoch: int = 0

@dataclass
class TrainingJob:
    """Training job configuration"""
    job_id: str
    config: TrainingConfig
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metrics: Optional[TrainingMetrics] = None
    checkpoint_path: Optional[str] = None
    error_message: Optional[str] = None

class CustomDataset(Dataset):
    """Custom dataset for training"""

    def __init__(self, texts: List[str], tokenizer, max_length: int = 512):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]

        # Tokenize text
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }

class CustomTrainer:
    """Advanced custom AI model trainer"""

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config
        self.current_job: Optional[TrainingJob] = None
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)

        # GPU availability
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.gpu_available = torch.cuda.is_available()

        # Model and tokenizer storage
        self.models: Dict[str, nn.Module] = {}
        self.tokenizers: Dict[str, Any] = {}

        # Training history
        self.training_history: List[Dict[str, Any]] = []

        logger.info(f"CustomTrainer initialized with device: {self.device}")

    async def create_training_job(self, config: TrainingConfig) -> str:
        """Create a new training job"""
        job_id = hashlib.md5(
            f"{config.base_model}_{config.task_type.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        job = TrainingJob(
            job_id=job_id,
            config=config,
            created_at=datetime.now()
        )

        self.training_jobs[job_id] = job

        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)

        logger.info(f"Created training job {job_id}")
        return job_id

    async def start_training(self, job_id: str) -> bool:
        """Start training for a specific job"""
        if job_id not in self.training_jobs:
            logger.error(f"Training job {job_id} not found")
            return False

        job = self.training_jobs[job_id]
        if job.status != "pending":
            logger.error(f"Training job {job_id} is not in pending state")
            return False

        self.current_job = job
        job.status = "running"
        job.started_at = datetime.now()

        try:
            # Start training in background
            training_task = asyncio.create_task(self._execute_training(job))

            logger.info(f"Started training job {job_id}")
            return True

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Failed to start training job {job_id}: {e}")
            return False

    async def _execute_training(self, job: TrainingJob):
        """Execute the actual training process"""
        try:
            logger.info(f"Executing training job {job.job_id}")

            # Load model and tokenizer
            model, tokenizer = await self._load_model_and_tokenizer(job.config)

            # Prepare datasets
            train_dataset, eval_dataset = await self._prepare_datasets(job.config, tokenizer)

            # Configure training
            training_args = self._create_training_args(job.config)

            # Create trainer
            trainer = self._create_trainer(
                model, tokenizer, train_dataset, eval_dataset, training_args, job.config
            )

            # Start training
            training_start = time.time()
            train_result = trainer.train()
            training_time = time.time() - training_start

            # Evaluate model
            eval_result = trainer.evaluate()

            # Save final model
            final_model_path = os.path.join(job.config.output_dir, "final_model")
            trainer.save_model(final_model_path)
            tokenizer.save_pretrained(final_model_path)

            # Calculate metrics
            metrics = TrainingMetrics(
                train_loss=train_result.training_loss,
                eval_loss=eval_result.get('eval_loss', 0.0),
                perplexity=np.exp(eval_result.get('eval_loss', 0.0)),
                training_time=training_time,
                samples_per_second=train_result.training_time / training_time if training_time > 0 else 0.0,
                gpu_memory_usage=self._get_gpu_memory_usage(),
                convergence_epoch=self._find_convergence_epoch(trainer.state.log_history)
            )

            # Update job status
            job.status = "completed"
            job.completed_at = datetime.now()
            job.metrics = metrics
            job.checkpoint_path = final_model_path

            # Store model
            self.models[job.job_id] = model
            self.tokenizers[job.job_id] = tokenizer

            # Record training history
            self._record_training_history(job, train_result, eval_result)

            logger.info(f"Training job {job.job_id} completed successfully")

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Training job {job.job_id} failed: {e}")

    async def _load_model_and_tokenizer(self, config: TrainingConfig) -> Tuple[nn.Module, Any]:
        """Load base model and tokenizer"""
        logger.info(f"Loading model {config.base_model}")

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(config.base_model)

        # Add padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            torch_dtype=torch.float16 if config.fp16 else torch.float32,
            device_map='auto' if self.gpu_available else None
        )

        # Resize token embeddings if needed
        model.resize_token_embeddings(len(tokenizer))

        # Move to device
        if not self.gpu_available:
            model = model.to(self.device)

        logger.info(f"Model loaded with {sum(p.numel() for p in model.parameters())} parameters")
        return model, tokenizer

    async def _prepare_datasets(self, config: TrainingConfig, tokenizer) -> Tuple[Optional[Dataset], Optional[Dataset]]:
        """Prepare training and evaluation datasets"""
        train_dataset = None
        eval_dataset = None

        # Load training data
        if config.train_data_path and os.path.exists(config.train_data_path):
            train_texts = await self._load_text_data(config.train_data_path)
            if train_texts:
                train_dataset = CustomDataset(
                    train_texts, tokenizer, config.max_seq_length
                )
                logger.info(f"Loaded {len(train_texts)} training samples")

        # Load evaluation data
        if config.val_data_path and os.path.exists(config.val_data_path):
            val_texts = await self._load_text_data(config.val_data_path)
            if val_texts:
                eval_dataset = CustomDataset(
                    val_texts, tokenizer, config.max_seq_length
                )
                logger.info(f"Loaded {len(val_texts)} validation samples")

        # If no eval dataset, use 10% of training data
        if train_dataset and not eval_dataset:
            train_size = int(0.9 * len(train_dataset))
            eval_size = len(train_dataset) - train_size
            train_dataset, eval_dataset = torch.utils.data.random_split(
                train_dataset, [train_size, eval_size]
            )
            logger.info(f"Split training data: {train_size} train, {eval_size} eval")

        return train_dataset, eval_dataset

    async def _load_text_data(self, file_path: str) -> List[str]:
        """Load text data from file"""
        texts = []

        try:
            if file_path.endswith('.jsonl'):
                # Load JSONL format
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line.strip())
                        if 'text' in data:
                            texts.append(data['text'])
                        elif 'prompt' in data and 'response' in data:
                            # Combine prompt and response
                            texts.append(f"{data['prompt']}\n\n{data['response']}")

            elif file_path.endswith('.json'):
                # Load JSON format
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, str):
                                texts.append(item)
                            elif isinstance(item, dict) and 'text' in item:
                                texts.append(item['text'])

            else:
                # Load plain text
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Split by paragraphs or lines
                    texts = [para.strip() for para in content.split('\n\n') if para.strip()]

        except Exception as e:
            logger.error(f"Failed to load data from {file_path}: {e}")

        return texts

    def _create_training_args(self, config: TrainingConfig) -> TrainingArguments:
        """Create training arguments"""
        return TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_train_epochs,
            learning_rate=config.learning_rate,
            per_device_train_batch_size=config.per_device_train_batch_size,
            per_device_eval_batch_size=config.per_device_eval_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            warmup_steps=config.warmup_steps,
            weight_decay=config.weight_decay,
            max_grad_norm=config.max_grad_norm,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps,
            fp16=config.fp16,
            dataloader_num_workers=config.dataloader_num_workers,
            save_total_limit=config.save_total_limit,
            load_best_model_at_end=config.load_best_model_at_end,
            metric_for_best_model=config.metric_for_best_model,
            greater_is_better=config.greater_is_better,
            evaluation_strategy="steps" if config.val_data_path else "no",
            save_strategy="steps",
            logging_dir=f"{config.output_dir}/logs",
            report_to=[],  # Disable wandb/tensorboard for simplicity
            remove_unused_columns=False,
        )

    def _create_trainer(self, model, tokenizer, train_dataset, eval_dataset,
                       training_args, config: TrainingConfig) -> Trainer:
        """Create custom trainer"""

        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False  # We're doing causal language modeling
        )

        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=tokenizer,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)]
        ]

        return trainer

    async def fine_tune_with_examples(self, base_model: str, examples: List[Dict[str, str]],
                                    task_type: TaskType, output_dir: str) -> str:
        """Fine-tune model with few examples"""
        # Create temporary training file
        temp_file = os.path.join(output_dir, "temp_examples.jsonl")

        with open(temp_file, 'w') as f:
            for example in examples:
                if 'prompt' in example and 'response' in example:
                    # Instruction following format
                    formatted_example = {
                        'text': f"### Instruction:\n{example['prompt']}\n\n### Response:\n{example['response']}"
                    }
                else:
                    # Simple text format
                    formatted_example = {'text': example.get('text', str(example))}

                f.write(json.dumps(formatted_example) + '\n')

        # Create training config
        config = TrainingConfig(
            base_model=base_model,
            task_type=task_type,
            training_method=TrainingMethod.FINE_TUNING,
            output_dir=output_dir,
            train_data_path=temp_file,
            num_train_epochs=1,  # Few-shot learning
            learning_rate=1e-4,
            per_device_train_batch_size=2,
            save_steps=50,
            eval_steps=50
        )

        # Create and start training job
        job_id = await self.create_training_job(config)
        success = await self.start_training(job_id)

        if success:
            # Wait for completion
            await self._wait_for_job_completion(job_id)
            return job_id
        else:
            raise Exception("Failed to start fine-tuning job")

    async def create_adapter_model(self, base_model: str, task_data: List[str],
                                 output_dir: str, adapter_type: str = "lora") -> str:
        """Create adapter model for specific task"""
        # Create temporary training file
        temp_file = os.path.join(output_dir, "adapter_data.jsonl")

        with open(temp_file, 'w') as f:
            for text in task_data:
                f.write(json.dumps({'text': text}) + '\n')

        # Determine training method based on adapter type
        if adapter_type.lower() == "lora":
            method = TrainingMethod.LORA_TRAINING
        else:
            method = TrainingMethod.ADAPTER_TRAINING

        # Create training config
        config = TrainingConfig(
            base_model=base_model,
            task_type=TaskType.CUSTOM_TASK,
            training_method=method,
            output_dir=output_dir,
            train_data_path=temp_file,
            num_train_epochs=3,
            learning_rate=1e-4,
            per_device_train_batch_size=4,
            save_steps=100
        )

        # Create and start training job
        job_id = await self.create_training_job(config)
        success = await self.start_training(job_id)

        if success:
            await self._wait_for_job_completion(job_id)
            return job_id
        else:
            raise Exception(f"Failed to create {adapter_type} model")

    async def distill_model(self, teacher_model: str, student_model: str,
                          train_data_path: str, output_dir: str) -> str:
        """Distill knowledge from teacher model to student model"""
        # Create training config for distillation
        config = TrainingConfig(
            base_model=student_model,
            task_type=TaskType.TEXT_GENERATION,
            training_method=TrainingMethod.DISTILLATION,
            output_dir=output_dir,
            train_data_path=train_data_path,
            num_train_epochs=5,
            learning_rate=5e-5,
            per_device_train_batch_size=8,
            save_steps=200,
            eval_steps=200
        )

        # Create and start training job
        job_id = await self.create_training_job(config)
        success = await self.start_training(job_id)

        if success:
            await self._wait_for_job_completion(job_id)
            return job_id
        else:
            raise Exception("Failed to start model distillation")

    async def evaluate_model(self, job_id: str, test_data_path: Optional[str] = None) -> Dict[str, float]:
        """Evaluate trained model"""
        if job_id not in self.training_jobs:
            raise ValueError(f"Training job {job_id} not found")

        job = self.training_jobs[job_id]
        if job.status != "completed" or job.job_id not in self.models:
            raise ValueError(f"Model for job {job_id} is not available")

        model = self.models[job.job_id]
        tokenizer = self.tokenizers[job.job_id]

        # Load test data if provided
        if test_data_path and os.path.exists(test_data_path):
            test_texts = await self._load_text_data(test_data_path)
            test_dataset = CustomDataset(test_texts, tokenizer, job.config.max_seq_length)

            # Create trainer for evaluation
            training_args = TrainingArguments(
                output_dir=job.config.output_dir,
                per_device_eval_batch_size=job.config.per_device_eval_batch_size,
                fp16=job.config.fp16
            )

            trainer = Trainer(
                model=model,
                args=training_args,
                eval_dataset=test_dataset,
                tokenizer=tokenizer
            )

            # Evaluate
            eval_results = trainer.evaluate()

            return {
                'eval_loss': eval_results.get('eval_loss', 0.0),
                'perplexity': np.exp(eval_results.get('eval_loss', 0.0)),
                'eval_samples_per_second': eval_results.get('eval_samples_per_second', 0.0)
            }

        return {}

    async def generate_text(self, job_id: str, prompt: str, max_length: int = 100,
                          temperature: float = 0.7) -> str:
        """Generate text using trained model"""
        if job_id not in self.training_jobs:
            raise ValueError(f"Training job {job_id} not found")

        job = self.training_jobs[job_id]
        if job.status != "completed" or job.job_id not in self.models:
            raise ValueError(f"Model for job {job_id} is not available")

        model = self.models[job.job_id]
        tokenizer = self.tokenizers[job.job_id]

        # Tokenize input
        inputs = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)

        # Move to device
        if self.gpu_available:
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from generated text
        if generated_text.startswith(prompt):
            generated_text = generated_text[len(prompt):].strip()

        return generated_text

    def _get_gpu_memory_usage(self) -> float:
        """Get GPU memory usage in GB"""
        if self.gpu_available and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024**3
        return 0.0

    def _find_convergence_epoch(self, log_history: List[Dict[str, Any]]) -> int:
        """Find the epoch where training converged"""
        if not log_history:
            return 0

        # Look for eval_loss trend
        eval_losses = [entry.get('eval_loss', float('inf')) for entry in log_history if 'eval_loss' in entry]

        if len(eval_losses) < 3:
            return 0

        # Find point where loss improvement becomes minimal
        for i in range(2, len(eval_losses)):
            recent_improvement = eval_losses[i-2] - eval_losses[i]
            if recent_improvement < 0.001:  # Less than 0.001 improvement
                return i

        return len(eval_losses) - 1

    def _record_training_history(self, job: TrainingJob, train_result, eval_result):
        """Record training history"""
        history_entry = {
            'job_id': job.job_id,
            'base_model': job.config.base_model,
            'task_type': job.config.task_type.value,
            'training_method': job.config.training_method.value,
            'created_at': job.created_at.isoformat(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'training_time': job.metrics.training_time if job.metrics else 0.0,
            'final_train_loss': train_result.training_loss,
            'final_eval_loss': eval_result.get('eval_loss', 0.0),
            'final_perplexity': np.exp(eval_result.get('eval_loss', 0.0)),
            'best_model_checkpoint': train_result.checkpoint
        }

        self.training_history.append(history_entry)

        # Keep only last 100 entries
        if len(self.training_history) > 100:
            self.training_history = self.training_history[-100:]

    async def _wait_for_job_completion(self, job_id: str, timeout: int = 3600):
        """Wait for training job to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if job_id not in self.training_jobs:
                raise ValueError(f"Training job {job_id} not found")

            job = self.training_jobs[job_id]
            if job.status in ["completed", "failed"]:
                return

            await asyncio.sleep(5)

        raise TimeoutError(f"Training job {job_id} did not complete within {timeout} seconds")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of training job"""
        if job_id not in self.training_jobs:
            return None

        job = self.training_jobs[job_id]

        status = {
            'job_id': job.job_id,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'base_model': job.config.base_model,
            'task_type': job.config.task_type.value,
            'training_method': job.config.training_method.value,
            'error_message': job.error_message
        }

        if job.metrics:
            status['metrics'] = asdict(job.metrics)

        return status

    def list_training_jobs(self) -> List[Dict[str, Any]]:
        """List all training jobs"""
        return [self.get_job_status(job_id) for job_id in self.training_jobs]

    def get_training_history(self) -> List[Dict[str, Any]]:
        """Get training history"""
        return self.training_history.copy()

    async def delete_job(self, job_id: str) -> bool:
        """Delete training job and associated files"""
        if job_id not in self.training_jobs:
            return False

        job = self.training_jobs[job_id]

        # Delete model from memory
        if job.job_id in self.models:
            del self.models[job.job_id]
        if job.job_id in self.tokenizers:
            del self.tokenizers[job.job_id]

        # Delete output directory
        try:
            import shutil
            if os.path.exists(job.config.output_dir):
                shutil.rmtree(job.config.output_dir)
        except Exception as e:
            logger.warning(f"Failed to delete output directory: {e}")

        # Remove from jobs
        del self.training_jobs[job_id]

        logger.info(f"Deleted training job {job_id}")
        return True

    async def shutdown(self):
        """Cleanup resources"""
        # Clear models from memory
        self.models.clear()
        self.tokenizers.clear()

        # Clear GPU cache
        if self.gpu_available and torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("CustomTrainer shutdown complete")

# Example usage
async def demonstrate_training():
    """Demonstrate custom training functionality"""
    trainer = CustomTrainer()

    # Create sample training data
    sample_examples = [
        {
            "prompt": "What is machine learning?",
            "response": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
        },
        {
            "prompt": "Explain neural networks.",
            "response": "Neural networks are computing systems inspired by biological neural networks that constitute animal brains. They consist of interconnected nodes that process information using connectionist approaches."
        }
    ]

    # Fine-tune with examples
    try:
        job_id = await trainer.fine_tune_with_examples(
            base_model="distilgpt2",  # Small model for demo
            examples=sample_examples,
            task_type=TaskType.QUESTION_ANSWERING,
            output_dir="./trained_model"
        )

        print(f"Started training job: {job_id}")

        # Wait for completion
        await trainer._wait_for_job_completion(job_id, timeout=300)

        # Check status
        status = trainer.get_job_status(job_id)
        print(f"Training status: {status['status']}")

        if status['status'] == 'completed':
            # Generate text with trained model
            generated = await trainer.generate_text(
                job_id=job_id,
                prompt="What is deep learning?",
                max_length=50
            )
            print(f"Generated text: {generated}")

    except Exception as e:
        print(f"Training failed: {e}")

    await trainer.shutdown()

if __name__ == "__main__":
    asyncio.run(demonstrate_training())