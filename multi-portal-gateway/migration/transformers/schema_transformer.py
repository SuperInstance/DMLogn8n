#!/usr/bin/env python3
"""
Schema Transformer
Handles database schema migration and transformation between different database types
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("schema_transformer")

class DataType(Enum):
    """Generic data types for cross-database compatibility"""
    INTEGER = "integer"
    BIGINT = "bigint"
    FLOAT = "float"
    DOUBLE = "double"
    DECIMAL = "decimal"
    STRING = "string"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    JSON = "json"
    UUID = "uuid"
    BINARY = "binary"
    ARRAY = "array"

@dataclass
class ColumnDefinition:
    """Column definition for schema transformation"""
    name: str
    data_type: DataType
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: bool = True
    default_value: Optional[Any] = None
    auto_increment: bool = False
    primary_key: bool = False
    unique: bool = False
    indexed: bool = False
    check_constraint: Optional[str] = None

@dataclass
class IndexDefinition:
    """Index definition for schema transformation"""
    name: str
    columns: List[str]
    unique: bool = False
    index_type: str = "btree"  # btree, hash, gist, gin, etc.
    partial_condition: Optional[str] = None
    where_clause: Optional[str] = None

@dataclass
class TableDefinition:
    """Complete table definition"""
    name: str
    columns: List[ColumnDefinition]
    indexes: List[IndexDefinition]
    primary_key: List[str]
    foreign_keys: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    table_options: Dict[str, Any]

class SchemaTransformer:
    """Transforms database schemas between different database types"""

    def __init__(self):
        self.type_mappings = self._initialize_type_mappings()
        self.constraint_transformers = self._initialize_constraint_transformers()

    def _initialize_type_mappings(self) -> Dict[str, Dict[str, str]]:
        """Initialize data type mappings between different databases"""
        return {
            "postgresql": {
                "integer": "INTEGER",
                "bigint": "BIGINT",
                "float": "REAL",
                "double": "DOUBLE PRECISION",
                "decimal": "DECIMAL",
                "string": "VARCHAR",
                "text": "TEXT",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "datetime": "TIMESTAMP",
                "timestamp": "TIMESTAMP",
                "json": "JSONB",
                "uuid": "UUID",
                "binary": "BYTEA",
                "array": "JSONB"
            },
            "mysql": {
                "integer": "INT",
                "bigint": "BIGINT",
                "float": "FLOAT",
                "double": "DOUBLE",
                "decimal": "DECIMAL",
                "string": "VARCHAR",
                "text": "TEXT",
                "boolean": "BOOLEAN",
                "date": "DATE",
                "datetime": "DATETIME",
                "timestamp": "TIMESTAMP",
                "json": "JSON",
                "uuid": "CHAR(36)",
                "binary": "BLOB",
                "array": "JSON"
            },
            "mongodb": {
                "integer": "NumberInt",
                "bigint": "NumberLong",
                "float": "Number",
                "double": "Number",
                "decimal": "Decimal128",
                "string": "String",
                "text": "String",
                "boolean": "Boolean",
                "date": "Date",
                "datetime": "Date",
                "timestamp": "Date",
                "json": "Object",
                "uuid": "String",
                "binary": "BinData",
                "array": "Array"
            },
            "redis": {
                "integer": "string",
                "bigint": "string",
                "float": "string",
                "double": "string",
                "decimal": "string",
                "string": "string",
                "text": "string",
                "boolean": "string",
                "date": "string",
                "datetime": "string",
                "timestamp": "string",
                "json": "hash",
                "uuid": "string",
                "binary": "string",
                "array": "list"
            }
        }

    def _initialize_constraint_transformers(self) -> Dict[str, callable]:
        """Initialize constraint transformation functions"""
        return {
            "foreign_key": self._transform_foreign_key,
            "unique": self._transform_unique_constraint,
            "check": self._transform_check_constraint,
            "not_null": self._transform_not_null_constraint,
            "default": self._transform_default_constraint
        }

    async def transform_schema(self, source_schema: Dict[str, Any], source_type: str,
                             target_type: str, transformation_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform database schema from source type to target type"""
        logger.info(f"Transforming schema from {source_type} to {target_type}")

        try:
            # Parse source schema
            table_defs = self._parse_source_schema(source_schema, source_type)

            # Apply transformation rules
            if transformation_rules:
                table_defs = self._apply_transformation_rules(table_defs, transformation_rules)

            # Transform to target database type
            target_schema = self._transform_to_target_type(table_defs, target_type)

            # Generate DDL statements
            ddl_statements = self._generate_ddl_statements(target_schema, target_type)

            return {
                "schema": target_schema,
                "ddl_statements": ddl_statements,
                "transformation_summary": self._generate_transformation_summary(
                    source_schema, target_schema, source_type, target_type
                )
            }

        except Exception as e:
            logger.error(f"Schema transformation failed: {e}")
            raise

    def _parse_source_schema(self, source_schema: Dict[str, Any], source_type: str) -> List[TableDefinition]:
        """Parse source schema into standardized format"""
        table_defs = []

        for table_name, table_info in source_schema.items():
            columns = []
            indexes = []
            foreign_keys = []
            constraints = []

            # Parse columns
            for column_info in table_info.get("columns", []):
                column = self._parse_column_definition(column_info, source_type)
                columns.append(column)

            # Parse indexes
            for index_info in table_info.get("indexes", []):
                index = self._parse_index_definition(index_info, source_type)
                indexes.append(index)

            # Parse foreign keys
            for fk_info in table_info.get("foreign_keys", []):
                foreign_keys.append(fk_info)

            # Parse constraints
            for constraint_info in table_info.get("constraints", []):
                constraints.append(constraint_info)

            # Identify primary key
            primary_key = [
                col.name for col in columns if col.primary_key
            ]

            table_def = TableDefinition(
                name=table_name,
                columns=columns,
                indexes=indexes,
                primary_key=primary_key,
                foreign_keys=foreign_keys,
                constraints=constraints,
                table_options=table_info.get("options", {})
            )
            table_defs.append(table_def)

        return table_defs

    def _parse_column_definition(self, column_info: Dict[str, Any], source_type: str) -> ColumnDefinition:
        """Parse column definition from source schema"""
        # Map source data type to generic type
        source_data_type = column_info.get("data_type", "").lower()
        generic_type = self._map_to_generic_type(source_data_type, source_type)

        return ColumnDefinition(
            name=column_info.get("column_name", ""),
            data_type=generic_type,
            length=column_info.get("character_maximum_length"),
            precision=column_info.get("numeric_precision"),
            scale=column_info.get("numeric_scale"),
            nullable=column_info.get("is_nullable", "YES") == "YES",
            default_value=column_info.get("column_default"),
            auto_increment=column_info.get("auto_increment", False),
            primary_key=column_info.get("is_primary_key", False),
            unique=column_info.get("is_unique", False),
            indexed=column_info.get("is_indexed", False),
            check_constraint=column_info.get("check_constraint")
        )

    def _parse_index_definition(self, index_info: Dict[str, Any], source_type: str) -> IndexDefinition:
        """Parse index definition from source schema"""
        # Extract column names from index definition
        index_def = index_info.get("indexdef", "")

        # Simple parsing - in practice, this would be more sophisticated
        columns = []
        if "CREATE INDEX" in index_def:
            # Extract column list from parentheses
            start = index_def.find("(") + 1
            end = index_def.rfind(")")
            column_list = index_def[start:end]
            columns = [col.strip() for col in column_list.split(",")]

        return IndexDefinition(
            name=index_info.get("indexname", ""),
            columns=columns,
            unique="UNIQUE" in index_def.upper(),
            index_type=self._extract_index_type(index_def),
            partial_condition=self._extract_partial_condition(index_def),
            where_clause=self._extract_where_clause(index_def)
        )

    def _map_to_generic_type(self, source_type: str, database_type: str) -> DataType:
        """Map database-specific type to generic type"""
        type_mapping = {
            "postgresql": {
                "integer": DataType.INTEGER,
                "bigint": DataType.BIGINT,
                "real": DataType.FLOAT,
                "double precision": DataType.DOUBLE,
                "decimal": DataType.DECIMAL,
                "numeric": DataType.DECIMAL,
                "varchar": DataType.STRING,
                "character varying": DataType.STRING,
                "text": DataType.TEXT,
                "boolean": DataType.BOOLEAN,
                "date": DataType.DATE,
                "timestamp": DataType.DATETIME,
                "timestamptz": DataType.DATETIME,
                "jsonb": DataType.JSON,
                "json": DataType.JSON,
                "uuid": DataType.UUID,
                "bytea": DataType.BINARY,
                "array": DataType.ARRAY
            },
            "mysql": {
                "int": DataType.INTEGER,
                "tinyint": DataType.INTEGER,
                "smallint": DataType.INTEGER,
                "mediumint": DataType.INTEGER,
                "bigint": DataType.BIGINT,
                "float": DataType.FLOAT,
                "double": DataType.DOUBLE,
                "decimal": DataType.DECIMAL,
                "varchar": DataType.STRING,
                "char": DataType.STRING,
                "text": DataType.TEXT,
                "longtext": DataType.TEXT,
                "boolean": DataType.BOOLEAN,
                "date": DataType.DATE,
                "datetime": DataType.DATETIME,
                "timestamp": DataType.DATETIME,
                "json": DataType.JSON,
                "binary": DataType.BINARY,
                "blob": DataType.BINARY,
                "longblob": DataType.BINARY
            }
        }

        db_types = type_mapping.get(database_type, {})
        return db_types.get(source_type, DataType.STRING)

    def _apply_transformation_rules(self, table_defs: List[TableDefinition],
                                 rules: Dict[str, Any]) -> List[TableDefinition]:
        """Apply custom transformation rules to schema"""
        transformed_defs = []

        for table_def in table_defs:
            # Apply table-level rules
            if table_def.name in rules.get("table_rules", {}):
                table_rules = rules["table_rules"][table_def.name]
                table_def = self._apply_table_rules(table_def, table_rules)

            # Apply column-level rules
            column_rules = rules.get("column_rules", {})
            for column in table_def.columns:
                if column.name in column_rules:
                    column_rule = column_rules[column.name]
                    column = self._apply_column_rules(column, column_rule)

            transformed_defs.append(table_def)

        return transformed_defs

    def _apply_table_rules(self, table_def: TableDefinition, rules: Dict[str, Any]) -> TableDefinition:
        """Apply table-level transformation rules"""
        # Rename table
        if "rename" in rules:
            table_def.name = rules["rename"]

        # Add columns
        if "add_columns" in rules:
            for col_def in rules["add_columns"]:
                column = ColumnDefinition(
                    name=col_def["name"],
                    data_type=DataType(col_def["type"]),
                    nullable=col_def.get("nullable", True),
                    default_value=col_def.get("default")
                )
                table_def.columns.append(column)

        # Drop columns
        if "drop_columns" in rules:
            column_names_to_drop = set(rules["drop_columns"])
            table_def.columns = [
                col for col in table_def.columns
                if col.name not in column_names_to_drop
            ]

        return table_def

    def _apply_column_rules(self, column: ColumnDefinition, rules: Dict[str, Any]) -> ColumnDefinition:
        """Apply column-level transformation rules"""
        # Rename column
        if "rename" in rules:
            column.name = rules["rename"]

        # Change data type
        if "type" in rules:
            column.data_type = DataType(rules["type"])

        # Set nullable
        if "nullable" in rules:
            column.nullable = rules["nullable"]

        # Set default value
        if "default" in rules:
            column.default_value = rules["default"]

        return column

    def _transform_to_target_type(self, table_defs: List[TableDefinition], target_type: str) -> Dict[str, Any]:
        """Transform standardized schema to target database type"""
        target_schema = {}

        for table_def in table_defs:
            transformed_table = {
                "columns": [],
                "indexes": [],
                "constraints": [],
                "primary_key": table_def.primary_key,
                "foreign_keys": table_def.foreign_keys,
                "options": table_def.table_options
            }

            # Transform columns
            for column in table_def.columns:
                transformed_column = self._transform_column_to_target_type(column, target_type)
                transformed_table["columns"].append(transformed_column)

            # Transform indexes
            for index in table_def.indexes:
                transformed_index = self._transform_index_to_target_type(index, target_type)
                transformed_table["indexes"].append(transformed_index)

            # Transform constraints
            for constraint in table_def.constraints:
                transformed_constraint = self._transform_constraint_to_target_type(
                    constraint, target_type
                )
                if transformed_constraint:
                    transformed_table["constraints"].append(transformed_constraint)

            target_schema[table_def.name] = transformed_table

        return target_schema

    def _transform_column_to_target_type(self, column: ColumnDefinition, target_type: str) -> Dict[str, Any]:
        """Transform column definition to target database type"""
        type_mapping = self.type_mappings.get(target_type, {})
        target_data_type = type_mapping.get(column.data_type.value, "VARCHAR")

        transformed = {
            "name": column.name,
            "type": target_data_type,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "unique": column.unique,
            "auto_increment": column.auto_increment
        }

        # Add type-specific attributes
        if column.data_type in [DataType.STRING] and column.length:
            transformed["length"] = column.length

        if column.data_type == DataType.DECIMAL:
            if column.precision:
                transformed["precision"] = column.precision
            if column.scale:
                transformed["scale"] = column.scale

        if column.default_value is not None:
            transformed["default"] = column.default_value

        if column.check_constraint:
            transformed["check"] = column.check_constraint

        return transformed

    def _transform_index_to_target_type(self, index: IndexDefinition, target_type: str) -> Dict[str, Any]:
        """Transform index definition to target database type"""
        transformed = {
            "name": index.name,
            "columns": index.columns,
            "unique": index.unique,
            "type": index.index_type
        }

        if index.partial_condition:
            transformed["partial"] = index.partial_condition

        if index.where_clause:
            transformed["where"] = index.where_clause

        return transformed

    def _transform_constraint_to_target_type(self, constraint: Dict[str, Any],
                                           target_type: str) -> Optional[Dict[str, Any]]:
        """Transform constraint to target database type"""
        constraint_type = constraint.get("type", "").lower()

        if constraint_type in self.constraint_transformers:
            transformer = self.constraint_transformers[constraint_type]
            return transformer(constraint, target_type)

        return constraint

    def _transform_foreign_key(self, constraint: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Transform foreign key constraint"""
        # Foreign keys are mostly standard across databases
        transformed = constraint.copy()

        # Handle database-specific syntax
        if target_type == "mysql":
            # MySQL specific foreign key options
            if "on_delete" not in transformed:
                transformed["on_delete"] = "RESTRICT"
            if "on_update" not in transformed:
                transformed["on_update"] = "RESTRICT"

        return transformed

    def _transform_unique_constraint(self, constraint: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Transform unique constraint"""
        # Unique constraints are standard
        return constraint

    def _transform_check_constraint(self, constraint: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Transform check constraint"""
        # Check constraints have slight syntax differences
        transformed = constraint.copy()

        if target_type == "mysql" and "condition" in transformed:
            # MySQL uses different syntax for some check conditions
            condition = transformed["condition"]
            # Transform PostgreSQL-specific syntax to MySQL
            if "ANY" in condition:
                condition = condition.replace("ANY(ARRAY[", "IN (").replace("])", ")")
            transformed["condition"] = condition

        return transformed

    def _transform_not_null_constraint(self, constraint: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Transform NOT NULL constraint"""
        # NOT NULL is standard
        return constraint

    def _transform_default_constraint(self, constraint: Dict[str, Any], target_type: str) -> Dict[str, Any]:
        """Transform DEFAULT constraint"""
        transformed = constraint.copy()

        # Handle database-specific default value syntax
        if target_type == "postgresql":
            if transformed.get("default") == "CURRENT_TIMESTAMP":
                transformed["default"] = "NOW()"
        elif target_type == "mysql":
            if transformed.get("default") == "NOW()":
                transformed["default"] = "CURRENT_TIMESTAMP"

        return transformed

    def _generate_ddl_statements(self, target_schema: Dict[str, Any], target_type: str) -> List[str]:
        """Generate DDL statements for target database"""
        ddl_statements = []

        for table_name, table_def in target_schema.items():
            # Generate CREATE TABLE statement
            create_statement = self._generate_create_table_statement(
                table_name, table_def, target_type
            )
            ddl_statements.append(create_statement)

            # Generate CREATE INDEX statements
            for index in table_def.get("indexes", []):
                index_statement = self._generate_create_index_statement(
                    table_name, index, target_type
                )
                ddl_statements.append(index_statement)

            # Generate ALTER TABLE statements for constraints
            for constraint in table_def.get("constraints", []):
                alter_statement = self._generate_alter_table_statement(
                    table_name, constraint, target_type
                )
                if alter_statement:
                    ddl_statements.append(alter_statement)

        return ddl_statements

    def _generate_create_table_statement(self, table_name: str, table_def: Dict[str, Any],
                                       target_type: str) -> str:
        """Generate CREATE TABLE statement"""
        columns_sql = []
        constraints_sql = []

        # Generate column definitions
        for column in table_def.get("columns", []):
            column_sql = self._generate_column_definition(column, target_type)
            columns_sql.append(column_sql)

        # Add primary key constraint
        if table_def.get("primary_key"):
            pk_columns = ", ".join(table_def["primary_key"])
            constraints_sql.append(f"PRIMARY KEY ({pk_columns})")

        # Combine columns and constraints
        all_columns = columns_sql + constraints_sql
        columns_str = ",\n  ".join(all_columns)

        create_sql = f"CREATE TABLE {table_name} (\n  {columns_str}\n)"

        # Add table options
        table_options = table_def.get("options", {})
        if table_options:
            options_sql = self._generate_table_options(table_options, target_type)
            create_sql += f"\n{options_sql}"

        create_sql += ";"
        return create_sql

    def _generate_column_definition(self, column: Dict[str, Any], target_type: str) -> str:
        """Generate column definition for CREATE TABLE"""
        column_sql = f"{column['name']} {column['type']}"

        # Add length for string types
        if column.get("length") and "VARCHAR" in column["type"].upper():
            column_sql += f"({column['length']})"

        # Add precision/scale for decimal types
        if column.get("precision"):
            if column.get("scale"):
                column_sql += f"({column['precision']}, {column['scale']})"
            else:
                column_sql += f"({column['precision']})"

        # Add NOT NULL
        if not column.get("nullable", True):
            column_sql += " NOT NULL"

        # Add UNIQUE
        if column.get("unique", False):
            column_sql += " UNIQUE"

        # Add AUTO_INCREMENT
        if column.get("auto_increment", False):
            if target_type == "postgresql":
                column_sql += " GENERATED ALWAYS AS IDENTITY"
            elif target_type == "mysql":
                column_sql += " AUTO_INCREMENT"

        # Add DEFAULT value
        if column.get("default") is not None:
            default_value = column["default"]
            if isinstance(default_value, str):
                default_value = f"'{default_value}'"
            column_sql += f" DEFAULT {default_value}"

        # Add CHECK constraint
        if column.get("check"):
            column_sql += f" CHECK ({column['check']})"

        return column_sql

    def _generate_create_index_statement(self, table_name: str, index: Dict[str, Any],
                                       target_type: str) -> str:
        """Generate CREATE INDEX statement"""
        unique_sql = "UNIQUE " if index.get("unique", False) else ""
        columns_str = ", ".join(index["columns"])

        index_sql = f"CREATE {unique_sql}INDEX {index['name']} ON {table_name} ({columns_str})"

        # Add index type if specified
        if index.get("type") and index["type"] != "btree":
            index_sql += f" USING {index['type']}"

        # Add partial condition if specified
        if index.get("partial"):
            index_sql += f" WHERE {index['partial']}"
        elif index.get("where"):
            index_sql += f" WHERE {index['where']}"

        index_sql += ";"
        return index_sql

    def _generate_alter_table_statement(self, table_name: str, constraint: Dict[str, Any],
                                       target_type: str) -> str:
        """Generate ALTER TABLE statement for constraints"""
        constraint_type = constraint.get("type", "").upper()

        if constraint_type == "FOREIGN KEY":
            sql = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint['name']} "
            sql += f"FOREIGN KEY ({constraint['column']}) REFERENCES {constraint['references_table']}({constraint['references_column']})"

            if constraint.get("on_delete"):
                sql += f" ON DELETE {constraint['on_delete']}"
            if constraint.get("on_update"):
                sql += f" ON UPDATE {constraint['on_update']}"

        elif constraint_type == "UNIQUE":
            columns = constraint.get("columns", [constraint.get("column")])
            columns_str = ", ".join(columns)
            sql = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint['name']} UNIQUE ({columns_str})"

        elif constraint_type == "CHECK":
            sql = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint['name']} CHECK ({constraint['condition']})"

        else:
            return None

        return sql + ";"

    def _generate_table_options(self, options: Dict[str, Any], target_type: str) -> str:
        """Generate table options"""
        options_sql = []

        if target_type == "mysql":
            if options.get("engine"):
                options_sql.append(f"ENGINE={options['engine']}")
            if options.get("charset"):
                options_sql.append(f"DEFAULT CHARSET={options['charset']}")
            if options.get("collation"):
                options_sql.append(f"COLLATE={options['collation']}")

        elif target_type == "postgresql":
            if options.get("tablespace"):
                options_sql.append(f"TABLESPACE {options['tablespace']}")

        if options_sql:
            return " " + " ".join(options_sql)
        return ""

    def _extract_index_type(self, index_def: str) -> str:
        """Extract index type from index definition"""
        if "USING" in index_def.upper():
            using_pos = index_def.upper().find("USING")
            rest = index_def[using_pos + 5:].strip()
            return rest.split()[0].lower()
        return "btree"

    def _extract_partial_condition(self, index_def: str) -> Optional[str]:
        """Extract partial condition from index definition"""
        if "WHERE" in index_def.upper():
            where_pos = index_def.upper().find("WHERE")
            return index_def[where_pos + 5:].strip()
        return None

    def _extract_where_clause(self, index_def: str) -> Optional[str]:
        """Extract WHERE clause from index definition"""
        return self._extract_partial_condition(index_def)

    def _generate_transformation_summary(self, source_schema: Dict[str, Any],
                                       target_schema: Dict[str, Any],
                                       source_type: str, target_type: str) -> Dict[str, Any]:
        """Generate summary of transformations performed"""
        summary = {
            "source_type": source_type,
            "target_type": target_type,
            "tables_transformed": len(target_schema),
            "total_columns": sum(len(table["columns"]) for table in target_schema.values()),
            "total_indexes": sum(len(table["indexes"]) for table in target_schema.values()),
            "total_constraints": sum(len(table["constraints"]) for table in target_schema.values()),
            "data_type_conversions": [],
            "constraint_transformations": [],
            "warnings": []
        }

        # Analyze data type conversions
        for table_name, table_def in target_schema.items():
            for column in table_def["columns"]:
                if column.get("original_type") and column["type"] != column["original_type"]:
                    summary["data_type_conversions"].append({
                        "table": table_name,
                        "column": column["name"],
                        "from": column["original_type"],
                        "to": column["type"]
                    })

        # Add warnings for potential issues
        if source_type != target_type:
            summary["warnings"].append(f"Cross-database migration from {source_type} to {target_type}")

        # Check for unsupported features
        if target_type == "mysql":
            summary["warnings"].append("MySQL does not support CHECK constraints before version 8.0.16")

        return summary

# Example usage
async def test_schema_transformer():
    """Test schema transformation"""
    transformer = SchemaTransformer()

    # Sample source schema (PostgreSQL)
    source_schema = {
        "characters": {
            "columns": [
                {
                    "column_name": "id",
                    "data_type": "uuid",
                    "is_nullable": "NO",
                    "is_primary_key": True,
                    "auto_increment": False
                },
                {
                    "column_name": "name",
                    "data_type": "character varying",
                    "character_maximum_length": 100,
                    "is_nullable": "NO"
                },
                {
                    "column_name": "level",
                    "data_type": "integer",
                    "is_nullable": "NO",
                    "column_default": "1"
                },
                {
                    "column_name": "created_at",
                    "data_type": "timestamp with time zone",
                    "is_nullable": "NO",
                    "column_default": "now()"
                }
            ],
            "indexes": [
                {
                    "indexname": "idx_characters_name",
                    "indexdef": "CREATE INDEX idx_characters_name ON characters USING btree (name);"
                }
            ]
        }
    }

    transformation_rules = {
        "column_rules": {
            "id": {
                "type": "string",
                "length": 36
            }
        }
    }

    try:
        result = await transformer.transform_schema(
            source_schema, "postgresql", "mysql", transformation_rules
        )

        print("Schema Transformation Result:")
        print(f"Tables transformed: {result['transformation_summary']['tables_transformed']}")
        print("\nDDL Statements:")
        for statement in result["ddl_statements"]:
            print(f"\n{statement}")

        print(f"\nTransformation Summary: {json.dumps(result['transformation_summary'], indent=2)}")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schema_transformer())