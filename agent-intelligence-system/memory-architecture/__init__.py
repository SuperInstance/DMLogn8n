"""
Hierarchical Memory Architecture for DMlogn8n Agent Intelligence System
========================================================================

Based on AgentDnDengine3.txt research, this implements a multi-level memory system
with capacity tied to character level, working memory, episodic memory, and semantic
memory layers with intelligent consolidation and retrieval.

Level Specifications:
- Level 1-4: 50 memories, working memory 5, consolidation threshold 100
- Level 5-10: 200 memories, working memory 10, consolidation threshold 200
- Level 11-16: 500 memories, working memory 15, consolidation threshold 400
- Level 17-20: 1000 memories, working memory 25, consolidation threshold 800

Key Components:
- Working Memory: Fast access, limited capacity, current context
- Episodic Memory: Event-based memories with temporal context
- Semantic Memory: Consolidated patterns and conceptual knowledge
- Consolidation System: Importance scoring and memory transfer
- Forgetting Mechanism: Capacity management with intelligent pruning
- ChromaDB Integration: Vector-based similarity search and retrieval
"""

from .core.memory_manager import MemoryManager
from .core.memory_base import MemoryBase, MemoryType, MemoryImportance
from .memory_types.working_memory import WorkingMemory
from .memory_types.episodic_memory import EpisodicMemory
from .memory_types.semantic_memory import SemanticMemory
from .consolidation.consolidation_engine import ConsolidationEngine
from .retrieval.vector_store import VectorStore
from .dashboard.memory_dashboard import MemoryDashboard

__version__ = "1.0.0"
__author__ = "DMlogn8n AI System"

__all__ = [
    "MemoryManager",
    "MemoryBase",
    "MemoryType",
    "MemoryImportance",
    "WorkingMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ConsolidationEngine",
    "VectorStore",
    "MemoryDashboard"
]