#!/usr/bin/env python3
"""
Neuro-Feedback System - Real-time Brain Activity Visualization
Advanced visualization and feedback system for neural signal monitoring and training.

This module provides comprehensive real-time visualization of brain activity,
enabling users to see their neural patterns, train cognitive skills, and receive
immediate feedback on their mental states for improved brain-computer interface
performance.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import PatchCollection
import seaborn as sns
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import tkinter as tk
from tkinter import ttk, Canvas, Frame, Label, Scale, Button
import pygame
from PIL import Image, ImageDraw, ImageTk
import cv2
from scipy import signal
from scipy.interpolate import interp1d

# Visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

# Local imports
from .neural_interface import ProcessedSignal, BrainWave
from .thought_detector import ThoughtPattern, ThoughtType

class FeedbackType(Enum):
    """Types of neuro-feedback displays"""
    BRAIN_MAP = "brain_map"  # 2D/3D brain activity map
    WAVE_FORM = "wave_form"  # Real-time EEG waveforms
    SPECTRUM = "spectrum"  # Frequency spectrum analysis
    CONNECTIVITY = "connectivity"  # Brain connectivity visualization
    PERFORMANCE = "performance"  # Performance metrics dashboard
    TRAINING = "training"  # Training game interface
    IMMERSIVE = "immersive"  # Full immersive feedback

class VisualizationMode(Enum):
    """Visualization rendering modes"""
    REAL_TIME = "real_time"  # Live streaming visualization
    HISTORICAL = "historical"  # Historical data analysis
    TRAINING = "training"  # Training mode with feedback
    ANALYSIS = "analysis"  # Deep analysis mode
    PRESENTATION = "presentation"  # Presentation-style display

@dataclass
class FeedbackSession:
    """Neuro-feedback session configuration"""
    session_id: str
    user_id: str
    start_time: float
    duration: float
    feedback_types: List[FeedbackType]
    target_metrics: Dict[str, float]
    baseline_data: Dict[str, Any]
    performance_thresholds: Dict[str, float]

@dataclass
class NeuroFeedback:
    """Real-time neuro-feedback data"""
    timestamp: float
    brain_activity: Dict[str, float]
    performance_metrics: Dict[str, float]
    target_achievement: Dict[str, bool]
    feedback_intensity: float
    recommendations: List[str]

class BrainVisualizer:
    """Advanced brain activity visualization engine"""

    def __init__(self, num_channels: int = 8):
        self.num_channels = num_channels
        self.channel_positions = self._generate_channel_positions()
        self.color_maps = self._initialize_color_maps()
        self.brain_topology = self._load_brain_topology()

    def _generate_channel_positions(self) -> Dict[str, Tuple[float, float]]:
        """Generate 2D positions for EEG channels (10-20 system approximation)"""
        positions = {
            'Fp1': (0.2, 0.8),
            'Fp2': (0.8, 0.8),
            'F3': (0.3, 0.6),
            'F4': (0.7, 0.6),
            'C3': (0.2, 0.5),
            'Cz': (0.5, 0.5),
            'C4': (0.8, 0.5),
            'P3': (0.3, 0.3),
            'P4': (0.7, 0.3),
            'O1': (0.2, 0.1),
            'O2': (0.8, 0.1)
        }

        # For fewer channels, select subset
        if self.num_channels <= len(positions):
            channel_names = list(positions.keys())[:self.num_channels]
            return {name: positions[name] for name in channel_names}

        return positions

    def _initialize_color_maps(self) -> Dict[str, Any]:
        """Initialize color schemes for brain visualization"""
        return {
            'brain_activity': plt.cm.RdYlBu_r,  # Red (high) to Blue (low)
            'connectivity': plt.cm.viridis,  # Green to yellow
            'performance': plt.cm.RdYlGn,  # Red (poor) to Green (excellent)
            'waves': plt.cm.Set3,  # Distinct colors for different waves
            'attention': plt.cm.hot,  # Hot colormap for attention
            'emotion': plt.cm.coolwarm  # Cool to warm for emotions
        }

    def _load_brain_topology(self) -> Dict[str, Any]:
        """Load brain topology for realistic visualization"""
        return {
            'outline_points': [
                (0.1, 0.9), (0.9, 0.9),  # Top
                (0.95, 0.5), (0.9, 0.1),  # Right side
                (0.1, 0.1), (0.05, 0.5)   # Left side
            ],
            'hemispheres': {
                'left': [(0.05, 0.1), (0.5, 0.1), (0.5, 0.9), (0.05, 0.9)],
                'right': [(0.5, 0.1), (0.95, 0.1), (0.95, 0.9), (0.5, 0.9)]
            },
            'lobes': {
                'frontal': [(0.2, 0.5), (0.8, 0.5), (0.8, 0.9), (0.2, 0.9)],
                'parietal': [(0.3, 0.3), (0.7, 0.3), (0.7, 0.5), (0.3, 0.5)],
                'occipital': [(0.3, 0.1), (0.7, 0.1), (0.7, 0.3), (0.3, 0.3)],
                'temporal': [(0.1, 0.4), (0.2, 0.4), (0.2, 0.7), (0.1, 0.7)]
            }
        }

    def create_brain_map(self, brain_activity: Dict[str, float],
                         mode: str = 'topo') -> go.Figure:
        """Create 2D brain activity map"""
        fig = go.Figure()

        # Create brain outline
        outline_x = [p[0] for p in self.brain_topology['outline_points']] + [self.brain_topology['outline_points'][0][0]]
        outline_y = [p[1] for p in self.brain_topology['outline_points']] + [self.brain_topology['outline_points'][0][1]]

        # Add brain outline
        fig.add_trace(go.Scatter(
            x=outline_x, y=outline_y,
            mode='lines',
            line=dict(color='black', width=2),
            name='Brain Outline',
            showlegend=False
        ))

        # Add channel activity
        if mode == 'channels':
            for i, (channel, pos) in enumerate(self.channel_positions.items()):
                activity = brain_activity.get(channel, 0.5)
                color = self.color_maps['brain_activity'](activity)

                # Add channel point
                fig.add_trace(go.Scatter(
                    x=[pos[0]], y=[pos[1]],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color=[f'rgb({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)})'],
                        line=dict(width=2, color='black')
                    ),
                    name=channel,
                    text=f'{channel}: {activity:.2f}',
                    showlegend=True
                ))

        # Create heatmap overlay
        if mode == 'heatmap':
            self._add_heatmap_overlay(fig, brain_activity)

        # Configure layout
        fig.update_layout(
            title='Real-time Brain Activity Map',
            xaxis=dict(range=[0, 1], showgrid=False, zeroline=False),
            yaxis=dict(range=[0, 1], showgrid=False, zeroline=False),
            showlegend=True,
            width=600,
            height=600,
            plot_bgcolor='lightgray'
        )

        return fig

    def _add_heatmap_overlay(self, fig: go.Figure, brain_activity: Dict[str, float]):
        """Add interpolated heatmap overlay to brain map"""
        # Create grid for interpolation
        grid_size = 50
        x_grid = np.linspace(0, 1, grid_size)
        y_grid = np.linspace(0, 1, grid_size)
        X, Y = np.meshgrid(x_grid, y_grid)

        # Interpolate activity values
        if self.channel_positions and brain_activity:
            positions = np.array(list(self.channel_positions.values()))
            values = np.array([brain_activity.get(ch, 0.5) for ch in self.channel_positions.keys()])

            try:
                from scipy.interpolate import RBFInterpolator
                interpolator = RBFInterpolator(positions, values)
                Z = interpolator(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)

                # Create heatmap
                fig.add_trace(go.Heatmap(
                    x=x_grid,
                    y=y_grid,
                    z=Z,
                    colorscale='RdYlBu_r',
                    showscale=True,
                    name='Brain Activity',
                    opacity=0.7
                ))
            except ImportError:
                # Fallback to simple distance-based interpolation
                Z = np.zeros_like(X)
                for i in range(grid_size):
                    for j in range(grid_size):
                        point = np.array([X[i, j], Y[i, j]])
                        distances = np.linalg.norm(positions - point, axis=1)
                        weights = 1 / (distances + 1e-6)
                        weights /= np.sum(weights)
                        Z[i, j] = np.sum(weights * values)

                fig.add_trace(go.Heatmap(
                    x=x_grid,
                    y=y_grid,
                    z=Z,
                    colorscale='RdYlBu_r',
                    showscale=True,
                    name='Brain Activity',
                    opacity=0.7
                ))

    def create_waveform_display(self, signals: np.ndarray,
                               brain_waves: Dict[str, float],
                               sampling_rate: int = 250) -> go.Figure:
        """Create real-time EEG waveform display"""
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Raw EEG Signals', 'Brain Wave Power', 'Signal Quality'],
            vertical_spacing=0.1
        )

        # Time axis
        time_axis = np.arange(signals.shape[0]) / sampling_rate

        # Plot raw signals
        for ch in range(min(signals.shape[1], 4)):  # Limit to 4 channels for clarity
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=signals[:, ch],
                    mode='lines',
                    name=f'Channel {ch+1}',
                    line=dict(width=1)
                ),
                row=1, col=1
            )

        # Plot brain wave powers
        wave_names = list(brain_waves.keys())
        wave_values = list(brain_waves.values())

        fig.add_trace(
            go.Bar(
                x=wave_names,
                y=wave_values,
                name='Brain Wave Power',
                marker_color=['red', 'orange', 'yellow', 'green', 'blue', 'purple'][:len(wave_names)]
            ),
            row=2, col=1
        )

        # Signal quality indicator (placeholder)
        quality_time = time_axis[-100:] if len(time_axis) > 100 else time_axis
        quality_values = np.random.uniform(0.7, 1.0, len(quality_time))  # Placeholder

        fig.add_trace(
            go.Scatter(
                x=quality_time,
                y=quality_values,
                mode='lines',
                name='Signal Quality',
                line=dict(color='green', width=2)
            ),
            row=3, col=1
        )

        # Update layout
        fig.update_layout(
            title='Real-time EEG Monitoring',
            height=800,
            showlegend=True
        )

        # Update x-axis labels
        fig.update_xaxes(title_text='Time (s)', row=3, col=1)
        fig.update_yaxes(title_text='Amplitude (μV)', row=1, col=1)
        fig.update_yaxes(title_text='Power', row=2, col=1)
        fig.update_yaxes(title_text='Quality', row=3, col=1, range=[0, 1])

        return fig

    def create_connectivity_map(self, connectivity_matrix: np.ndarray) -> go.Figure:
        """Create brain connectivity visualization"""
        fig = go.Figure()

        # Create heatmap of connectivity
        fig.add_trace(go.Heatmap(
            z=connectivity_matrix,
            colorscale='Viridis',
            name='Connectivity Strength',
            showscale=True
        ))

        # Add channel labels if available
        if self.channel_positions and len(self.channel_positions) == connectivity_matrix.shape[0]:
            channel_names = list(self.channel_positions.keys())
            fig.update_xaxes(ticktext=channel_names, tickvals=list(range(len(channel_names))))
            fig.update_yaxes(ticktext=channel_names, tickvals=list(range(len(channel_names))))

        fig.update_layout(
            title='Brain Connectivity Matrix',
            xaxis_title='Channels',
            yaxis_title='Channels',
            width=600,
            height=600
        )

        return fig

    def create_performance_dashboard(self, metrics: Dict[str, float],
                                    targets: Dict[str, float]) -> go.Figure:
        """Create performance metrics dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Focus Level', 'Relaxation', 'Cognitive Load', 'Progress'],
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )

        # Focus gauge
        focus_current = metrics.get('focus', 0.5)
        focus_target = targets.get('focus', 0.7)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=focus_current,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Focus"},
                gauge={
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, focus_target], 'color': "lightgray"},
                        {'range': [focus_target, 1], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': focus_target
                    }
                }
            ),
            row=1, col=1
        )

        # Relaxation gauge
        relax_current = metrics.get('relaxation', 0.5)
        relax_target = targets.get('relaxation', 0.6)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=relax_current,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Relaxation"},
                gauge={
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, relax_target], 'color': "lightgray"},
                        {'range': [relax_target, 1], 'color': "lightblue"}
                    ],
                    'threshold': {
                        'line': {'color': "orange", 'width': 4},
                        'thickness': 0.75,
                        'value': relax_target
                    }
                }
            ),
            row=1, col=2
        )

        # Cognitive load bar chart
        load_metrics = {
            'Working Memory': metrics.get('working_memory', 0.5),
            'Attention': metrics.get('attention', 0.5),
            'Processing': metrics.get('processing', 0.5),
            'Executive': metrics.get('executive', 0.5)
        }

        fig.add_trace(
            go.Bar(
                x=list(load_metrics.keys()),
                y=list(load_metrics.values()),
                name='Cognitive Load',
                marker_color='purple'
            ),
            row=2, col=1
        )

        # Progress over time (placeholder data)
        progress_time = np.arange(20)
        progress_values = np.random.uniform(0.3, 0.8, 20)  # Placeholder

        fig.add_trace(
            go.Scatter(
                x=progress_time,
                y=progress_values,
                mode='lines+markers',
                name='Progress',
                line=dict(color='orange', width=2)
            ),
            row=2, col=2
        )

        fig.update_layout(
            title='Performance Dashboard',
            height=800,
            showlegend=False
        )

        return fig

class FeedbackEngine:
    """Real-time feedback generation engine"""

    def __init__(self):
        self.feedback_strategies = self._initialize_feedback_strategies()
        self.performance_tracker = PerformanceTracker()
        self.adaptive_thresholds = AdaptiveThresholds()

    def _initialize_feedback_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize different feedback strategies"""
        return {
            'visual': {
                'type': 'visual',
                'modalities': ['color', 'brightness', 'animation', 'patterns'],
                'latency': 0.05,  # 50ms latency target
                'intensity_range': (0, 1),
                'adaptation_rate': 0.1
            },
            'auditory': {
                'type': 'auditory',
                'modalities': ['frequency', 'volume', 'rhythm', 'timbre'],
                'latency': 0.1,  # 100ms latency target
                'intensity_range': (0, 1),
                'frequency_range': (200, 2000)  # Hz
            },
            'haptic': {
                'type': 'haptic',
                'modalities': ['vibration', 'pressure', 'temperature'],
                'latency': 0.05,
                'intensity_range': (0, 1),
                'adaptation_rate': 0.15
            },
            'gamified': {
                'type': 'gamified',
                'modalities': ['points', 'levels', 'achievements', 'challenges'],
                'latency': 0.2,
                'intensity_range': (0, 100),
                'progress_tracking': True
            }
        }

    def generate_feedback(self, brain_activity: Dict[str, float],
                         targets: Dict[str, float],
                         strategy: str = 'visual') -> NeuroFeedback:
        """Generate real-time feedback based on brain activity"""
        current_time = time.time()

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(
            brain_activity, targets
        )

        # Check target achievement
        target_achievement = self._check_target_achievement(
            performance_metrics, targets
        )

        # Calculate feedback intensity
        feedback_intensity = self._calculate_feedback_intensity(
            performance_metrics, target_achievement
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            performance_metrics, target_achievement
        )

        # Create feedback object
        feedback = NeuroFeedback(
            timestamp=current_time,
            brain_activity=brain_activity,
            performance_metrics=performance_metrics,
            target_achievement=target_achievement,
            feedback_intensity=feedback_intensity,
            recommendations=recommendations
        )

        # Update performance tracker
        self.performance_tracker.update(feedback)

        return feedback

    def _calculate_performance_metrics(self, brain_activity: Dict[str, float],
                                     targets: Dict[str, float]) -> Dict[str, float]:
        """Calculate performance metrics from brain activity"""
        metrics = {}

        # Focus level (Beta/Alpha ratio)
        beta = brain_activity.get('beta', 0)
        alpha = brain_activity.get('alpha', 0)
        metrics['focus'] = beta / (alpha + 1e-10)
        metrics['focus'] = np.clip(metrics['focus'] / 2, 0, 1)  # Normalize

        # Relaxation level (Alpha/Theta ratio)
        theta = brain_activity.get('theta', 0)
        metrics['relaxation'] = alpha / (theta + 1e-10)
        metrics['relaxation'] = np.clip(metrics['relaxation'] / 3, 0, 1)

        # Cognitive load (Gamma/Beta ratio)
        gamma = brain_activity.get('gamma', 0)
        metrics['cognitive_load'] = gamma / (beta + 1e-10)
        metrics['cognitive_load'] = np.clip(metrics['cognitive_load'], 0, 1)

        # Mental effort
        total_power = sum(brain_activity.values())
        if total_power > 0:
            metrics['mental_effort'] = (beta + gamma) / total_power
        else:
            metrics['mental_effort'] = 0.5

        # Stress indicator (High Beta and Theta)
        high_beta = brain_activity.get('high_beta', 0)
        metrics['stress'] = (high_beta + theta) / (total_power + 1e-10)
        metrics['stress'] = np.clip(metrics['stress'], 0, 1)

        return metrics

    def _check_target_achievement(self, performance_metrics: Dict[str, float],
                                 targets: Dict[str, float]) -> Dict[str, bool]:
        """Check which performance targets are being achieved"""
        achievement = {}

        for metric, target_value in targets.items():
            current_value = performance_metrics.get(metric, 0)
            tolerance = 0.1  # 10% tolerance
            achievement[metric] = abs(current_value - target_value) <= tolerance

        return achievement

    def _calculate_feedback_intensity(self, performance_metrics: Dict[str, float],
                                    target_achievement: Dict[str, bool]) -> float:
        """Calculate feedback intensity based on performance"""
        if not target_achievement:
            return 0.5

        # Calculate achievement rate
        achieved_count = sum(target_achievement.values())
        total_count = len(target_achievement)
        achievement_rate = achieved_count / total_count

        # Calculate deviation from targets
        deviations = []
        for metric, achieved in target_achievement.items():
            if not achieved:
                current = performance_metrics.get(metric, 0)
                target = 0.7  # Default target
                deviation = abs(current - target)
                deviations.append(deviation)

        avg_deviation = np.mean(deviations) if deviations else 0

        # Calculate intensity (higher when further from target)
        intensity = achievement_rate * (1 - avg_deviation)
        return np.clip(intensity, 0, 1)

    def _generate_recommendations(self, performance_metrics: Dict[str, float],
                                target_achievement: Dict[str, bool]) -> List[str]:
        """Generate personalized recommendations based on performance"""
        recommendations = []

        # Focus recommendations
        if not target_achievement.get('focus', True):
            if performance_metrics['focus'] < 0.5:
                recommendations.append("Try to concentrate on a single point")
                recommendations.append("Reduce distractions in your environment")
            else:
                recommendations.append("Good focus! Maintain this level")

        # Relaxation recommendations
        if not target_achievement.get('relaxation', True):
            if performance_metrics['relaxation'] < 0.5:
                recommendations.append("Take deep breaths and relax your muscles")
                recommendations.append("Focus on pleasant, calming thoughts")
            else:
                recommendations.append("Excellent relaxation state")

        # Cognitive load recommendations
        if performance_metrics['cognitive_load'] > 0.8:
            recommendations.append("High mental load detected - consider taking a break")
        elif performance_metrics['cognitive_load'] < 0.3:
            recommendations.append("Low cognitive activity - try engaging in a mental task")

        # Stress recommendations
        if performance_metrics['stress'] > 0.7:
            recommendations.append("High stress detected - practice relaxation techniques")
            recommendations.append("Consider progressive muscle relaxation")

        return recommendations

class PerformanceTracker:
    """Track performance over time for adaptive feedback"""

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.performance_history = deque(maxlen=history_size)
        self.feedback_history = deque(maxlen=history_size)
        self.trend_analyzer = TrendAnalyzer()

    def update(self, feedback: NeuroFeedback):
        """Update performance history with new feedback"""
        self.performance_history.append({
            'timestamp': feedback.timestamp,
            'metrics': feedback.performance_metrics.copy(),
            'achievements': feedback.target_achievement.copy()
        })

        self.feedback_history.append(feedback)

        # Update trend analysis
        self.trend_analyzer.update(feedback)

    def get_performance_trends(self, window_size: int = 50) -> Dict[str, Any]:
        """Get recent performance trends"""
        if len(self.performance_history) < window_size:
            return {}

        recent_data = list(self.performance_history)[-window_size:]

        trends = {}
        for metric in ['focus', 'relaxation', 'cognitive_load']:
            values = [d['metrics'].get(metric, 0) for d in recent_data]
            if values:
                trends[metric] = {
                    'current': values[-1],
                    'average': np.mean(values),
                    'trend': 'improving' if values[-1] > values[0] else 'declining',
                    'stability': 1 - np.std(values)  # Higher is more stable
                }

        return trends

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.performance_history:
            return {}

        # Calculate session metrics
        session_duration = time.time() - self.performance_history[0]['timestamp']
        total_samples = len(self.performance_history)

        # Achievement rates
        achievement_counts = {}
        for data in self.performance_history:
            for metric, achieved in data['achievements'].items():
                if metric not in achievement_counts:
                    achievement_counts[metric] = {'achieved': 0, 'total': 0}
                achievement_counts[metric]['total'] += 1
                if achieved:
                    achievement_counts[metric]['achieved'] += 1

        achievement_rates = {
            metric: counts['achieved'] / counts['total']
            for metric, counts in achievement_counts.items()
        }

        return {
            'duration': session_duration,
            'total_samples': total_samples,
            'achievement_rates': achievement_rates,
            'average_performance': self.trend_analyzer.get_average_performance()
        }

class TrendAnalyzer:
    """Analyze performance trends over time"""

    def __init__(self):
        self.trend_data = {}
        self.update_frequency = 10  # Update every 10 samples

    def update(self, feedback: NeuroFeedback):
        """Update trend analysis with new feedback"""
        for metric, value in feedback.performance_metrics.items():
            if metric not in self.trend_data:
                self.trend_data[metric] = deque(maxlen=100)

            self.trend_data[metric].append({
                'timestamp': feedback.timestamp,
                'value': value
            })

    def get_trend(self, metric: str, window_size: int = 20) -> str:
        """Get trend for specific metric"""
        if metric not in self.trend_data or len(self.trend_data[metric]) < window_size:
            return 'insufficient_data'

        recent_values = [d['value'] for d in list(self.trend_data[metric])[-window_size:]]
        if len(recent_values) < 2:
            return 'stable'

        # Calculate linear trend
        x = np.arange(len(recent_values))
        slope = np.polyfit(x, recent_values, 1)[0]

        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'

    def get_average_performance(self) -> Dict[str, float]:
        """Get average performance across all metrics"""
        averages = {}
        for metric, data in self.trend_data.items():
            if data:
                values = [d['value'] for d in data]
                averages[metric] = np.mean(values)
        return averages

class AdaptiveThresholds:
    """Adaptive thresholds for personalized feedback"""

    def __init__(self):
        self.baseline_values = {}
        self.adaptation_rate = 0.05
        self.min_samples = 50

    def update_baseline(self, metrics: Dict[str, float]):
        """Update baseline values with new metrics"""
        for metric, value in metrics.items():
            if metric not in self.baseline_values:
                self.baseline_values[metric] = {
                    'values': deque(maxlen=100),
                    'baseline': value,
                    'std': 0.1
                }

            self.baseline_values[metric]['values'].append(value)

            # Update baseline and std if enough samples
            if len(self.baseline_values[metric]['values']) >= self.min_samples:
                values_array = np.array(list(self.baseline_values[metric]['values']))
                new_baseline = np.mean(values_array)
                new_std = np.std(values_array)

                # Adaptive update
                self.baseline_values[metric]['baseline'] = (
                    (1 - self.adaptation_rate) * self.baseline_values[metric]['baseline'] +
                    self.adaptation_rate * new_baseline
                )
                self.baseline_values[metric]['std'] = (
                    (1 - self.adaptation_rate) * self.baseline_values[metric]['std'] +
                    self.adaptation_rate * new_std
                )

    def get_adaptive_target(self, metric: str, difficulty: float = 0.5) -> float:
        """Get adaptive target for specific metric"""
        if metric not in self.baseline_values:
            return 0.7  # Default target

        baseline = self.baseline_values[metric]['baseline']
        std = self.baseline_values[metric]['std']

        # Set target based on difficulty (0 = easy, 1 = hard)
        if difficulty < 0.3:
            target = baseline + std * 0.5  # Easy target
        elif difficulty < 0.7:
            target = baseline + std  # Medium target
        else:
            target = baseline + std * 1.5  # Hard target

        return np.clip(target, 0, 1)

class NeuroFeedbackSystem:
    """Main neuro-feedback system integrating all components"""

    def __init__(self, visualization_backend: str = 'plotly'):
        self.visualization_backend = visualization_backend
        self.visualizer = BrainVisualizer()
        self.feedback_engine = FeedbackEngine()
        self.current_session = None

        # Real-time data
        self.data_queue = asyncio.Queue()
        self.feedback_queue = asyncio.Queue()
        self.visualization_queue = asyncio.Queue()

        # Threading
        self.is_running = False
        self.processing_tasks = []

        # GUI components
        self.root = None
        self.figures = {}

        # Metrics
        self.metrics = {
            'sessions_completed': 0,
            'total_training_time': 0,
            'average_improvement': 0,
            'user_satisfaction': 0
        }

        self.logger = logging.getLogger(__name__)

    async def initialize_session(self, user_id: str, duration: float,
                                feedback_types: List[FeedbackType],
                                target_metrics: Dict[str, float]) -> str:
        """Initialize a new neuro-feedback session"""
        session_id = f"session_{int(time.time())}_{user_id}"

        self.current_session = FeedbackSession(
            session_id=session_id,
            user_id=user_id,
            start_time=time.time(),
            duration=duration,
            feedback_types=feedback_types,
            target_metrics=target_metrics,
            baseline_data={},
            performance_thresholds={}
        )

        self.logger.info(f"Initialized neuro-feedback session: {session_id}")
        return session_id

    async def start_realtime_feedback(self):
        """Start real-time neuro-feedback"""
        if not self.current_session:
            raise RuntimeError("No active session")

        self.is_running = True

        # Start processing tasks
        self.processing_tasks = [
            asyncio.create_task(self._data_processing_loop()),
            asyncio.create_task(self._feedback_generation_loop()),
            asyncio.create_task(self._visualization_update_loop())
        ]

        self.logger.info("Started real-time neuro-feedback")

    async def stop_realtime_feedback(self):
        """Stop real-time neuro-feedback"""
        self.is_running = False

        # Cancel tasks
        for task in self.processing_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)

        self.logger.info("Stopped real-time neuro-feedback")

    async def add_neural_data(self, processed_signal: ProcessedSignal):
        """Add neural data for processing"""
        if self.is_running:
            await self.data_queue.put(processed_signal)

    async def _data_processing_loop(self):
        """Process neural data in real-time"""
        while self.is_running:
            try:
                # Get neural data
                processed_signal = await asyncio.wait_for(
                    self.data_queue.get(), timeout=1.0
                )

                # Extract brain activity
                brain_activity = {
                    'delta': processed_signal.brain_waves.get('DELTA', 0),
                    'theta': processed_signal.brain_waves.get('THETA', 0),
                    'alpha': processed_signal.brain_waves.get('ALPHA', 0),
                    'beta': processed_signal.brain_waves.get('BETA', 0),
                    'gamma': processed_signal.brain_waves.get('GAMMA', 0)
                }

                # Normalize activity values
                total_power = sum(brain_activity.values())
                if total_power > 0:
                    brain_activity = {k: v/total_power for k, v in brain_activity.items()}

                # Queue for feedback generation
                await self.feedback_queue.put({
                    'timestamp': processed_signal.timestamp,
                    'brain_activity': brain_activity,
                    'signal_quality': processed_signal.signal_quality
                })

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Data processing error: {e}")

    async def _feedback_generation_loop(self):
        """Generate feedback in real-time"""
        while self.is_running:
            try:
                # Get processed data
                data = await asyncio.wait_for(
                    self.feedback_queue.get(), timeout=1.0
                )

                # Generate feedback
                if self.current_session:
                    feedback = self.feedback_engine.generate_feedback(
                        data['brain_activity'],
                        self.current_session.target_metrics
                    )

                    # Queue for visualization
                    await self.visualization_queue.put({
                        'feedback': feedback,
                        'brain_activity': data['brain_activity'],
                        'signal_quality': data['signal_quality']
                    })

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Feedback generation error: {e}")

    async def _visualization_update_loop(self):
        """Update visualizations in real-time"""
        while self.is_running:
            try:
                # Get visualization data
                viz_data = await asyncio.wait_for(
                    self.visualization_queue.get(), timeout=1.0
                )

                # Update visualizations based on session types
                if self.current_session:
                    for feedback_type in self.current_session.feedback_types:
                        if feedback_type == FeedbackType.BRAIN_MAP:
                            await self._update_brain_map(viz_data)
                        elif feedback_type == FeedbackType.PERFORMANCE:
                            await self._update_performance_dashboard(viz_data)
                        elif feedback_type == FeedbackType.WAVE_FORM:
                            await self._update_waveform_display(viz_data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Visualization update error: {e}")

    async def _update_brain_map(self, viz_data: Dict[str, Any]):
        """Update brain map visualization"""
        brain_activity = viz_data['brain_activity']
        fig = self.visualizer.create_brain_map(brain_activity, mode='heatmap')
        self.figures['brain_map'] = fig

    async def _update_performance_dashboard(self, viz_data: Dict[str, Any]):
        """Update performance dashboard"""
        feedback = viz_data['feedback']
        if self.current_session:
            fig = self.visualizer.create_performance_dashboard(
                feedback.performance_metrics,
                self.current_session.target_metrics
            )
            self.figures['performance'] = fig

    async def _update_waveform_display(self, viz_data: Dict[str, Any]):
        """Update waveform display"""
        # This would need actual signal data from the processed signal
        # For now, create a placeholder
        signals = np.random.randn(250, 8)  # Placeholder
        brain_waves = viz_data['brain_activity']
        fig = self.visualizer.create_waveform_display(signals, brain_waves)
        self.figures['waveform'] = fig

    def create_gui(self) -> tk.Tk:
        """Create GUI for neuro-feedback display"""
        self.root = tk.Tk()
        self.root.title("Neuro-Feedback System")
        self.root.geometry("1400x900")

        # Create main frames
        control_frame = Frame(self.root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        display_frame = Frame(self.root)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel
        self._create_control_panel(control_frame)

        # Display area
        self._create_display_area(display_frame)

        return self.root

    def _create_control_panel(self, parent: Frame):
        """Create control panel"""
        Label(parent, text="Neuro-Feedback Controls", font=("Arial", 14, "bold")).pack(pady=10)

        # Session controls
        Label(parent, text="Session Duration (min):").pack()
        self.duration_scale = Scale(parent, from_=5, to=60, orient=tk.HORIZONTAL)
        self.duration_scale.set(30)
        self.duration_scale.pack(pady=5)

        # Feedback type selection
        Label(parent, text="Feedback Types:").pack(pady=10)
        self.feedback_vars = {}
        for feedback_type in FeedbackType:
            var = tk.BooleanVar(value=True)
            self.feedback_vars[feedback_type] = var
            tk.Checkbutton(parent, text=feedback_type.value.replace('_', ' ').title(),
                          variable=var).pack(anchor=tk.W)

        # Target metrics
        Label(parent, text="Target Metrics:", font=("Arial", 12, "bold")).pack(pady=10)

        self.target_scales = {}
        for metric in ['Focus', 'Relaxation', 'Cognitive Load']:
            Label(parent, text=f"{metric}:").pack()
            scale = Scale(parent, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL)
            scale.set(0.7)
            scale.pack(pady=5)
            self.target_scales[metric.lower().replace(' ', '_')] = scale

        # Control buttons
        Button(parent, text="Start Session", command=self._start_session_gui,
               bg="green", fg="white").pack(pady=10)
        Button(parent, text="Stop Session", command=self._stop_session_gui,
               bg="red", fg="white").pack(pady=5)
        Button(parent, text="Save Session", command=self._save_session_gui,
               bg="blue", fg="white").pack(pady=5)

    def _create_display_area(self, parent: Frame):
        """Create display area for visualizations"""
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Brain Map tab
        brain_map_frame = Frame(notebook)
        notebook.add(brain_map_frame, text="Brain Map")
        self.brain_map_label = Label(brain_map_frame, text="Brain Map will appear here",
                                     font=("Arial", 12))
        self.brain_map_label.pack(expand=True)

        # Performance Dashboard tab
        performance_frame = Frame(notebook)
        notebook.add(performance_frame, text="Performance")
        self.performance_label = Label(performance_frame, text="Performance metrics will appear here",
                                      font=("Arial", 12))
        self.performance_label.pack(expand=True)

        # Waveform tab
        waveform_frame = Frame(notebook)
        notebook.add(waveform_frame, text="Waveforms")
        self.waveform_label = Label(waveform_frame, text="EEG waveforms will appear here",
                                    font=("Arial", 12))
        self.waveform_label.pack(expand=True)

        # Recommendations tab
        recommendations_frame = Frame(notebook)
        notebook.add(recommendations_frame, text="Recommendations")
        self.recommendations_text = tk.Text(recommendations_frame, wrap=tk.WORD)
        self.recommendations_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _start_session_gui(self):
        """Start session from GUI"""
        if not self.is_running:
            # Get session parameters
            duration = self.duration_scale.get() * 60  # Convert to seconds
            feedback_types = [ft for ft, var in self.feedback_vars.items() if var.get()]
            target_metrics = {
                metric: scale.get()
                for metric, scale in self.target_scales.items()
            }

            # Start session in background
            asyncio.create_task(self._start_session_async(duration, feedback_types, target_metrics))

    async def _start_session_async(self, duration: float, feedback_types: List[FeedbackType],
                                 target_metrics: Dict[str, float]):
        """Start session asynchronously"""
        try:
            # Initialize session
            await self.initialize_session("gui_user", duration, feedback_types, target_metrics)

            # Start real-time feedback
            await self.start_realtime_feedback()

            # Update GUI
            if self.root:
                self.root.after(0, self._update_session_status, "Session Active")

        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            if self.root:
                self.root.after(0, self._update_session_status, f"Error: {e}")

    def _stop_session_gui(self):
        """Stop session from GUI"""
        if self.is_running:
            asyncio.create_task(self.stop_realtime_feedback())
            if self.root:
                self.root.after(0, self._update_session_status, "Session Stopped")

    def _save_session_gui(self):
        """Save session data from GUI"""
        if self.feedback_engine.performance_tracker.performance_history:
            session_summary = self.feedback_engine.performance_tracker.get_session_summary()
            filename = f"session_{int(time.time())}_summary.json"

            try:
                with open(filename, 'w') as f:
                    json.dump(session_summary, f, indent=2)

                if self.root:
                    self.root.after(0, self._update_session_status, f"Session saved to {filename}")
            except Exception as e:
                if self.root:
                    self.root.after(0, self._update_session_status, f"Save failed: {e}")

    def _update_session_status(self, status: str):
        """Update session status in GUI"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=status)
        else:
            # Create status label if it doesn't exist
            if self.root:
                self.status_label = Label(self.root, text=status, font=("Arial", 10))
                self.status_label.pack(side=tk.BOTTOM, pady=5)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current or last session"""
        if self.current_session:
            session_summary = {
                'session_id': self.current_session.session_id,
                'user_id': self.current_session.user_id,
                'duration': time.time() - self.current_session.start_time,
                'target_metrics': self.current_session.target_metrics,
                'performance_summary': self.feedback_engine.performance_tracker.get_session_summary()
            }

            return session_summary

        return {}

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            **self.metrics,
            'is_running': self.is_running,
            'current_session': self.current_session.session_id if self.current_session else None,
            'queue_sizes': {
                'data_queue': self.data_queue.qsize(),
                'feedback_queue': self.feedback_queue.qsize(),
                'visualization_queue': self.visualization_queue.qsize()
            }
        }

# Main interface for external use
async def create_neuro_feedback_system(visualization_backend: str = 'plotly') -> NeuroFeedbackSystem:
    """Create and initialize a neuro-feedback system"""
    system = NeuroFeedbackSystem(visualization_backend)
    return system

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create neuro-feedback system
        neuro_system = await create_neuro_feedback_system()

        # Initialize session
        await neuro_system.initialize_session(
            user_id="example_user",
            duration=300,  # 5 minutes
            feedback_types=[
                FeedbackType.BRAIN_MAP,
                FeedbackType.PERFORMANCE,
                FeedbackType.WAVE_FORM
            ],
            target_metrics={
                'focus': 0.7,
                'relaxation': 0.6,
                'cognitive_load': 0.5
            }
        )

        # Start real-time feedback
        await neuro_system.start_realtime_feedback()

        # Simulate some neural data (in real use, would come from neural interface)
        from .neural_interface import create_neural_interface

        neural_interface = await create_neural_interface("simulator")
        await neural_interface.calibrate(duration=5.0)

        # Process signals for a while
        for _ in range(50):
            signal = neural_interface.get_latest_signal()
            if signal:
                await neuro_system.add_neural_data(signal)
            await asyncio.sleep(0.1)

        # Get session summary
        summary = neuro_system.get_session_summary()
        print(f"Session summary: {summary}")

        # Get metrics
        metrics = neuro_system.get_metrics()
        print(f"System metrics: {metrics}")

        # Stop feedback
        await neuro_system.stop_realtime_feedback()
        await neural_interface.shutdown()

    asyncio.run(main())