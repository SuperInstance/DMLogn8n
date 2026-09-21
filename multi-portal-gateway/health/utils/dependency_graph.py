"""
Dependency Graph Management

Manages service dependencies and provides dependency analysis
for cascade failure detection and impact assessment.
"""

import logging
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class DependencyNode:
    """Represents a service node in the dependency graph"""
    service_id: str
    name: str
    service_type: str
    critical: bool = False
    status: str = "unknown"
    dependencies: Set[str] = None
    dependents: Set[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.dependents is None:
            self.dependents = set()

@dataclass
class DependencyIssue:
    """Represents a dependency-related issue"""
    service_id: str
    dependency_id: str
    dependency_status: str
    impact_level: str  # high, medium, low
    description: str
    affected_services: List[str]

class DependencyGraph:
    """Manages service dependency relationships"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nodes: Dict[str, DependencyNode] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)

    def add_service(self, service_id: str, name: str, service_type: str, critical: bool = False) -> None:
        """Add a service to the dependency graph"""
        if service_id not in self.nodes:
            self.nodes[service_id] = DependencyNode(
                service_id=service_id,
                name=name,
                service_type=service_type,
                critical=critical
            )
            self.logger.debug(f"Added service {service_id} to dependency graph")

    def add_dependency(self, service_id: str, dependency_id: str) -> None:
        """Add a dependency relationship"""
        # Ensure both services exist
        if service_id not in self.nodes:
            self.add_service(service_id, service_id, "unknown")
        if dependency_id not in self.nodes:
            self.add_service(dependency_id, dependency_id, "unknown")

        # Add dependency relationship
        self.dependencies[service_id].add(dependency_id)
        self.dependents[dependency_id].add(service_id)

        # Update node relationships
        self.nodes[service_id].dependencies.add(dependency_id)
        self.nodes[dependency_id].dependents.add(service_id)

        self.logger.debug(f"Added dependency: {service_id} -> {dependency_id}")

    def remove_service(self, service_id: str) -> None:
        """Remove a service from the dependency graph"""
        if service_id not in self.nodes:
            return

        # Remove all dependencies
        for dep_id in self.dependencies[service_id]:
            self.dependents[dep_id].discard(service_id)
            self.nodes[dep_id].dependents.discard(service_id)

        # Remove all dependents
        for dependent_id in self.dependents[service_id]:
            self.dependencies[dependent_id].discard(service_id)
            self.nodes[dependent_id].dependencies.discard(service_id)

        # Remove from dictionaries
        del self.dependencies[service_id]
        del self.dependents[service_id]
        del self.nodes[service_id]

        self.logger.debug(f"Removed service {service_id} from dependency graph")

    def remove_dependency(self, service_id: str, dependency_id: str) -> None:
        """Remove a dependency relationship"""
        if service_id in self.dependencies:
            self.dependencies[service_id].discard(dependency_id)

        if dependency_id in self.dependents:
            self.dependents[dependency_id].discard(service_id)

        if service_id in self.nodes:
            self.nodes[service_id].dependencies.discard(dependency_id)

        if dependency_id in self.nodes:
            self.nodes[dependency_id].dependents.discard(service_id)

        self.logger.debug(f"Removed dependency: {service_id} -> {dependency_id}")

    def get_dependencies(self, service_id: str) -> Set[str]:
        """Get direct dependencies of a service"""
        return self.dependencies.get(service_id, set())

    def get_dependents(self, service_id: str) -> Set[str]:
        """Get services that depend on this service"""
        return self.dependents.get(service_id, set())

    def get_all_dependencies(self, service_id: str) -> Set[str]:
        """Get all transitive dependencies of a service"""
        visited = set()
        queue = deque([service_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)

            for dep in self.dependencies.get(current, set()):
                if dep not in visited:
                    queue.append(dep)

        # Remove the service itself from the result
        visited.discard(service_id)
        return visited

    def get_all_dependents(self, service_id: str) -> Set[str]:
        """Get all transitive dependents of a service"""
        visited = set()
        queue = deque([service_id])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)

            for dependent in self.dependents.get(current, set()):
                if dependent not in visited:
                    queue.append(dependent)

        # Remove the service itself from the result
        visited.discard(service_id)
        return visited

    def update_service_status(self, service_id: str, status: str) -> None:
        """Update the status of a service"""
        if service_id in self.nodes:
            self.nodes[service_id].status = status
            self.logger.debug(f"Updated status for {service_id}: {status}")

    def check_dependency_health(self, service_id: str, health_results: Dict[str, Any]) -> List[DependencyIssue]:
        """Check dependency health for a specific service"""
        issues = []
        dependencies = self.get_dependencies(service_id)

        for dep_id in dependencies:
            dep_health = health_results.get(dep_id)
            if not dep_health:
                issues.append(DependencyIssue(
                    service_id=service_id,
                    dependency_id=dep_id,
                    dependency_status="unknown",
                    impact_level="medium",
                    description=f"Dependency {dep_id} has no health data",
                    affected_services=[service_id]
                ))
            elif dep_health.get("status") in ["critical", "degraded"]:
                impact_level = self._calculate_impact_level(service_id, dep_id, dep_health.get("status"))
                affected_services = self.get_all_dependents(service_id)

                issues.append(DependencyIssue(
                    service_id=service_id,
                    dependency_id=dep_id,
                    dependency_status=dep_health.get("status"),
                    impact_level=impact_level,
                    description=f"Dependency {dep_id} is {dep_health.get('status')}",
                    affected_services=list(affected_services)
                ))

        return issues

    def detect_cascade_failures(self, failed_services: List[str]) -> Dict[str, Any]:
        """Detect potential cascade failures"""
        cascade_info = {
            "at_risk_services": set(),
            "critical_paths": [],
            "impact_assessment": {}
        }

        for failed_service in failed_services:
            # Find all services that depend on the failed service
            affected_services = self.get_all_dependents(failed_service)

            for service in affected_services:
                if service not in failed_services:
                    cascade_info["at_risk_services"].add(service)

            # Analyze critical paths
            critical_path = self._find_critical_path(failed_service)
            if critical_path:
                cascade_info["critical_paths"].append(critical_path)

        # Convert to list for JSON serialization
        cascade_info["at_risk_services"] = list(cascade_info["at_risk_services"])

        # Assess impact
        cascade_info["impact_assessment"] = self._assess_cascade_impact(failed_services, cascade_info["at_risk_services"])

        return cascade_info

    def find_dependency_cycles(self) -> List[List[str]]:
        """Find circular dependencies in the graph"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependencies.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def get_service_dependency_depth(self, service_id: str) -> int:
        """Get the maximum depth of dependencies for a service"""
        if service_id not in self.nodes:
            return 0

        def get_depth(current_id: str, visited: Set[str]) -> int:
            if current_id in visited:
                return 0  # Cycle detected

            visited.add(current_id)
            max_depth = 0

            for dep in self.dependencies.get(current_id, set()):
                depth = 1 + get_depth(dep, visited.copy())
                max_depth = max(max_depth, depth)

            return max_depth

        return get_depth(service_id, set())

    def get_critical_services(self) -> List[str]:
        """Get list of critical services based on dependencies"""
        critical_services = []

        for service_id, node in self.nodes.items():
            # Service is critical if it's marked as critical
            if node.critical:
                critical_services.append(service_id)
                continue

            # Service is critical if many other services depend on it
            dependents_count = len(self.get_all_dependents(service_id))
            if dependents_count >= 3:  # Threshold for criticality
                critical_services.append(service_id)

        return critical_services

    def get_dependency_graph_data(self) -> Dict[str, Any]:
        """Get dependency graph data for visualization"""
        nodes = []
        edges = []

        for service_id, node in self.nodes.items():
            nodes.append({
                "id": service_id,
                "name": node.name,
                "type": node.service_type,
                "status": node.status,
                "critical": node.critical,
                "dependency_count": len(node.dependencies),
                "dependent_count": len(node.dependents)
            })

        for service_id, deps in self.dependencies.items():
            for dep_id in deps:
                edges.append({
                    "from": service_id,
                    "to": dep_id,
                    "type": "dependency"
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "critical_services": self.get_critical_services(),
            "cycles": self.find_dependency_cycles()
        }

    def _calculate_impact_level(self, service_id: str, dependency_id: str, dependency_status: str) -> str:
        """Calculate the impact level of a dependency issue"""
        # Check if the dependency is critical
        dep_node = self.nodes.get(dependency_id)
        service_node = self.nodes.get(service_id)

        if not dep_node or not service_node:
            return "medium"

        # High impact if dependency is critical or service is critical
        if dep_node.critical or service_node.critical:
            return "high"

        # High impact if dependency status is critical
        if dependency_status == "critical":
            return "high"

        # Medium impact for degraded dependencies
        if dependency_status == "degraded":
            return "medium"

        return "low"

    def _find_critical_path(self, service_id: str) -> Optional[List[str]]:
        """Find a critical dependency path from a failed service"""
        # Find the longest chain of dependencies from the failed service
        def longest_path(current_id: str, visited: Set[str]) -> List[str]:
            if current_id in visited:
                return []

            visited.add(current_id)
            max_path = []

            for dependent in self.dependents.get(current_id, set()):
                path = [current_id] + longest_path(dependent, visited.copy())
                if len(path) > len(max_path):
                    max_path = path

            return max_path

        return longest_path(service_id, set()) if longest_path(service_id, set()) else None

    def _assess_cascade_impact(self, failed_services: List[str], at_risk_services: List[str]) -> Dict[str, Any]:
        """Assess the impact of potential cascade failures"""
        impact = {
            "total_affected_services": len(at_risk_services),
            "critical_services_affected": 0,
            "business_impact": "unknown",
            "recommended_actions": []
        }

        # Count critical services affected
        for service_id in at_risk_services:
            if service_id in self.nodes and self.nodes[service_id].critical:
                impact["critical_services_affected"] += 1

        # Assess business impact
        if impact["critical_services_affected"] > 0:
            impact["business_impact"] = "high"
        elif len(at_risk_services) > 5:
            impact["business_impact"] = "medium"
        else:
            impact["business_impact"] = "low"

        # Generate recommendations
        if impact["business_impact"] == "high":
            impact["recommended_actions"].append("Immediate intervention required")
            impact["recommended_actions"].append("Consider activating disaster recovery procedures")
        elif impact["business_impact"] == "medium":
            impact["recommended_actions"].append("Monitor affected services closely")
            impact["recommended_actions"].append("Prepare contingency plans")
        else:
            impact["recommended_actions"].append("Continue normal monitoring")

        return impact

    def validate_dependencies(self) -> Dict[str, Any]:
        """Validate the dependency graph for issues"""
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        # Check for cycles
        cycles = self.find_dependency_cycles()
        if cycles:
            validation["is_valid"] = False
            validation["issues"].append(f"Circular dependencies detected: {cycles}")

        # Check for orphaned services (no dependencies and no dependents)
        orphaned_services = []
        for service_id, node in self.nodes.items():
            if not node.dependencies and not node.dependents:
                orphaned_services.append(service_id)

        if orphaned_services:
            validation["warnings"].append(f"Orphaned services found: {orphaned_services}")

        # Check for self-dependencies
        self_dependencies = []
        for service_id, deps in self.dependencies.items():
            if service_id in deps:
                self_dependencies.append(service_id)

        if self_dependencies:
            validation["is_valid"] = False
            validation["issues"].append(f"Self-dependencies detected: {self_dependencies}")

        return validation

    def export_graph(self, format: str = "dict") -> Any:
        """Export the dependency graph in various formats"""
        graph_data = {
            "nodes": {},
            "edges": []
        }

        # Export nodes
        for service_id, node in self.nodes.items():
            graph_data["nodes"][service_id] = {
                "name": node.name,
                "type": node.service_type,
                "critical": node.critical,
                "status": node.status,
                "dependencies": list(node.dependencies),
                "dependents": list(node.dependents)
            }

        # Export edges
        for service_id, deps in self.dependencies.items():
            for dep_id in deps:
                graph_data["edges"].append({
                    "from": service_id,
                    "to": dep_id
                })

        if format == "dict":
            return graph_data
        elif format == "json":
            import json
            return json.dumps(graph_data, indent=2)
        elif format == "dot":
            return self._export_dot_format(graph_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_dot_format(self, graph_data: Dict[str, Any]) -> str:
        """Export graph in Graphviz DOT format"""
        dot_lines = ["digraph dependencies {"]
        dot_lines.append("  rankdir=LR;")

        # Add nodes
        for node_id, node_info in graph_data["nodes"].items():
            color = "red" if node_info["critical"] else "black"
            shape = "box" if node_info["status"] == "healthy" else "ellipse"
            dot_lines.append(f'  "{node_id}" [label="{node_info["name"]}", color="{color}", shape={shape}];')

        # Add edges
        for edge in graph_data["edges"]:
            dot_lines.append(f'  "{edge["from"]}" -> "{edge["to"]}";')

        dot_lines.append("}")
        return "\n".join(dot_lines)