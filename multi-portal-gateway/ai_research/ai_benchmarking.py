"""
Comprehensive AI Benchmarking System for DMLogn8n
Advanced performance evaluation, comparison, and analysis tools for AI models
Based on latest research in AI evaluation and benchmarking (2024-2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import psutil
import gc
from collections import defaultdict, deque
import json
import warnings
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, roc_auc_score,
    confusion_matrix, classification_report, mean_squared_error,
    mean_absolute_error, r2_score
)
from scipy import stats
import wandb
from tqdm import tqdm


@dataclass
class BenchmarkConfig:
    """Configuration for AI benchmarking"""
    # Evaluation parameters
    num_runs: int = 5
    batch_size: int = 32
    max_samples: int = 10000
    warmup_runs: int = 2

    # Metrics to track
    track_accuracy: bool = True
    track_latency: bool = True
    track_memory: bool = True
    track_throughput: bool = True
    track_energy: bool = False  # Requires additional setup

    # Model categories
    test_transformers: bool = True
    test_multimodal: bool = True
    test_gnns: bool = True
    test_diffusion: bool = True
    test_rl: bool = True
    test_few_shot: bool = True
    test_continual: bool = True

    # Dataset configurations
    dataset_sizes: Dict[str, int] = field(default_factory=lambda: {
        'small': 1000,
        'medium': 5000,
        'large': 10000
    })

    # Hardware profiling
    profile_gpu: bool = True
    profile_cpu: bool = True
    mixed_precision: bool = True

    # Output settings
    save_results: bool = True
    save_plots: bool = True
    wandb_logging: bool = False
    output_dir: str = "./benchmark_results"


class BenchmarkMetrics:
    """Container for benchmark metrics"""
    def __init__(self):
        self.metrics = defaultdict(list)
        self.metadata = {}
        self.timestamps = []

    def add_metric(self, name: str, value: Union[float, int], timestamp: Optional[float] = None):
        """Add a metric value"""
        self.metrics[name].append(value)
        if timestamp is not None:
            self.timestamps.append(timestamp)
        elif len(self.timestamps) == 0:
            self.timestamps.append(time.time())

    def add_metadata(self, key: str, value: Any):
        """Add metadata"""
        self.metadata[key] = value

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        if metric_name not in self.metrics:
            return {}

        values = self.metrics[metric_name]
        return {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values),
            'q25': np.percentile(values, 25),
            'q75': np.percentile(values, 75),
            'count': len(values)
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to pandas DataFrame"""
        data = {}
        for metric_name, values in self.metrics.items():
            stats = self.get_stats(metric_name)
            for stat_name, stat_value in stats.items():
                data[f"{metric_name}_{stat_name}"] = [stat_value]

        return pd.DataFrame(data)


class LatencyProfiler:
    """Profile inference latency and throughput"""
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def profile_inference_time(self, model: nn.Module, input_data: torch.Tensor,
                             num_runs: Optional[int] = None) -> Dict[str, float]:
        """Profile inference time"""
        if num_runs is None:
            num_runs = self.config.num_runs

        model.eval()
        model.to(self.device)
        input_data = input_data.to(self.device)

        # Warmup runs
        with torch.no_grad():
            for _ in range(self.config.warmup_runs):
                _ = model(input_data)

        # Timing runs
        times = []
        with torch.no_grad():
            for _ in range(num_runs):
                start_time = time.perf_counter()
                output = model(input_data)
                if self.device.type == 'cuda':
                    torch.cuda.synchronize()
                end_time = time.perf_counter()
                times.append(end_time - start_time)

        # Calculate metrics
        return {
            'mean_latency': np.mean(times),
            'std_latency': np.std(times),
            'min_latency': np.min(times),
            'max_latency': np.max(times),
            'p95_latency': np.percentile(times, 95),
            'p99_latency': np.percentile(times, 99),
            'throughput': input_data.size(0) / np.mean(times)  # samples per second
        }

    def profile_batch_sizes(self, model: nn.Module, input_shape: Tuple[int, ...],
                           batch_sizes: List[int]) -> Dict[int, Dict[str, float]]:
        """Profile performance across different batch sizes"""
        results = {}

        for batch_size in batch_sizes:
            input_data = torch.randn(batch_size, *input_shape[1:])
            results[batch_size] = self.profile_inference_time(model, input_data)

        return results


class MemoryProfiler:
    """Profile memory usage during inference"""
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def profile_memory_usage(self, model: nn.Module, input_data: torch.Tensor) -> Dict[str, float]:
        """Profile memory usage"""
        model.eval()
        model.to(self.device)
        input_data = input_data.to(self.device)

        # Clear cache
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()

        initial_memory = 0
        if self.device.type == 'cuda':
            initial_memory = torch.cuda.memory_allocated()

        # Forward pass
        with torch.no_grad():
            output = model(input_data)

        peak_memory = 0
        if self.device.type == 'cuda':
            peak_memory = torch.cuda.max_memory_allocated()

        # Calculate memory metrics
        return {
            'initial_memory_mb': initial_memory / (1024 ** 2),
            'peak_memory_mb': peak_memory / (1024 ** 2),
            'memory_increase_mb': (peak_memory - initial_memory) / (1024 ** 2),
            'parameters_mb': sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 ** 2),
            'gradients_mb': sum(p.numel() * p.element_size() for p in model.parameters() if p.requires_grad) / (1024 ** 2)
        }


class AccuracyBenchmark:
    """Benchmark model accuracy on various tasks"""
    def __init__(self, config: BenchmarkConfig):
        self.config = config

    def benchmark_classification(self, model: nn.Module, test_dataloader,
                               task_name: str = "classification") -> Dict[str, float]:
        """Benchmark classification accuracy"""
        model.eval()
        device = next(model.parameters()).device

        all_predictions = []
        all_labels = []
        all_probabilities = []

        with torch.no_grad():
            for batch in test_dataloader:
                if isinstance(batch, (list, tuple)):
                    x, y = batch[0], batch[1]
                else:
                    x, y = batch.x, batch.y

                x = x.to(device)
                y = y.to(device)

                outputs = model(x)
                probabilities = F.softmax(outputs, dim=-1)
                predictions = outputs.argmax(dim=-1)

                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(y.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())

        # Compute metrics
        accuracy = accuracy_score(all_labels, all_predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_predictions, average='weighted')

        # Try to compute AUC (handle binary and multi-class cases)
        try:
            if len(np.unique(all_labels)) == 2:
                # Binary classification
                auc = roc_auc_score(all_labels, np.array(all_probabilities)[:, 1])
            else:
                # Multi-class classification
                auc = roc_auc_score(all_labels, all_probabilities, multi_class='ovr', average='weighted')
        except:
            auc = 0.0

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_roc': auc,
            'num_samples': len(all_labels),
            'num_classes': len(np.unique(all_labels))
        }

    def benchmark_regression(self, model: nn.Module, test_dataloader,
                            task_name: str = "regression") -> Dict[str, float]:
        """Benchmark regression accuracy"""
        model.eval()
        device = next(model.parameters()).device

        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for batch in test_dataloader:
                if isinstance(batch, (list, tuple)):
                    x, y = batch[0], batch[1]
                else:
                    x, y = batch.x, batch.y

                x = x.to(device)
                y = y.to(device)

                outputs = model(x)
                predictions = outputs.squeeze()

                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(y.cpu().numpy())

        # Compute metrics
        mse = mean_squared_error(all_labels, all_predictions)
        mae = mean_absolute_error(all_labels, all_predictions)
        r2 = r2_score(all_labels, all_predictions)
        rmse = np.sqrt(mse)

        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
            'num_samples': len(all_labels)
        }


class ModelComparator:
    """Compare multiple models across various metrics"""
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results = {}
        self.models = {}

    def add_model(self, name: str, model: nn.Module, model_type: str = "unknown"):
        """Add a model for comparison"""
        self.models[name] = {
            'model': model,
            'type': model_type,
            'parameters': sum(p.numel() for p in model.parameters())
        }

    def run_comparison(self, test_dataloaders: Dict[str, Any]) -> Dict[str, Dict]:
        """Run comprehensive comparison"""
        results = {}

        for model_name, model_info in self.models.items():
            print(f"Benchmarking model: {model_name}")
            model = model_info['model']
            model_type = model_info['type']

            model_results = {
                'model_info': {
                    'name': model_name,
                    'type': model_type,
                    'parameters': model_info['parameters']
                }
            }

            # Initialize profilers
            latency_profiler = LatencyProfiler(self.config)
            memory_profiler = MemoryProfiler(self.config)
            accuracy_benchmark = AccuracyBenchmark(self.config)

            # Get sample input for profiling
            sample_batch = next(iter(test_dataloaders.get('default', test_dataloaders[list(test_dataloaders.keys())[0]])))
            if isinstance(sample_batch, (list, tuple)):
                sample_input = sample_batch[0]
            else:
                sample_input = sample_batch.x

            # Profile latency
            if self.config.track_latency:
                latency_results = latency_profiler.profile_inference_time(model, sample_input)
                model_results['latency'] = latency_results

                # Profile different batch sizes
                batch_sizes = [1, 4, 16, 32, 64]
                batch_results = latency_profiler.profile_batch_sizes(model, sample_input.shape, batch_sizes)
                model_results['batch_performance'] = batch_results

            # Profile memory
            if self.config.track_memory:
                memory_results = memory_profiler.profile_memory_usage(model, sample_input)
                model_results['memory'] = memory_results

            # Profile accuracy
            if self.config.track_accuracy:
                for task_name, dataloader in test_dataloaders.items():
                    if task_name != 'default':
                        try:
                            if model_type in ['classification', 'transformer', 'few_shot']:
                                accuracy_results = accuracy_benchmark.benchmark_classification(
                                    model, dataloader, task_name
                                )
                            elif model_type in ['regression', 'rl']:
                                accuracy_results = accuracy_benchmark.benchmark_regression(
                                    model, dataloader, task_name
                                )
                            else:
                                # Try classification first, fall back to regression
                                try:
                                    accuracy_results = accuracy_benchmark.benchmark_classification(
                                        model, dataloader, task_name
                                    )
                                except:
                                    accuracy_results = accuracy_benchmark.benchmark_regression(
                                        model, dataloader, task_name
                                    )

                            model_results[f'accuracy_{task_name}'] = accuracy_results
                        except Exception as e:
                            print(f"Error benchmarking {task_name} for {model_name}: {e}")
                            model_results[f'accuracy_{task_name}'] = {'error': str(e)}

            results[model_name] = model_results

        self.results = results
        return results

    def generate_comparison_report(self, save_path: Optional[str] = None) -> str:
        """Generate comprehensive comparison report"""
        report = []
        report.append("# AI Model Benchmarking Report\n")
        report.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary table
        report.append("## Model Summary\n")
        report.append("| Model | Type | Parameters | Mean Latency (ms) | Peak Memory (MB) | Best Accuracy |")
        report.append("|-------|------|------------|-------------------|------------------|---------------|")

        for model_name, results in self.results.items():
            model_info = results['model_info']
            latency = results.get('latency', {}).get('mean_latency', 0) * 1000  # Convert to ms
            memory = results.get('memory', {}).get('peak_memory_mb', 0)

            # Find best accuracy
            best_accuracy = 0
            for key, value in results.items():
                if key.startswith('accuracy_') and isinstance(value, dict):
                    accuracy = value.get('accuracy', 0)
                    best_accuracy = max(best_accuracy, accuracy)

            report.append(f"| {model_name} | {model_info['type']} | {model_info['parameters']:,} | "
                         f"{latency:.2f} | {memory:.1f} | {best_accuracy:.3f} |")

        # Detailed results
        report.append("\n## Detailed Results\n")

        for model_name, results in self.results.items():
            report.append(f"\n### {model_name}\n")
            model_info = results['model_info']
            report.append(f"**Type:** {model_info['type']}\n")
            report.append(f"**Parameters:** {model_info['parameters']:,}\n")

            # Latency details
            if 'latency' in results:
                latency = results['latency']
                report.append(f"\n**Latency Performance:**\n")
                report.append(f"- Mean: {latency['mean_latency']*1000:.2f} ms\n")
                report.append(f"- Std: {latency['std_latency']*1000:.2f} ms\n")
                report.append(f"- P95: {latency['p95_latency']*1000:.2f} ms\n")
                report.append(f"- Throughput: {latency['throughput']:.1f} samples/s\n")

            # Memory details
            if 'memory' in results:
                memory = results['memory']
                report.append(f"\n**Memory Usage:**\n")
                report.append(f"- Peak: {memory['peak_memory_mb']:.1f} MB\n")
                report.append(f"- Parameters: {memory['parameters_mb']:.1f} MB\n")

            # Accuracy details
            report.append(f"\n**Task Performance:**\n")
            for key, value in results.items():
                if key.startswith('accuracy_') and isinstance(value, dict) and 'error' not in value:
                    task_name = key.replace('accuracy_', '')
                    report.append(f"- {task_name.capitalize()}:")
                    for metric, val in value.items():
                        if isinstance(val, float):
                            report.append(f"  - {metric}: {val:.3f}")
                        else:
                            report.append(f"  - {metric}: {val}")
                    report.append("")

        report_text = "\n".join(report)

        if save_path:
            with open(save_path, 'w') as f:
                f.write(report_text)

        return report_text

    def plot_comparisons(self, save_dir: Optional[str] = None):
        """Create comparison plots"""
        if save_dir is None:
            save_dir = self.config.output_dir

        # Extract data for plotting
        model_names = list(self.results.keys())
        latencies = []
        memories = []
        parameters = []
        accuracies = []

        for model_name in model_names:
            results = self.results[model_name]
            latencies.append(results.get('latency', {}).get('mean_latency', 0) * 1000)
            memories.append(results.get('memory', {}).get('peak_memory_mb', 0))
            parameters.append(results['model_info']['parameters'])

            # Find best accuracy
            best_acc = 0
            for key, value in results.items():
                if key.startswith('accuracy_') and isinstance(value, dict):
                    acc = value.get('accuracy', 0)
                    best_acc = max(best_acc, acc)
            accuracies.append(best_acc)

        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Latency comparison
        axes[0, 0].bar(model_names, latencies)
        axes[0, 0].set_title('Mean Latency Comparison')
        axes[0, 0].set_ylabel('Latency (ms)')
        axes[0, 0].tick_params(axis='x', rotation=45)

        # Memory comparison
        axes[0, 1].bar(model_names, memories)
        axes[0, 1].set_title('Peak Memory Comparison')
        axes[0, 1].set_ylabel('Memory (MB)')
        axes[0, 1].tick_params(axis='x', rotation=45)

        # Parameter count comparison
        axes[1, 0].bar(model_names, [p/1e6 for p in parameters])
        axes[1, 0].set_title('Model Size Comparison')
        axes[1, 0].set_ylabel('Parameters (M)')
        axes[1, 0].tick_params(axis='x', rotation=45)

        # Accuracy comparison
        axes[1, 1].bar(model_names, accuracies)
        axes[1, 1].set_title('Best Accuracy Comparison')
        axes[1, 1].set_ylabel('Accuracy')
        axes[1, 1].tick_params(axis='x', rotation=45)

        plt.tight_layout()

        if save_dir:
            plt.savefig(f"{save_dir}/model_comparison.png", dpi=300, bbox_inches='tight')
        else:
            plt.show()

        # Create scatter plot: Accuracy vs Latency
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(latencies, accuracies, s=[p/1e4 for p in parameters],
                            c=range(len(model_names)), cmap='viridis', alpha=0.7)
        plt.xlabel('Mean Latency (ms)')
        plt.ylabel('Best Accuracy')
        plt.title('Accuracy vs Latency (bubble size = model parameters)')

        for i, name in enumerate(model_names):
            plt.annotate(name, (latencies[i], accuracies[i]), xytext=(5, 5),
                        textcoords='offset points', fontsize=9)

        plt.colorbar(scatter, label='Model Index')
        plt.grid(True, alpha=0.3)

        if save_dir:
            plt.savefig(f"{save_dir}/accuracy_vs_latency.png", dpi=300, bbox_inches='tight')
        else:
            plt.show()


class BenchmarkSuite:
    """Complete benchmarking suite for AI models"""
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.comparator = ModelComparator(config)
        self.metrics = BenchmarkMetrics()

        # Initialize wandb if enabled
        if config.wandb_logging:
            wandb.init(project="dmlogn8n-benchmarking", config=config.__dict__)

    def benchmark_transformer_models(self, models: Dict[str, nn.Module], test_data: torch.Tensor):
        """Benchmark transformer models"""
        print("Benchmarking transformer models...")

        for name, model in models.items():
            self.comparator.add_model(name, model, "transformer")

        # Create dummy dataloader for testing
        test_dataloader = [(test_data, torch.randint(0, 1000, (test_data.size(0),)))]

        results = self.comparator.run_comparison({'transformer': test_dataloader})
        return results

    def benchmark_multimodal_models(self, models: Dict[str, nn.Module], test_data: Dict[str, torch.Tensor]):
        """Benchmark multimodal models"""
        print("Benchmarking multimodal models...")

        for name, model in models.items():
            self.comparator.add_model(name, model, "multimodal")

        # Create multimodal test dataloader
        test_dataloader = [(test_data, torch.randint(0, 10, (test_data['image'].size(0),)))]

        results = self.comparator.run_comparison({'multimodal': test_dataloader})
        return results

    def benchmark_gnn_models(self, models: Dict[str, nn.Module], test_data: torch.Tensor):
        """Benchmark graph neural network models"""
        print("Benchmarking GNN models...")

        for name, model in models.items():
            self.comparator.add_model(name, model, "gnn")

        # Create GNN test dataloader
        test_dataloader = [(test_data, torch.randint(0, 10, (test_data.size(0),)))]

        results = self.comparator.run_comparison({'gnn': test_dataloader})
        return results

    def benchmark_diffusion_models(self, models: Dict[str, nn.Module], test_data: torch.Tensor):
        """Benchmark diffusion models"""
        print("Benchmarking diffusion models...")

        for name, model in models.items():
            self.comparator.add_model(name, model, "diffusion")

        # Create diffusion test dataloader
        test_dataloader = [(test_data, torch.randint(0, 1000, (test_data.size(0),)))]

        results = self.comparator.run_comparison({'diffusion': test_dataloader})
        return results

    def benchmark_rl_agents(self, agents: Dict[str, Any], test_env):
        """Benchmark reinforcement learning agents"""
        print("Benchmarking RL agents...")

        for name, agent in agents.items():
            self.comparator.add_model(name, agent, "rl")

        # Create RL test dataloader
        test_dataloader = [('rl', test_env)]

        results = self.comparator.run_comparison({'rl': test_dataloader})
        return results

    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("Running full benchmark suite...")

        all_results = {}

        # Create test data
        test_sizes = self.config.dataset_sizes
        test_data = {
            'small': torch.randn(test_sizes['small'], 256),
            'medium': torch.randn(test_sizes['medium'], 256),
            'large': torch.randn(test_sizes['large'], 256)
        }

        # Benchmark different model types
        if self.config.test_transformers:
            # Create dummy transformer models for testing
            transformer_models = {
                'small_transformer': nn.Sequential(
                    nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 100)
                ),
                'large_transformer': nn.Sequential(
                    nn.Linear(256, 512), nn.ReLU(), nn.Linear(512, 100)
                )
            }
            all_results['transformers'] = self.benchmark_transformer_models(
                transformer_models, test_data['medium']
            )

        if self.config.test_multimodal:
            # Create dummy multimodal models
            multimodal_models = {
                'vision_model': nn.Sequential(
                    nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 100)
                ),
                'text_model': nn.Sequential(
                    nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 100)
                )
            }
            all_results['multimodal'] = self.benchmark_multimodal_models(
                multimodal_models, {'image': test_data['small']}
            )

        # Generate comprehensive report
        if self.config.save_results:
            report = self.comparator.generate_comparison_report(
                f"{self.config.output_dir}/benchmark_report.md"
            )

        if self.config.save_plots:
            self.comparator.plot_comparisons(self.config.output_dir)

        # Log to wandb if enabled
        if self.config.wandb_logging:
            for model_name, results in self.comparator.results.items():
                wandb.log({f"{model_name}_latency": results.get('latency', {}).get('mean_latency', 0),
                          f"{model_name}_memory": results.get('memory', {}).get('peak_memory_mb', 0)})

        return all_results


def create_benchmark_config(benchmark_type: str = "standard") -> BenchmarkConfig:
    """Create benchmark configuration"""
    if benchmark_type == "quick":
        return BenchmarkConfig(
            num_runs=3,
            batch_size=16,
            max_samples=1000,
            track_energy=False
        )
    elif benchmark_type == "comprehensive":
        return BenchmarkConfig(
            num_runs=10,
            batch_size=64,
            max_samples=50000,
            track_energy=True,
            profile_gpu=True,
            profile_cpu=True
        )
    else:
        return BenchmarkConfig()


if __name__ == "__main__":
    print("Creating comprehensive AI benchmarking system...")

    # Create configuration
    config = create_benchmark_config("standard")
    benchmark_suite = BenchmarkSuite(config)

    print(f"Benchmark configuration:")
    print(f"  - Number of runs: {config.num_runs}")
    print(f"  - Batch size: {config.batch_size}")
    print(f"  - Track latency: {config.track_latency}")
    print(f"  - Track memory: {config.track_memory}")
    print(f"  - Track accuracy: {config.track_accuracy}")

    # Create test models for demonstration
    test_models = {
        'model_a': nn.Sequential(
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 10)
        ),
        'model_b': nn.Sequential(
            nn.Linear(256, 256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 10)
        ),
        'model_c': nn.Sequential(
            nn.Linear(256, 512), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(512, 256), nn.ReLU(), nn.Linear(256, 128),
            nn.ReLU(), nn.Linear(128, 10)
        )
    }

    # Add models to comparator
    for name, model in test_models.items():
        benchmark_suite.comparator.add_model(name, model, "classification")

    # Create test data
    test_data = torch.randn(1000, 256)
    test_labels = torch.randint(0, 10, (1000,))

    # Create test dataloader
    test_dataloader = list(zip(torch.split(test_data, 32), torch.split(test_labels, 32)))

    print("\nRunning model comparison...")
    results = benchmark_suite.comparator.run_comparison({'test_task': test_dataloader})

    # Generate report
    print("\nGenerating comparison report...")
    report = benchmark_suite.comparator.generate_comparison_report()
    print("Report generated successfully!")

    # Create plots
    print("Creating comparison plots...")
    benchmark_suite.comparator.plot_comparisons()

    # Print summary
    print("\nBenchmark Results Summary:")
    for model_name, model_results in results.items():
        latency = model_results.get('latency', {}).get('mean_latency', 0) * 1000
        memory = model_results.get('memory', {}).get('peak_memory_mb', 0)
        accuracy = model_results.get('accuracy_test_task', {}).get('accuracy', 0)

        print(f"  {model_name}:")
        print(f"    - Latency: {latency:.2f} ms")
        print(f"    - Memory: {memory:.1f} MB")
        print(f"    - Accuracy: {accuracy:.3f}")

    print("\nAI benchmarking system initialized successfully!")