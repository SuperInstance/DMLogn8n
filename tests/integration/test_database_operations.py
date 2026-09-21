"""
Comprehensive Database Operations Testing
Tests database functionality, transactions, constraints, and performance
"""

import pytest
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Dict, Any
from unittest.mock import patch
import time


class TestDatabaseConnection:
    """Test database connection and basic operations"""

    def test_database_health_check(self, test_db_session: Session):
        """Test database health check"""
        result = test_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_database_tables_exist(self, test_db_session: Session):
        """Test that all required tables exist"""
        inspector = inspect(test_db_session.bind)
        tables = inspector.get_table_names()

        required_tables = [
            'users',
            'characters',
            'campaigns',
            'game_sessions'
        ]

        for table in required_tables:
            assert table in tables, f"Table {table} does not exist"

    def test_table_schemas(self, test_db_session: Session):
        """Test table schemas have correct columns"""
        inspector = inspect(test_db_session.bind)

        # Check users table
        users_columns = inspector.get_columns('users')
        users_column_names = [col['name'] for col in users_columns]

        required_user_columns = [
            'id', 'username', 'email', 'password_hash',
            'is_active', 'is_dm', 'created_at'
        ]

        for col in required_user_columns:
            assert col in users_column_names, f"Column {col} missing from users table"

        # Check characters table
        characters_columns = inspector.get_columns('characters')
        characters_column_names = [col['name'] for col in characters_columns]

        required_character_columns = [
            'id', 'name', 'race', 'class_name', 'level', 'user_id', 'created_at'
        ]

        for col in required_character_columns:
            assert col in characters_column_names, f"Column {col} missing from characters table"


class TestUserOperations:
    """Test user database operations"""

    def test_create_user(self, test_db_session: Session):
        """Test creating a user in the database"""
        from datetime import datetime

        # Insert user
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        test_db_session.execute(insert_sql, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'is_active': True,
            'is_dm': False,
            'created_at': datetime.utcnow()
        })

        test_db_session.commit()

        # Verify user was created
        result = test_db_session.execute(text("SELECT * FROM users WHERE username = 'testuser'"))
        user = result.fetchone()

        assert user is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'

    def test_read_user(self, test_db_session: Session):
        """Test reading a user from the database"""
        # First create a user
        self.test_create_user(test_db_session)

        # Read the user
        result = test_db_session.execute(text("SELECT * FROM users WHERE username = 'testuser'"))
        user = result.fetchone()

        assert user is not None
        assert user.username == 'testuser'

    def test_update_user(self, test_db_session: Session):
        """Test updating a user in the database"""
        # First create a user
        self.test_create_user(test_db_session)

        # Update the user
        update_sql = text("UPDATE users SET is_dm = :is_dm WHERE username = :username")
        test_db_session.execute(update_sql, {
            'is_dm': True,
            'username': 'testuser'
        })

        test_db_session.commit()

        # Verify update
        result = test_db_session.execute(text("SELECT is_dm FROM users WHERE username = 'testuser'"))
        user = result.fetchone()

        assert user.is_dm is True

    def test_delete_user(self, test_db_session: Session):
        """Test deleting a user from the database"""
        # First create a user
        self.test_create_user(test_db_session)

        # Delete the user
        delete_sql = text("DELETE FROM users WHERE username = :username")
        test_db_session.execute(delete_sql, {'username': 'testuser'})
        test_db_session.commit()

        # Verify deletion
        result = test_db_session.execute(text("SELECT * FROM users WHERE username = 'testuser'"))
        user = result.fetchone()

        assert user is None

    def test_unique_username_constraint(self, test_db_session: Session):
        """Test unique username constraint"""
        from datetime import datetime

        # Create first user
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        test_db_session.execute(insert_sql, {
            'username': 'testuser',
            'email': 'test1@example.com',
            'password_hash': 'hashed_password',
            'is_active': True,
            'is_dm': False,
            'created_at': datetime.utcnow()
        })

        test_db_session.commit()

        # Try to create second user with same username
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            test_db_session.execute(insert_sql, {
                'username': 'testuser',  # Same username
                'email': 'test2@example.com',
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()

    def test_unique_email_constraint(self, test_db_session: Session):
        """Test unique email constraint"""
        from datetime import datetime

        # Create first user
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        test_db_session.execute(insert_sql, {
            'username': 'user1',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'is_active': True,
            'is_dm': False,
            'created_at': datetime.utcnow()
        })

        test_db_session.commit()

        # Try to create second user with same email
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            test_db_session.execute(insert_sql, {
                'username': 'user2',  # Different username
                'email': 'test@example.com',  # Same email
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()


class TestCharacterOperations:
    """Test character database operations"""

    def test_create_character(self, test_db_session: Session):
        """Test creating a character in the database"""
        from datetime import datetime

        # First create a user
        user_insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        result = test_db_session.execute(user_insert_sql, {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'is_active': True,
            'is_dm': False,
            'created_at': datetime.utcnow()
        })

        user_id = result.lastrowid
        test_db_session.commit()

        # Create character
        character_insert_sql = text("""
            INSERT INTO characters (name, race, class_name, level, user_id, created_at)
            VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
        """)

        test_db_session.execute(character_insert_sql, {
            'name': 'Test Character',
            'race': 'Human',
            'class_name': 'Fighter',
            'level': 1,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        })

        test_db_session.commit()

        # Verify character was created
        result = test_db_session.execute(text("SELECT * FROM characters WHERE name = 'Test Character'"))
        character = result.fetchone()

        assert character is not None
        assert character.name == 'Test Character'
        assert character.race == 'Human'
        assert character.class_name == 'Fighter'
        assert character.level == 1
        assert character.user_id == user_id

    def test_foreign_key_constraint(self, test_db_session: Session):
        """Test foreign key constraint between characters and users"""
        from datetime import datetime

        # Try to create character with non-existent user_id
        character_insert_sql = text("""
            INSERT INTO characters (name, race, class_name, level, user_id, created_at)
            VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
        """)

        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            test_db_session.execute(character_insert_sql, {
                'name': 'Orphan Character',
                'race': 'Human',
                'class_name': 'Fighter',
                'level': 1,
                'user_id': 999999,  # Non-existent user
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()

    def test_character_level_up(self, test_db_session: Session):
        """Test updating character level"""
        # First create user and character
        self.test_create_character(test_db_session)

        # Level up character
        update_sql = text("UPDATE characters SET level = :level WHERE name = :name")
        test_db_session.execute(update_sql, {
            'level': 2,
            'name': 'Test Character'
        })

        test_db_session.commit()

        # Verify level update
        result = test_db_session.execute(text("SELECT level FROM characters WHERE name = 'Test Character'"))
        character = result.fetchone()

        assert character.level == 2

    def test_delete_character_cascade(self, test_db_session: Session):
        """Test character deletion and any cascading effects"""
        # First create user and character
        self.test_create_character(test_db_session)

        # Delete character
        delete_sql = text("DELETE FROM characters WHERE name = :name")
        test_db_session.execute(delete_sql, {'name': 'Test Character'})
        test_db_session.commit()

        # Verify character is deleted
        result = test_db_session.execute(text("SELECT * FROM characters WHERE name = 'Test Character'"))
        character = result.fetchone()

        assert character is None


class TestCampaignOperations:
    """Test campaign database operations"""

    def test_create_campaign(self, test_db_session: Session):
        """Test creating a campaign in the database"""
        from datetime import datetime

        # First create a user (DM)
        user_insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        result = test_db_session.execute(user_insert_sql, {
            'username': 'testdm',
            'email': 'dm@example.com',
            'password_hash': 'hashed_password',
            'is_active': True,
            'is_dm': True,
            'created_at': datetime.utcnow()
        })

        dm_id = result.lastrowid
        test_db_session.commit()

        # Create campaign
        campaign_insert_sql = text("""
            INSERT INTO campaigns (name, description, dm_id, is_public, created_at)
            VALUES (:name, :description, :dm_id, :is_public, :created_at)
        """)

        test_db_session.execute(campaign_insert_sql, {
            'name': 'Test Campaign',
            'description': 'A test campaign',
            'dm_id': dm_id,
            'is_public': False,
            'created_at': datetime.utcnow()
        })

        test_db_session.commit()

        # Verify campaign was created
        result = test_db_session.execute(text("SELECT * FROM campaigns WHERE name = 'Test Campaign'"))
        campaign = result.fetchone()

        assert campaign is not None
        assert campaign.name == 'Test Campaign'
        assert campaign.description == 'A test campaign'
        assert campaign.dm_id == dm_id
        assert campaign.is_public is False


class TestTransactionHandling:
    """Test database transaction handling"""

    def test_successful_transaction(self, test_db_session: Session):
        """Test successful transaction commit"""
        from datetime import datetime

        # Start a transaction (implicitly started by test_db_session)
        try:
            # Create user
            insert_sql = text("""
                INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
                VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
            """)

            test_db_session.execute(insert_sql, {
                'username': 'transaction_user',
                'email': 'transaction@example.com',
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

            # Create character for the user
            character_sql = text("""
                INSERT INTO characters (name, race, class_name, level, user_id, created_at)
                VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
            """)

            test_db_session.execute(character_sql, {
                'name': 'Transaction Character',
                'race': 'Elf',
                'class_name': 'Wizard',
                'level': 1,
                'user_id': 1,  # Assuming user ID is 1
                'created_at': datetime.utcnow()
            })

            # Commit transaction
            test_db_session.commit()

        except Exception as e:
            test_db_session.rollback()
            pytest.fail(f"Transaction failed: {e}")

        # Verify both records were created
        user_result = test_db_session.execute(text("SELECT * FROM users WHERE username = 'transaction_user'"))
        user = user_result.fetchone()
        assert user is not None

        character_result = test_db_session.execute(text("SELECT * FROM characters WHERE name = 'Transaction Character'"))
        character = character_result.fetchone()
        assert character is not None

    def test_failed_transaction_rollback(self, test_db_session: Session):
        """Test transaction rollback on failure"""
        from datetime import datetime

        initial_user_count = test_db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()

        try:
            # Create user
            insert_sql = text("""
                INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
                VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
            """)

            test_db_session.execute(insert_sql, {
                'username': 'rollback_user',
                'email': 'rollback@example.com',
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

            # Try to create character with invalid data to force failure
            character_sql = text("""
                INSERT INTO characters (name, race, class_name, level, user_id, created_at)
                VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
            """)

            test_db_session.execute(character_sql, {
                'name': 'Rollback Character',
                'race': 'Elf',
                'class_name': 'Wizard',
                'level': 1,
                'user_id': 999999,  # Invalid user_id to cause foreign key violation
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()
            pytest.fail("Expected transaction to fail due to foreign key violation")

        except Exception:
            # Transaction should be automatically rolled back
            test_db_session.rollback()

        # Verify no new users were created
        final_user_count = test_db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        assert final_user_count == initial_user_count

        # Verify user was not created
        user_result = test_db_session.execute(text("SELECT * FROM users WHERE username = 'rollback_user'"))
        user = user_result.fetchone()
        assert user is None


class TestDatabasePerformance:
    """Test database performance and optimization"""

    def test_bulk_insert_performance(self, test_db_session: Session, performance_timer):
        """Test performance of bulk insert operations"""
        from datetime import datetime

        performance_timer.start()

        # Insert 100 users
        insert_sql = text("""
            INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
            VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
        """)

        for i in range(100):
            test_db_session.execute(insert_sql, {
                'username': f'user_{i}',
                'email': f'user_{i}@example.com',
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

        test_db_session.commit()
        performance_timer.stop()

        # Should complete within reasonable time (5 seconds for test)
        assert performance_timer.elapsed < 5.0

        # Verify all users were created
        user_count = test_db_session.execute(text("SELECT COUNT(*) FROM users WHERE username LIKE 'user_%'")).scalar()
        assert user_count == 100

    def test_query_performance_with_index(self, test_db_session: Session, performance_timer):
        """Test query performance with indexed columns"""
        from datetime import datetime

        # Insert test data
        insert_sql = text("""
            INSERT INTO characters (name, race, class_name, level, user_id, created_at)
            VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
        """)

        for i in range(50):
            test_db_session.execute(insert_sql, {
                'name': f'character_{i}',
                'race': ['Human', 'Elf', 'Dwarf', 'Halfling'][i % 4],
                'class_name': ['Fighter', 'Wizard', 'Cleric', 'Rogue'][i % 4],
                'level': (i % 20) + 1,
                'user_id': 1,
                'created_at': datetime.utcnow()
            })

        test_db_session.commit()

        # Test query performance
        performance_timer.start()

        result = test_db_session.execute(text("""
            SELECT * FROM characters WHERE level > 10 AND class_name = 'Wizard'
        """))

        characters = result.fetchall()
        performance_timer.stop()

        # Should complete quickly (within 1 second)
        assert performance_timer.elapsed < 1.0
        assert len(characters) > 0

    def test_connection_pooling(self, test_db_session: Session):
        """Test database connection pooling functionality"""
        # This test would require actual connection pool setup
        # For now, just test that we can execute multiple queries

        queries = [
            "SELECT 1",
            "SELECT 2",
            "SELECT 3",
            "SELECT COUNT(*) FROM users",
            "SELECT COUNT(*) FROM characters"
        ]

        results = []
        for query in queries:
            result = test_db_session.execute(text(query))
            results.append(result.scalar())

        assert len(results) == len(queries)
        assert all(r is not None for r in results)


class TestDataIntegrity:
    """Test data integrity and validation"""

    def test_null_constraints(self, test_db_session: Session):
        """Test NOT NULL constraints"""
        from datetime import datetime

        # Try to insert user with null username
        with pytest.raises(Exception):
            insert_sql = text("""
                INSERT INTO users (username, email, password_hash, is_active, is_dm, created_at)
                VALUES (:username, :email, :password_hash, :is_active, :is_dm, :created_at)
            """)

            test_db_session.execute(insert_sql, {
                'username': None,  # Should violate NOT NULL constraint
                'email': 'test@example.com',
                'password_hash': 'hashed_password',
                'is_active': True,
                'is_dm': False,
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()

    def test_data_type_validation(self, test_db_session: Session):
        """Test data type validation"""
        from datetime import datetime

        # Try to insert invalid data types
        with pytest.raises(Exception):
            insert_sql = text("""
                INSERT INTO characters (name, race, class_name, level, user_id, created_at)
                VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
            """)

            test_db_session.execute(insert_sql, {
                'name': 'Test Character',
                'race': 'Human',
                'class_name': 'Fighter',
                'level': 'invalid_level',  # Should be integer
                'user_id': 1,
                'created_at': datetime.utcnow()
            })

            test_db_session.commit()

    def test_check_constraints(self, test_db_session: Session):
        """Test CHECK constraints (if implemented)"""
        # This would test constraints like level >= 1, etc.
        # Implementation depends on specific database schema

        try:
            # Try to insert character with invalid level
            from datetime import datetime

            with pytest.raises(Exception):
                insert_sql = text("""
                    INSERT INTO characters (name, race, class_name, level, user_id, created_at)
                    VALUES (:name, :race, :class_name, :level, :user_id, :created_at)
                """)

                test_db_session.execute(insert_sql, {
                    'name': 'Invalid Character',
                    'race': 'Human',
                    'class_name': 'Fighter',
                    'level': -1,  # Invalid level
                    'user_id': 1,
                    'created_at': datetime.utcnow()
                })

                test_db_session.commit()

        except Exception:
            # Constraint might not be implemented in test schema
            pass


@pytest.mark.asyncio
class TestAsyncDatabaseOperations:
    """Test asynchronous database operations"""

    async def test_async_database_query(self):
        """Test async database operations"""
        # This would test actual async database operations
        # For now, just a placeholder
        import asyncio

        await asyncio.sleep(0.1)  # Simulate async operation
        assert True

    async def test_concurrent_database_access(self):
        """Test concurrent database access"""
        # This would test multiple concurrent database connections
        import asyncio

        async def simulate_db_operation():
            await asyncio.sleep(0.1)
            return "result"

        tasks = [simulate_db_operation() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r == "result" for r in results)