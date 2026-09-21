#!/usr/bin/env python3
"""
Demo script to showcase the quality assurance system.
This script contains various code quality issues for demonstration purposes.
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# Global variable (potential issue)
global_counter = 0

# Magic number (code smell)
DEFAULT_TIMEOUT = 30  # Should be a named constant


def bad_function(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arg10):
    """This function has too many parameters and other issues."""
    global global_counter
    global_counter += 1

    # Complex nested logic (high cyclomatic complexity)
    result = None
    if arg1 > 0:
        if arg2 < 0:
            if arg3 == "test":
                for i in range(100):  # Hardcoded number
                    if i % 2 == 0:
                        for j in range(50):  # Another nested loop
                            if j % 3 == 0:
                                # String concatenation in loop (performance issue)
                                result = result + f"processing {i},{j};"  # Potential NoneType error
    elif arg1 == 0:
        # Bare except clause (security issue)
        try:
            x = 1 / arg2  # Potential division by zero
        except:  # Bad practice - should specify exception type
            pass
    else:
        result = str(arg1)

    return result


class GodClass:
    """This class violates Single Responsibility Principle."""

    def __init__(self):
        self.data = []
        self.config = {}
        self.logger = None
        self.database = None
        self.cache = {}
        self.validators = {}
        self.transformers = {}
        self.serializers = {}
        self.parsers = {}
        self.formatters = {}
        self.calculators = {}
        self.generators = {}
        self.processors = {}
        self.filters = {}
        self.mappers = {}
        self.reducers = {}

    def process_data(self, data):
        """Process data - too many responsibilities."""
        # Validate data
        if not data:
            raise ValueError("Data cannot be empty")

        # Transform data
        transformed = []
        for item in data:
            if isinstance(item, dict):
                # Complex processing logic
                if 'value' in item:
                    value = item['value']
                    if value > 100:
                        transformed.append(self._process_large_value(value))
                    elif value < 0:
                        transformed.append(self._process_negative_value(value))
                    else:
                        transformed.append(self._process_normal_value(value))
                else:
                    transformed.append(self._process_missing_value(item))
            elif isinstance(item, list):
                transformed.append(self._process_list(item))
            else:
                transformed.append(self._process_scalar(item))

        return transformed

    def _process_large_value(self, value):
        """Helper method with inefficient logic."""
        # Expensive operation that could be cached
        result = []
        for i in range(value):
            if i % 2 == 0:
                result.append(i * 2)
            else:
                result.append(i * 3)
        return result

    def _process_negative_value(self, value):
        return abs(value)

    def _process_normal_value(self, value):
        return value * 1.1

    def _process_missing_value(self, item):
        return item

    def _process_list(self, item):
        return [x * 2 for x in item]

    def _process_scalar(self, item):
        return item

    def validate_data(self, data):
        """Another responsibility - validation."""
        if not isinstance(data, (list, dict)):
            return False

        if isinstance(data, list):
            return len(data) > 0

        return True

    def save_to_database(self, data):
        """Another responsibility - database operations."""
        # Database operation without proper error handling
        connection = self._get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO table VALUES (%s)", (json.dumps(data),))
        connection.commit()
        connection.close()

    def _get_connection(self):
        """Database connection without connection pooling."""
        # This should use connection pooling
        import sqlite3
        return sqlite3.connect(':memory:')

    def log_operation(self, operation, data):
        """Another responsibility - logging."""
        print(f"Operation: {operation}, Data: {data}")

    def cache_result(self, key, value):
        """Another responsibility - caching."""
        self.cache[key] = value

    def format_output(self, data):
        """Another responsibility - formatting."""
        return json.dumps(data, indent=2)


# Memory-intensive function
def memory_intensive_function():
    """This function creates large objects unnecessarily."""
    # Creates large list in memory
    large_list = list(range(1000000))  # Could use generator instead

    # Creates multiple copies of data
    copies = []
    for i in range(10):
        copies.append(large_list.copy())  # Memory intensive

    return len(copies)


# Security vulnerability
def unsafe_function(user_input):
    """This function has security vulnerabilities."""
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # Unsafe

    # Command injection vulnerability
    os.system(f"echo {user_input}")  # Unsafe

    # eval vulnerability
    result = eval(user_input)  # Extremely dangerous

    return result, query


# Performance anti-pattern
def slow_search(items, target):
    """Inefficient search - should use set or dictionary."""
    result = []
    for item in items:  # O(n) search
        if item == target:
            result.append(item)
    return result


# Missing documentation
def undocumented_function(x, y):
    # No docstring
    return x + y


# TODO: Refactor this function
def needs_refactoring():
    """This function has TODO comments and other issues."""
    # TODO: Break this into smaller functions
    # FIXME: Handle edge cases properly
    # HACK: This is a temporary solution

    data = []
    for i in range(100):
        data.append(i * 2)

    # More complex logic that should be refactored
    result = []
    for item in data:
        if item % 2 == 0:
            result.append(item * 3)
        else:
            result.append(item * 5)

    return result


# Exception handling issues
def poor_error_handling():
    """Poor exception handling example."""
    try:
        # Risky operation
        with open('nonexistent_file.txt', 'r') as f:
            content = f.read()
    except:  # Bare except - bad practice
        print("Something went wrong")
        return None

    try:
        x = 1 / 0
    except Exception as e:  # Too broad exception
        print(f"Error: {e}")

    return content


# Inheritance issues
class BaseClass:
    """Base class with no docstring."""

    def method1(self):
        pass

    def method2(self):
        pass


class SubClass(BaseClass):
    """Subclass that doesn't use base class methods."""

    def completely_different_functionality(self):
        """Doesn't relate to base class - violates LSP."""
        return "This has nothing to do with BaseClass"


# Main execution with no proper structure
if __name__ == "__main__":
    # Direct execution without proper structure
    data = [1, 2, 3, 4, 5]
    result = bad_function(10, -5, "test", "extra", "params", "here", "to", "trigger", "warnings", "about", "too", "many", "params")

    god_class = GodClass()
    processed = god_class.process_data(data)

    memory_result = memory_intensive_function()
    search_result = slow_search(data, 3)

    print("Demo execution completed - this code has many quality issues!")