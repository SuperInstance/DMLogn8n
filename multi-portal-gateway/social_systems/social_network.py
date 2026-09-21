#!/usr/bin/env python3
"""
DMLogn8n Social Network - Comprehensive Social Graph and Relationship System

Handles social graph tracking, relationships, influence systems, social interactions,
friend networks, rivalries, alliances, and social dynamics.

Features:
- Social graph management with complex relationships
- Friendship and follower systems
- Rivalry and competition tracking
- Alliance and coalition systems
- Social influence and reputation spread
- Relationship strength and history
- Social clustering and community detection
- Network analysis and insights
- Social recommendation systems
- Trust and credibility scoring
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import math
from collections import defaultdict, deque

class RelationshipType(Enum):
    """Types of social relationships"""
    FRIEND = "friend"
    BEST_FRIEND = "best_friend"
    FAMILY = "family"
    MENTOR = "mentor"
    STUDENT = "student"
    RIVAL = "rival"
    ENEMY = "enemy"
    ALLY = "ally"
    NEUTRAL = "neutral"
    ACQUAINTANCE = "acquaintance"
    COLLEAGUE = "colleague"
    PARTNER = "partner"
    SPOUSE = "spouse"
    MENTEE = "mentee"

class RelationshipStatus(Enum):
    """Status of relationships"""
    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"
    DORMANT = "dormant"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"

class InteractionType(Enum):
    """Types of social interactions"""
    CHAT = "chat"
    GIFT = "gift"
    TRADE = "trade"
    QUEST = "quest"
    PARTY = "party"
    GUILD = "guild"
    PVP = "pvp"
    HELP = "help"
    COLLABORATE = "collaborate"
    COMPETE = "compete"
    MENTION = "mention"
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    VISIT = "visit"

class InfluenceType(Enum):
    """Types of social influence"""
    REPUTATION = "reputation"
    BEHAVIOR = "behavior"
    OPINION = "opinion"
    SKILL = "skill"
    KNOWLEDGE = "knowledge"
    TREND = "trend"
    MOVEMENT = "movement"
    DECISION = "decision"

class NetworkRole(Enum):
    """Social network roles"""
    HUB = "hub"           # Well-connected individual
    BRIDGE = "bridge"     # Connects different clusters
    PERIPHERY = "periphery" # Limited connections
    CORE = "core"         # Central to community
    INFLUENCER = "influencer" # High influence score
    LONER = "loner"       # Minimal social connections
    CONNECTOR = "connector" # Links multiple groups

@dataclass
class SocialRelationship:
    """Individual social relationship between two entities"""
    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    status: RelationshipStatus
    strength: float  # 0.0 to 1.0
    created_date: datetime
    last_interaction: datetime
    interaction_count: int = 0
    trust_score: float = 0.5
    influence_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)

@dataclass
class SocialInteraction:
    """Record of a social interaction"""
    id: str
    source_id: str
    target_id: str
    interaction_type: InteractionType
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    impact: float = 0.0  # Impact on relationship strength
    visibility: str = "public"  # public, private, mutual
    duration: Optional[float] = None
    location: Optional[str] = None
    participants: List[str] = field(default_factory=list)

@dataclass
class SocialNode:
    """Node in the social graph representing an entity"""
    id: str
    name: str
    entity_type: str  # player, npc, guild, faction
    attributes: Dict[str, Any] = field(default_factory=dict)
    connections: Set[str] = field(default_factory=set)
    role: NetworkRole = NetworkRole.PERIPHERY
    influence_score: float = 0.0
    activity_level: float = 0.0
    trust_score: float = 0.5
    reputation_score: float = 0.0
    last_active: datetime = field(default_factory=datetime.now)
    created_date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

@dataclass
class SocialCluster:
    """Cluster of socially connected entities"""
    id: str
    name: str
    members: Set[str] = field(default_factory=set)
    center_nodes: List[str] = field(default_factory=list)
    density: float = 0.0
    cohesion_score: float = 0.0
    primary_relationship: RelationshipType = RelationshipType.FRIEND
    formation_date: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SocialInfluence:
    """Social influence propagating through the network"""
    id: str
    source_id: str
    influence_type: InfluenceType
    content: Dict[str, Any]
    strength: float
    created_date: datetime
    affected_nodes: List[str] = field(default_factory=list)
    propagation_path: List[str] = field(default_factory=list)
    decay_rate: float = 0.1
    max_distance: int = 3

@dataclass
class SocialRecommendation:
    """Social recommendation for connections or activities"""
    id: str
    target_id: str
    recommendation_type: str  # friend, join_guild, party, quest
    suggested_entities: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    expires_date: Optional[datetime] = None

class SocialNetwork:
    """Main social network management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.nodes: Dict[str, SocialNode] = {}
        self.relationships: Dict[str, SocialRelationship] = {}
        self.interactions: Dict[str, List[SocialInteraction]] = defaultdict(list)
        self.clusters: Dict[str, SocialCluster] = {}
        self.influences: Dict[str, SocialInfluence] = {}
        self.recommendations: Dict[str, List[SocialRecommendation]] = defaultdict(list)

        # Social graph adjacency lists
        self.adjacency_list: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.reverse_adjacency: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Network analysis cache
        self.network_metrics: Dict[str, Dict] = {}
        self.centrality_scores: Dict[str, Dict[str, float]] = {}
        self.path_cache: Dict[str, Dict[str, List[str]]] = {}

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_relationships_per_node": 1000,
            "interaction_decay_days": 90,
            "relationship_decay_rate": 0.01,  # Daily decay
            "influence_propagation_interval": 300,  # 5 minutes
            "recommendation_refresh_interval": 3600,  # 1 hour
            "network_analysis_interval": 1800,  # 30 minutes
            "min_interaction_impact": 0.01,
            "max_interaction_impact": 0.1,
            "trust_decay_rate": 0.005,
            "influence_decay_rate": 0.1,
            "cluster_min_size": 3,
            "recommendation_limit": 10,
            "relationship_strength_threshold": 0.1,
            "influence_propagation_threshold": 0.05
        }

    async def create_node(self, entity_id: str, name: str, entity_type: str, attributes: Dict = None) -> Dict:
        """Create a new social node"""
        try:
            if entity_id in self.nodes:
                return {"success": False, "error": "Node already exists"}

            # Create node
            node = SocialNode(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                attributes=attributes or {},
                created_date=datetime.now()
            )

            # Store node
            self.nodes[entity_id] = node
            self.adjacency_list[entity_id] = {}
            self.reverse_adjacency[entity_id] = {}

            # Initialize network metrics
            self.network_metrics[entity_id] = {
                "degree": 0,
                "in_degree": 0,
                "out_degree": 0,
                "clustering_coefficient": 0.0,
                "betweenness": 0.0,
                "closeness": 0.0,
                "eigenvector": 0.0,
                "page_rank": 0.0,
                "last_calculated": datetime.now()
            }

            self.logger.info(f"Created social node: {entity_id} ({name})")

            return {
                "success": True,
                "node_id": entity_id,
                "node": asdict(node),
                "message": f"Social node created for {name}"
            }

        except Exception as e:
            self.logger.error(f"Error creating social node: {e}")
            return {"success": False, "error": str(e)}

    async def create_relationship(self, source_id: str, target_id: str, relationship_type: RelationshipType,
                                 strength: float = 0.5, metadata: Dict = None) -> Dict:
        """Create a new social relationship"""
        try:
            # Validate nodes exist
            if source_id not in self.nodes or target_id not in self.nodes:
                return {"success": False, "error": "One or both nodes not found"}

            if source_id == target_id:
                return {"success": False, "error": "Cannot create self-relationship"}

            # Check for existing relationship
            existing_id = f"{source_id}_{target_id}"
            if existing_id in self.relationships:
                return {"success": False, "error": "Relationship already exists"}

            # Validate strength
            strength = max(0.0, min(1.0, strength))

            # Create relationship
            relationship = SocialRelationship(
                id=existing_id,
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                status=RelationshipStatus.ACTIVE,
                strength=strength,
                created_date=datetime.now(),
                last_interaction=datetime.now(),
                trust_score=0.5,
                metadata=metadata or {}
            )

            # Store relationship
            self.relationships[existing_id] = relationship

            # Update adjacency lists
            self.adjacency_list[source_id][target_id] = strength
            self.reverse_adjacency[target_id][source_id] = strength

            # Update node connections
            self.nodes[source_id].connections.add(target_id)
            self.nodes[target_id].connections.add(source_id)

            # Update node roles
            await self._update_node_roles(source_id)
            await self._update_node_roles(target_id)

            # Record initial interaction
            await self._record_interaction(
                source_id, target_id, InteractionType.MENTION,
                {"action": "relationship_created", "type": relationship_type.value},
                impact=strength * 0.1
            )

            self.logger.info(f"Created relationship: {source_id} -> {target_id} ({relationship_type.value})")

            return {
                "success": True,
                "relationship_id": existing_id,
                "relationship": asdict(relationship),
                "message": f"Created {relationship_type.value} relationship"
            }

        except Exception as e:
            self.logger.error(f"Error creating relationship: {e}")
            return {"success": False, "error": str(e)}

    async def record_interaction(self, source_id: str, target_id: str, interaction_type: InteractionType,
                               context: Dict = None, impact: float = None, participants: List[str] = None) -> Dict:
        """Record a social interaction between entities"""
        try:
            # Validate nodes exist
            if source_id not in self.nodes or target_id not in self.nodes:
                return {"success": False, "error": "One or both nodes not found"}

            # Calculate impact if not provided
            if impact is None:
                impact = random.uniform(
                    self.config["min_interaction_impact"],
                    self.config["max_interaction_impact"]
                )

            # Adjust impact based on interaction type
            type_multipliers = {
                InteractionType.GIFT: 0.2,
                InteractionType.HELP: 0.15,
                InteractionType.COLLABORATE: 0.1,
                InteractionType.CHAT: 0.05,
                InteractionType.PARTY: 0.12,
                InteractionType.QUEST: 0.1,
                InteractionType.PVP: -0.05,  # Negative impact for PvP
                InteractionType.COMPETE: -0.02,
                InteractionType.LIKE: 0.02,
                InteractionType.COMMENT: 0.03,
                InteractionType.SHARE: 0.04
            }
            impact *= type_multipliers.get(interaction_type, 0.05)

            # Record interaction
            interaction = SocialInteraction(
                id=str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                interaction_type=interaction_type,
                timestamp=datetime.now(),
                context=context or {},
                impact=impact,
                participants=participants or []
            )

            # Store interaction
            self.interactions[f"{source_id}_{target_id}"].append(interaction)

            # Update relationship if exists
            relationship_id = f"{source_id}_{target_id}"
            if relationship_id in self.relationships:
                relationship = self.relationships[relationship_id]
                relationship.last_interaction = datetime.now()
                relationship.interaction_count += 1

                # Update relationship strength
                old_strength = relationship.strength
                relationship.strength = max(0.0, min(1.0, relationship.strength + impact))

                # Update trust score
                if impact > 0:
                    relationship.trust_score = min(1.0, relationship.trust_score + impact * 0.5)
                else:
                    relationship.trust_score = max(0.0, relationship.trust_score + impact * 0.3)

                # Update adjacency lists
                self.adjacency_list[source_id][target_id] = relationship.strength
                self.reverse_adjacency[target_id][source_id] = relationship.strength

                # Add to history
                relationship.history.append({
                    "timestamp": datetime.now().isoformat(),
                    "interaction_id": interaction.id,
                    "type": interaction_type.value,
                    "impact": impact,
                    "strength_change": relationship.strength - old_strength
                })

                # Remove old interactions to prevent memory bloat
                cutoff_date = datetime.now() - timedelta(days=self.config["interaction_decay_days"])
                self.interactions[f"{source_id}_{target_id}"] = [
                    i for i in self.interactions[f"{source_id}_{target_id}"]
                    if i.timestamp > cutoff_date
                ]

            # Update node activity levels
            self.nodes[source_id].last_active = datetime.now()
            self.nodes[source_id].activity_level = min(1.0, self.nodes[source_id].activity_level + 0.01)
            self.nodes[target_id].activity_level = min(1.0, self.nodes[target_id].activity_level + 0.01)

            # Update network metrics
            await self._update_network_metrics(source_id)
            await self._update_network_metrics(target_id)

            self.logger.info(f"Recorded interaction: {source_id} -> {target_id} ({interaction_type.value}, impact: {impact:.3f})")

            return {
                "success": True,
                "interaction_id": interaction.id,
                "impact": impact,
                "message": f"Recorded {interaction_type.value} interaction"
            }

        except Exception as e:
            self.logger.error(f"Error recording interaction: {e}")
            return {"success": False, "error": str(e)}

    async def get_relationships(self, entity_id: str, relationship_type: Optional[RelationshipType] = None,
                               min_strength: float = 0.0, status: Optional[RelationshipStatus] = None) -> Dict:
        """Get relationships for an entity"""
        try:
            if entity_id not in self.nodes:
                return {"success": False, "error": "Node not found"}

            relationships = []

            # Get outgoing relationships
            for target_id, rel_id in [(tid, f"{entity_id}_{tid}") for tid in self.nodes[entity_id].connections]:
                if rel_id in self.relationships:
                    rel = self.relationships[rel_id]

                    # Apply filters
                    if relationship_type and rel.relationship_type != relationship_type:
                        continue
                    if rel.strength < min_strength:
                        continue
                    if status and rel.status != status:
                        continue

                    # Get target node info
                    target_node = self.nodes.get(target_id)
                    if target_node:
                        rel_data = asdict(rel)
                        rel_data["target_name"] = target_node.name
                        rel_data["target_type"] = target_node.entity_type
                        relationships.append(rel_data)

            # Sort by strength (descending)
            relationships.sort(key=lambda x: x["strength"], reverse=True)

            return {
                "success": True,
                "entity_id": entity_id,
                "relationships": relationships,
                "total_count": len(relationships)
            }

        except Exception as e:
            self.logger.error(f"Error getting relationships: {e}")
            return {"success": False, "error": str(e)}

    async def get_friends_of_friends(self, entity_id: str, max_depth: int = 2, min_strength: float = 0.3) -> Dict:
        """Get friends of friends network"""
        try:
            if entity_id not in self.nodes:
                return {"success": False, "error": "Node not found"}

            visited = set()
            queue = deque([(entity_id, 0)])
            result = {}

            while queue:
                current_id, depth = queue.popleft()

                if current_id in visited or depth >= max_depth:
                    continue

                visited.add(current_id)

                # Get direct connections
                for neighbor_id, strength in self.adjacency_list[current_id].items():
                    if strength >= min_strength and neighbor_id not in visited:

                        if depth == 0:
                            # Direct friends
                            result[neighbor_id] = {
                                "name": self.nodes[neighbor_id].name,
                                "relationship_strength": strength,
                                "depth": depth + 1,
                                "mutual_friends": []
                            }
                        else:
                            # Friends of friends
                            if neighbor_id not in result:
                                result[neighbor_id] = {
                                    "name": self.nodes[neighbor_id].name,
                                    "relationship_strength": strength,
                                    "depth": depth + 1,
                                    "mutual_friends": []
                                }

                            # Add current node as mutual friend
                            if depth == 1:
                                result[neighbor_id]["mutual_friends"].append({
                                    "id": current_id,
                                    "name": self.nodes[current_id].name
                                })

                        queue.append((neighbor_id, depth + 1))

            # Remove the original entity from results
            if entity_id in result:
                del result[entity_id]

            return {
                "success": True,
                "entity_id": entity_id,
                "network": result,
                "total_count": len(result),
                "max_depth": max_depth
            }

        except Exception as e:
            self.logger.error(f"Error getting friends of friends: {e}")
            return {"success": False, "error": str(e)}

    async def find_shortest_path(self, source_id: str, target_id: str, min_strength: float = 0.1) -> Dict:
        """Find shortest path between two entities in the social graph"""
        try:
            if source_id not in self.nodes or target_id not in self.nodes:
                return {"success": False, "error": "One or both nodes not found"}

            if source_id == target_id:
                return {"success": True, "path": [source_id], "length": 0}

            # Check cache first
            cache_key = f"{source_id}_{target_id}"
            if cache_key in self.path_cache:
                cached_path = self.path_cache[cache_key]
                if cached_path and self._path_still_valid(cached_path, min_strength):
                    return {
                        "success": True,
                        "path": cached_path,
                        "length": len(cached_path) - 1,
                        "cached": True
                    }

            # BFS for shortest path
            visited = set([source_id])
            queue = deque([(source_id, [source_id])])

            while queue:
                current_id, path = queue.popleft()

                # Check neighbors
                for neighbor_id, strength in self.adjacency_list[current_id].items():
                    if strength < min_strength:
                        continue

                    if neighbor_id == target_id:
                        result_path = path + [target_id]

                        # Cache the result
                        self.path_cache[cache_key] = result_path
                        self.path_cache[f"{target_id}_{source_id}"] = result_path[::-1]

                        return {
                            "success": True,
                            "path": result_path,
                            "length": len(result_path) - 1
                        }

                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, path + [neighbor_id]))

            return {
                "success": False,
                "error": "No path found between entities",
                "path": [],
                "length": -1
            }

        except Exception as e:
            self.logger.error(f"Error finding shortest path: {e}")
            return {"success": False, "error": str(e)}

    async def calculate_social_influence(self, entity_id: str) -> Dict:
        """Calculate social influence metrics for an entity"""
        try:
            if entity_id not in self.nodes:
                return {"success": False, "error": "Node not found"}

            node = self.nodes[entity_id]

            # Calculate various influence metrics
            metrics = {}

            # 1. Network reach (number of unique connections within N degrees)
            metrics["direct_reach"] = len(self.adjacency_list[entity_id])
            metrics["second_degree_reach"] = await self._calculate_n_degree_reach(entity_id, 2)
            metrics["third_degree_reach"] = await self._calculate_n_degree_reach(entity_id, 3)

            # 2. Relationship strength distribution
            relationships = list(self.adjacency_list[entity_id].values())
            if relationships:
                metrics["avg_relationship_strength"] = sum(relationships) / len(relationships)
                metrics["strong_connections"] = sum(1 for s in relationships if s > 0.7)
                metrics["weak_connections"] = sum(1 for s in relationships if s < 0.3)
            else:
                metrics["avg_relationship_strength"] = 0.0
                metrics["strong_connections"] = 0
                metrics["weak_connections"] = 0

            # 3. Trust and credibility scores
            trust_scores = []
            for target_id in node.connections:
                rel_id = f"{entity_id}_{target_id}"
                if rel_id in self.relationships:
                    trust_scores.append(self.relationships[rel_id].trust_score)

            if trust_scores:
                metrics["avg_trust_score"] = sum(trust_scores) / len(trust_scores)
                metrics["trust_network_size"] = len(trust_scores)
            else:
                metrics["avg_trust_score"] = 0.0
                metrics["trust_network_size"] = 0

            # 4. Activity and engagement metrics
            metrics["activity_level"] = node.activity_level
            metrics["total_interactions"] = sum(
                len(interactions) for interactions in self.interactions.values()
                if entity_id in interactions[0].id.split('_')
            )

            # 5. Centrality scores (calculated separately)
            if entity_id in self.centrality_scores:
                metrics.update(self.centrality_scores[entity_id])

            # 6. Cluster influence
            metrics["cluster_memberships"] = len([
                cluster for cluster in self.clusters.values()
                if entity_id in cluster.members
            ])

            # 7. Overall influence score (weighted combination)
            influence_score = (
                metrics["direct_reach"] * 0.1 +
                metrics["second_degree_reach"] * 0.05 +
                metrics["avg_relationship_strength"] * 0.2 +
                metrics["avg_trust_score"] * 0.2 +
                metrics["activity_level"] * 0.15 +
                self.centrality_scores.get(entity_id, {}).get("betweenness", 0) * 0.1 +
                self.centrality_scores.get(entity_id, {}).get("page_rank", 0) * 0.1
            )

            metrics["overall_influence_score"] = min(1.0, influence_score / 100)  # Normalize to 0-1

            # Update node
            node.influence_score = metrics["overall_influence_score"]

            return {
                "success": True,
                "entity_id": entity_id,
                "influence_metrics": metrics,
                "influence_score": metrics["overall_influence_score"]
            }

        except Exception as e:
            self.logger.error(f"Error calculating social influence: {e}")
            return {"success": False, "error": str(e)}

    async def propagate_influence(self, source_id: str, influence_type: InfluenceType,
                                content: Dict, strength: float = 0.5, max_distance: int = 3) -> Dict:
        """Propagate social influence through the network"""
        try:
            if source_id not in self.nodes:
                return {"success": False, "error": "Source node not found"}

            # Create influence object
            influence = SocialInfluence(
                id=str(uuid.uuid4()),
                source_id=source_id,
                influence_type=influence_type,
                content=content,
                strength=strength,
                created_date=datetime.now(),
                max_distance=max_distance
            )

            # Propagation queue (node_id, distance, current_strength)
            queue = deque([(source_id, 0, strength)])
            visited = set([source_id])
            affected_nodes = [source_id]

            while queue:
                current_id, distance, current_strength = queue.popleft()

                if distance >= max_distance or current_strength < self.config["influence_propagation_threshold"]:
                    continue

                # Propagate to neighbors
                for neighbor_id, relationship_strength in self.adjacency_list[current_id].items():
                    if neighbor_id in visited:
                        continue

                    # Calculate propagation strength based on relationship
                    propagation_strength = current_strength * relationship_strength * (1 - influence.decay_rate)

                    if propagation_strength >= self.config["influence_propagation_threshold"]:
                        visited.add(neighbor_id)
                        affected_nodes.append(neighbor_id)
                        queue.append((neighbor_id, distance + 1, propagation_strength))

                        # Apply influence effect to target node
                        await self._apply_influence_effect(neighbor_id, influence, propagation_strength)

            influence.affected_nodes = affected_nodes
            influence.propagation_path = list(visited)
            self.influences[influence.id] = influence

            self.logger.info(f"Influence propagated from {source_id}: affected {len(affected_nodes)} nodes")

            return {
                "success": True,
                "influence_id": influence.id,
                "affected_nodes": affected_nodes,
                "total_affected": len(affected_nodes),
                "propagation_distance": max(visited.count(x) for x in visited) if visited else 0
            }

        except Exception as e:
            self.logger.error(f"Error propagating influence: {e}")
            return {"success": False, "error": str(e)}

    async def detect_social_clusters(self, min_cluster_size: int = None) -> Dict:
        """Detect social clusters (communities) in the network"""
        try:
            min_size = min_cluster_size or self.config["cluster_min_size"]

            # Clear existing clusters
            self.clusters.clear()

            # Use community detection algorithm (simplified Louvain method)
            clusters = await self._louvain_community_detection(min_size)

            # Store clusters
            for i, cluster_members in enumerate(clusters):
                cluster_id = f"cluster_{i}"

                # Calculate cluster metrics
                density = await self._calculate_cluster_density(cluster_members)
                center_nodes = await self._find_cluster_centers(cluster_members)
                cohesion = await self._calculate_cluster_cohesion(cluster_members)

                # Determine primary relationship type
                primary_rel = await self._determine_cluster_relationship_type(cluster_members)

                cluster = SocialCluster(
                    id=cluster_id,
                    name=f"Social Cluster {i+1}",
                    members=set(cluster_members),
                    center_nodes=center_nodes,
                    density=density,
                    cohesion_score=cohesion,
                    primary_relationship=primary_rel
                )

                self.clusters[cluster_id] = cluster

            # Update node roles based on cluster membership
            for node in self.nodes.values():
                await self._update_node_roles(node.id)

            self.logger.info(f"Detected {len(clusters)} social clusters")

            return {
                "success": True,
                "clusters_detected": len(clusters),
                "clusters": [asdict(cluster) for cluster in self.clusters.values()],
                "average_cluster_size": sum(len(c.members) for c in self.clusters.values()) / len(self.clusters) if self.clusters else 0
            }

        except Exception as e:
            self.logger.error(f"Error detecting social clusters: {e}")
            return {"success": False, "error": str(e)}

    async def generate_recommendations(self, entity_id: str, recommendation_types: List[str] = None) -> Dict:
        """Generate social recommendations for an entity"""
        try:
            if entity_id not in self.nodes:
                return {"success": False, "error": "Node not found"}

            if not recommendation_types:
                recommendation_types = ["friend", "join_guild", "party", "quest"]

            recommendations = []

            # Friend recommendations
            if "friend" in recommendation_types:
                friend_recs = await self._generate_friend_recommendations(entity_id)
                recommendations.extend(friend_recs)

            # Guild recommendations
            if "join_guild" in recommendation_types:
                guild_recs = await self._generate_guild_recommendations(entity_id)
                recommendations.extend(guild_recs)

            # Party recommendations
            if "party" in recommendation_types:
                party_recs = await self._generate_party_recommendations(entity_id)
                recommendations.extend(party_recs)

            # Quest/activity recommendations
            if "quest" in recommendation_types:
                quest_recs = await self._generate_quest_recommendations(entity_id)
                recommendations.extend(quest_recs)

            # Sort by confidence score and limit
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            recommendations = recommendations[:self.config["recommendation_limit"]]

            # Store recommendations
            self.recommendations[entity_id] = recommendations

            return {
                "success": True,
                "entity_id": entity_id,
                "recommendations": [asdict(rec) for rec in recommendations],
                "total_count": len(recommendations)
            }

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_network_health(self) -> Dict:
        """Analyze overall network health and metrics"""
        try:
            if not self.nodes:
                return {"success": False, "error": "No nodes in network"}

            # Global network metrics
            total_nodes = len(self.nodes)
            total_edges = sum(len(connections) for connections in self.adjacency_list.values()) // 2
            total_relationships = len(self.relationships)

            # Connectivity metrics
            connected_components = await self._find_connected_components()
            largest_component_size = max(len(comp) for comp in connected_components) if connected_components else 0

            # Density
            max_possible_edges = total_nodes * (total_nodes - 1) / 2
            network_density = total_edges / max_possible_edges if max_possible_edges > 0 else 0

            # Average degree
            avg_degree = (2 * total_edges) / total_nodes if total_nodes > 0 else 0

            # Clustering coefficient (average)
            clustering_coeffs = []
            for node_id in self.nodes:
                cc = await self._calculate_local_clustering_coefficient(node_id)
                clustering_coeffs.append(cc)
            avg_clustering = sum(clustering_coeffs) / len(clustering_coeffs) if clustering_coeffs else 0

            # Activity levels
            active_nodes = sum(1 for node in self.nodes.values() if node.activity_level > 0.1)
            activity_rate = active_nodes / total_nodes if total_nodes > 0 else 0

            # Influence distribution
            influence_scores = [node.influence_score for node in self.nodes.values()]
            avg_influence = sum(influence_scores) / len(influence_scores) if influence_scores else 0
            influence_inequality = self._calculate_gini_coefficient(influence_scores)

            # Trust distribution
            trust_scores = []
            for rel in self.relationships.values():
                trust_scores.append(rel.trust_score)
            avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0

            # Interaction metrics
            recent_interactions = 0
            cutoff_time = datetime.now() - timedelta(days=7)
            for interactions in self.interactions.values():
                recent_interactions += sum(1 for inter in interactions if inter.timestamp > cutoff_time)

            # Cluster metrics
            avg_cluster_size = 0
            if self.clusters:
                avg_cluster_size = sum(len(cluster.members) for cluster in self.clusters.values()) / len(self.clusters)

            health_metrics = {
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "total_edges": total_edges,
                "network_density": network_density,
                "average_degree": avg_degree,
                "average_clustering_coefficient": avg_clustering,
                "connected_components": len(connected_components),
                "largest_component_size": largest_component_size,
                "activity_rate": activity_rate,
                "average_influence": avg_influence,
                "influence_inequality": influence_inequality,
                "average_trust": avg_trust,
                "recent_interactions_7_days": recent_interactions,
                "total_clusters": len(self.clusters),
                "average_cluster_size": avg_cluster_size,
                "health_score": self._calculate_network_health_score({
                    "density": network_density,
                    "activity": activity_rate,
                    "trust": avg_trust,
                    "clustering": avg_clustering,
                    "components": 1 - (len(connected_components) / total_nodes) if total_nodes > 0 else 0
                })
            }

            return {
                "success": True,
                "health_metrics": health_metrics,
                "analysis_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing network health: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    async def _update_node_roles(self, entity_id: str):
        """Update the network role of a node based on its connections"""
        if entity_id not in self.nodes:
            return

        node = self.nodes[entity_id]
        connections = len(self.adjacency_list[entity_id])

        # Calculate metrics for role determination
        influence = node.influence_score
        activity = node.activity_level
        trust = node.trust_score

        # Determine role based on metrics
        if connections > 50 and influence > 0.7:
            node.role = NetworkRole.HUB
        elif connections > 20 and influence > 0.5:
            node.role = NetworkRole.CONNECTOR
        elif connections > 30:
            node.role = NetworkRole.CORE
        elif connections < 5:
            node.role = NetworkRole.LONER
        elif influence > 0.8:
            node.role = NetworkRole.INFLUENCER
        else:
            node.role = NetworkRole.PERIPHERY

    async def _record_interaction(self, source_id: str, target_id: str, interaction_type: InteractionType,
                                context: Dict, impact: float):
        """Record an interaction (internal method)"""
        await self.record_interaction(source_id, target_id, interaction_type, context, impact)

    async def _update_network_metrics(self, entity_id: str):
        """Update network metrics for a node"""
        if entity_id not in self.nodes:
            return

        # Calculate degree centrality
        degree = len(self.adjacency_list[entity_id])
        in_degree = len(self.reverse_adjacency[entity_id])
        out_degree = degree - in_degree

        # Update cached metrics
        if entity_id not in self.network_metrics:
            self.network_metrics[entity_id] = {}

        self.network_metrics[entity_id].update({
            "degree": degree,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "last_calculated": datetime.now()
        })

    async def _calculate_n_degree_reach(self, entity_id: str, n: int) -> int:
        """Calculate number of unique nodes within n degrees"""
        visited = set([entity_id])
        queue = deque([(entity_id, 0)])

        while queue:
            current_id, depth = queue.popleft()

            if depth >= n:
                continue

            for neighbor_id in self.adjacency_list[current_id]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))

        return len(visited) - 1  # Exclude the source node

    async def _apply_influence_effect(self, target_id: str, influence: SocialInfluence, strength: float):
        """Apply influence effect to a target node"""
        node = self.nodes.get(target_id)
        if not node:
            return

        # Apply effects based on influence type
        if influence.influence_type == InfluenceType.REPUTATION:
            node.reputation_score = min(1.0, node.reputation_score + strength * 0.1)
        elif influence.influence_type == InfluenceType.OPINION:
            # Update opinion based on influence content
            pass  # Would integrate with opinion system
        elif influence.influence_type == InfluenceType.TREND:
            # Update activity level
            node.activity_level = min(1.0, node.activity_level + strength * 0.05)

    def _path_still_valid(self, path: List[str], min_strength: float) -> bool:
        """Check if a cached path is still valid"""
        for i in range(len(path) - 1):
            source, target = path[i], path[i + 1]
            if self.adjacency_list.get(source, {}).get(target, 0) < min_strength:
                return False
        return True

    async def _louvain_community_detection(self, min_size: int) -> List[List[str]]:
        """Simplified Louvain community detection algorithm"""
        # This is a simplified version - real implementation would be more complex
        visited = set()
        clusters = []

        for node_id in self.nodes:
            if node_id in visited:
                continue

            # Find connected component
            component = []
            queue = deque([node_id])

            while queue:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    component.append(current)
                    queue.extend(self.adjacency_list[current].keys())

            if len(component) >= min_size:
                clusters.append(component)

        return clusters

    async def _calculate_cluster_density(self, members: List[str]) -> float:
        """Calculate density of a cluster"""
        if len(members) < 2:
            return 0.0

        possible_edges = len(members) * (len(members) - 1) / 2
        actual_edges = 0

        for i, member1 in enumerate(members):
            for member2 in members[i+1:]:
                if member1 in self.adjacency_list and member2 in self.adjacency_list[member1]:
                    actual_edges += 1

        return actual_edges / possible_edges

    async def _find_cluster_centers(self, members: List[str]) -> List[str]:
        """Find central nodes in a cluster"""
        if not members:
            return []

        # Calculate degree for each member within cluster
        cluster_degrees = {}
        for member in members:
            degree = 0
            for other in members:
                if other != member and other in self.adjacency_list.get(member, {}):
                    degree += 1
            cluster_degrees[member] = degree

        # Return nodes with highest degree (top 20%)
        sorted_nodes = sorted(cluster_degrees.items(), key=lambda x: x[1], reverse=True)
        top_count = max(1, len(sorted_nodes) // 5)
        return [node for node, degree in sorted_nodes[:top_count]]

    async def _calculate_cluster_cohesion(self, members: List[str]) -> float:
        """Calculate cohesion score of a cluster"""
        if len(members) < 2:
            return 0.0

        total_strength = 0.0
        edge_count = 0

        for i, member1 in enumerate(members):
            for member2 in members[i+1:]:
                if member2 in self.adjacency_list.get(member1, {}):
                    total_strength += self.adjacency_list[member1][member2]
                    edge_count += 1

        if edge_count == 0:
            return 0.0

        return total_strength / edge_count

    async def _determine_cluster_relationship_type(self, members: List[str]) -> RelationshipType:
        """Determine the primary relationship type in a cluster"""
        if not members:
            return RelationshipType.ACQUAINTANCE

        # Count relationship types within cluster
        type_counts = defaultdict(int)

        for member1 in members:
            for member2 in members:
                if member1 != member2:
                    rel_id = f"{member1}_{member2}"
                    if rel_id in self.relationships:
                        type_counts[self.relationships[rel_id].relationship_type] += 1

        # Return most common relationship type
        if type_counts:
            return max(type_counts.items(), key=lambda x: x[1])[0]

        return RelationshipType.ACQUAINTANCE

    async def _generate_friend_recommendations(self, entity_id: str) -> List[SocialRecommendation]:
        """Generate friend recommendations"""
        recommendations = []

        # Get friends of friends
        fof_result = await self.get_friends_of_friends(entity_id, max_depth=2, min_strength=0.2)

        for friend_id, friend_data in fof_result["network"].items():
            # Skip if already connected
            if friend_id in self.nodes[entity_id].connections:
                continue

            # Calculate confidence based on mutual friends and strength
            mutual_friends_count = len(friend_data["mutual_friends"])
            strength = friend_data["relationship_strength"]

            confidence = (mutual_friends_count * 0.3 + strength * 0.7) / 2.0

            if confidence > 0.3:
                rec = SocialRecommendation(
                    id=str(uuid.uuid4()),
                    target_id=entity_id,
                    recommendation_type="friend",
                    suggested_entities=[friend_id],
                    confidence_score=confidence,
                    reasons=[
                        f"Connected through {mutual_friends_count} mutual friends",
                        f"Network strength: {strength:.2f}"
                    ],
                    expires_date=datetime.now() + timedelta(days=7)
                )
                recommendations.append(rec)

        return recommendations

    async def _generate_guild_recommendations(self, entity_id: str) -> List[SocialRecommendation]:
        """Generate guild recommendations"""
        recommendations = []

        # This would integrate with your guild system
        # For now, return placeholder recommendations

        return recommendations

    async def _generate_party_recommendations(self, entity_id: str) -> List[SocialRecommendation]:
        """Generate party recommendations"""
        recommendations = []

        # Find players with similar activity levels and compatible roles
        node = self.nodes[entity_id]

        for candidate_id, candidate_node in self.nodes.items():
            if candidate_id == entity_id or candidate_id in node.connections:
                continue

            # Calculate compatibility
            activity_similarity = 1.0 - abs(node.activity_level - candidate_node.activity_level)
            trust_compatibility = candidate_node.trust_score

            confidence = (activity_similarity + trust_compatibility) / 2.0

            if confidence > 0.4:
                rec = SocialRecommendation(
                    id=str(uuid.uuid4()),
                    target_id=entity_id,
                    recommendation_type="party",
                    suggested_entities=[candidate_id],
                    confidence_score=confidence,
                    reasons=[
                        f"Similar activity level: {activity_similarity:.2f}",
                        f"Trust score: {trust_compatibility:.2f}"
                    ],
                    expires_date=datetime.now() + timedelta(hours=6)
                )
                recommendations.append(rec)

        return recommendations

    async def _generate_quest_recommendations(self, entity_id: str) -> List[SocialRecommendation]:
        """Generate quest/activity recommendations"""
        recommendations = []

        # This would integrate with your quest system
        # For now, return placeholder recommendations

        return recommendations

    async def _find_connected_components(self) -> List[List[str]]:
        """Find all connected components in the network"""
        visited = set()
        components = []

        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                queue = deque([node_id])

                while queue:
                    current = queue.popleft()
                    if current not in visited:
                        visited.add(current)
                        component.append(current)
                        queue.extend(self.adjacency_list[current].keys())

                components.append(component)

        return components

    async def _calculate_local_clustering_coefficient(self, node_id: str) -> float:
        """Calculate local clustering coefficient for a node"""
        neighbors = list(self.adjacency_list[node_id].keys())
        k = len(neighbors)

        if k < 2:
            return 0.0

        # Count edges between neighbors
        edges_between_neighbors = 0
        for i in range(k):
            for j in range(i + 1, k):
                if neighbors[j] in self.adjacency_list[neighbors[i]]:
                    edges_between_neighbors += 1

        possible_edges = k * (k - 1) / 2
        return edges_between_neighbors / possible_edges

    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        n = len(values)
        cumulative_sum = 0
        for i, value in enumerate(sorted_values):
            cumulative_sum += (i + 1) * value

        return (2 * cumulative_sum) / (n * sum(sorted_values)) - (n + 1) / n

    def _calculate_network_health_score(self, metrics: Dict) -> float:
        """Calculate overall network health score"""
        weights = {
            "density": 0.2,
            "activity": 0.3,
            "trust": 0.25,
            "clustering": 0.15,
            "components": 0.1
        }

        health_score = sum(
            weights[metric] * value for metric, value in metrics.items()
        )

        return min(1.0, health_score)

    async def start_background_tasks(self):
        """Start background analysis tasks"""
        if self._running:
            return

        self._running = True

        # Influence propagation task
        self._background_tasks.append(
            asyncio.create_task(self._influence_propagation_task())
        )

        # Network analysis task
        self._background_tasks.append(
            asyncio.create_task(self._network_analysis_task())
        )

        # Recommendation refresh task
        self._background_tasks.append(
            asyncio.create_task(self._recommendation_refresh_task())
        )

        # Relationship decay task
        self._background_tasks.append(
            asyncio.create_task(self._relationship_decay_task())
        )

    async def stop_background_tasks(self):
        """Stop background analysis tasks"""
        self._running = False

        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()

    async def _influence_propagation_task(self):
        """Periodic influence propagation"""
        while self._running:
            try:
                # Process pending influences
                for influence in list(self.influences.values()):
                    if datetime.now() - influence.created_date > timedelta(hours=1):
                        # Influence has expired
                        del self.influences[influence.id]

                await asyncio.sleep(self.config["influence_propagation_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in influence propagation task: {e}")
                await asyncio.sleep(60)

    async def _network_analysis_task(self):
        """Periodic network analysis"""
        while self._running:
            try:
                # Update centrality scores for all nodes
                for node_id in self.nodes:
                    await self.calculate_social_influence(node_id)

                # Detect communities
                await self.detect_social_clusters()

                await asyncio.sleep(self.config["network_analysis_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in network analysis task: {e}")
                await asyncio.sleep(300)

    async def _recommendation_refresh_task(self):
        """Periodic recommendation refresh"""
        while self._running:
            try:
                # Refresh recommendations for active nodes
                for node_id, node in self.nodes.items():
                    if node.activity_level > 0.2:  # Only for active nodes
                        await self.generate_recommendations(node_id)

                await asyncio.sleep(self.config["recommendation_refresh_interval"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in recommendation refresh task: {e}")
                await asyncio.sleep(600)

    async def _relationship_decay_task(self):
        """Periodic relationship strength decay"""
        while self._running:
            try:
                # Apply decay to all relationships
                for relationship in self.relationships.values():
                    if relationship.status == RelationshipStatus.ACTIVE:
                        # Decay strength
                        relationship.strength *= (1 - self.config["relationship_decay_rate"])

                        # Decay trust
                        relationship.trust_score *= (1 - self.config["trust_decay_rate"])

                        # Update adjacency lists
                        self.adjacency_list[relationship.source_id][relationship.target_id] = relationship.strength
                        self.reverse_adjacency[relationship.target_id][relationship.source_id] = relationship.strength

                await asyncio.sleep(86400)  # Daily

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in relationship decay task: {e}")
                await asyncio.sleep(3600)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize social network
        social_network = SocialNetwork()

        # Start background tasks
        await social_network.start_background_tasks()

        # Create some nodes
        await social_network.create_node("player1", "Alice", "player")
        await social_network.create_node("player2", "Bob", "player")
        await social_network.create_node("player3", "Charlie", "player")
        await social_network.create_node("player4", "Diana", "player")
        await social_network.create_node("player5", "Eve", "player")

        # Create relationships
        await social_network.create_relationship("player1", "player2", RelationshipType.FRIEND, 0.8)
        await social_network.create_relationship("player1", "player3", RelationshipType.FRIEND, 0.6)
        await social_network.create_relationship("player2", "player3", RelationshipType.FRIEND, 0.7)
        await social_network.create_relationship("player3", "player4", RelationshipType.COLLEAGUE, 0.5)
        await social_network.create_relationship("player4", "player5", RelationshipType.FRIEND, 0.9)

        # Record some interactions
        await social_network.record_interaction("player1", "player2", InteractionType.CHAT, {"topic": "adventure"})
        await social_network.record_interaction("player2", "player3", InteractionType.PARTY, {"quest": "dragon_hunt"})
        await social_network.record_interaction("player4", "player5", InteractionType.GIFT, {"item": "potion"})

        # Get relationships
        rels = await social_network.get_relationships("player1")
        print(f"Player1 relationships: {len(rels['relationships'])}")

        # Find shortest path
        path = await social_network.find_shortest_path("player1", "player5")
        print(f"Shortest path from player1 to player5: {path}")

        # Calculate social influence
        influence = await social_network.calculate_social_influence("player1")
        print(f"Player1 influence score: {influence['influence_score']:.3f}")

        # Detect social clusters
        clusters = await social_network.detect_social_clusters()
        print(f"Social clusters detected: {clusters['clusters_detected']}")

        # Analyze network health
        health = await social_network.analyze_network_health()
        print(f"Network health score: {health['health_metrics']['health_score']:.3f}")

        # Generate recommendations
        recs = await social_network.generate_recommendations("player1")
        print(f"Recommendations for player1: {len(recs['recommendations'])}")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await social_network.stop_background_tasks()

    asyncio.run(main())