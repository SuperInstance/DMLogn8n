"""
Game State definition
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class GameState:
    """Current game state for decision making"""
    environment: Dict[str, Any] = field(default_factory=dict)
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    current_objective: Optional[str] = None
    combat_status: bool = False
    resources: Dict[str, Any] = field(default_factory=dict)
    time_info: Dict[str, Any] = field(default_factory=dict)