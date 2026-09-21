"""
AI Transparency System - Shows Agent Decision Process
Makes AI thinking visible to players for transparency and learning
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionTier(Enum):
    REFLEX = "reflex"  # <100ms
    TACTICAL = "tactical"  # 1-3s
    STRATEGIC = "strategic"  # 3-7s
    CREATIVE = "creative"  # >7s

class ThoughtProcess:
    """Captures AI agent's thought process"""

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.current_situation = {}
        self.considered_options = []
        self.weights = {}
        self.final_decision = {}
        self.reasoning = ""

class AITransparency:
    """Manages AI transparency for human observers"""

    def __init__(self):
        self.active_processes: Dict[str, ThoughtProcess] = {}
        self.observers: Set[str] = set()  # Players watching this AI
        self.thought_history: List[Dict] = []
        self.learning_insights: Dict[str, List] = {}

    async def start_thought_process(self, character_id: str, situation: Dict) -> str:
        """Begin transparent thought process for a decision"""
        process_id = f"thought_{datetime.utcnow().timestamp()}"

        thought = ThoughtProcess(character_id)
        thought.current_situation = situation
        self.active_processes[process_id] = thought

        # Broadcast thought initiation
        await self.broadcast_thought_update(character_id, {
            "stage": "analysis",
            "message": "Analyzing situation...",
            "process_id": process_id
        })

        # Stage 1: Analyze situation (reflex tier)
        analysis = await self.analyze_situation(character_id, situation)
        thought.reasoning = analysis["reasoning"]
        thought.weights = analysis["weights"]

        await self.broadcast_thought_update(character_id, {
            "stage": "options",
            "message": "Considering options...",
            "process_id": process_id,
            "analysis": analysis,
            "options": analysis["options"]
        })

        # Stage 2: Select tier based on complexity
        tier = await self.select_decision_tier(situation, analysis["complexity"])

        # Stage 3: Generate decision using appropriate tier
        if tier == DecisionTier.REFLEX:
            decision = await self.reflex_decision(character_id, situation)
        elif tier == DecisionTier.TACTICAL:
            decision = await self.tactical_decision(character_id, situation, analysis)
        elif tier == DecisionTier.STRATEGIC:
            decision = await self.strategic_decision(character_id, situation, analysis)
        else:
            decision = await self.creative_decision(character_id, situation, analysis)

        thought.final_decision = decision
        thought.reasoning = f"Used {tier.value} reasoning for this decision"

        # Save to learning history
        await self.save_learning_insight(character_id, situation, decision)

        # Broadcast final decision
        await self.broadcast_thought_update(character_id, {
            "stage": "decision",
            "message": f"Decision made: {decision['action']}",
            "process_id": process_id,
            "decision": decision,
            "confidence": decision["confidence"],
            "execution_time": decision.get("estimated_time", 0.0)
        })

        # Clean up
        del self.active_processes[process_id]
        return process_id

    async def analyze_situation(self, character_id: str, situation: Dict) -> Dict:
        """Analyze situation and identify options"""
        # Quick analysis for reflex decisions
        threats = situation.get("threats", [])
        opportunities = situation.get("opportunities", [])
        resources = situation.get("available_resources", [])

        options = []
        if threats:
            options.append({
                "action": "defensive_posture",
                "priority": 0.8,
                "reasoning": "Threats detected - need defense"
            })
            options.append({
                "action": "retreat",
                "priority": 0.6,
                "reasoning": "Strategic retreat to better position"
            })

        if opportunities:
            options.append({
                "action": "exploit_opportunity",
                "priority": 0.9,
                "reasoning": "High value opportunity available"
            })

        if resources:
            options.append({
                "action": "use_resources",
                "priority": 0.7,
                "reasoning": "Have resources that could help"
            })

        return {
            "options": options,
            "complexity": self.assess_complexity(situation),
            "reasoning": f"Identified {len(options)} options based on {len(threats)} threats and {len(opportunities)} opportunities"
        }

    async def select_decision_tier(self, situation: Dict, complexity: float) -> DecisionTier:
        """Select appropriate decision tier based on situation"""
        if complexity < 3:
            return DecisionTier.REFLEX
        elif complexity < 7:
            return DecisionTier.TACTICAL
        elif complexity < 15:
            return DecisionTier.STRATEGIC
        else:
            return DecisionTier.CREATIVE

    async def reflex_decision(self, character_id: str, situation: Dict) -> Dict:
        """Quick reflex-level decision"""
        # Simple rule-based decision
        return {
            "action": "quick_reaction",
            "confidence": 0.6,
            "reasoning": "Reflexive response to immediate threat",
            "estimated_time": 0.1
        }

    async def tactical_decision(self, character_id: str, situation: Dict,
                              analysis: Dict) -> Dict:
        """Consider multiple factors with short-term thinking"""
        # Weigh options from analysis
        best_option = max(analysis["options"], key=lambda x: x["priority"])

        return {
            "action": best_option["action"],
            "confidence": 0.8,
            "reasoning": f"Selected {best_option['action']} with priority {best_option['priority']}",
            "estimated_time": 2.0
        }

    async def strategic_decision(self, character_id: str, situation: Dict,
                               analysis: Dict) -> Dict:
        """Consider long-term consequences"""
        # Check memory for similar situations
        past_outcomes = await self.get_relevant_experiences(character_id, situation)

        # Factor in character personality
        personality = await self.get_character_personality(character_id)

        return {
            "action": "strategic_positioning",
            "confidence": 0.9,
            "reasoning": f"Strategic decision based on {personality} and {len(past_outcomes)} past experiences",
            "estimated_time": 5.0
        }

    async def creative_decision(self, character_id: str, situation: Dict,
                               analysis: Dict) -> Dict:
        """Novel solution for complex problems"""
        # Generate creative option
        return {
            "action": "innovative_solution",
            "confidence": 0.7,
            "reasoning": "Creative approach considering unique factors",
            "estimated_time": 10.0
        }

    async def broadcast_thought_update(self, character_id: str, update: Dict):
        """Broadcast thought process to observers"""
        message = {
            "type": "ai_thought",
            "character_id": character_id,
            "update": update,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all observers
        for observer_id in self.observers:
            # Would send via message router
            logger.info(f"Broadcasting thought update to observer {observer_id}")
            # await self.send_to_observer(observer_id, message)

    async def save_learning_insight(self, character_id: str, situation: Dict, decision: Dict):
        """Save decision outcome for learning"""
        insight = {
            "situation": situation,
            "decision": decision,
            "outcome": "pending",  # To be updated when action completes
            "timestamp": datetime.utcnow().isoformat()
        }

        if character_id not in self.learning_insights:
            self.learning_insights[character_id] = []
        self.learning_insights[character_id].append(insight)

    def assess_complexity(self, situation: Dict) -> float:
        """Assess situation complexity on 0-100 scale"""
        factors = [
            len(situation.get("threats", [])) * 10,
            len(situation.get("allies", [])) * 5,
            len(situation.get("objectives", [])) * 8,
            10 if situation.get("time_pressure", False) else 0,
            15 if situation.get("unknown_factors", False) else 0
        ]
        return min(100, sum(factors))

    async def get_relevant_experiences(self, character_id: str, situation: Dict) -> List[Dict]:
        """Retrieve past experiences relevant to current situation"""
        # This would query character's memory database
        # For now, return placeholder
        return []

    async def get_character_personality(self, character_id: str) -> Dict:
        """Get character personality traits"""
        # This would fetch from character database
        return {
            "aggression": 0.5,
            "curiosity": 0.8,
            "risk_tolerance": 0.6
            "preferred_approach": "balanced"
        }

    def add_observer(self, observer_id: str):
        """Add a player to observe AI thinking"""
        self.observers.add(observer_id)
        logger.info(f"Added observer {observer_id} for AI transparency")

    def remove_observer(self, observer_id: str):
        """Remove observer from AI transparency"""
        self.observers.discard(observer_id)
        logger.info(f"Removed observer {observer_id} from AI transparency")