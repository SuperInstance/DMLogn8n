#!/usr/bin/env python3
"""
Migration Planning and Dependency Analysis
Analyzes database structure and creates optimized migration plans
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import networkx as nx
from enum import Enum

from migration_engine import TableMigrationPlan, DatabaseType, MigrationConfig, DatabaseConnector

logger = logging.getLogger("migration_planner")

class MigrationStrategy(Enum):
    """Migration strategy types"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    DEPENDENCY_AWARE = "dependency_aware"

class TablePriority(Enum):
    """Table migration priority"""
    CRITICAL = 1  # Core tables (users, characters)
    HIGH = 2      # Important tables (sessions, campaigns)
    MEDIUM = 3    # Secondary tables (memories, decisions)
    LOW = 4       # Auxiliary tables (logs, metrics)

@dataclass
class DependencyGraph:
    """Table dependency graph"""
    graph: nx.DiGraph
    tables: Dict[str, Dict[str, Any]]
    foreign_keys: Dict[str, List[Tuple[str, str]]]  # table -> [(fk_column, referenced_table)]
    orphaned_tables: List[str]

@dataclass
class MigrationPlan:
    """Complete migration plan"""
    migration_id: str
    strategy: MigrationStrategy
    total_tables: int
    estimated_duration_hours: float
    estimated_data_size_gb: float
    phases: List['MigrationPhase']
    dependencies_resolved: bool
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: List[str]

@dataclass
class MigrationPhase:
    """Phase of migration plan"""
    phase_id: int
    name: str
    description: str
    tables: List[str]
    estimated_duration_minutes: float
    parallelizable: bool
    dependencies: List[str]  # Phase dependencies
    priority: TablePriority
    rollback_plan: str

class MigrationPlanner:
    """Advanced migration planning engine"""

    def __init__(self):
        self.dependency_cache: Dict[str, DependencyGraph] = {}
        self.priority_rules = self._load_priority_rules()
        self.risk_factors = self._load_risk_factors()

    def _load_priority_rules(self) -> Dict[str, TablePriority]:
        """Load table priority rules"""
        return {
            # Critical core tables
            "users": TablePriority.CRITICAL,
            "characters": TablePriority.CRITICAL,
            "campaigns": TablePriority.CRITICAL,
            "sessions": TablePriority.HIGH,

            # High importance
            "session_participants": TablePriority.HIGH,
            "memories": TablePriority.HIGH,
            "decisions": TablePriority.HIGH,
            "training_data": TablePriority.MEDIUM,

            # Medium importance
            "model_versions": TablePriority.MEDIUM,
            "combat_records": TablePriority.MEDIUM,
            "dialogue_history": TablePriority.MEDIUM,

            # Low importance
            "logs": TablePriority.LOW,
            "metrics": TablePriority.LOW,
            "analytics": TablePriority.LOW,
            "temp_data": TablePriority.LOW,
        }

    def _load_risk_factors(self) -> Dict[str, float]:
        """Load risk assessment factors"""
        return {
            "large_table": 0.3,          # Tables with >1M rows
            "complex_schema": 0.2,       # Tables with >20 columns
            "many_dependencies": 0.2,    # Tables with >5 dependencies
            "foreign_key_cascade": 0.15, # Tables with cascade operations
            "custom_types": 0.1,         # Tables with custom data types
            "partial_indexes": 0.05,     # Tables with partial indexes
        }

    async def create_plan(self, config: MigrationConfig) -> List[TableMigrationPlan]:
        """Create detailed migration plan with dependency analysis"""
        logger.info(f"Creating migration plan for {len(config.tables)} tables")

        # Step 1: Analyze source database structure
        dependency_graph = await self._analyze_dependencies(config)

        # Step 2: Resolve migration order
        migration_order = self._resolve_migration_order(dependency_graph)

        # Step 3: Group tables into phases
        phases = self._group_into_phases(migration_order, dependency_graph)

        # Step 4: Create detailed table plans
        table_plans = await self._create_table_plans(config, dependency_graph, phases)

        # Step 5: Optimize for performance
        optimized_plans = self._optimize_migration_plans(table_plans, config)

        logger.info(f"Created migration plan with {len(optimized_plans)} table plans")
        return optimized_plans

    async def _analyze_dependencies(self, config: MigrationConfig) -> DependencyGraph:
        """Analyze table dependencies and foreign key relationships"""
        logger.info("Analyzing database dependencies")

        source_connector = self._get_connector(config.source_config)
        await source_connector.connect()

        try:
            # Create dependency graph
            graph = nx.DiGraph()
            tables = {}
            foreign_keys = defaultdict(list)

            # Analyze each table
            for table_name in config.tables:
                table_info = await source_connector.get_table_info(table_name)
                tables[table_name] = table_info

                # Add table to graph
                graph.add_node(table_name, **table_info)

                # Analyze foreign keys
                fk_info = await self._analyze_foreign_keys(source_connector, table_name)
                for fk_column, referenced_table in fk_info:
                    foreign_keys[table_name].append((fk_column, referenced_table))

                    # Add dependency edge
                    if referenced_table in config.tables:
                        graph.add_edge(referenced_table, table_name,
                                     type="foreign_key",
                                     column=fk_column)

            # Check for orphaned tables (tables with no dependencies)
            orphaned_tables = [
                table for table in config.tables
                if graph.in_degree(table) == 0 and graph.out_degree(table) == 0
            ]

            dependency_graph = DependencyGraph(
                graph=graph,
                tables=tables,
                foreign_keys=dict(foreign_keys),
                orphaned_tables=orphaned_tables
            )

            # Cache for future use
            cache_key = self._generate_cache_key(config)
            self.dependency_cache[cache_key] = dependency_graph

            logger.info(f"Analyzed {len(tables)} tables with {len(foreign_keys)} foreign key relationships")
            return dependency_graph

        finally:
            await source_connector.disconnect()

    async def _analyze_foreign_keys(self, connector: DatabaseConnector, table_name: str) -> List[Tuple[str, str]]:
        """Analyze foreign key constraints for a table"""
        try:
            # This is a simplified implementation
            # In practice, you'd query the information schema

            # For PostgreSQL
            if isinstance(connector, type(connector.__class__.__bases__[0])) or connector.db_type == DatabaseType.POSTGRESQL:
                query = """
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS referenced_table,
                        ccu.column_name AS referenced_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = $1
                """

                results = await connector.execute_query(query)
                return [(row['column_name'], row['referenced_table']) for row in results]

            # For other databases, implement similar logic
            return []

        except Exception as e:
            logger.warning(f"Failed to analyze foreign keys for {table_name}: {e}")
            return []

    def _resolve_migration_order(self, dependency_graph: DependencyGraph) -> List[str]:
        """Resolve table migration order using topological sorting"""
        try:
            # Use topological sort to determine migration order
            # Dependencies must be migrated before dependents
            migration_order = list(nx.topological_sort(dependency_graph.graph))

            logger.info(f"Resolved migration order: {' -> '.join(migration_order)}")
            return migration_order

        except nx.NetworkXError as e:
            # Handle circular dependencies
            logger.warning(f"Circular dependencies detected: {e}")

            # Find strongly connected components (circular dependencies)
            sccs = list(nx.strongly_connected_components(dependency_graph.graph))

            # Break cycles by removing minimal edges
            graph_copy = dependency_graph.graph.copy()
            for scc in sccs:
                if len(scc) > 1:
                    # This is a cycle, break it
                    self._break_cycle(graph_copy, scc)

            migration_order = list(nx.topological_sort(graph_copy))
            return migration_order

    def _break_cycle(self, graph: nx.DiGraph, cycle: Set[str]):
        """Break circular dependency by removing the lowest priority edge"""
        cycle_edges = list(graph.subgraph(cycle).edges())

        # Sort by priority (remove edge to lowest priority table)
        def edge_priority(edge):
            source, target = edge
            source_priority = self.priority_rules.get(source, TablePriority.LOW).value
            target_priority = self.priority_rules.get(target, TablePriority.LOW).value
            return max(source_priority, target_priority)

        cycle_edges.sort(key=edge_priority)

        # Remove the lowest priority edge
        if cycle_edges:
            edge_to_remove = cycle_edges[0]
            graph.remove_edge(*edge_to_remove)
            logger.warning(f"Breaking cycle by removing edge: {edge_to_remove[0]} -> {edge_to_remove[1]}")

    def _group_into_phases(self, migration_order: List[str], dependency_graph: DependencyGraph) -> List[MigrationPhase]:
        """Group tables into migration phases based on dependencies and priority"""
        phases = []
        current_phase_tables = []
        current_phase_dependencies = set()
        phase_id = 1

        for table_name in migration_order:
            table_dependencies = set(dependency_graph.graph.predecessors(table_name))

            # Check if this table can be included in current phase
            if table_dependencies.issubset(current_phase_dependencies):
                current_phase_tables.append(table_name)
                current_phase_dependencies.add(table_name)
            else:
                # Start new phase
                if current_phase_tables:
                    phase = self._create_phase(phase_id, current_phase_tables, dependency_graph)
                    phases.append(phase)
                    phase_id += 1

                current_phase_tables = [table_name]
                current_phase_dependencies = {table_name}.union(table_dependencies)

        # Add final phase
        if current_phase_tables:
            phase = self._create_phase(phase_id, current_phase_tables, dependency_graph)
            phases.append(phase)

        logger.info(f"Created {len(phases)} migration phases")
        return phases

    def _create_phase(self, phase_id: int, tables: List[str], dependency_graph: DependencyGraph) -> MigrationPhase:
        """Create a migration phase"""
        # Determine phase priority based on highest priority table
        priorities = [self.priority_rules.get(table, TablePriority.LOW).value for table in tables]
        phase_priority = TablePriority(min(priorities))

        # Estimate duration (rough calculation)
        total_rows = sum(
            dependency_graph.tables[table].get("row_count", 0)
            for table in tables
        )
        estimated_duration = total_rows / 10000  # Assume 10k rows per minute

        # Check if tables can be migrated in parallel
        parallelizable = len(tables) > 1 and all(
            dependency_graph.graph.in_degree(table) == 0 or
            all(pred in tables for pred in dependency_graph.graph.predecessors(table))
            for table in tables
        )

        phase_name = f"Phase {phase_id}: {', '.join(tables[:3])}{'...' if len(tables) > 3 else ''}"

        return MigrationPhase(
            phase_id=phase_id,
            name=phase_name,
            description=f"Migrate {len(tables)} tables in priority group",
            tables=tables,
            estimated_duration_minutes=estimated_duration,
            parallelizable=parallelizable,
            dependencies=[],  # Phase dependencies handled by ordering
            priority=phase_priority,
            rollback_plan=f"Rollback phase {phase_id} using backup files"
        )

    async def _create_table_plans(self, config: MigrationConfig, dependency_graph: DependencyGraph,
                                phases: List[MigrationPhase]) -> List[TableMigrationPlan]:
        """Create detailed migration plans for each table"""
        table_plans = []

        for phase in phases:
            for table_name in phase.tables:
                table_info = dependency_graph.tables[table_name]

                # Calculate table size estimate
                row_count = table_info.get("row_count", 0)
                estimated_size = self._estimate_table_size(table_info, row_count)

                # Determine dependencies
                dependencies = list(dependency_graph.graph.predecessors(table_name))

                plan = TableMigrationPlan(
                    table_name=table_name,
                    source_type=DatabaseType(config.source_config["type"]),
                    target_type=DatabaseType(config.target_config["type"]),
                    row_count=row_count,
                    estimated_size_mb=estimated_size,
                    dependencies=dependencies,
                    transformation_required=self._needs_transformation(config, table_name),
                    index_rebuild_required=self._needs_index_rebuild(table_info),
                    validation_queries=self._generate_validation_queries(table_name, table_info),
                    batch_strategy=self._determine_batch_strategy(table_name, row_count),
                    key_column=self._determine_key_column(table_info)
                )

                table_plans.append(plan)

        return table_plans

    def _estimate_table_size(self, table_info: Dict[str, Any], row_count: int) -> float:
        """Estimate table size in MB"""
        columns = table_info.get("columns", [])

        # Estimate average row size based on column types
        row_size_bytes = 0
        for column in columns:
            data_type = column.get("data_type", "").lower()

            if "integer" in data_type or "int" in data_type:
                row_size_bytes += 4
            elif "bigint" in data_type:
                row_size_bytes += 8
            elif "float" in data_type or "double" in data_type or "numeric" in data_type:
                row_size_bytes += 8
            elif "varchar" in data_type or "char" in data_type:
                max_length = column.get("character_maximum_length", 255)
                row_size_bytes += min(max_length, 255)  # Assume average usage
            elif "text" in data_type:
                row_size_bytes += 500  # Assume average text size
            elif "json" in data_type or "jsonb" in data_type:
                row_size_bytes += 1000  # Assume average JSON size
            elif "timestamp" in data_type or "datetime" in data_type:
                row_size_bytes += 8
            elif "boolean" in data_type:
                row_size_bytes += 1
            else:
                row_size_bytes += 50  # Default estimate

        # Add overhead for indexes and other metadata
        row_size_bytes *= 1.3

        # Convert to MB
        size_mb = (row_count * row_size_bytes) / (1024 * 1024)
        return max(0.001, size_mb)  # Minimum 1KB

    def _needs_transformation(self, config: MigrationConfig, table_name: str) -> bool:
        """Determine if table needs data transformation"""
        # Check if source and target databases are different types
        if config.source_config["type"] != config.target_config["type"]:
            return True

        # Check if transformation rules exist for this table
        if config.transformation_rules and table_name in config.transformation_rules:
            return True

        return False

    def _needs_index_rebuild(self, table_info: Dict[str, Any]) -> bool:
        """Determine if indexes need to be rebuilt"""
        indexes = table_info.get("indexes", [])

        # Rebuild if there are many indexes or complex indexes
        if len(indexes) > 5:
            return True

        # Check for complex index definitions
        for index in indexes:
            index_def = index.get("indexdef", "").lower()
            if "unique" in index_def or "partial" in index_def or "expression" in index_def:
                return True

        return False

    def _generate_validation_queries(self, table_name: str, table_info: Dict[str, Any]) -> List[str]:
        """Generate validation queries for the table"""
        queries = [
            f"SELECT COUNT(*) FROM {table_name}",
        ]

        # Add specific validations based on table characteristics
        columns = table_info.get("columns", [])

        # Validate important columns
        important_columns = ["id", "created_at", "updated_at", "is_active"]
        for col in important_columns:
            if any(c.get("column_name") == col for c in columns):
                queries.append(f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL")

        # Add data integrity checks
        if table_name == "characters":
            queries.extend([
                "SELECT COUNT(*) FROM characters WHERE level < 1 OR level > 20",
                "SELECT COUNT(DISTINCT id) FROM characters"
            ])
        elif table_name == "sessions":
            queries.extend([
                "SELECT COUNT(*) FROM sessions WHERE start_time > end_time",
                "SELECT COUNT(DISTINCT campaign_id) FROM sessions"
            ])

        return queries

    def _determine_batch_strategy(self, table_name: str, row_count: int) -> str:
        """Determine optimal batching strategy"""
        if row_count < 1000:
            return "full_table"
        elif "created_at" in table_name or "updated_at" in table_name:
            return "timestamp_based"
        elif "id" in table_name:
            return "id_based"
        else:
            return "offset_based"

    def _determine_key_column(self, table_info: Dict[str, Any]) -> str:
        """Determine the best column for batching"""
        columns = table_info.get("columns", [])

        # Look for primary key candidates
        for col in columns:
            col_name = col.get("column_name", "").lower()
            if col_name in ["id", "uuid", "pk", "primary_key"]:
                return col.get("column_name")

        # Look for timestamp columns
        for col in columns:
            col_name = col.get("column_name", "").lower()
            if "created_at" in col_name or "timestamp" in col_name:
                return col.get("column_name")

        # Fall back to first column
        if columns:
            return columns[0].get("column_name")

        return "id"

    def _optimize_migration_plans(self, table_plans: List[TableMigrationPlan], config: MigrationConfig) -> List[TableMigrationPlan]:
        """Optimize migration plans for performance and reliability"""
        optimized_plans = []

        # Sort by priority and dependencies
        table_plans.sort(key=lambda p: (
            self.priority_rules.get(p.table_name, TablePriority.LOW).value,
            len(p.dependencies),
            -p.row_count  # Larger tables first within same priority
        ))

        for plan in table_plans:
            # Apply optimizations
            if plan.row_count > 100000:
                # For large tables, use smaller batch sizes
                plan.batch_strategy = "id_based"

            if plan.estimated_size_mb > 1000:
                # For very large tables, add additional validation
                plan.validation_queries.append(f"SELECT MD5(STRING_AGG(CAST(id AS TEXT), ',')) FROM {plan.table_name}")

            optimized_plans.append(plan)

        return optimized_plans

    def _generate_cache_key(self, config: MigrationConfig) -> str:
        """Generate cache key for dependency analysis"""
        import hashlib

        key_data = {
            "source": config.source_config,
            "target": config.target_config,
            "tables": sorted(config.tables)
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_connector(self, config: Dict[str, Any]) -> DatabaseConnector:
        """Get database connector (simplified for planning)"""
        # This would normally use the same connector factory as the main engine
        from migration_engine import PostgreSQLConnector, RedisConnector

        db_type = config.get("type", "postgresql").lower()

        if db_type == "postgresql":
            return PostgreSQLConnector(config)
        elif db_type == "redis":
            return RedisConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    async def analyze_migration_risk(self, config: MigrationConfig) -> Dict[str, Any]:
        """Analyze migration risks and provide recommendations"""
        logger.info("Analyzing migration risks")

        risk_score = 0.0
        risk_factors = []
        recommendations = []

        # Analyze database differences
        if config.source_config["type"] != config.target_config["type"]:
            risk_score += 0.3
            risk_factors.append("Cross-database migration type conversion")
            recommendations.append("Perform thorough testing of data type conversions")

        # Analyze data volume
        total_estimated_size = 0
        for table_name in config.tables:
            # Estimate size (simplified)
            total_estimated_size += 100  # Placeholder estimate

        if total_estimated_size > 10000:  # >10GB
            risk_score += 0.2
            risk_factors.append("Large data volume")
            recommendations.append("Consider incremental migration approach")

        # Analyze complexity
        if len(config.tables) > 50:
            risk_score += 0.15
            risk_factors.append("High table count")
            recommendations.append("Break migration into smaller batches")

        # Analyze transformation requirements
        if config.transformation_rules:
            risk_score += 0.1
            risk_factors.append("Complex data transformations required")
            recommendations.append("Test transformation rules thoroughly")

        # Determine overall risk level
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
        elif risk_score < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "estimated_data_size_mb": total_estimated_size,
            "complexity_score": len(config.tables) / 10.0  # Normalized complexity
        }

    async def create_migration_timeline(self, table_plans: List[TableMigrationPlan],
                                      config: MigrationConfig) -> Dict[str, Any]:
        """Create detailed migration timeline"""
        logger.info("Creating migration timeline")

        # Calculate total duration
        total_duration_minutes = sum(
            plan.estimated_size_mb / 100  # Assume 100MB per minute
            for plan in table_plans
        )

        # Add overhead for validation, verification, etc.
        total_duration_minutes *= 1.3

        # Create timeline phases
        phases = []
        current_time = 0

        # Add backup phase
        backup_duration = total_duration_minutes * 0.1  # 10% of migration time
        phases.append({
            "name": "Backup Phase",
            "duration_minutes": backup_duration,
            "start_time": current_time,
            "end_time": current_time + backup_duration,
            "description": "Create full backups of source tables"
        })
        current_time += backup_duration

        # Add migration phases (grouped by priority)
        priority_groups = defaultdict(list)
        for plan in table_plans:
            priority = self.priority_rules.get(plan.table_name, TablePriority.LOW)
            priority_groups[priority].append(plan)

        for priority in [TablePriority.CRITICAL, TablePriority.HIGH, TablePriority.MEDIUM, TablePriority.LOW]:
            if priority in priority_groups:
                plans_in_group = priority_groups[priority]
                group_duration = sum(
                    plan.estimated_size_mb / 100
                    for plan in plans_in_group
                )

                phases.append({
                    "name": f"{priority.name} Priority Migration",
                    "duration_minutes": group_duration,
                    "start_time": current_time,
                    "end_time": current_time + group_duration,
                    "tables": [plan.table_name for plan in plans_in_group],
                    "description": f"Migrate {len(plans_in_group)} {priority.name.lower()} priority tables"
                })
                current_time += group_duration

        # Add verification phase
        verification_duration = total_duration_minutes * 0.15  # 15% of migration time
        phases.append({
            "name": "Verification Phase",
            "duration_minutes": verification_duration,
            "start_time": current_time,
            "end_time": current_time + verification_duration,
            "description": "Verify migration integrity and data consistency"
        })

        return {
            "total_duration_minutes": total_duration_minutes,
            "total_duration_hours": total_duration_minutes / 60,
            "estimated_completion": datetime.now() + timedelta(minutes=total_duration_minutes),
            "phases": phases,
            "parallelizable_phases": len([p for p in phases if p.get("tables") and len(p["tables"]) > 1])
        }

    async def estimate_resource_requirements(self, table_plans: List[TableMigrationPlan]) -> Dict[str, Any]:
        """Estimate resource requirements for migration"""
        total_size_mb = sum(plan.estimated_size_mb for plan in table_plans)
        total_rows = sum(plan.row_count for plan in table_plans)

        # Estimate memory requirements
        # Assume we need memory for batch processing and transformations
        memory_gb = max(4, total_size_mb / 1024 * 0.5)  # 50% of total size, minimum 4GB

        # Estimate CPU requirements
        # Based on complexity and transformation needs
        cpu_cores = max(2, len(table_plans) / 10)  # 1 core per 10 tables, minimum 2 cores

        # Estimate storage requirements
        # Source + target + backups + temp space
        storage_gb = (total_size_mb / 1024) * 3.5  # 3.5x total size for safety

        # Estimate network bandwidth (if migrating between servers)
        network_mbps = min(1000, total_size_mb / 100)  # Cap at 1Gbps

        return {
            "memory_gb": round(memory_gb, 2),
            "cpu_cores": int(cpu_cores),
            "storage_gb": round(storage_gb, 2),
            "network_mbps": int(network_mbps),
            "estimated_peak_cpu": 0.8,  # 80% CPU usage during peak
            "estimated_peak_memory": 0.7,  # 70% memory usage during peak
            "io_intensity": "high" if total_size_mb > 10000 else "medium",
            "recommended_instance_type": self._recommend_instance_type(memory_gb, cpu_cores)
        }

    def _recommend_instance_type(self, memory_gb: float, cpu_cores: int) -> str:
        """Recommend AWS/Azure instance type based on requirements"""
        if memory_gb < 8 and cpu_cores <= 2:
            return "t3.medium or equivalent"
        elif memory_gb < 16 and cpu_cores <= 4:
            return "t3.large or equivalent"
        elif memory_gb < 32 and cpu_cores <= 8:
            return "m5.large or equivalent"
        else:
            return "m5.xlarge or higher (memory optimized)"

# Example usage and testing
async def test_planner():
    """Test the migration planner"""
    planner = MigrationPlanner()

    config = MigrationConfig(
        migration_id="test_migration",
        name="Test Migration",
        description="Test migration for planning",
        migration_type=MigrationType.DATA,
        source_config={
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "user": "test",
            "password": "test",
            "database": "test_db"
        },
        target_config={
            "type": "postgresql",
            "host": "localhost",
            "port": 5433,
            "user": "test",
            "password": "test",
            "database": "target_db"
        },
        tables=["characters", "campaigns", "sessions", "memories", "decisions"]
    )

    try:
        plans = await planner.create_plan(config)

        print(f"Created {len(plans)} table migration plans:")
        for plan in plans:
            print(f"  - {plan.table_name}: {plan.row_count} rows, {plan.estimated_size_mb:.2f} MB")

        # Analyze risks
        risk_analysis = await planner.analyze_migration_risk(config)
        print(f"\nRisk Analysis: {risk_analysis['risk_level']} (score: {risk_analysis['risk_score']:.2f})")
        for factor in risk_analysis['risk_factors']:
            print(f"  - {factor}")

        # Create timeline
        timeline = await planner.create_migration_timeline(plans, config)
        print(f"\nEstimated Duration: {timeline['total_duration_hours']:.1f} hours")
        print(f"Estimated Completion: {timeline['estimated_completion']}")

        # Resource requirements
        resources = await planner.estimate_resource_requirements(plans)
        print(f"\nResource Requirements:")
        print(f"  - Memory: {resources['memory_gb']} GB")
        print(f"  - CPU: {resources['cpu_cores']} cores")
        print(f"  - Storage: {resources['storage_gb']} GB")
        print(f"  - Recommended: {resources['recommended_instance_type']}")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_planner())