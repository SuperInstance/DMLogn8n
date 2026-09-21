#!/usr/bin/env python3
"""
DMLogn8n Database Integration Tests
Comprehensive database integration and data flow testing
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import random
import string

import psycopg2
import psycopg2.extras
import redis
import pymongo
from pymongo import MongoClient
import aiohttp

# Import test framework
from integration_test_suite import TestResult, TestStatus

class DatabaseIntegrationTests:
    """
    Comprehensive database integration testing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('database_integration')
        self.postgres_url = config['database_url']
        self.redis_url = config['redis_url']
        self.mongo_url = config.get('mongo_url', 'mongodb://localhost:27017')

        # Test data tracking
        self.test_records = {
            'users': [],
            'characters': [],
            'sessions': [],
            'messages': []
        }

    async def test_database_connection(self) -> TestResult:
        """
        Test database connections and basic connectivity
        """
        result = TestResult(
            name="database_connection",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            connection_tests = {
                'postgresql': await self.test_postgresql_connection(),
                'redis': await self.test_redis_connection(),
                'mongodb': await self.test_mongodb_connection()
            }

            all_connected = all(test['connected'] for test in connection_tests.values())

            result.status = TestStatus.PASSED if all_connected else TestStatus.FAILED
            result.message = "All database connections successful" if all_connected else "Some database connections failed"
            result.details = connection_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Database connection test failed: {str(e)}"
            self.logger.error(f"Database connection test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_postgresql_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(self.postgres_url)

            # Test basic query
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]

                # Test table existence
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('users', 'characters', 'game_sessions', 'messages');
                """)
                tables = [row[0] for row in cursor.fetchall()]

            conn.close()

            return {
                'connected': True,
                'version': version,
                'tables_found': tables,
                'message': 'PostgreSQL connection successful'
            }

        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    async def test_redis_connection(self) -> Dict[str, Any]:
        """Test Redis connection"""
        try:
            r = redis.from_url(self.redis_url)

            # Test basic operations
            test_key = f"test_connection_{uuid.uuid4().hex}"
            r.set(test_key, "test_value", ex=60)
            retrieved_value = r.get(test_key)
            r.delete(test_key)

            # Test info
            info = r.info()

            return {
                'connected': True,
                'redis_version': info.get('redis_version'),
                'test_operation_successful': retrieved_value == b'test_value',
                'memory_usage': info.get('used_memory_human'),
                'message': 'Redis connection successful'
            }

        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    async def test_mongodb_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection"""
        try:
            client = MongoClient(self.mongo_url, serverSelectionTimeoutMS=5000)

            # Test connection
            client.admin.command('ping')

            # List databases
            databases = client.list_database_names()

            # Test collections if dmlog database exists
            collections = []
            if 'dmlog' in databases:
                db = client.dmlog
                collections = db.list_collection_names()

            client.close()

            return {
                'connected': True,
                'databases_found': databases,
                'collections_found': collections,
                'message': 'MongoDB connection successful'
            }

        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    async def test_data_integrity(self) -> TestResult:
        """
        Test data integrity across different database operations
        """
        result = TestResult(
            name="data_integrity",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            integrity_tests = {
                'user_data_integrity': await self.test_user_data_integrity(),
                'character_data_integrity': await self.test_character_data_integrity(),
                'session_data_integrity': await self.test_session_data_integrity(),
                'transaction_consistency': await self.test_transaction_consistency(),
                'data_validation': await self.test_data_validation(),
                'cascade_operations': await self.test_cascade_operations()
            }

            all_passed = all(test.get('success', False) for test in integrity_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Data integrity test completed" if all_passed else "Some data integrity tests failed"
            result.details = integrity_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Data integrity test failed: {str(e)}"
            self.logger.error(f"Data integrity test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    def generate_test_user_data(self) -> Dict[str, Any]:
        """Generate test user data"""
        user_id = uuid.uuid4()
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.dmlog.local"

        return {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': 'hashed_password_' + uuid.uuid4().hex,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'is_active': True,
            'preferences': json.dumps({
                'theme': 'dark',
                'notifications': True
            })
        }

    async def test_user_data_integrity(self) -> Dict[str, Any]:
        """Test user data integrity"""
        try:
            test_user = self.generate_test_user_data()

            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Insert user
                    insert_query = """
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, username, email, created_at;
                    """
                    cursor.execute(insert_query, (
                        test_user['id'], test_user['username'], test_user['email'],
                        test_user['password_hash'], test_user['created_at'],
                        test_user['updated_at'], test_user['is_active'], test_user['preferences']
                    ))
                    inserted_data = cursor.fetchone()

                    # Verify insertion
                    cursor.execute("SELECT * FROM users WHERE id = %s", (test_user['id'],))
                    retrieved_data = cursor.fetchone()

                    # Test data consistency
                    integrity_check = (
                        retrieved_data[1] == test_user['username'] and  # username
                        retrieved_data[2] == test_user['email'] and     # email
                        retrieved_data[6] == test_user['is_active']    # is_active
                    )

                    self.test_records['users'].append(test_user['id'])

                    return {
                        'success': integrity_check,
                        'inserted_data': {
                            'id': str(inserted_data[0]),
                            'username': inserted_data[1],
                            'email': inserted_data[2]
                        },
                        'retrieved_data': {
                            'id': str(retrieved_data[0]),
                            'username': retrieved_data[1],
                            'email': retrieved_data[2]
                        },
                        'integrity_check': integrity_check,
                        'message': 'User data integrity test passed' if integrity_check else 'User data integrity test failed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_test_character_data(self, user_id: str) -> Dict[str, Any]:
        """Generate test character data"""
        character_id = uuid.uuid4()

        return {
            'id': character_id,
            'user_id': user_id,
            'name': f"TestChar_{uuid.uuid4().hex[:6]}",
            'class': 'warrior',
            'level': 1,
            'experience': 0,
            'attributes': json.dumps({
                'strength': 16,
                'dexterity': 14,
                'constitution': 15,
                'intelligence': 12,
                'wisdom': 13,
                'charisma': 11
            }),
            'background': 'Test character for integration testing',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    async def test_character_data_integrity(self) -> Dict[str, Any]:
        """Test character data integrity"""
        try:
            if not self.test_records['users']:
                # Create a user first
                user_test = await self.test_user_data_integrity()
                if not user_test['success']:
                    return {'success': False, 'error': 'Failed to create test user'}

            user_id = self.test_records['users'][0]
            test_character = self.generate_test_character_data(user_id)

            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Insert character
                    insert_query = """
                        INSERT INTO characters (id, user_id, name, class, level, experience, attributes, background, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, name, class, level;
                    """
                    cursor.execute(insert_query, (
                        test_character['id'], test_character['user_id'], test_character['name'],
                        test_character['class'], test_character['level'], test_character['experience'],
                        test_character['attributes'], test_character['background'],
                        test_character['created_at'], test_character['updated_at']
                    ))
                    inserted_data = cursor.fetchone()

                    # Verify insertion and JSON data
                    cursor.execute("SELECT * FROM characters WHERE id = %s", (test_character['id'],))
                    retrieved_data = cursor.fetchone()

                    # Parse JSON attributes for comparison
                    retrieved_attributes = json.loads(retrieved_data[6]) if retrieved_data[6] else {}
                    original_attributes = json.loads(test_character['attributes'])

                    integrity_check = (
                        retrieved_data[1] == test_character['user_id'] and    # user_id
                        retrieved_data[2] == test_character['name'] and       # name
                        retrieved_data[3] == test_character['class'] and      # class
                        retrieved_data[4] == test_character['level'] and      # level
                        retrieved_attributes == original_attributes           # attributes JSON
                    )

                    self.test_records['characters'].append(test_character['id'])

                    return {
                        'success': integrity_check,
                        'inserted_data': {
                            'id': str(inserted_data[0]),
                            'name': inserted_data[1],
                            'class': inserted_data[2],
                            'level': inserted_data[3]
                        },
                        'retrieved_attributes': retrieved_attributes,
                        'original_attributes': original_attributes,
                        'integrity_check': integrity_check,
                        'message': 'Character data integrity test passed' if integrity_check else 'Character data integrity test failed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_test_session_data(self, character_id: str) -> Dict[str, Any]:
        """Generate test session data"""
        session_id = uuid.uuid4()

        return {
            'id': session_id,
            'character_id': character_id,
            'scenario': 'tavern_adventure',
            'status': 'active',
            'started_at': datetime.now(),
            'last_activity': datetime.now(),
            'session_data': json.dumps({
                'current_scene': 'tavern',
                'npcs_present': ['tavern_keeper', 'travelers'],
                'plot_points': ['mysterious_stranger_arrived']
            })
        }

    async def test_session_data_integrity(self) -> Dict[str, Any]:
        """Test game session data integrity"""
        try:
            if not self.test_records['characters']:
                # Create a character first
                character_test = await self.test_character_data_integrity()
                if not character_test['success']:
                    return {'success': False, 'error': 'Failed to create test character'}

            character_id = self.test_records['characters'][0]
            test_session = self.generate_test_session_data(character_id)

            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Insert session
                    insert_query = """
                        INSERT INTO game_sessions (id, character_id, scenario, status, started_at, last_activity, session_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, scenario, status;
                    """
                    cursor.execute(insert_query, (
                        test_session['id'], test_session['character_id'], test_session['scenario'],
                        test_session['status'], test_session['started_at'],
                        test_session['last_activity'], test_session['session_data']
                    ))
                    inserted_data = cursor.fetchone()

                    # Verify insertion and JSON data
                    cursor.execute("SELECT * FROM game_sessions WHERE id = %s", (test_session['id'],))
                    retrieved_data = cursor.fetchone()

                    # Parse JSON session data for comparison
                    retrieved_session_data = json.loads(retrieved_data[7]) if retrieved_data[7] else {}
                    original_session_data = json.loads(test_session['session_data'])

                    integrity_check = (
                        retrieved_data[1] == test_session['character_id'] and  # character_id
                        retrieved_data[2] == test_session['scenario'] and       # scenario
                        retrieved_data[3] == test_session['status'] and        # status
                        retrieved_session_data == original_session_data        # session_data JSON
                    )

                    self.test_records['sessions'].append(test_session['id'])

                    return {
                        'success': integrity_check,
                        'inserted_data': {
                            'id': str(inserted_data[0]),
                            'scenario': inserted_data[1],
                            'status': inserted_data[2]
                        },
                        'retrieved_session_data': retrieved_session_data,
                        'original_session_data': original_session_data,
                        'integrity_check': integrity_check,
                        'message': 'Session data integrity test passed' if integrity_check else 'Session data integrity test failed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_transaction_consistency(self) -> Dict[str, Any]:
        """Test database transaction consistency"""
        try:
            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Begin transaction
                    cursor.execute("BEGIN;")

                    # Create user
                    test_user = self.generate_test_user_data()
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        test_user['id'], test_user['username'], test_user['email'],
                        test_user['password_hash'], test_user['created_at'],
                        test_user['updated_at'], test_user['is_active'], test_user['preferences']
                    ))

                    # Create character for that user
                    test_character = self.generate_test_character_data(test_user['id'])
                    cursor.execute("""
                        INSERT INTO characters (id, user_id, name, class, level, experience, attributes, background, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        test_character['id'], test_character['user_id'], test_character['name'],
                        test_character['class'], test_character['level'], test_character['experience'],
                        test_character['attributes'], test_character['background'],
                        test_character['created_at'], test_character['updated_at']
                    ))

                    # Rollback transaction to test consistency
                    cursor.execute("ROLLBACK;")

                    # Verify that neither user nor character was created
                    cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", (test_user['id'],))
                    user_exists = cursor.fetchone()[0] > 0

                    cursor.execute("SELECT COUNT(*) FROM characters WHERE id = %s", (test_character['id'],))
                    character_exists = cursor.fetchone()[0] > 0

                    transaction_consistent = not user_exists and not character_exists

                    return {
                        'success': transaction_consistent,
                        'user_rollback_successful': not user_exists,
                        'character_rollback_successful': not character_exists,
                        'message': 'Transaction consistency test passed' if transaction_consistent else 'Transaction consistency test failed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_data_validation(self) -> Dict[str, Any]:
        """Test data validation constraints"""
        try:
            validation_tests = []

            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Test 1: Duplicate email constraint
                    test_user1 = self.generate_test_user_data()
                    test_user2 = self.generate_test_user_data()
                    test_user2['email'] = test_user1['email']  # Same email

                    # Insert first user
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        test_user1['id'], test_user1['username'], test_user1['email'],
                        test_user1['password_hash'], test_user1['created_at'],
                        test_user1['updated_at'], test_user1['is_active'], test_user1['preferences']
                    ))

                    # Try to insert second user with same email (should fail)
                    try:
                        cursor.execute("""
                            INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            test_user2['id'], test_user2['username'], test_user2['email'],
                            test_user2['password_hash'], test_user2['created_at'],
                            test_user2['updated_at'], test_user2['is_active'], test_user2['preferences']
                        ))
                        duplicate_email_prevented = False
                    except psycopg2.IntegrityError:
                        duplicate_email_prevented = True
                        conn.rollback()

                    validation_tests.append({
                        'test': 'duplicate_email_constraint',
                        'success': duplicate_email_prevented,
                        'message': 'Duplicate email constraint working' if duplicate_email_prevented else 'Duplicate email constraint failed'
                    })

                    # Test 2: Not null constraints
                    try:
                        cursor.execute("INSERT INTO users (id, username) VALUES (%s, %s)",
                                     (uuid.uuid4(), 'test_user'))
                        not_null_constraint_working = False
                        conn.rollback()
                    except psycopg2.IntegrityError:
                        not_null_constraint_working = True
                        conn.rollback()

                    validation_tests.append({
                        'test': 'not_null_constraint',
                        'success': not_null_constraint_working,
                        'message': 'NOT NULL constraints working' if not_null_constraint_working else 'NOT NULL constraints failed'
                    })

                    # Test 3: Foreign key constraint
                    if self.test_records['users']:
                        # Try to create character with non-existent user
                        fake_user_id = uuid.uuid4()
                        test_character = self.generate_test_character_data(fake_user_id)

                        try:
                            cursor.execute("""
                                INSERT INTO characters (id, user_id, name, class, level, experience, attributes, background, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                test_character['id'], test_character['user_id'], test_character['name'],
                                test_character['class'], test_character['level'], test_character['experience'],
                                test_character['attributes'], test_character['background'],
                                test_character['created_at'], test_character['updated_at']
                            ))
                            foreign_key_constraint_working = False
                            conn.rollback()
                        except psycopg2.IntegrityError:
                            foreign_key_constraint_working = True
                            conn.rollback()

                        validation_tests.append({
                            'test': 'foreign_key_constraint',
                            'success': foreign_key_constraint_working,
                            'message': 'Foreign key constraints working' if foreign_key_constraint_working else 'Foreign key constraints failed'
                        })

                    # Test 4: Check constraints
                    try:
                        cursor.execute("INSERT INTO characters (id, user_id, name, class, level, experience, attributes, background, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                     (uuid.uuid4(), self.test_records['users'][0] if self.test_records['users'] else uuid.uuid4(),
                                      'test_char', 'invalid_class', -1, -100, '{}', 'test', datetime.now(), datetime.now()))
                        check_constraint_working = False
                        conn.rollback()
                    except psycopg2.IntegrityError:
                        check_constraint_working = True
                        conn.rollback()

                    validation_tests.append({
                        'test': 'check_constraint',
                        'success': check_constraint_working,
                        'message': 'CHECK constraints working' if check_constraint_working else 'CHECK constraints failed'
                    })

                all_passed = all(test['success'] for test in validation_tests)

                return {
                    'success': all_passed,
                    'validation_tests': validation_tests,
                    'passed_tests': sum(1 for test in validation_tests if test['success']),
                    'total_tests': len(validation_tests),
                    'message': f"Data validation test passed ({len(validation_tests)} tests)" if all_passed else "Some data validation tests failed"
                }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_cascade_operations(self) -> Dict[str, Any]:
        """Test cascade delete operations"""
        try:
            if not self.test_records['users']:
                # Create test data first
                user_test = await self.test_user_data_integrity()
                character_test = await self.test_character_data_integrity()
                session_test = await self.test_session_data_integrity()

                if not all(test['success'] for test in [user_test, character_test, session_test]):
                    return {'success': False, 'error': 'Failed to create test data'}

            user_id = self.test_records['users'][0]
            character_id = self.test_records['characters'][0]
            session_id = self.test_records['sessions'][0]

            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Check initial state
                    cursor.execute("SELECT COUNT(*) FROM characters WHERE user_id = %s", (user_id,))
                    initial_character_count = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM game_sessions WHERE character_id = %s", (character_id,))
                    initial_session_count = cursor.fetchone()[0]

                    # Delete user (should cascade to characters and sessions)
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

                    # Check cascade effects
                    cursor.execute("SELECT COUNT(*) FROM users WHERE id = %s", (user_id,))
                    remaining_users = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM characters WHERE user_id = %s", (user_id,))
                    remaining_characters = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM game_sessions WHERE character_id = %s", (character_id,))
                    remaining_sessions = cursor.fetchone()[0]

                    cascade_working = (
                        remaining_users == 0 and
                        remaining_characters == 0 and
                        remaining_sessions == 0
                    )

                    # Clean up test records
                    self.test_records['users'].remove(user_id)
                    self.test_records['characters'].remove(character_id)
                    self.test_records['sessions'].remove(session_id)

                    return {
                        'success': cascade_working,
                        'initial_character_count': initial_character_count,
                        'initial_session_count': initial_session_count,
                        'remaining_users': remaining_users,
                        'remaining_characters': remaining_characters,
                        'remaining_sessions': remaining_sessions,
                        'message': 'Cascade operations working correctly' if cascade_working else 'Cascade operations failed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_database_performance(self) -> TestResult:
        """
        Test database performance under various conditions
        """
        result = TestResult(
            name="database_performance",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            performance_tests = {
                'query_performance': await self.test_query_performance(),
                'index_effectiveness': await self.test_index_effectiveness(),
                'concurrent_operations': await self.test_concurrent_database_operations(),
                'large_dataset_performance': await self.test_large_dataset_performance()
            }

            all_passed = all(test.get('success', False) for test in performance_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Database performance test completed" if all_passed else "Some database performance tests failed"
            result.details = performance_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Database performance test failed: {str(e)}"
            self.logger.error(f"Database performance test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_query_performance(self) -> Dict[str, Any]:
        """Test query performance"""
        try:
            queries = [
                {
                    'name': 'user_lookup_by_email',
                    'query': "SELECT * FROM users WHERE email = %s",
                    'params': ['test@example.com'],
                    'max_time': 0.1
                },
                {
                    'name': 'character_lookup_by_user',
                    'query': "SELECT * FROM characters WHERE user_id = %s",
                    'params': [uuid.uuid4()],
                    'max_time': 0.1
                },
                {
                    'name': 'session_lookup_with_join',
                    'query': """
                        SELECT gs.*, c.name as character_name, u.username
                        FROM game_sessions gs
                        JOIN characters c ON gs.character_id = c.id
                        JOIN users u ON c.user_id = u.id
                        WHERE gs.status = 'active'
                        LIMIT 10
                    """,
                    'params': [],
                    'max_time': 0.2
                }
            ]

            query_results = []
            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    for query_test in queries:
                        start_time = time.time()
                        cursor.execute(query_test['query'], query_test['params'])
                        results = cursor.fetchall()
                        query_time = time.time() - start_time

                        within_threshold = query_time <= query_test['max_time']

                        query_results.append({
                            'query_name': query_test['name'],
                            'execution_time': query_time,
                            'max_time': query_test['max_time'],
                            'within_threshold': within_threshold,
                            'results_returned': len(results),
                            'success': within_threshold
                        })

                avg_execution_time = sum(r['execution_time'] for r in query_results) / len(query_results)
                all_within_threshold = all(r['within_threshold'] for r in query_results)

                return {
                    'success': all_within_threshold,
                    'avg_execution_time': avg_execution_time,
                    'query_results': query_results,
                    'message': f"Query performance test passed (avg: {avg_execution_time:.3f}s)" if all_within_threshold else "Some queries exceeded performance thresholds"
                }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_index_effectiveness(self) -> Dict[str, Any]:
        """Test index effectiveness"""
        try:
            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Get index information
                    cursor.execute("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                        FROM pg_stat_user_indexes
                        WHERE schemaname = 'public'
                        ORDER BY idx_scan DESC;
                    """)
                    index_stats = cursor.fetchall()

                    # Check if commonly queried columns have indexes
                    cursor.execute("""
                        SELECT a.attname, i.relname as index_name
                        FROM pg_attribute a
                        JOIN pg_class t ON a.attrelid = t.oid
                        JOIN pg_index ix ON a.attrelid = ix.indrelid AND a.attnum = ANY(ix.indkey)
                        JOIN pg_class i ON ix.indexrelid = i.oid
                        WHERE t.relname IN ('users', 'characters', 'game_sessions')
                        AND a.attnum > 0
                        AND a.attname IN ('email', 'user_id', 'character_id', 'status')
                        GROUP BY a.attname, i.relname
                        ORDER BY a.attname;
                    """)
                    indexed_columns = cursor.fetchall()

                    # Test query execution plans
                    test_queries = [
                        ("EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com'", []),
                        ("EXPLAIN ANALYZE SELECT * FROM characters WHERE user_id = %s", [uuid.uuid4()]),
                        ("EXPLAIN ANALYZE SELECT * FROM game_sessions WHERE status = 'active'", [])
                    ]

                    execution_plans = []
                    for query, params in test_queries:
                        cursor.execute(query, params)
                        plan = cursor.fetchone()[0]
                        uses_index = 'Index Scan' in plan or 'Index Only Scan' in plan
                        execution_plans.append({
                            'query': query.split('SELECT')[1].strip(),
                            'uses_index': uses_index,
                            'plan_preview': plan[:100] + '...' if len(plan) > 100 else plan
                        })

                    indexes_working = len(indexed_columns) >= 3  # At least email, user_id, character_id indexed
                    queries_use_indexes = any(plan['uses_index'] for plan in execution_plans)

                    return {
                        'success': indexes_working and queries_use_indexes,
                        'index_stats_count': len(index_stats),
                        'indexed_columns': [(col[0], col[1]) for col in indexed_columns],
                        'execution_plans': execution_plans,
                        'indexes_found': len(indexed_columns),
                        'queries_using_indexes': sum(1 for plan in execution_plans if plan['uses_index']),
                        'message': 'Index effectiveness test passed' if (indexes_working and queries_use_indexes) else 'Index optimization needed'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_concurrent_database_operations(self) -> Dict[str, Any]:
        """Test concurrent database operations"""
        try:
            import concurrent.futures

            def concurrent_insert():
                try:
                    conn = psycopg2.connect(self.postgres_url)
                    test_user = self.generate_test_user_data()

                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            test_user['id'], test_user['username'], test_user['email'],
                            test_user['password_hash'], test_user['created_at'],
                            test_user['updated_at'], test_user['is_active'], test_user['preferences']
                        ))
                        conn.commit()

                        # Clean up immediately
                        cursor.execute("DELETE FROM users WHERE id = %s", (test_user['id'],))
                        conn.commit()

                    conn.close()
                    return True
                except Exception:
                    return False

            # Run 10 concurrent insert operations
            concurrent_operations = 10
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_insert) for _ in range(concurrent_operations)]
                results = [future.result() for future in futures]

            success_rate = sum(results) / len(results)

            return {
                'success': success_rate >= 0.8,
                'concurrent_operations': concurrent_operations,
                'successful_operations': sum(results),
                'success_rate': success_rate,
                'message': f"Concurrent operations test passed ({success_rate:.1%} success rate)" if success_rate >= 0.8 else "Concurrent operations need optimization"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_large_dataset_performance(self) -> Dict[str, Any]:
        """Test performance with larger datasets"""
        try:
            # This test will create and query a larger dataset
            test_records = 1000
            conn = psycopg2.connect(self.postgres_url)

            try:
                with conn.cursor() as cursor:
                    # Create test table if not exists
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS performance_test (
                            id UUID PRIMARY KEY,
                            data TEXT,
                            created_at TIMESTAMP,
                            index_field INTEGER
                        );

                        CREATE INDEX IF NOT EXISTS idx_performance_test_index_field ON performance_test(index_field);
                    """)

                    # Insert test data
                    start_time = time.time()
                    for i in range(test_records):
                        cursor.execute("""
                            INSERT INTO performance_test (id, data, created_at, index_field)
                            VALUES (%s, %s, %s, %s)
                        """, (uuid.uuid4(), f"test_data_{i}", datetime.now(), i % 100))
                    conn.commit()
                    insert_time = time.time() - start_time

                    # Test indexed query
                    start_time = time.time()
                    cursor.execute("SELECT COUNT(*) FROM performance_test WHERE index_field = %s", (50,))
                    count_result = cursor.fetchone()[0]
                    indexed_query_time = time.time() - start_time

                    # Test full table scan
                    start_time = time.time()
                    cursor.execute("SELECT COUNT(*) FROM performance_test WHERE data LIKE '%test%'")
                    full_scan_result = cursor.fetchone()[0]
                    full_scan_time = time.time() - start_time

                    # Cleanup
                    cursor.execute("DROP TABLE IF EXISTS performance_test;")
                    conn.commit()

                    performance_acceptable = (
                        insert_time < 5.0 and          # Insert under 5 seconds
                        indexed_query_time < 0.1 and   # Indexed query under 100ms
                        full_scan_time < 1.0           # Full scan under 1 second
                    )

                    return {
                        'success': performance_acceptable,
                        'test_records': test_records,
                        'insert_time': insert_time,
                        'indexed_query_time': indexed_query_time,
                        'full_scan_time': full_scan_time,
                        'indexed_result_count': count_result,
                        'full_scan_result_count': full_scan_result,
                        'performance_acceptable': performance_acceptable,
                        'message': 'Large dataset performance test passed' if performance_acceptable else 'Large dataset performance needs optimization'
                    }

            finally:
                conn.close()

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_data_flow_integration(self) -> TestResult:
        """
        Test data flow between different database systems
        """
        result = TestResult(
            name="data_flow_integration",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            flow_tests = {
                'postgresql_to_redis': await self.test_postgresql_to_redis_flow(),
                'redis_to_postgresql': await self.test_redis_to_postgresql_flow(),
                'mongodb_integration': await self.test_mongodb_integration(),
                'cache_consistency': await self.test_cache_consistency()
            }

            all_passed = all(test.get('success', False) for test in flow_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "Data flow integration test completed" if all_passed else "Some data flow tests failed"
            result.details = flow_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"Data flow integration test failed: {str(e)}"
            self.logger.error(f"Data flow integration test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_postgresql_to_redis_flow(self) -> Dict[str, Any]:
        """Test data flow from PostgreSQL to Redis"""
        try:
            # Create test user in PostgreSQL
            test_user = self.generate_test_user_data()

            conn = psycopg2.connect(self.postgres_url)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, created_at, updated_at, is_active, preferences)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, username, email;
                    """, (
                        test_user['id'], test_user['username'], test_user['email'],
                        test_user['password_hash'], test_user['created_at'],
                        test_user['updated_at'], test_user['is_active'], test_user['preferences']
                    ))
                    user_data = cursor.fetchone()
                    conn.commit()
            finally:
                conn.close()

            # Simulate caching user data in Redis
            r = redis.from_url(self.redis_url)
            cache_key = f"user:{user_data[0]}"
            cached_data = {
                'id': str(user_data[0]),
                'username': user_data[1],
                'email': user_data[2],
                'cached_at': datetime.now().isoformat()
            }
            r.setex(cache_key, 3600, json.dumps(cached_data))  # Cache for 1 hour

            # Verify cache
            retrieved_cache = r.get(cache_key)
            cache_valid = retrieved_cache is not None

            # Cleanup
            r.delete(cache_key)
            conn = psycopg2.connect(self.postgres_url)
            conn.cursor().execute("DELETE FROM users WHERE id = %s", (user_data[0],))
            conn.commit()
            conn.close()

            return {
                'success': cache_valid,
                'cache_key': cache_key,
                'cached_data': cached_data,
                'cache_valid': cache_valid,
                'message': 'PostgreSQL to Redis flow working' if cache_valid else 'PostgreSQL to Redis flow failed'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_redis_to_postgresql_flow(self) -> Dict[str, Any]:
        """Test data flow from Redis to PostgreSQL"""
        try:
            # Store temporary data in Redis
            r = redis.from_url(self.redis_url)
            temp_key = f"temp_session:{uuid.uuid4()}"
            session_data = {
                'user_id': str(uuid.uuid4()),
                'scenario': 'test_scenario',
                'started_at': datetime.now().isoformat(),
                'temporary_data': 'This is temporary session data'
            }
            r.setex(temp_key, 300, json.dumps(session_data))  # Expire in 5 minutes

            # Retrieve from Redis and prepare for PostgreSQL
            retrieved_data = r.get(temp_key)
            if retrieved_data:
                session_info = json.loads(retrieved_data)

                # Simulate persisting to PostgreSQL (this would normally be in a background job)
                conn = psycopg2.connect(self.postgres_url)
                try:
                    with conn.cursor() as cursor:
                        # Create temporary sessions table if not exists
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS temp_sessions (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                user_id UUID,
                                scenario TEXT,
                                started_at TIMESTAMP,
                                session_data JSONB,
                                created_at TIMESTAMP DEFAULT NOW()
                            );
                        """)

                        # Insert session data
                        cursor.execute("""
                            INSERT INTO temp_sessions (user_id, scenario, started_at, session_data)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id;
                        """, (
                            session_info['user_id'],
                            session_info['scenario'],
                            datetime.fromisoformat(session_info['started_at'].replace('Z', '+00:00')),
                            json.dumps(session_info)
                        ))
                        session_id = cursor.fetchone()[0]
                        conn.commit()

                        # Verify persistence
                        cursor.execute("SELECT * FROM temp_sessions WHERE id = %s", (session_id,))
                        persisted_data = cursor.fetchone()

                        # Cleanup
                        cursor.execute("DELETE FROM temp_sessions WHERE id = %s", (session_id,))
                        conn.commit()

                        return {
                            'success': persisted_data is not None,
                            'session_id': str(session_id),
                            'original_data': session_info,
                            'persisted_data': {
                                'user_id': str(persisted_data[1]) if persisted_data else None,
                                'scenario': persisted_data[2] if persisted_data else None
                            },
                            'message': 'Redis to PostgreSQL flow working' if persisted_data else 'Redis to PostgreSQL flow failed'
                        }

                finally:
                    conn.close()
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrieve data from Redis'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_mongodb_integration(self) -> Dict[str, Any]:
        """Test MongoDB integration"""
        try:
            client = MongoClient(self.mongo_url, serverSelectionTimeoutMS=5000)

            # Test basic operations
            db = client.dmlog_test
            collection = db.test_integration

            # Insert test document
            test_doc = {
                'user_id': str(uuid.uuid4()),
                'event_type': 'test_event',
                'timestamp': datetime.now(),
                'data': {
                    'test_field': 'test_value',
                    'nested': {
                        'field1': 'value1',
                        'field2': 'value2'
                    }
                }
            }

            insert_result = collection.insert_one(test_doc)
            doc_id = insert_result.inserted_id

            # Retrieve document
            retrieved_doc = collection.find_one({'_id': doc_id})

            # Update document
            collection.update_one(
                {'_id': doc_id},
                {'$set': {'updated': True, 'last_update': datetime.now()}}
            )

            # Verify update
            updated_doc = collection.find_one({'_id': doc_id})

            # Cleanup
            collection.delete_one({'_id': doc_id})
            client.close()

            integration_working = (
                retrieved_doc is not None and
                updated_doc is not None and
                updated_doc.get('updated') == True
            )

            return {
                'success': integration_working,
                'document_id': str(doc_id),
                'original_data': test_doc,
                'retrieved': retrieved_doc is not None,
                'updated': updated_doc.get('updated') if updated_doc else False,
                'message': 'MongoDB integration working' if integration_working else 'MongoDB integration failed'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_cache_consistency(self) -> Dict[str, Any]:
        """Test cache consistency across multiple cache operations"""
        try:
            r = redis.from_url(self.redis_url)

            # Test data
            test_key = f"consistency_test:{uuid.uuid4()}"
            original_data = {
                'user_id': str(uuid.uuid4()),
                'session_data': 'test_session_data',
                'version': 1,
                'timestamp': datetime.now().isoformat()
            }

            # Store original data
            r.set(test_key, json.dumps(original_data))

            # Simulate multiple cache operations
            operations = []

            # Read operation 1
            data1 = json.loads(r.get(test_key) or '{}')
            operations.append(('read1', data1 == original_data))

            # Update operation
            updated_data = original_data.copy()
            updated_data['version'] = 2
            updated_data['updated_at'] = datetime.now().isoformat()
            r.set(test_key, json.dumps(updated_data))
            operations.append(('update', True))

            # Read operation 2
            data2 = json.loads(r.get(test_key) or '{}')
            operations.append(('read2', data2['version'] == 2))

            # Expire operation
            r.expire(test_key, 1)  # Expire in 1 second
            await asyncio.sleep(1.1)  # Wait for expiration

            # Read after expiration
            data3 = r.get(test_key)
            operations.append(('read_expired', data3 is None))

            # Check consistency
            all_consistent = all(op[1] for op in operations)

            return {
                'success': all_consistent,
                'operations': operations,
                'all_consistent': all_consistent,
                'message': 'Cache consistency maintained' if all_consistent else 'Cache consistency issues detected'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup_test_data(self):
        """Clean up test data from all databases"""
        try:
            # Clean up PostgreSQL
            conn = psycopg2.connect(self.postgres_url)
            try:
                with conn.cursor() as cursor:
                    for user_id in self.test_records['users']:
                        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    for character_id in self.test_records['characters']:
                        cursor.execute("DELETE FROM characters WHERE id = %s", (character_id,))
                    for session_id in self.test_records['sessions']:
                        cursor.execute("DELETE FROM game_sessions WHERE id = %s", (session_id,))
                    conn.commit()
            finally:
                conn.close()

            # Clean up Redis
            r = redis.from_url(self.redis_url)
            for key in r.scan_iter("test:*"):
                r.delete(key)
            for key in r.scan_iter("user:*"):
                r.delete(key)
            for key in r.scan_iter("temp_session:*"):
                r.delete(key)

            # Reset test records
            self.test_records = {
                'users': [],
                'characters': [],
                'sessions': [],
                'messages': []
            }

            self.logger.info("Test data cleanup completed")

        except Exception as e:
            self.logger.error(f"Test data cleanup failed: {e}")